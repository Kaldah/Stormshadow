#!/bin/sh

set -e

cleanup() {
  echo "[*] Cleaning up..."

  # Remove the Docker container if running/stopped
  if sudo docker ps -a --format '{{.Names}}' | grep -q "^sip-victim$"; then
    echo "[*] Removing existing container 'sip-victim'..."
    sudo docker rm -f sip-victim
  fi

  echo "[*] Cleanup complete."
}

trap cleanup EXIT INT TERM

# Initial cleanup before run (avoid leftovers)
cleanup

echo "[*] Starting Docker container..."

sudo docker run --rm -it \
  --network host \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  -v "$(pwd)/scripts:/opt/scripts" \
  --name sip-victim \
  asterisk-sip-server

# When container exits, the trap above will run cleanup again
