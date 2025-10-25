#!/bin/bash

# SYE Agent Tools - Command Line Interface for Claude Code
# Usage: ./sye-tools.sh <command> [params...]

SYE_NEO4J_URL="http://localhost:3001"

case "$1" in
  "where-are-we")
    echo "🧠 SYE Agent Knowledge Graph Context"
    echo "📍 Location: $(pwd)"
    echo "🗄️  Knowledge Graph Stats:"
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d '{"action":"get_stats","params":{}}' | jq '.result'
    echo ""
    echo "📋 Available Tools:"
    echo "  • create-symptom <description> [severity]"
    echo "  • find-similar <description> [limit]" 
    echo "  • query-graph <cypher>"
    echo "  • get-stats"
    echo "  • warm-cache [limit]"
    echo "  • cache-stats"
    echo "  • invalidate-cache <symptom-id>"
    echo ""
    echo "💡 Try: ./sye-tools.sh find-similar 'slow API'"
    ;;
    
  "get-stats")
    echo "📊 Knowledge Graph Statistics:"
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d '{"action":"get_stats","params":{}}' | jq '.result'
    ;;
    
  "create-symptom")
    if [ -z "$2" ]; then
      echo "Usage: $0 create-symptom <description> [severity]"
      exit 1
    fi
    DESCRIPTION="$2"
    SEVERITY="${3:-medium}"
    echo "🆕 Creating symptom: $DESCRIPTION"
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d "{\"action\":\"create_symptom\",\"params\":{\"description\":\"$DESCRIPTION\",\"severity\":\"$SEVERITY\"}}" | jq '.result'
    ;;
    
  "find-similar")
    if [ -z "$2" ]; then
      echo "Usage: $0 find-similar <description> [limit]"
      exit 1
    fi
    DESCRIPTION="$2"
    LIMIT="${3:-5}"
    echo "🔍 Finding similar symptoms for: $DESCRIPTION"
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d "{\"action\":\"get_similar_symptoms\",\"params\":{\"description\":\"$DESCRIPTION\",\"limit\":$LIMIT}}" | jq '.result'
    ;;
    
  "query-graph")
    if [ -z "$2" ]; then
      echo "Usage: $0 query-graph <cypher-query>"
      exit 1
    fi
    CYPHER="$2"
    echo "🔍 Executing query: $CYPHER"
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d "{\"action\":\"query_graph\",\"params\":{\"cypher\":\"$CYPHER\"}}" | jq '.result'
    ;;
    
  "warm-cache")
    LIMIT="${2:-50}"
    echo "🔥 Warming cache with $LIMIT recent symptoms..."
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d "{\"action\":\"warm_cache\",\"params\":{\"limit\":$LIMIT}}" | jq '.result'
    ;;
    
  "cache-stats")
    echo "📊 Cache Performance Statistics:"
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d '{"action":"cache_stats","params":{}}' | jq '.result'
    ;;
    
  "invalidate-cache")
    if [ -z "$2" ]; then
      echo "Usage: $0 invalidate-cache <symptom-id>"
      exit 1
    fi
    SYMPTOM_ID="$2"
    echo "🗑️  Invalidating cache for symptom: $SYMPTOM_ID"
    curl -s -X POST $SYE_NEO4J_URL -H 'Content-Type: application/json' -d "{\"action\":\"invalidate_cache\",\"params\":{\"symptom_id\":\"$SYMPTOM_ID\"}}" | jq '.result'
    ;;
    
  "health")
    echo "🏥 System Health Check:"
    echo "Neo4j MCP Server: $(curl -s $SYE_NEO4J_URL/health | jq -r '.status')"
    echo "Neo4j Database: $(curl -s http://neo4j:7474/browser/ >/dev/null 2>&1 && echo 'healthy' || echo 'unhealthy')"
    echo "Redis Cache: $(redis-cli -h redis ping 2>/dev/null || echo 'unhealthy')"
    ;;
    
  "examples")
    echo "🎯 Example Commands:"
    echo ""
    echo "# Get current context"
    echo "./sye-tools.sh where-are-we"
    echo ""
    echo "# Create a new symptom"
    echo "./sye-tools.sh create-symptom 'Database connection timeout' high"
    echo ""
    echo "# Find similar issues"
    echo "./sye-tools.sh find-similar 'timeout'"
    echo ""
    echo "# Query the knowledge graph"
    echo "./sye-tools.sh query-graph 'MATCH (s:Symptom) RETURN s.description LIMIT 5'"
    echo ""
    echo "# Get statistics"
    echo "./sye-tools.sh get-stats"
    echo ""
    echo "# Cache Management"
    echo "./sye-tools.sh warm-cache 100       # Pre-load 100 symptoms"
    echo "./sye-tools.sh cache-stats          # Show cache performance"
    echo "./sye-tools.sh invalidate-cache <id> # Clear specific cache entry"
    ;;
    
  *)
    echo "🤖 SYE Agent Tools"
    echo ""
    echo "Usage: $0 <command> [parameters...]"
    echo ""
    echo "Commands:"
    echo "  where-are-we    - Get current context and knowledge graph status"
    echo "  get-stats       - Show knowledge graph statistics"
    echo "  create-symptom  - Create new symptom: <description> [severity]"
    echo "  find-similar    - Find similar symptoms: <description> [limit]"
    echo "  query-graph     - Execute Cypher query: <cypher>"
    echo "  warm-cache      - Pre-populate cache with recent symptoms: [limit]"
    echo "  cache-stats     - Show cache performance statistics"
    echo "  invalidate-cache- Invalidate cache for symptom: <symptom-id>"
    echo "  health          - System health check"
    echo "  examples        - Show example usage"
    echo ""
    echo "💡 Start with: $0 where-are-we"
    ;;
esac