"""Semantic cache for Neo4j node queries using RedisVL."""

import json
from typing import Any, Dict, List, Optional

from redisvl.extensions.llmcache import SemanticCache
from redisvl.utils.vectorize import BaseVectorizer

from embedding_utils import get_embedding_generator
from redis_utils import RedisConnection


class CustomVectorizer(BaseVectorizer):
  """Custom vectorizer using sentence-transformers for RedisVL."""

  def __init__(self):
    """Initialize with embedding generator."""
    generator = get_embedding_generator()
    # Initialize parent with model name and dims as integer
    super().__init__(
      model=generator.model_name,
      dims=generator.embedding_dim,  # Pass dims as int, not property
    )
    # Store generator reference for embedding operations
    object.__setattr__(self, "_generator", generator)

  def embed(self, text: str, **kwargs) -> List[float]:
    """Generate embedding for text."""
    embedding = self._generator.embed(text)
    return embedding.tolist()

  def embed_many(self, texts: List[str], **kwargs) -> List[List[float]]:
    """Generate embeddings for multiple texts."""
    embeddings = self._generator.embed_batch(texts)
    return embeddings.tolist()


class Neo4jSemanticCache:
  """Semantic cache for Neo4j node query results."""

  def __init__(self, distance_threshold: float = 0.2):
    """
    Initialize semantic cache.

    Args:
        distance_threshold: Maximum vector distance for cache hit (0.0-1.0)
                          Lower = stricter matching
                          Typical: 0.1-0.3
    """
    self.redis_conn = RedisConnection()
    self.vectorizer = CustomVectorizer()
    self.distance_threshold = distance_threshold

    # Initialize RedisVL semantic cache
    self.cache = SemanticCache(
      name="neo4j_node_cache",
      redis_client=self.redis_conn.get_client(),
      distance_threshold=distance_threshold,
      vectorizer=self.vectorizer,
    )

    print(f"✅ Semantic cache initialized (threshold: {distance_threshold})")

  def check(
    self, query_text: str, node_label: Optional[str] = None
  ) -> Optional[List[Dict[str, Any]]]:
    """
    Check cache for semantically similar queries.

    Args:
        query_text: The query text (e.g., "database connection drops")
        node_label: Optional node label filter (Symptom, Error, Action)

    Returns:
        List of matching nodes if cache hit, None if miss
    """
    # Create cache key with label filter
    cache_key = f"{node_label}:{query_text}" if node_label else query_text

    # Check semantic cache
    result = self.cache.check(prompt=cache_key)

    if result:
      # Parse cached data
      cached_data = result[0]  # RedisVL returns list of matches
      response = cached_data.get("response")

      if response:
        try:
          nodes = json.loads(response)
          print(f"✅ Cache HIT (distance: {cached_data.get('distance', 'N/A')})")
          return nodes
        except json.JSONDecodeError:
          print("⚠️  Cache hit but invalid JSON, treating as miss")
          return None

    print("❌ Cache MISS")
    return None

  def store(
    self, query_text: str, nodes: List[Dict[str, Any]], node_label: Optional[str] = None
  ):
    """
    Store query results in cache.

    Args:
        query_text: The query text
        nodes: List of Neo4j nodes that matched
        node_label: Optional node label filter
    """
    # Create cache key with label filter
    cache_key = f"{node_label}:{query_text}" if node_label else query_text

    # Serialize nodes to JSON
    response = json.dumps(nodes)

    # Store in cache
    self.cache.store(prompt=cache_key, response=response)

    print(f"✅ Stored {len(nodes)} nodes in cache")

  def clear(self):
    """Clear all cached data."""
    self.cache.clear()
    print("✅ Cache cleared")

  def stats(self) -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats (size, hit rate, etc.)
    """
    # Get index info from Redis
    client = self.redis_conn.get_client()
    info = client.info()

    return {
      "redis_memory_used": info.get("used_memory_human", "N/A"),
      "redis_connected_clients": info.get("connected_clients", 0),
      "cache_threshold": self.distance_threshold,
      "embedding_dimensions": self.vectorizer.dims,
    }


# Global cache instance
_semantic_cache: Optional[Neo4jSemanticCache] = None


def get_semantic_cache() -> Neo4jSemanticCache:
  """
  Get or create global semantic cache instance.

  Returns:
      Singleton Neo4jSemanticCache instance
  """
  global _semantic_cache
  if _semantic_cache is None:
    _semantic_cache = Neo4jSemanticCache(distance_threshold=0.2)
  return _semantic_cache
