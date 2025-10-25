#!/usr/bin/env node

// Simple Neo4j interface for Claude Code MCP integration
const neo4j = require('neo4j-driver');
const http = require('http');

class SimpleNeo4jMCP {
  constructor() {
    this.driver = null;
    this.connect();
    this.startServer();
  }

  async connect() {
    const uri = process.env.NEO4J_URI || 'bolt://neo4j:7687';
    const user = process.env.NEO4J_USER || 'neo4j';
    const password = process.env.NEO4J_PASSWORD || 'password123';
    
    this.driver = neo4j.driver(uri, neo4j.auth.basic(user, password));
    
    try {
      const session = this.driver.session();
      await session.run('RETURN 1');
      await session.close();
      console.log('✅ Connected to Neo4j at', uri);
    } catch (error) {
      console.error('❌ Failed to connect to Neo4j:', error.message);
    }
  }

  async createSymptom(description, severity = 'medium', context = {}) {
    const session = this.driver.session();
    try {
      const result = await session.run(`
        CREATE (s:Symptom {
          id: randomUUID(),
          description: $description,
          severity: $severity,
          context_json: $context_json,
          created_at: datetime()
        })
        RETURN s.id as id, s.description as description
      `, {
        description,
        severity,
        context_json: JSON.stringify(context)
      });
      
      const record = result.records[0];
      return {
        id: record.get('id'),
        description: record.get('description'),
        message: `Created symptom: ${description}`
      };
    } finally {
      await session.close();
    }
  }

  async getSimilarSymptoms(description, limit = 5) {
    const session = this.driver.session();
    try {
      const result = await session.run(`
        MATCH (s:Symptom)
        WHERE s.description CONTAINS $keyword
        RETURN s.id as id, s.description as description, s.severity as severity
        ORDER BY s.created_at DESC
        LIMIT $limit
      `, {
        keyword: description.split(' ')[0],
        limit: neo4j.int(limit)
      });
      
      return result.records.map(record => ({
        id: record.get('id'),
        description: record.get('description'),
        severity: record.get('severity')
      }));
    } finally {
      await session.close();
    }
  }

  async getKnowledgeGraphStats() {
    const session = this.driver.session();
    try {
      const result = await session.run(`
        MATCH (s:Symptom) WITH count(s) as symptoms
        MATCH (c:Cause) WITH symptoms, count(c) as causes  
        MATCH (a:Action) WITH symptoms, causes, count(a) as actions
        MATCH ()-[r]->() WITH symptoms, causes, actions, count(r) as relationships
        RETURN symptoms, causes, actions, relationships
      `);
      
      const record = result.records[0];
      return {
        symptoms: record.get('symptoms').toNumber(),
        causes: record.get('causes').toNumber(),
        actions: record.get('actions').toNumber(),
        relationships: record.get('relationships').toNumber()
      };
    } finally {
      await session.close();
    }
  }

  async queryGraph(cypher, params = {}) {
    const session = this.driver.session();
    try {
      const result = await session.run(cypher, params);
      return result.records.map(record => record.toObject());
    } finally {
      await session.close();
    }
  }

  startServer() {
    const server = http.createServer(async (req, res) => {
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
      
      if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
      }

      if (req.method === 'GET' && req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'healthy', timestamp: new Date().toISOString() }));
        return;
      }

      if (req.method === 'GET' && req.url === '/tools') {
        const tools = [
          {
            name: 'create_symptom',
            description: 'Create a new symptom in the knowledge graph',
            parameters: {
              description: 'string (required)',
              severity: 'string (optional: low, medium, high, critical)',
              context: 'object (optional)'
            }
          },
          {
            name: 'get_similar_symptoms',
            description: 'Find similar symptoms for context',
            parameters: {
              description: 'string (required)',
              limit: 'number (optional, default: 5)'
            }
          },
          {
            name: 'get_stats',
            description: 'Get knowledge graph statistics',
            parameters: {}
          },
          {
            name: 'query_graph',
            description: 'Execute custom Cypher query',
            parameters: {
              cypher: 'string (required)',
              params: 'object (optional)'
            }
          }
        ];
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ tools }));
        return;
      }

      if (req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
          try {
            const { action, params } = JSON.parse(body);
            let result;

            switch (action) {
              case 'create_symptom':
                result = await this.createSymptom(params.description, params.severity, params.context);
                break;
              case 'get_similar_symptoms':
                result = await this.getSimilarSymptoms(params.description, params.limit);
                break;
              case 'get_stats':
                result = await this.getKnowledgeGraphStats();
                break;
              case 'query_graph':
                result = await this.queryGraph(params.cypher, params.params);
                break;
              default:
                throw new Error(`Unknown action: ${action}`);
            }

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true, result }));
          } catch (error) {
            console.error('Error:', error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: error.message }));
          }
        });
        return;
      }

      res.writeHead(404);
      res.end('Not Found');
    });

    const port = process.env.MCP_NEO4J_PORT || 3001;
    server.listen(port, () => {
      console.log(`🧠 Neo4j MCP Server running on port ${port}`);
      console.log(`🔗 Neo4j: ${process.env.NEO4J_URI || 'bolt://neo4j:7687'}`);
    });
  }
}

if (require.main === module) {
  new SimpleNeo4jMCP();
}

module.exports = SimpleNeo4jMCP;