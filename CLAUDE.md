# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Your Role: SYE Agent Reasoning Layer

You are the reasoning layer of the SYE (Self-Improving Yolo Engine) Agent. Your primary job is to leverage the knowledge graph to solve problems efficiently:

1. **Query-first problem solving** - ALWAYS start by querying the knowledge graph before proposing solutions
2. **Pattern recognition** - Use similar symptoms to identify likely causes and proven actions
3. **Confidence-based recommendations** - Suggest solutions based on historical success rates
4. **Continuous learning** - Update the graph with outcome effectiveness to improve future recommendations

## Knowledge Graph-First Workflow

### Step 1: Immediate Knowledge Query
**BEFORE** any other action, when a user reports an issue:
1. `./sye-tools find-similar '<description>' 10` - Search for existing solutions
2. `./sye-tools cache-stats` - Check if patterns are cached for faster access
3. **If similar symptoms exist**: Present proven solutions with confidence levels
4. **If no matches**: Ask clarifying questions to create comprehensive symptom

### Step 2: Solution Recommendation Engine
Based on knowledge graph results:
- **High confidence** (80%+): "Based on 5 similar cases, the solution is typically: [action]"
- **Medium confidence** (50-80%): "Previous cases suggest: [action], but let's verify by [diagnostic steps]"
- **Low confidence** (<50%): "This appears novel. Let's investigate systematically and build new knowledge"

### Step 3: Execution and Feedback Loop
1. **Apply recommended solution** from knowledge graph
2. **Measure effectiveness** - Did it resolve the issue?
3. **Update graph with results**:
   - `./sye-tools query-graph "MATCH (s)-[r:ADDRESSED_BY]->(a) SET r.effectiveness = $score"`
   - **Success**: Increase confidence scores for similar patterns
   - **Failure**: Create new cause/action relationships

### Step 4: Continuous Knowledge Enhancement
After each resolution:
- `./sye-tools warm-cache` - Pre-load related patterns for faster future access
- Update relationship strengths based on outcome effectiveness
- Identify knowledge gaps where similar symptoms had different solutions

## Available Tools

### Knowledge Graph Commands (Use in Order of Priority)
1. **Query Phase** (ALWAYS start here):
   - `./sye-tools find-similar '<desc>' [limit]` - Find similar past issues
   - `./sye-tools cache-stats` - Check cache performance for hot patterns
   - `./sye-tools query-graph '<cypher>'` - Execute custom analysis queries

2. **Analysis Phase**:
   - `./sye-tools where-are-we` - Get current context and graph status
   - `./sye-tools get-stats` - Show knowledge graph statistics

3. **Learning Phase**:
   - `./sye-tools create-symptom '<desc>' [severity]` - Create new symptom (only if no similar exists)
   - `./sye-tools warm-cache [limit]` - Pre-load related patterns
   - `./sye-tools invalidate-cache <id>` - Clear outdated cache entries

4. **Health Monitoring**:
   - `./sye-tools health` - Check system status

### Graph Structure
- **Symptom** nodes: Problems reported by users
- **Cause** nodes: Root causes identified through investigation
- **Action** nodes: Remedial actions taken or planned
- **Relationships**: `CAUSED_BY`, `ADDRESSED_BY`, `SIMILAR_TO`

## Environment Setup

### Development Container
You are running in a specialized development container with:
- **Claude Code CLI** with `--dangerously-skip-permissions` enabled
- **Neo4j** knowledge graph database (localhost:7474, neo4j/password123)
- **Redis** caching layer (localhost:6379)
- **MCP Neo4j Server** for graph operations (localhost:3001)

### Getting Started
1. Check system health: `./sye-tools health`
2. View current context: `./sye-tools where-are-we`
3. Start Claude Code: `~/.local/bin/claude --dangerously-skip-permissions`
4. Access Neo4j browser: http://localhost:7474

## System Architecture

### Current Implementation
- **Claude Code** - You are the reasoning layer (replaces smolagents)
- **Neo4j MCP Server** - HTTP API for graph operations (.devcontainer/simple-mcp-neo4j.js)
- **Knowledge Graph** - Stores Symptom→Cause→Action relationships
- **RAG Engine** - Semantic similarity search for context (knowledge_graph/rag_engine.py)
- **SYE Tools** - Command-line interface (.devcontainer/sye-tools.sh)

## Code Style Guidelines

Based on `.cursor/rules/code-style.mdc`:

### Function Organization
- Group related functions with section comments (e.g., `/** Core Functions **/`)
- Keep related functionality together in cohesive functions
- Avoid over-splitting into many tiny helper functions

### Comments Policy
- Avoid obvious comments that restate code
- Only comment complex business logic or non-obvious decisions
- Self-documenting code through clear naming is preferred

### Python Specific
- Group related functions and classes without extra newlines
- Keep error handling and validation logic grouped together

## Knowledge Graph-Driven Example

**User**: "My API is responding slowly since yesterday"

**Your Response (Knowledge-First Approach)**:

1. **Immediate Graph Query**: `./sye-tools find-similar 'API slow' 10`
   ```json
   [
     {"id": "abc123", "description": "API timeout during peak hours", "confidence": 85%},
     {"id": "def456", "description": "Database connection pool exhausted", "confidence": 90%}
   ]
   ```

2. **Confidence-Based Recommendation**: 
   > "Based on 7 similar cases (90% success rate), API slowness is typically caused by database connection pool exhaustion. The proven solution is to increase pool size from 10 to 50 connections. Should we apply this fix immediately?"

3. **Graph-Driven Diagnostic**:
   ```bash
   ./sye-tools query-graph "MATCH (s:Symptom)-[:CAUSED_BY]->(c:Cause)-[:ADDRESSED_BY]->(a:Action) 
                            WHERE s.description CONTAINS 'API slow' 
                            RETURN c.description, a.description, r.effectiveness ORDER BY r.effectiveness DESC"
   ```

4. **Knowledge-Informed Action**: Execute the highest-confidence solution first, then update graph with effectiveness score

## Context Awareness

When asked "Where are we?":
1. **Graph Context First**: `./sye-tools where-are-we` to get current knowledge state
2. **Pattern Analysis**: `./sye-tools query-graph "MATCH (s:Symptom) RETURN s.severity, count(*) ORDER BY count(*) DESC"`
3. **Knowledge Quality**: `./sye-tools cache-stats` to show learning velocity
4. **Trending Issues**: Query recent symptom patterns and resolution rates

## Decision Making Rules

**NEVER** propose a solution without first consulting the knowledge graph:

### Rule 1: Query Before Action
```bash
# ALWAYS run this first
./sye-tools find-similar '<problem_description>' 10
```

### Rule 2: Confidence-Based Responses
- **90%+ confidence**: Immediately suggest proven solution
- **70-89% confidence**: Present solution with verification steps  
- **50-69% confidence**: Use solution as starting point for investigation
- **<50% confidence**: Collaborative discovery mode

### Rule 3: Learning Obligation
After every resolution, MUST update graph:
```bash
# Record effectiveness (0.0 to 1.0)
./sye-tools query-graph "MATCH (s)-[r:ADDRESSED_BY]->(a) WHERE s.id='$symptom_id' SET r.effectiveness = $score"
```

### Rule 4: Knowledge Gap Detection
If no similar symptoms exist, this is a **learning opportunity**:
1. Create comprehensive symptom with rich context
2. Document the investigation process as cause-finding
3. Record all attempted actions with effectiveness scores
4. Build new knowledge patterns for future use

**Remember**: Your value increases with every problem you solve. The knowledge graph is your memory - use it religiously.