#!/usr/bin/env python3
"""
Example usage of the MultiModelClassifier
"""

import json

from agent import MultiModelClassifier
from redis_client import RedisClient


def example_log_classification():
  """Example: Classify a production log entry"""
  print("\n" + "=" * 60)
  print("Example 1: Log Entry Classification")
  print("=" * 60 + "\n")

  classifier = MultiModelClassifier()

  log_input = """2024-10-25 10:23:45 ERROR [database] Query timeout after 30s
Connection pool exhausted, 50/50 connections in use
Blocked on: SELECT * FROM orders WHERE status = 'pending'"""

  result = classifier.classify(log_input)

  print("\n📊 Classification Object:")
  print(f"  Classification ID: {result['classification_id']}")

  print("\n  Symptom:")
  print(f"    Text: {result['symptom']['text']}")
  print(f"    Confidence: {result['symptom']['confidence']}")
  print(f"    Models: {', '.join(result['symptom']['model_consensus'])}")

  print("\n  Cause:")
  print(f"    Text: {result['cause']['text']}")
  print(f"    Confidence: {result['cause']['confidence']}")
  print(f"    Models: {', '.join(result['cause']['model_consensus'])}")

  print("\n  Action:")
  print(f"    Text: {result['action']['text']}")
  print(f"    Confidence: {result['action']['confidence']}")
  print(f"    Models: {', '.join(result['action']['model_consensus'])}")

  print("\n  Model Opinions:")
  print("\n    GPT-5 Response:")
  print(f"      {json.dumps(result['gpt_opinion'], indent=6)}")
  print("\n    Gemini Response:")
  print(f"      {json.dumps(result['gemini_opinion'], indent=6)}")
  print("\n    Claude Final Decision:")
  print(f"      {json.dumps(result.get('claude_decision', {}), indent=6)}")


def example_text_classification():
  """Example: Classify plain text error description"""
  print("\n" + "=" * 60)
  print("Example 2: Plain Text Classification")
  print("=" * 60 + "\n")

  classifier = MultiModelClassifier()

  text_input = "High CPU usage after deploying new model version. Latency increased from 100ms to 2000ms."

  result = classifier.classify(text_input)

  print("\n📊 Classification Object:")
  print(f"  Classification ID: {result['classification_id']}")

  print("\n  Symptom:")
  print(f"    Text: {result['symptom']['text']}")
  print(f"    Confidence: {result['symptom']['confidence']}")
  print(f"    Models: {', '.join(result['symptom']['model_consensus'])}")

  print("\n  Cause:")
  print(f"    Text: {result['cause']['text']}")
  print(f"    Confidence: {result['cause']['confidence']}")
  print(f"    Models: {', '.join(result['cause']['model_consensus'])}")

  print("\n  Action:")
  print(f"    Text: {result['action']['text']}")
  print(f"    Confidence: {result['action']['confidence']}")
  print(f"    Models: {', '.join(result['action']['model_consensus'])}")

  print("\n  Model Opinions:")
  print("\n    GPT-5 Response:")
  print(f"      {json.dumps(result['gpt_opinion'], indent=6)}")
  print("\n    Gemini Response:")
  print(f"      {json.dumps(result['gemini_opinion'], indent=6)}")
  print("\n    Claude Final Decision:")
  print(f"      {json.dumps(result.get('claude_decision', {}), indent=6)}")


def example_retrieve_classification(classification_id: str):
  """Example: Retrieve a stored classification"""
  print("\n" + "=" * 60)
  print("Example 3: Retrieve Stored Classification")
  print("=" * 60 + "\n")

  redis_client = RedisClient()
  result = redis_client.get_classification(classification_id)

  if result:
    print(f"✅ Found classification: {classification_id}")
    print(f"\n  Symptom: {result['symptom']['text']}")
    print(f"  Cause: {result['cause']['text']}")
    print(f"  Action: {result['action']['text']}")
    print(f"\n  Created at: {result['metadata'].get('created_at', 'N/A')}")
  else:
    print(f"❌ Classification not found: {classification_id}")


def example_similarity_search():
  """Example: Search for similar classifications"""
  print("\n" + "=" * 60)
  print("Example 4: Similarity Search")
  print("=" * 60 + "\n")

  from tools import similarity_search_tool

  search_text = "database query timeout"
  results = similarity_search_tool(search_text, "symptom")

  if results:
    print(f"Found {len(results)} similar symptoms:")
    for i, result in enumerate(results, 1):
      print(f"\n  {i}. {result['text']}")
      print(f"     Similarity: {result['similarity_score']:.2f}")
      print(f"     ID: {result['id']}")
  else:
    print("No similar entries found")


