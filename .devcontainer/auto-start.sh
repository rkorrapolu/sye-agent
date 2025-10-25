#!/bin/bash

echo "🚀 SYE Agent Auto-Start Initialization"

# Set PATH for Claude Code
export PATH="/home/vscode/.local/bin:$PATH"
echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> ~/.bashrc

# Wait for databases
echo "⏳ Waiting for databases..."
until curl -f http://neo4j:7474/browser/ > /dev/null 2>&1; do
    echo "Waiting for Neo4j..."
    sleep 2
done

until redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Waiting for Redis..."
    sleep 2
done

echo "✅ Databases ready!"

# Start MCP servers
echo "🧠 Starting MCP servers..."
cd /workspace

# Kill any existing servers
pkill -f "simple-mcp-neo4j.js" 2>/dev/null || true

# Start Neo4j MCP server
nohup node .devcontainer/simple-mcp-neo4j.js > logs/mcp-neo4j.log 2>&1 &
MCP_PID=$!

# Wait for server to start
sleep 3

# Verify server is running
if curl -s http://localhost:3001/health > /dev/null; then
    echo "✅ Neo4j MCP server running (PID: $MCP_PID)"
else
    echo "❌ Neo4j MCP server failed to start"
    cat logs/mcp-neo4j.log 2>/dev/null || echo "No log file found"
fi

# Create symlink for easy access to tools
ln -sf /workspace/.devcontainer/sye-tools.sh /workspace/sye-tools
chmod +x /workspace/sye-tools

echo "🎉 SYE Agent Ready!"
echo ""
echo "📋 Available Commands:"
echo "  • ./sye-tools where-are-we  - Get current context"
echo "  • ./sye-tools examples      - Show example usage"
echo "  • ~/.local/bin/claude --dangerously-skip-permissions  - Start Claude Code"
echo ""
echo "🧠 Knowledge Graph Tools:"
echo "  • Neo4j Browser: http://localhost:7474 (neo4j/password123)"
echo "  • MCP Server: http://localhost:3001"
echo ""

# Test the setup
echo "🧪 Testing setup..."
./sye-tools health

echo "✨ Ready for reasoning! Try: ./sye-tools where-are-we"