#!/bin/bash
set -e

echo "🚀 Setting up SYE Claude Reasoning Layer..."

# Create necessary directories
mkdir -p /home/vscode/.config/claude
mkdir -p /workspace/knowledge_graph
mkdir -p /workspace/logs

# Install additional Python packages
pip install --user \
    langchain>=0.1.0 \
    langchain-community>=0.0.20 \
    chromadb>=0.4.0

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
until curl -f http://neo4j:7474/browser/ > /dev/null 2>&1; do
    echo "Waiting for Neo4j..."
    sleep 2
done

# Wait for Redis to be ready  
echo "⏳ Waiting for Redis to be ready..."
until redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Waiting for Redis..."
    sleep 2
done

# Initialize Neo4j with basic constraints
echo "🗄️ Initializing Neo4j schema..."
python3 /workspace/.devcontainer/init_neo4j.py

# Start MCP servers in background
echo "🔌 Starting MCP servers..."
nohup node /workspace/.devcontainer/mcp-neo4j-server.js > /workspace/logs/mcp-neo4j.log 2>&1 &
nohup node /workspace/.devcontainer/mcp-composio-server.js > /workspace/logs/mcp-composio.log 2>&1 &

echo "✅ SYE Claude Reasoning Layer setup complete!"

# Run auto-start script
/workspace/.devcontainer/auto-start.sh

echo "🔗 Neo4j Browser: http://localhost:7474"
echo "📊 Redis: redis://localhost:6379"
echo "🧠 Claude Code ready with --dangerously-skip-permissions"
echo ""
echo "Try: ./sye-tools where-are-we"