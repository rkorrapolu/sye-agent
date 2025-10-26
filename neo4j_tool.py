"""Custom smolagents tool for Neo4j knowledge graph operations."""
from smolagents import Tool
from typing import Dict, Any
import json
from neo4j_utils import Neo4jConnection, write_knowledge_graph, generate_visualization_url
from semantic_cache import get_semantic_cache


class Neo4jKnowledgeGraphTool(Tool):
    """Tool for interacting with Neo4j knowledge graph database."""

    name = "neo4j_knowledge_graph"
    description = """
    This tool allows you to interact with a Neo4j knowledge graph database.

    Operations:
    - write_graph: Persist a knowledge graph to Neo4j (JSON format)
    - query_existing: Check if a node already exists (returns True/False)
    - get_stats: Get statistics about the graph (node counts, etc.)

    Example usage:
    - write_graph({"nodes": [...], "relationships": [...]})
    - query_existing("Database connection drops", "Symptom")
    - get_stats()
    """

    inputs = {
        "operation": {
            "type": "string",
            "description": "Operation to perform: 'write_graph', 'query_existing', or 'get_stats'"
        },
        "data": {
            "type": "string",
            "description": "JSON string with operation data. For write_graph: full graph JSON. For query_existing: {'name': 'entity name', 'label': 'Symptom|Error|Action'}",
            "nullable": True
        }
    }

    output_type = "string"

    def __init__(self):
        """Initialize tool with Neo4j connection."""
        super().__init__()
        self.conn = Neo4jConnection()

    def forward(self, operation: str, data: str = "{}") -> str:
        """
        Execute Neo4j operation.

        Args:
            operation: Operation type
            data: JSON string with operation data

        Returns:
            Result as JSON string
        """
        try:
            data_dict = json.loads(data) if isinstance(data, str) else data

            if operation == "write_graph":
                return self._write_graph(data_dict)
            elif operation == "query_existing":
                return self._query_existing(data_dict)
            elif operation == "get_stats":
                return self._get_stats()
            else:
                return json.dumps({"error": f"Unknown operation: {operation}"})

        except Exception as e:
            return json.dumps({"error": str(e)})

    def _write_graph(self, graph_json: Dict) -> str:
        """Write graph to Neo4j."""
        num_nodes, num_rels, run_id = write_knowledge_graph(self.conn, graph_json)

        # Get node IDs for visualization (we'll need to query them back)
        # For now, just return counts
        result = {
            "success": True,
            "nodes_created": num_nodes,
            "relationships_created": num_rels,
            "run_id": run_id
        }

        return json.dumps(result)

    def _query_existing(self, query_data: Dict) -> str:
        """
        Query if a node exists (with semantic cache).

        Flow:
        1. Check semantic cache for similar queries
        2. If cache hit: return cached Neo4j nodes
        3. If cache miss: query Neo4j, store results in cache
        """
        name = query_data.get("name")
        label = query_data.get("label")

        if not name or not label:
            return json.dumps({"error": "Missing 'name' or 'label' in query"})

        # Step 1: Check semantic cache
        cache = get_semantic_cache()
        cached_nodes = cache.check(name, label)

        if cached_nodes:
            # Cache hit - return cached results
            return json.dumps({
                "source": "cache",
                "nodes": cached_nodes,
                "count": len(cached_nodes)
            })

        # Step 2: Cache miss - query Neo4j
        query = f"""
        MATCH (n:{label})
        WHERE n.name = $name
        RETURN id(n) as node_id, n.name as name, n.created_at as created_at,
               n.times_seen as times_seen
        LIMIT 1
        """

        results = self.conn.execute_query(query, {"name": name})

        # Format results for caching
        nodes = []
        for r in results:
            nodes.append({
                "node_id": r["node_id"],
                "name": r["name"],
                "created_at": r.get("created_at"),
                "times_seen": r.get("times_seen", 1)
            })

        # Step 3: Store results in cache for future queries
        cache.store(name, nodes, label)

        # Return results
        if nodes:
            return json.dumps({
                "source": "neo4j",
                "nodes": nodes,
                "count": len(nodes)
            })
        else:
            return json.dumps({
                "source": "neo4j",
                "nodes": [],
                "count": 0
            })

    def _get_stats(self) -> str:
        """Get graph statistics."""
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        """

        results = self.conn.execute_query(query)

        total_nodes = sum(r["count"] for r in results)

        # Count relationships
        rel_query = "MATCH ()-[r]->() RETURN count(r) as count"
        rel_results = self.conn.execute_query(rel_query)
        total_rels = rel_results[0]["count"] if rel_results else 0

        return json.dumps({
            "total_nodes": total_nodes,
            "total_relationships": total_rels,
            "nodes_by_label": results
        })

    def __del__(self):
        """Clean up connection on deletion."""
        if hasattr(self, 'conn'):
            self.conn.close()
