#!/usr/bin/env bash
# Stop everything (Gazebo, SITL, RViz); keeps the container
cd "$(dirname "$0")/.."
docker compose stop
