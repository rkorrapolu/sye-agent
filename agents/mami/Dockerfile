FROM redis/redis-stack-server:latest AS redis-builder

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=redis-builder /opt/redis-stack /opt/redis-stack

# Base dependencies
RUN apt-get update && apt-get install -y \
  wget \
  curl \
  supervisor \
  procps \
  openjdk-21-jre-headless \
  bash \
  docker.io \
  && rm -rf /var/lib/apt/lists/*

# Symlink Redis Stack binaries
RUN ln -s /opt/redis-stack/bin/redis-server /usr/local/bin/redis-stack-server \
  && ln -s /opt/redis-stack/bin/redis-cli /usr/local/bin/redis-cli

ENV NEO4J_VERSION=2025.09.0
ENV NEO4J_HOME=/var/lib/neo4j

RUN wget https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz \
  && tar -xzf neo4j-community-${NEO4J_VERSION}-unix.tar.gz \
  && mv neo4j-community-${NEO4J_VERSION} ${NEO4J_HOME} \
  && rm neo4j-community-${NEO4J_VERSION}-unix.tar.gz

# Configure Neo4j
RUN echo "server.default_listen_address=0.0.0.0" >> ${NEO4J_HOME}/conf/neo4j.conf \
  && echo "server.bolt.listen_address=0.0.0.0:7687" >> ${NEO4J_HOME}/conf/neo4j.conf \
  && echo "server.http.listen_address=0.0.0.0:7474" >> ${NEO4J_HOME}/conf/neo4j.conf

RUN mkdir -p /var/log/supervisor

WORKDIR /sye/mami

COPY pyproject.toml .python-version ./
COPY uv.lock ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY agent.py redis_client.py tools.py main.py example.py test_setup.py \
  cache_warmup.py embedding_utils.py neo4j_tool.py neo4j_utils.py \
  redis_utils.py semantic_cache.py ./
COPY .env ./ 

RUN docker pull ghcr.io/coroot/logparser || echo "Warning: Could not pull logparser image during build"

# Copy entrypoint script that generates supervisord config and starts services
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Starts services then opens interactive bash
COPY dev-shell.sh /usr/local/bin/dev-shell.sh
RUN chmod +x /usr/local/bin/dev-shell.sh

EXPOSE 6379 7474 7687

# Use entrypoint script to load .env and start supervisord
CMD ["/usr/local/bin/entrypoint.sh"]
