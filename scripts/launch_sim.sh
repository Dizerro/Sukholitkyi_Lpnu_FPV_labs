#!/usr/bin/env bash
cd "$(dirname "$0")/.."
docker compose exec sim bash -lc \
  "source /opt/ros/humble/setup.bash && source /opt/ardu_ws/install/setup.bash && export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:/opt/ardu_ws/install/ardupilot_gazebo/share && ros2 launch ardupilot_gz_bringup iris_maze.launch.py"
