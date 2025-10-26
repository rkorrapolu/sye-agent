#!/bin/bash
set -e

# Load environment variables
if [ -f /sye/mami/.env ]; then
  echo "Loading environment variables from .env..."
  export $(grep -v '^#' /sye/mami/.env | xargs)
else
  echo "Warning: .env file not found at /sye/mami/.env"
fi

# Set defaults if not provided
export REDIS_PORT=${REDIS_PORT:-6379}
export NEO4J_USERNAME=${NEO4J_USERNAME:-neo4j}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-hackathon2024}

# Print loaded variables for debugging
echo "Environment variables loaded:"
env | grep -E "^(REDIS_|NEO4J_|OPENAI_|GOOGLE_|ANTHROPIC_)" | cut -d= -f1 | sort

# Force complete Neo4j password reset
if [ -n "$NEO4J_PASSWORD" ]; then
  echo "Forcing Neo4j password reset to: ${NEO4J_PASSWORD}"
  rm -rf "$NEO4J_HOME/data/dbms/auth"
  rm -rf "$NEO4J_HOME/data/databases/system"
  mkdir -p "$NEO4J_HOME/data/dbms"
  mkdir -p "$NEO4J_HOME/data/databases"
fi

# Generate supervisord configuration dynamically
echo "Creating supervisord configuration..."
mkdir -p /etc/supervisor/conf.d
cat > /etc/supervisor/conf.d/supervisord.conf <<EOF
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[unix_http_server]
file=/var/run/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[program:redis]
command=/usr/local/bin/redis-stack-server --bind 0.0.0.0 --port ${REDIS_PORT} --protected-mode no --daemonize no --loadmodule /opt/redis-stack/lib/redisearch.so --loadmodule /opt/redis-stack/lib/rejson.so --loadmodule /opt/redis-stack/lib/redistimeseries.so --loadmodule /opt/redis-stack/lib/redisbloom.so
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
priority=1

[program:neo4j]
command=bash -c 'export NEO4J_AUTH="${NEO4J_USERNAME}/${NEO4J_PASSWORD}" && /var/lib/neo4j/bin/neo4j console'
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
priority=2

[program:mami]
command=/sye/mami/.venv/bin/python main.py
directory=/sye/mami
autostart=false
autorestart=false
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
priority=3
environment=PYTHONUNBUFFERED="1"
EOF

# Verify config file was created
if [ -f /etc/supervisor/conf.d/supervisord.conf ]; then
  echo "✅ Supervisord configuration created successfully"
  echo "Config file contents:"
  cat /etc/supervisor/conf.d/supervisord.conf
else
  echo "❌ Failed to create supervisord configuration"
  exit 1
fi

# Start supervisord
echo "Starting supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

