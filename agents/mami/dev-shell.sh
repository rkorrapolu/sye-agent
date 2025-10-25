#!/usr/bin/env bash
set -euo pipefail

# Ensure logs directory exists
mkdir -p /var/log/supervisor

# Start supervisord in the background (Redis + Neo4j + app)
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf &
SUP_PID=$!

echo "Services starting (supervisord pid=$SUP_PID). Waiting briefly..."
sleep 3

# Show service status
ps aux | grep -E "redis-server|neo4j|supervisord" | grep -v grep || true

# Drop into interactive shell with uv on PATH
export PATH="/sye/mami/.venv/bin:$PATH:/root/.local/bin:$PATH"
cd /sye/mami
exec bash -l
