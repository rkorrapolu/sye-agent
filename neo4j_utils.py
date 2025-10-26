"""Neo4j utilities for knowledge graph persistence."""
import os
from typing import Dict, List, Any, Optional, Tuple
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv
import json
from datetime import datetime
import uuid

load_dotenv()

class Neo4jConnection:
    """Manages Neo4j database connection."""

    def __init__(self):
        """Initialize connection using environment variables."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        self._connect()

    def _connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            print(f"✅ Connected to Neo4j at {self.uri}")
        except ServiceUnavailable as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            print("Make sure Neo4j is running: docker-compose up -d")
            raise

    def close(self):
        """Close the driver connection."""
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")

    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def write_transaction(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a write transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        with self.driver.session() as session:
            result = session.execute_write(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return [dict(record) for record in result]


def create_node(
    conn: Neo4jConnection,
    label: str,
    properties: Dict[str, Any],
    run_id: str
) -> int:
    """
    Create a node in Neo4j with metadata.

    Args:
        conn: Neo4j connection
        label: Node label (Symptom, Error, Action)
        properties: Node properties (must include 'name')
        run_id: UUID for this agent run

    Returns:
        Neo4j internal node ID
    """
    query = f"""
    CREATE (n:{label})
    SET n += $properties
    SET n.created_at = timestamp()
    SET n.source = 'agent'
    SET n.run_id = $run_id
    RETURN id(n) as node_id
    """

    result = conn.write_transaction(query, {
        "properties": properties,
        "run_id": run_id
    })

    return result[0]["node_id"]


def create_relationship(
    conn: Neo4jConnection,
    rel_type: str,
    start_node_id: int,
    end_node_id: int,
    properties: Dict[str, Any],
    run_id: str
) -> int:
    """
    Create a relationship between two nodes.

    Args:
        conn: Neo4j connection
        rel_type: Relationship type (CAUSES, RELATES, FIXES, TRIGGERS)
        start_node_id: Neo4j ID of start node
        end_node_id: Neo4j ID of end node
        properties: Relationship properties
        run_id: UUID for this agent run

    Returns:
        Neo4j internal relationship ID
    """
    query = f"""
    MATCH (a), (b)
    WHERE id(a) = $start_id AND id(b) = $end_id
    CREATE (a)-[r:{rel_type}]->(b)
    SET r += $properties
    SET r.created_at = timestamp()
    SET r.run_id = $run_id
    RETURN id(r) as rel_id
    """

    result = conn.write_transaction(query, {
        "start_id": start_node_id,
        "end_id": end_node_id,
        "properties": properties,
        "run_id": run_id
    })

    return result[0]["rel_id"]


def write_knowledge_graph(
    conn: Neo4jConnection,
    graph_json: Dict[str, Any]
) -> Tuple[int, int, str]:
    """
    Write a complete knowledge graph to Neo4j.

    Args:
        conn: Neo4j connection
        graph_json: Graph structure with 'nodes' and 'relationships' keys

    Returns:
        Tuple of (num_nodes_created, num_relationships_created, run_id)
    """
    run_id = str(uuid.uuid4())

    # Map agent node IDs to Neo4j node IDs
    id_mapping = {}

    # Create nodes
    nodes = graph_json.get("nodes", [])
    for node in nodes:
        agent_id = node["id"]
        label = node["label"]
        properties = node.get("properties", {})

        neo4j_id = create_node(conn, label, properties, run_id)
        id_mapping[agent_id] = neo4j_id

    # Create relationships
    relationships = graph_json.get("relationships", [])
    for rel in relationships:
        rel_type = rel["type"]
        start_agent_id = rel["start_node_id"]
        end_agent_id = rel["end_node_id"]
        properties = rel.get("properties", {})

        # Map agent IDs to Neo4j IDs
        start_neo4j_id = id_mapping[start_agent_id]
        end_neo4j_id = id_mapping[end_agent_id]

        create_relationship(
            conn, rel_type, start_neo4j_id, end_neo4j_id, properties, run_id
        )

    return len(nodes), len(relationships), run_id


def generate_visualization_url(node_ids: List[int], base_url: str = "http://localhost:7474") -> str:
    """
    Generate a Neo4j Browser URL to visualize specific nodes.

    Args:
        node_ids: List of Neo4j internal node IDs
        base_url: Neo4j Browser base URL

    Returns:
        Complete URL with pre-populated query
    """
    # Create Cypher query to show these nodes and their relationships
    ids_str = ",".join(map(str, node_ids))
    query = f"MATCH (n) WHERE id(n) IN [{ids_str}] OPTIONAL MATCH (n)-[r]-(m) RETURN n, r, m"

    # URL encode the query
    import urllib.parse
    encoded_query = urllib.parse.quote(query)

    return f"{base_url}/browser/?cmd=play&arg={encoded_query}"
