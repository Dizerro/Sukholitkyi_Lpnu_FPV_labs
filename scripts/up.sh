#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
xhost +local:docker >/dev/null
docker compose up -d
echo "Container is up. Next: ./scripts/launch_sim.sh"
