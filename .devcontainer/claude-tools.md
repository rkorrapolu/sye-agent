# SYE Agent - Available Tools for Claude Code

## 🧠 Neo4j Knowledge Graph Tools

**Server:** http://localhost:3001
**Status:** ✅ Running

### Available Commands:

#### 1. Get Knowledge Graph Statistics
```bash
curl -X POST http://localhost:3001 \
  -H 'Content-Type: application/json' \
  -d '{"action":"get_stats","params":{}}'
```

#### 2. Create New Symptom
```bash
curl -X POST http://localhost:3001 \
  -H 'Content-Type: application/json' \
  -d '{
    "action":"create_symptom",
    "params":{
      "description":"API response time is slow",
      "severity":"high",
      "context":{"endpoint":"/api/users"}
    }
  }'
```

#### 3. Find Similar Symptoms
```bash
curl -X POST http://localhost:3001 \
  -H 'Content-Type: application/json' \
  -d '{
    "action":"get_similar_symptoms",
    "params":{
      "description":"slow API",
      "limit":5
    }
  }'
```

#### 4. Execute Custom Cypher Query
```bash
curl -X POST http://localhost:3001 \
  -H 'Content-Type: application/json' \
  -d '{
    "action":"query_graph",
    "params":{
      "cypher":"MATCH (s:Symptom)-[r:CAUSED_BY]->(c:Cause) RETURN s.description, c.description LIMIT 5"
    }
  }'
```

## 🌍 Context: "Where are we?"

When Claude asks "Where are we?", use these tools to provide rich context:

1. **Current Location**: `/workspace` (SYE Agent repository)
2. **Knowledge Graph**: Use `get_stats` to show current knowledge state
3. **Recent Activity**: Query recent symptoms/causes/actions
4. **Available Tools**: List all available MCP tools

## 💡 Usage Tips

- All tools return JSON responses with `{success: true/false, result: ...}`
- The Neo4j database contains sample data about API performance issues
- Use `query_graph` for complex analysis and pattern discovery
- Graph relationships: Symptom → CAUSED_BY → Cause → ADDRESSED_BY → Action