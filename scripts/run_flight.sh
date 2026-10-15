#!/usr/bin/env bash
# Usage: ./scripts/run_flight.sh DX DY   (offsets from Table 2.3)
cd "$(dirname "$0")/.."
DX=${1:-4.0}
DY=${2:-0.0}
docker compose exec sim bash -lc \
  "mkdir -p ~/fpv_labs/logs && source /opt/ros/humble/setup.bash && source /opt/ardu_ws/install/setup.bash && source ~/fpv_labs/install/setup.bash && ros2 run fpv_lab2 flight_test --ros-args -p dx:=$DX -p dy:=$DY 2>&1 | tee ~/fpv_labs/logs/flight_\$(date +%Y%m%d_%H%M%S).log"
