#!/usr/bin/env bash
set -euo pipefail
IFACE="${1:?Usage: $0 <iface>}"
sudo tc filter del dev "$IFACE" egress prio 1 handle 1 bpf 2>/dev/null || true
sudo tc qdisc del dev "$IFACE" clsact 2>/dev/null || true
# pinned maps are under /sys/fs/bpf/tc/globals/ (auto-managed by tc/libbpf)
echo "[ok] detached from $IFACE"
