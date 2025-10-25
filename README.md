# Self-Improving Yolo Engine

SYE (Self-Improving Yolo Engine) is designed to demonstrate a self-improving knowledge system that learns from production errors. In this project, “YOLO” means identifying the right context of input, whether logs, text, or images.

SYE is a self-improving AI agent that learns production insights in real time. A loop from input, classification, verification, and graph update.

The agent uses **smolagents**, **Neo4j**, and **Redis** to build a lightweight self-improving knowledge graph that shows:
1. Classification of user input into **Symptom**, **Cause**, and **Action**.  
2. Storing and linking this in Neo4j as a mini knowledge graph.  
3. Simulated self-improvement, the system updates relationships when verified by a user.

## Overview
Every user input (log, message, or observation) is processed by the agent and categorized into one of three types:

- **Symptom** (What’s happening?)  
- **Cause** (Why it happens?)  
- **Action** (How to fix it?)  

After classification, the user verifies or adjusts these categories. The system then updates the knowledge graph, learning stronger patterns for future use.

## Goal

1. **Input** (text log, message)  
2. **smol-agent classification** → Symptom / Cause / Action  
3. **Neo4j graph storage** (create or update nodes & relationships)  
4. **Feedback loop** — user modifies or approves classification  
5. **Graph update** — store user feedback and new connections  

## Setup

### Steps
1. Start Neo4j and Redis via Docker Compose.
2. Run `main.py` to start processing user input.
3. Enter logs or short text.
4. Inspect relationships in the Neo4j browser (`localhost:7474`).
5. Verify or update classifications and rerun.

## Team Breakdown

| Role | Member Tasks | Deliverables |
|------|---------------|--------------|
| **Agent & Logic Dev** | Build smol-agent pipeline for categorization. Define prompt templates for Symptom, Cause, Action. | Classification script (`agent.py`) working with simple text. |
| **Graph Dev** | Integrate Neo4j. Write simple CRUD for nodes and relations (`graph.py`). | Function to insert/update relationships: Symptom → Cause → Action. |
| **Backend/API Dev** | Connect agent + graph via FastAPI or Streamlit for quick I/O testing. | Simple interactive UI endpoint that takes text input and returns graph JSON. |
| **Demo & Feedback Lead** | Handle Redis caching for fast lookup, prepare example inputs, polish the README/demo flow. | Live demo and example queries showing learning from user corrections. |

## Demo Scenario
Input example:  
> “High CPU usage after deploying new model version.”

Agent response →  
- Symptom: “High CPU usage”  
- Cause: “Model update increases load”  
- Action: “Scale up container or optimize inference”  

Neo4j graph shows:
```
(:Symptom {name:"High CPU"})
   -> (:Cause {name:"Model update"})
   -> (:Action {name:"Scale resources"})
```

User corrects if necessary. Agent stores the validated relationship for future predictions.

## Stretch Goals
- Add embeddings for similarity-based lookup.  
- Visualize graph relationships in browser.  
- Cache last N queries in Redis for rapid recall.  

---

### Redis vs Neo4j

**Redis strengths:**
- **Speed**: Sub-millisecond lookups critical for production observability
- **Simple setup**: 5 minutes vs 15-20 for Neo4j
- **State management**: Perfect for agent memory and caching recent classifications

**Neo4j advantages:**
- **Relationship queries**: Native pattern matching (e.g., "find all symptoms leading to this cause")
- **Multi-hop reasoning**: Natural graph traversal for learning patterns
- **Self-improvement**: Confidence score updates on relationships are elegant

### Graph Schema

**Node Types:**
1. **Symptom** - Observable problems (high latency, locked connections, replication lag)
2. **Cause** - Root causes (ALTER TABLE lock, full table scan)
3. **Action** - Remediation steps (terminate query, use CHECK constraints)
4. **Input** - Raw user input
5. **Incident** - Aggregates multiple symptoms

**Key Relationships:**
- `LEADS_TO` (Symptom → Cause) with confidence score
- `RESOLVED_BY` (Cause → Action) with effectiveness score
- `SIMILAR_TO` (for clustering similar patterns)

The [AIOps](https://coroot.com/blog/engineering/using-ai-for-troubleshooting-openai-vs-deepseek/) example maps to:
```cypher
(s:Symptom {text:"High query latency"})-[:LEADS_TO {confidence:0.85}]->
(c:Cause {text:"ALTER TABLE lock"})-[:RESOLVED_BY {effectiveness:0.92}]->
(a:Action {text:"Terminate with pg_terminate_backend"})
```

## System Architecture

### Three-Agent Design

**1. ClassifierAgent** (CodeAgent)
- Ingests raw logs/metrics using `coroot/logparser` tool
- Extracts Symptom, Cause, Action using LLM reasoning
- Outputs Python code with structured results

**2. DecisionAgent** (CodeAgent)  
- Queries knowledge graph for similar patterns
- Decides: CREATE_NEW, UPDATE_EXISTING, or ASK_CLARIFICATION
- Uses similarity_search and graph_query tools

**3. ExecutorAgent** (CodeAgent)
- Executes Cypher queries to update Neo4j
- Updates Redis cache for fast lookups
- Increments confidence scores based on user feedback

### Data Flow Sequence

```
User Input → Classifier → Verification → Decision → Executor → Storage
     ↑                                                            │
     └────────────────── Learning Feedback ──────────────────────┘
```

## Execution Strategy

### Hybrid Approach

**Step 1: Redis MVP**
- Build basic Symptom→Cause→Action storage in Redis JSON
- Get one agent working end-to-end
- Focus on core functionality

**Step 2: Add Neo4j**
- Migrate Redis data to Neo4j
- Build graph relationships
- Prepare visualization for demo

**Step 3: Demo Polish**
- Show Redis for real-time speed
- Show Neo4j Browser for visual "wow factor"
- Demonstrate learning via confidence updates

## Tool Integration: coroot/logparser

The `logparser` tool will be your first tool:[6]

```python
@tool
def parse_logs(log_text: str) -> dict:
    """Extract patterns using coroot/logparser"""
    # Run: echo log_text | docker run -i ghcr.io/coroot/logparser
    # Returns: {pattern, severity, frequency, components}
```

This gives structured data to feed the ClassifierAgent.

## Critical Success Factors

1. Docker Compose running (Redis + Neo4j)
2. One ClassifierAgent working
3. `logparser_tool` functional
4. Redis storage operational
5. User verification loop
6. One complete demo scenario

**Stretch goals:**
- Neo4j visualization
- Parallel agent execution
- Embeddings for similarity
- Web UI with Streamlit
