#!/usr/bin/env bash
# Remove the container completely (the image and your files stay)
cd "$(dirname "$0")/.."
docker compose down
