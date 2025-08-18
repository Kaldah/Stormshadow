#!/usr/bin/env bash
set -euo pipefail
IFACE="${1:?Usage: $0 <iface>}"

echo "== qdisc on $IFACE =="
tc qdisc show dev "$IFACE" || true

echo "\n== egress filters =="
tc filter show dev "$IFACE" egress || true

echo "\n== ingress filters =="
tc filter show dev "$IFACE" ingress || true

echo "\n== pinned maps =="
if [ -d /sys/fs/bpf/tc/globals ]; then
  ls -l /sys/fs/bpf/tc/globals || true
  for m in spoof_cfg spoof_rr; do
    p="/sys/fs/bpf/tc/globals/$m"
    if [ -e "$p" ]; then
      echo "-- dump $m --"
      sudo bpftool map dump pinned "$p" || true
    fi
  done
else
  echo "(none)"
fi

echo "\n== bpftool net =="
bpftool net || true
