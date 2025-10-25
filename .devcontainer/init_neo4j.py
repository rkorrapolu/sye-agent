#!/usr/bin/env python3

import os
import time
from neo4j import GraphDatabase

def wait_for_neo4j(driver, max_retries=30):
    """Wait for Neo4j to be ready"""
    for i in range(max_retries):
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            print("✅ Neo4j is ready!")
            return True
        except Exception as e:
            print(f"⏳ Waiting for Neo4j... ({i+1}/{max_retries})")
            time.sleep(2)
    return False

def initialize_schema(driver):
    """Initialize Neo4j schema with constraints and indexes"""
    
    constraints_and_indexes = [
        # Unique constraints
        "CREATE CONSTRAINT symptom_id_unique IF NOT EXISTS FOR (s:Symptom) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT cause_id_unique IF NOT EXISTS FOR (c:Cause) REQUIRE c.id IS UNIQUE", 
        "CREATE CONSTRAINT action_id_unique IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE",
        
        # Indexes for performance
        "CREATE INDEX symptom_description_idx IF NOT EXISTS FOR (s:Symptom) ON (s.description)",
        "CREATE INDEX cause_category_idx IF NOT EXISTS FOR (c:Cause) ON (c.category)",
        "CREATE INDEX action_type_idx IF NOT EXISTS FOR (a:Action) ON (a.type)",
        "CREATE INDEX symptom_severity_idx IF NOT EXISTS FOR (s:Symptom) ON (s.severity)",
        "CREATE INDEX created_at_idx IF NOT EXISTS FOR (n) ON (n.created_at)",
        
        # Full-text search indexes
        "CALL db.index.fulltext.createNodeIndex('symptom_search', ['Symptom'], ['description']) YIELD name",
        "CALL db.index.fulltext.createNodeIndex('cause_search', ['Cause'], ['description']) YIELD name",
        "CALL db.index.fulltext.createNodeIndex('action_search', ['Action'], ['description']) YIELD name"
    ]
    
    with driver.session() as session:
        for query in constraints_and_indexes:
            try:
                session.run(query)
                print(f"✅ Executed: {query[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                    print(f"⚠️  Already exists: {query[:50]}...")
                else:
                    print(f"❌ Error with: {query[:50]}... - {e}")

def create_sample_data(driver):
    """Create sample data for testing"""
    
    sample_data_queries = [
        # Sample symptom
        """
        MERGE (s:Symptom {id: 'sample-api-slow', description: 'API response time is over 5 seconds', 
                         severity: 'high', context: {endpoint: '/api/users', method: 'GET'}, 
                         created_at: datetime()})
        """,
        
        # Sample causes
        """
        MERGE (c1:Cause {id: 'sample-db-query', description: 'Database query not optimized', 
                         category: 'performance', confidence: 0.8, created_at: datetime()})
        MERGE (c2:Cause {id: 'sample-memory-leak', description: 'Memory leak in application', 
                         category: 'resource', confidence: 0.6, created_at: datetime()})
        """,
        
        # Sample actions
        """
        MERGE (a1:Action {id: 'sample-add-index', description: 'Add database index on user_id column', 
                         type: 'database', estimated_time: '30 minutes', risk_level: 'low', 
                         created_at: datetime()})
        MERGE (a2:Action {id: 'sample-restart-service', description: 'Restart application service', 
                         type: 'infrastructure', estimated_time: '5 minutes', risk_level: 'medium', 
                         created_at: datetime()})
        """,
        
        # Sample relationships
        """
        MATCH (s:Symptom {id: 'sample-api-slow'}), (c:Cause {id: 'sample-db-query'})
        MERGE (s)-[r:CAUSED_BY {confidence: 0.8, created_at: datetime()}]->(c)
        """,
        
        """
        MATCH (c:Cause {id: 'sample-db-query'}), (a:Action {id: 'sample-add-index'})
        MERGE (c)-[r:ADDRESSED_BY {effectiveness: 0.9, created_at: datetime()}]->(a)
        """,
        
        """
        MATCH (s:Symptom {id: 'sample-api-slow'}), (c:Cause {id: 'sample-memory-leak'})
        MERGE (s)-[r:CAUSED_BY {confidence: 0.6, created_at: datetime()}]->(c)
        """,
        
        """
        MATCH (c:Cause {id: 'sample-memory-leak'}), (a:Action {id: 'sample-restart-service'})
        MERGE (c)-[r:ADDRESSED_BY {effectiveness: 0.7, created_at: datetime()}]->(a)
        """
    ]
    
    with driver.session() as session:
        for query in sample_data_queries:
            try:
                session.run(query)
                print(f"✅ Created sample data")
            except Exception as e:
                print(f"❌ Error creating sample data: {e}")

def main():
    # Connection details
    uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    user = os.getenv('NEO4J_USER', 'neo4j') 
    password = os.getenv('NEO4J_PASSWORD', 'password123')
    
    print(f"🔌 Connecting to Neo4j at {uri}...")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        # Wait for Neo4j to be ready
        if not wait_for_neo4j(driver):
            print("❌ Neo4j failed to become ready")
            return
        
        # Initialize schema
        print("🏗️  Initializing Neo4j schema...")
        initialize_schema(driver)
        
        # Create sample data
        print("📝 Creating sample data...")
        create_sample_data(driver)
        
        # Verify setup
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()['total_nodes']
            print(f"📊 Total nodes in graph: {total_nodes}")
            
        print("🎉 Neo4j initialization complete!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()