#!/bin/bash

echo "🔌 Starting SYE MCP Servers..."

# Create logs directory
mkdir -p /workspace/logs

# Kill any existing MCP servers
pkill -f "mcp-neo4j-server.js" 2>/dev/null || true
pkill -f "mcp-composio-server.js" 2>/dev/null || true

# Wait for databases to be ready
echo "⏳ Waiting for Neo4j and Redis..."
until curl -f http://neo4j:7474/browser/ > /dev/null 2>&1; do
    echo "Waiting for Neo4j..."
    sleep 2
done

until redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Waiting for Redis..."
    sleep 2
done

echo "✅ Databases ready!"

# Set environment variables
export NEO4J_URI="bolt://neo4j:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password123"
export REDIS_URL="redis://redis:6379"

# Start Neo4j MCP server
echo "🧠 Starting Neo4j MCP server..."
cd /workspace
nohup node .devcontainer/mcp-neo4j-server.js > logs/mcp-neo4j.log 2>&1 &
NEO4J_MCP_PID=$!

# Start Composio MCP server  
echo "🔧 Starting Composio MCP server..."
nohup node .devcontainer/mcp-composio-server.js > logs/mcp-composio.log 2>&1 &
COMPOSIO_MCP_PID=$!

# Wait a moment for servers to start
sleep 3

# Check if servers are running
if ps -p $NEO4J_MCP_PID > /dev/null; then
    echo "✅ Neo4j MCP server running (PID: $NEO4J_MCP_PID)"
else
    echo "❌ Neo4j MCP server failed to start"
    cat logs/mcp-neo4j.log
fi

if ps -p $COMPOSIO_MCP_PID > /dev/null; then
    echo "✅ Composio MCP server running (PID: $COMPOSIO_MCP_PID)"
else
    echo "❌ Composio MCP server failed to start"
    cat logs/mcp-composio.log
fi

echo "🎉 MCP servers startup complete!"
echo "📋 Server status:"
ps aux | grep -E "(mcp-neo4j|mcp-composio)" | grep -v grep || echo "No MCP servers found"

# Save PIDs for later cleanup
echo $NEO4J_MCP_PID > /tmp/mcp-neo4j.pid
echo $COMPOSIO_MCP_PID > /tmp/mcp-composio.pid