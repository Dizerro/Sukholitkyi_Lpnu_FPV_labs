#!/usr/bin/env bash
# Start the container (does not start the simulator)
set -e
cd "$(dirname "$0")/.."
xhost +local:docker >/dev/null
docker compose up -d
echo "Container is up. Next: ./scripts/launch_sim.sh"
