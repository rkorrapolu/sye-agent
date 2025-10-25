#!/usr/bin/env node

const { Server } = require('@anthropic/mcp-server');
const neo4j = require('neo4j-driver');

class Neo4jMCPServer {
  constructor() {
    this.driver = null;
    this.server = new Server({
      name: 'neo4j-sye',
      version: '1.0.0'
    });
    
    this.setupHandlers();
  }

  async connect() {
    const uri = process.env.NEO4J_URI || 'bolt://neo4j:7687';
    const user = process.env.NEO4J_USER || 'neo4j';
    const password = process.env.NEO4J_PASSWORD || 'password123';
    
    this.driver = neo4j.driver(uri, neo4j.auth.basic(user, password));
    
    // Test connection
    const session = this.driver.session();
    try {
      await session.run('RETURN 1');
      console.log('✅ Connected to Neo4j');
    } finally {
      await session.close();
    }
  }

  setupHandlers() {
    // Tool: Create Symptom node
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      switch (name) {
        case 'create_symptom':
          return await this.createSymptom(args);
        case 'create_cause':
          return await this.createCause(args);
        case 'create_action':
          return await this.createAction(args);
        case 'link_symptom_cause':
          return await this.linkSymptomCause(args);
        case 'link_cause_action':
          return await this.linkCauseAction(args);
        case 'query_knowledge_graph':
          return await this.queryKnowledgeGraph(args);
        case 'get_similar_symptoms':
          return await this.getSimilarSymptoms(args);
        case 'update_action_result':
          return await this.updateActionResult(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });

    // List available tools
    this.server.setRequestHandler('tools/list', async () => {
      return {
        tools: [
          {
            name: 'create_symptom',
            description: 'Create a new symptom node in the knowledge graph',
            inputSchema: {
              type: 'object',
              properties: {
                description: { type: 'string' },
                severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
                context: { type: 'object' }
              },
              required: ['description']
            }
          },
          {
            name: 'create_cause',
            description: 'Create a new cause node in the knowledge graph',
            inputSchema: {
              type: 'object',
              properties: {
                description: { type: 'string' },
                category: { type: 'string' },
                confidence: { type: 'number', minimum: 0, maximum: 1 }
              },
              required: ['description']
            }
          },
          {
            name: 'create_action',
            description: 'Create a new action node in the knowledge graph',
            inputSchema: {
              type: 'object',
              properties: {
                description: { type: 'string' },
                type: { type: 'string' },
                estimated_time: { type: 'string' },
                risk_level: { type: 'string', enum: ['low', 'medium', 'high'] }
              },
              required: ['description']
            }
          },
          {
            name: 'link_symptom_cause',
            description: 'Create relationship between symptom and cause',
            inputSchema: {
              type: 'object',
              properties: {
                symptom_id: { type: 'string' },
                cause_id: { type: 'string' },
                confidence: { type: 'number', minimum: 0, maximum: 1 }
              },
              required: ['symptom_id', 'cause_id']
            }
          },
          {
            name: 'link_cause_action',
            description: 'Create relationship between cause and action',
            inputSchema: {
              type: 'object',
              properties: {
                cause_id: { type: 'string' },
                action_id: { type: 'string' },
                effectiveness: { type: 'number', minimum: 0, maximum: 1 }
              },
              required: ['cause_id', 'action_id']
            }
          },
          {
            name: 'query_knowledge_graph',
            description: 'Query the knowledge graph with Cypher',
            inputSchema: {
              type: 'object',
              properties: {
                cypher: { type: 'string' },
                params: { type: 'object' }
              },
              required: ['cypher']
            }
          },
          {
            name: 'get_similar_symptoms',
            description: 'Find similar symptoms for RAG context',
            inputSchema: {
              type: 'object',
              properties: {
                description: { type: 'string' },
                limit: { type: 'number', default: 5 }
              },
              required: ['description']
            }
          },
          {
            name: 'update_action_result',
            description: 'Update action with results and effectiveness',
            inputSchema: {
              type: 'object',
              properties: {
                action_id: { type: 'string' },
                result: { type: 'string' },
                effectiveness: { type: 'number', minimum: 0, maximum: 1 },
                notes: { type: 'string' }
              },
              required: ['action_id', 'result']
            }
          }
        ]
      };
    });
  }