def example_semantic_cache():
  """Example: Semantic cache with Neo4j integration"""
  print("\n" + "=" * 60)
  print("Example 5: Semantic Cache & Knowledge Graph")
  print("=" * 60 + "\n")

  classifier = MultiModelClassifier()

  log_input = """2024-10-26 14:30:12 ERROR [api-gateway] Rate limit exceeded
Service experiencing throttling on downstream API
429 responses from payment-service endpoint"""

  result = classifier.classify(log_input)

  print("\n📊 Classification with Graph Integration:")
  print(f"  Classification ID: {result['classification_id']}")

  print("\n  Knowledge Graph Status:")
  kg_info = result.get("knowledge_graph", {})
  print(f"    Success: {kg_info.get('success', False)}")
  print(f"    Nodes Created: {kg_info.get('nodes_created', 0)}")
  print(f"    Relationships Created: {kg_info.get('relationships_created', 0)}")
  print(f"    Run ID: {kg_info.get('run_id', 'N/A')}")

  print("\n  Semantic Matches (cached similar patterns):")
  semantic_matches = result.get("semantic_matches", {})
  if semantic_matches:
    for category, matches in semantic_matches.items():
      print(f"\n    {category.capitalize()}:")
      for match in matches[:3]:
        print(f"      - {match.get('name', 'N/A')}")
  else:
    print("    No semantic matches found (first occurrence)")

  print("\n  Redis Similarity Matches:")
  similarity_matches = result.get("similarity_matches", {})
  if similarity_matches:
    for category, matches in similarity_matches.items():
      print(f"\n    {category.capitalize()}:")
      for match in matches[:2]:
        print(
          f"      - {match.get('text', 'N/A')} (score: {match.get('similarity_score', 0):.2f})"
        )
  else:
    print("    No Redis matches found")


def example_neo4j_stats():
  """Example: Get Neo4j graph statistics"""
  print("\n" + "=" * 60)
  print("Example 6: Knowledge Graph Statistics")
  print("=" * 60 + "\n")

  try:
    import json

    from neo4j_tool import Neo4jKnowledgeGraphTool

    neo4j_tool = Neo4jKnowledgeGraphTool()
    stats_json = neo4j_tool.forward("get_stats")
    stats = json.loads(stats_json)

    print("📊 Neo4j Knowledge Graph Statistics:")
    print(f"\n  Total Nodes: {stats.get('total_nodes', 0)}")
    print(f"  Total Relationships: {stats.get('total_relationships', 0)}")

    print("\n  Nodes by Label:")
    for label_info in stats.get("nodes_by_label", []):
      print(f"    {label_info['label']}: {label_info['count']}")

  except Exception as e:
    print(f"⚠️  Could not retrieve stats: {e}")
    print("Make sure Neo4j is running: docker-compose up -d")


def example_cache_warmup():
  """Example: Warm semantic cache from Neo4j"""
  print("\n" + "=" * 60)
  print("Example 7: Cache Warmup")
  print("=" * 60 + "\n")

  try:
    from cache_warmup import warmup_cache

    print("🔄 Warming semantic cache from Neo4j...")
    warmup_cache()
    print("✅ Cache warmup complete")

    from semantic_cache import get_semantic_cache

    cache = get_semantic_cache()
    stats = cache.stats()

    print("\n📊 Cache Statistics:")
    print(f"  Redis Memory Used: {stats.get('redis_memory_used', 'N/A')}")
    print(f"  Connected Clients: {stats.get('redis_connected_clients', 0)}")
    print(f"  Distance Threshold: {stats.get('cache_threshold', 0.2)}")
    print(f"  Embedding Dimensions: {stats.get('embedding_dimensions', 0)}")

  except Exception as e:
    print(f"⚠️  Cache warmup failed: {e}")
    print("Make sure Redis and Neo4j are running: docker-compose up -d")


if __name__ == "__main__":
  import sys

  print("SYE-Agent MAMI: Example Usage")
  print("=" * 60)

  if len(sys.argv) > 1:
    example_num = sys.argv[1]

    if example_num == "1":
      example_log_classification()
    elif example_num == "2":
      example_text_classification()
    elif example_num == "3":
      if len(sys.argv) > 2:
        example_retrieve_classification(sys.argv[2])
      else:
        print("Usage: python example.py 3 <classification_id>")
    elif example_num == "4":
      example_similarity_search()
    elif example_num == "5":
      example_semantic_cache()
    elif example_num == "6":
      example_neo4j_stats()
    elif example_num == "7":
      example_cache_warmup()
    else:
      print(f"Unknown example: {example_num}")
      print("Available examples: 1, 2, 3, 4, 5, 6, 7")
  else:
    print("\nUsage: python example.py <example_number>")
    print("\nAvailable examples:")
    print("  1 - Log entry classification")
    print("  2 - Plain text classification")
    print("  3 - Retrieve stored classification (requires classification_id)")
    print("  4 - Similarity search")
    print("  5 - Semantic cache & knowledge graph integration")
    print("  6 - Neo4j graph statistics")
    print("  7 - Cache warmup from Neo4j")
    print("\nExample: python example.py 1")
