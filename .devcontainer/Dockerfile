FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for MCP servers
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Claude Code CLI properly
RUN mkdir -p /home/vscode/.local/bin && \
    curl -fsSL https://claude.ai/install.sh | bash -s -- --bin-dir=/home/vscode/.local/bin || \
    curl -fsSL https://claude.ai/install.sh | bash && \
    cp ~/.local/bin/claude /home/vscode/.local/bin/ 2>/dev/null || \
    echo "Claude Code installation attempted" && \
    echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> /home/vscode/.bashrc

# Install Python dependencies for MCP and Neo4j
RUN pip install --no-cache-dir \
    neo4j>=6.0.0 \
    redis>=7.0.0 \
    fastapi>=0.115.0 \
    httpx>=0.28.0 \
    pydantic>=2.0.0 \
    python-dotenv>=1.0.0 \
    sentence-transformers>=2.0.0 \
    numpy>=1.24.0

# Install available MCP servers (some may not exist yet)
RUN npm install -g @anthropic/mcp-server-filesystem || echo "Some MCP servers not available"

# Create workspace directory
RUN mkdir -p /workspace

# Set working directory
WORKDIR /workspace

# Copy MCP configuration
COPY .devcontainer/mcp-config.json /home/vscode/.config/claude/mcp_config.json
COPY .devcontainer/claude-config.json /home/vscode/.config/claude/config.json

# Set ownership for vscode user
RUN chown -R vscode:vscode /home/vscode/.config

USER vscode