  async createSymptom(args) {
    const session = this.driver.session();
    try {
      const result = await session.run(
        'CREATE (s:Symptom {id: randomUUID(), description: $description, severity: $severity, context: $context, created_at: datetime()}) RETURN s',
        args
      );
      return { content: [{ type: 'text', text: `Created symptom: ${JSON.stringify(result.records[0].get('s').properties)}` }] };
    } finally {
      await session.close();
    }
  }

  async createCause(args) {
    const session = this.driver.session();
    try {
      const result = await session.run(
        'CREATE (c:Cause {id: randomUUID(), description: $description, category: $category, confidence: $confidence, created_at: datetime()}) RETURN c',
        args
      );
      return { content: [{ type: 'text', text: `Created cause: ${JSON.stringify(result.records[0].get('c').properties)}` }] };
    } finally {
      await session.close();
    }
  }

  async createAction(args) {
    const session = this.driver.session();
    try {
      const result = await session.run(
        'CREATE (a:Action {id: randomUUID(), description: $description, type: $type, estimated_time: $estimated_time, risk_level: $risk_level, created_at: datetime()}) RETURN a',
        args
      );
      return { content: [{ type: 'text', text: `Created action: ${JSON.stringify(result.records[0].get('a').properties)}` }] };
    } finally {
      await session.close();
    }
  }

  async linkSymptomCause(args) {
    const session = this.driver.session();
    try {
      const result = await session.run(
        'MATCH (s:Symptom {id: $symptom_id}), (c:Cause {id: $cause_id}) CREATE (s)-[r:CAUSED_BY {confidence: $confidence, created_at: datetime()}]->(c) RETURN r',
        args
      );
      return { content: [{ type: 'text', text: `Linked symptom to cause with confidence: ${args.confidence}` }] };
    } finally {
      await session.close();
    }
  }

  async linkCauseAction(args) {
    const session = this.driver.session();
    try {
      const result = await session.run(
        'MATCH (c:Cause {id: $cause_id}), (a:Action {id: $action_id}) CREATE (c)-[r:ADDRESSED_BY {effectiveness: $effectiveness, created_at: datetime()}]->(a) RETURN r',
        args
      );
      return { content: [{ type: 'text', text: `Linked cause to action with effectiveness: ${args.effectiveness}` }] };
    } finally {
      await session.close();
    }
  }

  async queryKnowledgeGraph(args) {
    const session = this.driver.session();
    try {
      const result = await session.run(args.cypher, args.params || {});
      const records = result.records.map(record => record.toObject());
      return { content: [{ type: 'text', text: JSON.stringify(records, null, 2) }] };
    } finally {
      await session.close();
    }
  }

  async getSimilarSymptoms(args) {
    const session = this.driver.session();
    try {
      // Simple similarity based on description keywords
      const result = await session.run(
        'MATCH (s:Symptom) WHERE s.description CONTAINS $keyword RETURN s ORDER BY s.created_at DESC LIMIT $limit',
        { keyword: args.description.split(' ')[0], limit: args.limit || 5 }
      );
      const symptoms = result.records.map(record => record.get('s').properties);
      return { content: [{ type: 'text', text: `Similar symptoms: ${JSON.stringify(symptoms, null, 2)}` }] };
    } finally {
      await session.close();
    }
  }

  async updateActionResult(args) {
    const session = this.driver.session();
    try {
      const result = await session.run(
        'MATCH (a:Action {id: $action_id}) SET a.result = $result, a.effectiveness = $effectiveness, a.notes = $notes, a.completed_at = datetime() RETURN a',
        args
      );
      return { content: [{ type: 'text', text: `Updated action result: ${JSON.stringify(result.records[0].get('a').properties)}` }] };
    } finally {
      await session.close();
    }
  }

  async start() {
    await this.connect();
    await this.server.connect(process.stdin, process.stdout);
  }
}

if (require.main === module) {
  const server = new Neo4jMCPServer();
  server.start().catch(console.error);
}

module.exports = Neo4jMCPServer;