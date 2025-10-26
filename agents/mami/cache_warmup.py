"""Warm up semantic cache with existing Neo4j nodes."""

from neo4j_utils import Neo4jConnection
from semantic_cache import get_semantic_cache


def warmup_cache():
  """
  Load all existing Neo4j nodes into semantic cache.

  This improves cache hit rate for existing knowledge.
  """
  print("Starting cache warmup...")

  conn = Neo4jConnection()
  cache = get_semantic_cache()

  # Get all nodes grouped by label
  query = """
    MATCH (n)
    WHERE n.name IS NOT NULL
    RETURN labels(n)[0] as label,
           id(n) as node_id,
           n.name as name,
           n.created_at as created_at,
           n.times_seen as times_seen
    ORDER BY label, n.times_seen DESC
    """

  results = conn.execute_query(query)
  conn.close()

  if not results:
    print("No existing nodes found in Neo4j")
    return

  # Group by label
  by_label = {}
  for r in results:
    label = r["label"]
    if label not in by_label:
      by_label[label] = []

    by_label[label].append(
      {
        "node_id": r["node_id"],
        "name": r["name"],
        "created_at": r["created_at"],
        "times_seen": r.get("times_seen", 1),
      }
    )

  # Store in cache
  total_stored = 0
  for label, nodes in by_label.items():
    for node in nodes:
      # Store individual nodes in cache
      cache.store(query_text=node["name"], nodes=[node], node_label=label)
      total_stored += 1

  print(f"✅ Cache warmed up with {total_stored} nodes from Neo4j")
  print(f"   Labels: {list(by_label.keys())}")
  print(f"   Breakdown: {[(l, len(n)) for l, n in by_label.items()]}")


if __name__ == "__main__":
  warmup_cache()
