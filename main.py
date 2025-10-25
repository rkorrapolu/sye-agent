#!/usr/bin/env python3

import os
import json
import subprocess
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from neo4j import GraphDatabase
import redis

# Import our RAG engine (conditional for container vs local)
try:
    import sys
    sys.path.append('/workspace')
    from knowledge_graph.rag_engine import get_knowledge_context
except ImportError:
    # Fallback for when running without ML dependencies
    def get_knowledge_context(description: str) -> str:
        return f"# Knowledge Graph Context\n\nNo RAG context available for: {description}\nRunning in basic mode without sentence transformers."

app = FastAPI(title="SYE Agent", description="Self-Improving Yolo Engine with Claude Code Reasoning")

# Database connections
neo4j_driver = None
redis_client = None

class SymptomRequest(BaseModel):
    description: str
    severity: str = "medium"
    context: Dict[str, Any] = {}

class WorkflowResponse(BaseModel):
    session_id: str
    symptom_id: str
    claude_analysis: str
    rag_context: str
    next_steps: list

@app.on_event("startup")
async def startup_event():
    global neo4j_driver, redis_client
    
    # Connect to Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
    
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    # Connect to Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url)
    
    print("✅ Connected to Neo4j and Redis")

@app.on_event("shutdown")
async def shutdown_event():
    if neo4j_driver:
        neo4j_driver.close()
    if redis_client:
        redis_client.close()

@app.get("/")
async def root():
    return {
        "message": "SYE Agent is running!", 
        "status": "ready",
        "features": [
            "Claude Code Reasoning Layer",
            "Neo4j Knowledge Graph", 
            "RAG Context Engine",
            "MCP Database Tools",
            "Collaborative Problem Solving"
        ]
    }

@app.get("/health")
async def health_check():
    try:
        # Test Neo4j connection
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 as test")
            neo4j_status = "connected" if result.single() else "disconnected"
        
        # Test Redis connection
        redis_status = "connected" if redis_client.ping() else "disconnected"
        
        # Test Claude Code availability (check if claude command exists)
        try:
            subprocess.run(["which", "claude"], check=True, capture_output=True)
            claude_status = "available"
        except:
            claude_status = "not_available"
        
        return {
            "neo4j": neo4j_status,
            "redis": redis_status,
            "claude_code": claude_status,
            "overall": "healthy" if all([
                neo4j_status == "connected", 
                redis_status == "connected",
                claude_status == "available"
            ]) else "unhealthy"
        }
    except Exception as e:
        return {"error": str(e), "overall": "unhealthy"}

@app.post("/analyze-symptom", response_model=WorkflowResponse)
async def analyze_symptom(symptom: SymptomRequest):
    """Start collaborative problem-solving workflow with Claude Code"""
    try:
        # Generate session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Create symptom in knowledge graph
        with neo4j_driver.session() as session:
            result = session.run("""
                CREATE (s:Symptom {
                    id: randomUUID(),
                    description: $description,
                    severity: $severity,
                    context_json: $context_json,
                    created_at: datetime(),
                    session_id: $session_id
                })
                RETURN s.id as symptom_id
            """, {
                "description": symptom.description,
                "severity": symptom.severity, 
                "context_json": json.dumps(symptom.context),
                "session_id": session_id
            })
            symptom_id = result.single()["symptom_id"]
        
        # Get RAG context
        rag_context = get_knowledge_context(symptom.description)
        
        # Prepare Claude Code prompt with RAG context
        claude_prompt = f"""
# SYE Agent: Collaborative Problem Solving

## Current Symptom:
**Description**: {symptom.description}
**Severity**: {symptom.severity}
**Context**: {json.dumps(symptom.context, indent=2)}

{rag_context}

## Your Role:
You are the reasoning layer for the SYE (Self-Improving Yolo Engine) system. Your job is to:

1. **Analyze** this symptom using the knowledge graph context above
2. **Propose** the most likely causes based on historical data
3. **Suggest** specific actions to investigate or resolve the issue
4. **Use MCP tools** to interact with the knowledge graph and systems

## Available MCP Tools:
- `create_cause` - Add new cause hypotheses to knowledge graph
- `create_action` - Add action plans to knowledge graph  
- `link_symptom_cause` - Connect symptoms to causes with confidence scores
- `query_knowledge_graph` - Run Cypher queries for deeper analysis
- `analyze_repository` - Examine code/config for root causes
- `run_tests` - Execute tests to validate hypotheses
- `monitor_metrics` - Check current system health

## Next Steps:
Please start by analyzing this symptom and propose your investigation approach.
"""

        # For now, return the prompt that would be sent to Claude
        # In a real implementation, this would invoke Claude Code with MCP tools
        claude_analysis = f"Claude Code would analyze: {symptom.description}\n\nWith context:\n{rag_context}"
        
        next_steps = [
            "Analyze symptom with RAG context",
            "Propose likely causes using historical data", 
            "Create investigation plan",
            "Execute actions with user collaboration",
            "Update knowledge graph with results"
        ]
        
        return WorkflowResponse(
            session_id=session_id,
            symptom_id=symptom_id,
            claude_analysis=claude_analysis,
            rag_context=rag_context,
            next_steps=next_steps
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
async def get_session_status(session_id: str):
    """Get status of a collaborative session"""
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (s:Symptom {session_id: $session_id})
            OPTIONAL MATCH (s)-[:CAUSED_BY]->(c:Cause)
            OPTIONAL MATCH (c)-[:ADDRESSED_BY]->(a:Action)
            RETURN s, collect(DISTINCT c) as causes, collect(DISTINCT a) as actions
        """, {"session_id": session_id})
        
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "symptom": dict(record["s"]),
            "causes": [dict(c) for c in record["causes"] if c],
            "actions": [dict(a) for a in record["actions"] if a]
        }

@app.get("/knowledge-graph/stats")
async def get_knowledge_stats():
    """Get knowledge graph statistics"""
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (s:Symptom) WITH count(s) as symptoms
            MATCH (c:Cause) WITH symptoms, count(c) as causes  
            MATCH (a:Action) WITH symptoms, causes, count(a) as actions
            MATCH ()-[r]->() WITH symptoms, causes, actions, count(r) as relationships
            RETURN symptoms, causes, actions, relationships
        """)
        
        stats = result.single()
        return {
            "total_symptoms": stats["symptoms"],
            "total_causes": stats["causes"], 
            "total_actions": stats["actions"],
            "total_relationships": stats["relationships"]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)