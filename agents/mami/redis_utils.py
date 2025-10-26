"""Redis utilities for semantic caching."""

import os
from typing import Optional

import redis
from dotenv import load_dotenv

load_dotenv()


class RedisConnection:
  """Manages Redis database connection."""

  def __init__(self):
    """Initialize connection using environment variables."""
    self.host = os.getenv("REDIS_HOST", "localhost")
    self.port = int(os.getenv("REDIS_PORT", 6379))
    self.password = os.getenv("REDIS_PASSWORD", "")
    self.db = int(os.getenv("REDIS_DB", 0))
    self.client: Optional[redis.Redis] = None
    self._connect()

  def _connect(self):
    """Establish connection to Redis."""
    try:
      # Only pass password if it's not empty
      connection_params = {
        "host": self.host,
        "port": self.port,
        "db": self.db,
        "decode_responses": True,
      }

      # Only add password if it's actually set
      if self.password:
        connection_params["password"] = self.password

      self.client = redis.Redis(**connection_params)

      # Verify connectivity
      self.client.ping()
      print(f"✅ Connected to Redis at {self.host}:{self.port}")
    except redis.ConnectionError as e:
      print(f"❌ Failed to connect to Redis: {e}")
      print("Make sure Redis is running: docker-compose up -d")
      raise

  def close(self):
    """Close the Redis connection."""
    if self.client:
      self.client.close()
      print("Redis connection closed")

  def get_client(self) -> redis.Redis:
    """Get the Redis client instance."""
    return self.client
