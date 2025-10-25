FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
  wget \
  curl \
  gnupg \
  supervisor \
  procps \
  openjdk-21-jre-headless \
  bash \
  docker.io \
  make \
  gcc \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

RUN wget https://download.redis.io/releases/redis-8.0.4.tar.gz \
  && tar xzf redis-8.0.4.tar.gz \
  && cd redis-8.0.4 \
  && make \
  && make install \
  && cd .. \
  && rm -rf redis-8.0.4 redis-8.0.4.tar.gz

ENV NEO4J_VERSION=2025.09.0
ENV NEO4J_HOME=/var/lib/neo4j
ENV NEO4J_AUTH=neo4j/sye2025

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

COPY agent.py redis_client.py tools.py main.py example.py test_setup.py ./
COPY .env ./ 

RUN docker pull ghcr.io/coroot/logparser || echo "Warning: Could not pull logparser image during build"

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Starts services then opens interactive bash
COPY dev-shell.sh /usr/local/bin/dev-shell.sh
RUN chmod +x /usr/local/bin/dev-shell.sh

EXPOSE 5769 7474 7687

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
