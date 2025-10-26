#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t sye-agent-mami:latest .

echo "Removing existing container (if any)..."
docker rm -f sye-mami 2>/dev/null || true

echo "Starting container in interactive mode..."
docker run -it --name sye-mami \
  -p 6379:6379 \
  -p 7474:7474 \
  -p 7687:7687 \
  sye-agent-mami:latest /usr/local/bin/dev-shell.sh

echo "Container stopped."
