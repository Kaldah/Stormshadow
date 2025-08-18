#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:?Usage: $0 <iface>}"

show_state() {
	echo "--- qdisc ---"; tc qdisc show dev "$IFACE" || true
	echo "--- egress filters ---"; tc filter show dev "$IFACE" egress || true
	echo "--- ingress filters ---"; tc filter show dev "$IFACE" ingress || true
}

echo "[i] Before detach state for $IFACE"; show_state

# Try to remove specific bpf filter (prio 1 handle 1) if present
sudo tc filter del dev "$IFACE" egress prio 1 handle 1 bpf 2>/dev/null || true

# Also attempt to delete any remaining bpf filters on egress/ingress defensively
for DIR in egress ingress; do
	# shellcheck disable=SC2016
	while sudo tc filter show dev "$IFACE" "$DIR" 2>/dev/null | grep -q "\bbpf\b"; do
		# Delete the first bpf filter found (best-effort)
		# We can't easily parse prio/handle reliably without awk; try common combos
		sudo tc filter del dev "$IFACE" "$DIR" prio 1 2>/dev/null || true
		sudo tc filter del dev "$IFACE" "$DIR" 2>/dev/null || true
		break
	done
done

# Remove clsact qdisc if present
sudo tc qdisc del dev "$IFACE" clsact 2>/dev/null || true

# Cleanup pinned maps that tc/libbpf may have left around
if [ -d /sys/fs/bpf/tc/globals ]; then
	for m in spoof_cfg spoof_rr; do
		if [ -e "/sys/fs/bpf/tc/globals/$m" ]; then
			sudo rm -f "/sys/fs/bpf/tc/globals/$m" 2>/dev/null || true
		fi
	done
	# try to prune empty dirs (best-effort)
	sudo rmdir /sys/fs/bpf/tc/globals 2>/dev/null || true
	sudo rmdir /sys/fs/bpf/tc 2>/dev/null || true
fi

echo "[i] After detach state for $IFACE"; show_state
echo "[ok] detached from $IFACE"
