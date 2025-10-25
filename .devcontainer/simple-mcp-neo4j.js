#!/usr/bin/env node

// Simple Neo4j interface for Claude Code MCP integration
const neo4j = require('neo4j-driver');
const redis = require('redis');
const crypto = require('crypto');
const http = require('http');

class SimpleNeo4jMCP {
  constructor() {
    this.driver = null;
    this.redisClient = null;
    this.cacheStats = { hits: 0, misses: 0 };
    this.connect();
    this.connectRedis();
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

  async connectRedis() {
    const redisUrl = process.env.REDIS_URL || 'redis://redis:6379';
    
    try {
      this.redisClient = redis.createClient({ url: redisUrl });
      
      this.redisClient.on('error', (err) => {
        console.error('❌ Redis Client Error:', err);
      });
      
      this.redisClient.on('connect', () => {
        console.log('✅ Connected to Redis at', redisUrl);
      });
      
      await this.redisClient.connect();
    } catch (error) {
      console.error('❌ Failed to connect to Redis:', error.message);
      this.redisClient = null;
    }
  }

  generateSymptomCacheKey(description) {
    return `symptom:${crypto.createHash('md5').update(description.toLowerCase().trim()).digest('hex')}`;
  }

  async getCachedSymptomData(description) {
    if (!this.redisClient) return null;
    
    try {
      const cacheKey = this.generateSymptomCacheKey(description);
      const cached = await this.redisClient.get(cacheKey);
      
      if (cached) {
        this.cacheStats.hits++;
        const data = JSON.parse(cached);
        console.log(`🎯 Cache HIT for symptom: ${description.substring(0, 50)}...`);
        return data;
      }
      
      this.cacheStats.misses++;
      console.log(`❌ Cache MISS for symptom: ${description.substring(0, 50)}...`);
      return null;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  }

  async cacheSymptomData(description, symptomData, ttl = 3600) {
    if (!this.redisClient) return;
    
    try {
      const cacheKey = this.generateSymptomCacheKey(description);
      
      const fullContext = await this.getFullSymptomContext(symptomData.id);
      
      const cacheData = {
        symptom: symptomData,
        causes: fullContext.causes,
        actions: fullContext.actions,
        relationships: fullContext.relationships,
        cached_at: new Date().toISOString(),
        ttl
      };
      
      await this.redisClient.setEx(cacheKey, ttl, JSON.stringify(cacheData));
      console.log(`💾 Cached symptom data: ${description.substring(0, 50)}...`);
    } catch (error) {
      console.error('Cache write error:', error);
    }
  }

  async getFullSymptomContext(symptomId) {
    const session = this.driver.session();
    try {
      const result = await session.run(`
        MATCH (s:Symptom {id: $symptomId})
        OPTIONAL MATCH (s)-[r1:CAUSED_BY]->(c:Cause)
        OPTIONAL MATCH (c)-[r2:ADDRESSED_BY]->(a:Action)
        OPTIONAL MATCH (s)-[r3:SIMILAR_TO]->(similar:Symptom)
        RETURN s,
               collect(DISTINCT {cause: c, relationship: r1}) as causes,
               collect(DISTINCT {action: a, relationship: r2}) as actions,
               collect(DISTINCT {similar: similar, relationship: r3}) as relationships
      `, { symptomId });
      
      if (result.records.length === 0) {
        return { causes: [], actions: [], relationships: [] };
      }
      
      const record = result.records[0];
      return {
        causes: record.get('causes').filter(c => c.cause !== null),
        actions: record.get('actions').filter(a => a.action !== null),
        relationships: record.get('relationships').filter(r => r.similar !== null)
      };
    } finally {
      await session.close();
    }
  }

  async invalidateSymptomCache(symptomId) {
    if (!this.redisClient) return;
    
    try {
      const session = this.driver.session();
      const result = await session.run(`
        MATCH (s:Symptom {id: $symptomId})
        RETURN s.description as description
      `, { symptomId });
      await session.close();
      
      if (result.records.length > 0) {
        const description = result.records[0].get('description');
        const cacheKey = this.generateSymptomCacheKey(description);
        await this.redisClient.del(cacheKey);
        console.log(`🗑️  Invalidated cache for symptom: ${description.substring(0, 50)}...`);
      }
    } catch (error) {
      console.error('Cache invalidation error:', error);
    }
  }

  async warmCache(limit = 50) {
    if (!this.redisClient) return { message: 'Redis not available' };
    
    try {
      const session = this.driver.session();
      const result = await session.run(`
        MATCH (s:Symptom)
        RETURN s.id as id, s.description as description, s.severity as severity
        ORDER BY s.created_at DESC
        LIMIT $limit
      `, { limit: neo4j.int(limit) });
      
      let warmed = 0;
      for (const record of result.records) {
        const symptomData = {
          id: record.get('id'),
          description: record.get('description'),
          severity: record.get('severity')
        };
        
        const cached = await this.getCachedSymptomData(symptomData.description);
        if (!cached) {
          await this.cacheSymptomData(symptomData.description, symptomData);
          warmed++;
        }
      }
      
      await session.close();
      return { 
        message: `Warmed ${warmed} symptoms in cache`,
        total_checked: result.records.length,
        cache_stats: this.cacheStats
      };
    } catch (error) {
      console.error('Cache warming error:', error);
      return { error: error.message };
    }
  }

  async getCacheStats() {
    const stats = { ...this.cacheStats };
    
    if (this.redisClient) {
      try {
        const info = await this.redisClient.info('memory');
        const keyspace = await this.redisClient.info('keyspace');
        
        stats.redis_connected = true;
        stats.redis_memory = info;
        stats.redis_keyspace = keyspace;
        
        const symptomKeys = await this.redisClient.keys('symptom:*');
        stats.cached_symptoms = symptomKeys.length;
      } catch (error) {
        stats.redis_error = error.message;
      }
    } else {
      stats.redis_connected = false;
    }
    
    return stats;
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
      const symptomData = {
        id: record.get('id'),
        description: record.get('description'),
        severity,
        message: `Created symptom: ${description}`
      };
      
      await this.cacheSymptomData(description, symptomData);
      
      return symptomData;
    } finally {
      await session.close();
    }
  }

  async getSimilarSymptoms(description, limit = 5) {
    const cached = await this.getCachedSymptomData(description);
    if (cached && cached.relationships && cached.relationships.length > 0) {
      console.log(`🎯 Returning cached similar symptoms for: ${description.substring(0, 50)}...`);
      return cached.relationships.slice(0, limit).map(r => ({
        id: r.similar.properties.id,
        description: r.similar.properties.description,
        severity: r.similar.properties.severity
      }));
    }
    
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
          },
          {
            name: 'warm_cache',
            description: 'Pre-populate cache with recent symptoms',
            parameters: {
              limit: 'number (optional, default: 50)'
            }
          },
          {
            name: 'cache_stats',
            description: 'Get cache performance statistics',
            parameters: {}
          },
          {
            name: 'invalidate_cache',
            description: 'Invalidate cache for a specific symptom',
            parameters: {
              symptom_id: 'string (required)'
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
              case 'warm_cache':
                result = await this.warmCache(params.limit);
                break;
              case 'cache_stats':
                result = await this.getCacheStats();
                break;
              case 'invalidate_cache':
                result = await this.invalidateSymptomCache(params.symptom_id);
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