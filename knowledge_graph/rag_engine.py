#!/usr/bin/env python3

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np
from neo4j import GraphDatabase
import redis

@dataclass
class KnowledgeNode:
    id: str
    type: str  # 'symptom', 'cause', 'action'
    description: str
    embedding: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RagContext:
    similar_symptoms: List[KnowledgeNode]
    related_causes: List[KnowledgeNode] 
    successful_actions: List[KnowledgeNode]
    confidence_scores: Dict[str, float]

class SYEKnowledgeGraphRAG:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.neo4j_driver = None
        self.redis_client = None
        self.connect_databases()
    
    def connect_databases(self):
        """Connect to Neo4j and Redis"""
        # Neo4j connection
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password123')
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Redis connection for embedding cache
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis_client = redis.from_url(redis_url)
        
        print("✅ Connected to Neo4j and Redis for RAG")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text with Redis caching"""
        cache_key = f"embedding:{hash(text)}"
        
        # Try to get from cache
        cached_embedding = self.redis_client.get(cache_key)
        if cached_embedding:
            return np.frombuffer(cached_embedding, dtype=np.float32)
        
        # Generate new embedding
        embedding = self.embedding_model.encode(text)
        
        # Cache the embedding
        self.redis_client.setex(cache_key, 3600, embedding.tobytes())  # Cache for 1 hour
        
        return embedding

    def get_similar_symptoms(self, symptom_description: str, limit: int = 5) -> List[KnowledgeNode]:
        """Find similar symptoms using semantic similarity"""
        symptom_embedding = self.generate_embedding(symptom_description)
        
        with self.neo4j_driver.session() as session:
            # Get all symptoms with their descriptions
            result = session.run("""
                MATCH (s:Symptom)
                RETURN s.id as id, s.description as description, 
                       s.severity as severity, s.context as context
                ORDER BY s.created_at DESC
                LIMIT 50
            """)
            
            symptoms = []
            for record in result:
                node_embedding = self.generate_embedding(record['description'])
                similarity = np.dot(symptom_embedding, node_embedding) / (
                    np.linalg.norm(symptom_embedding) * np.linalg.norm(node_embedding)
                )
                
                symptoms.append({
                    'node': KnowledgeNode(
                        id=record['id'],
                        type='symptom',
                        description=record['description'],
                        embedding=node_embedding,
                        metadata={
                            'severity': record['severity'],
                            'context': record['context']
                        }
                    ),
                    'similarity': similarity
                })
            
            # Sort by similarity and return top results
            symptoms.sort(key=lambda x: x['similarity'], reverse=True)
            return [item['node'] for item in symptoms[:limit]]

    def get_causes_for_symptoms(self, symptom_ids: List[str]) -> List[KnowledgeNode]:
        """Get causes linked to similar symptoms"""
        if not symptom_ids:
            return []
            
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:Symptom)-[r:CAUSED_BY]->(c:Cause)
                WHERE s.id IN $symptom_ids
                RETURN c.id as id, c.description as description,
                       c.category as category, c.confidence as confidence,
                       avg(r.confidence) as avg_relationship_confidence
                ORDER BY avg_relationship_confidence DESC
            """, symptom_ids=symptom_ids)
            
            causes = []
            for record in result:
                causes.append(KnowledgeNode(
                    id=record['id'],
                    type='cause',
                    description=record['description'],
                    metadata={
                        'category': record['category'],
                        'confidence': record['confidence'],
                        'relationship_confidence': record['avg_relationship_confidence']
                    }
                ))
            
            return causes

    def get_actions_for_causes(self, cause_ids: List[str]) -> List[KnowledgeNode]:
        """Get actions that have been effective for similar causes"""
        if not cause_ids:
            return []
            
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Cause)-[r:ADDRESSED_BY]->(a:Action)
                WHERE c.id IN $cause_ids
                RETURN a.id as id, a.description as description,
                       a.type as action_type, a.risk_level as risk_level,
                       a.estimated_time as estimated_time,
                       avg(r.effectiveness) as avg_effectiveness,
                       count(r) as usage_count
                ORDER BY avg_effectiveness DESC, usage_count DESC
            """, cause_ids=cause_ids)
            
            actions = []
            for record in result:
                actions.append(KnowledgeNode(
                    id=record['id'],
                    type='action',
                    description=record['description'],
                    metadata={
                        'action_type': record['action_type'],
                        'risk_level': record['risk_level'],
                        'estimated_time': record['estimated_time'],
                        'effectiveness': record['avg_effectiveness'],
                        'usage_count': record['usage_count']
                    }
                ))
            
            return actions

    def get_rag_context(self, symptom_description: str) -> RagContext:
        """Get comprehensive RAG context for a symptom"""
        # Find similar symptoms
        similar_symptoms = self.get_similar_symptoms(symptom_description)
        
        # Get causes for those symptoms
        symptom_ids = [s.id for s in similar_symptoms]
        related_causes = self.get_causes_for_symptoms(symptom_ids)
        
        # Get actions for those causes
        cause_ids = [c.id for c in related_causes]
        successful_actions = self.get_actions_for_causes(cause_ids)
        
        # Calculate confidence scores
        confidence_scores = {
            'symptom_similarity': np.mean([0.8, 0.6, 0.4]) if similar_symptoms else 0.0,  # Placeholder
            'cause_relevance': np.mean([c.metadata.get('confidence', 0.5) for c in related_causes]) if related_causes else 0.0,
            'action_effectiveness': np.mean([a.metadata.get('effectiveness', 0.5) for a in successful_actions]) if successful_actions else 0.0
        }
        
        return RagContext(
            similar_symptoms=similar_symptoms,
            related_causes=related_causes,
            successful_actions=successful_actions,
            confidence_scores=confidence_scores
        )

    def format_context_for_claude(self, context: RagContext) -> str:
        """Format RAG context as text for Claude"""
        formatted_context = "# Knowledge Graph Context\n\n"
        
        if context.similar_symptoms:
            formatted_context += "## Similar Symptoms Seen Before:\n"
            for symptom in context.similar_symptoms[:3]:  # Top 3
                severity = symptom.metadata.get('severity', 'unknown')
                formatted_context += f"- **{symptom.description}** (Severity: {severity})\n"
            formatted_context += "\n"
        
        if context.related_causes:
            formatted_context += "## Likely Causes Based on History:\n"
            for cause in context.related_causes[:3]:  # Top 3
                confidence = cause.metadata.get('confidence', 0)
                category = cause.metadata.get('category', 'general')
                formatted_context += f"- **{cause.description}** (Category: {category}, Confidence: {confidence:.1%})\n"
            formatted_context += "\n"
        
        if context.successful_actions:
            formatted_context += "## Actions That Have Worked:\n"
            for action in context.successful_actions[:3]:  # Top 3
                effectiveness = action.metadata.get('effectiveness', 0)
                risk = action.metadata.get('risk_level', 'unknown')
                time = action.metadata.get('estimated_time', 'unknown')
                formatted_context += f"- **{action.description}** (Effectiveness: {effectiveness:.1%}, Risk: {risk}, Time: {time})\n"
            formatted_context += "\n"
        
        # Add confidence summary
        formatted_context += "## Context Confidence:\n"
        for metric, score in context.confidence_scores.items():
            formatted_context += f"- {metric.replace('_', ' ').title()}: {score:.1%}\n"
        
        if not any([context.similar_symptoms, context.related_causes, context.successful_actions]):
            formatted_context += "No similar cases found in knowledge graph. This appears to be a new type of issue.\n"
        
        return formatted_context

    def update_embeddings_for_new_nodes(self):
        """Update embeddings for nodes that don't have them yet"""
        with self.neo4j_driver.session() as session:
            # This would be called periodically to ensure all nodes have embeddings
            # For now, embeddings are generated on-demand
            pass

    def close(self):
        """Close database connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.redis_client:
            self.redis_client.close()

# Convenience function for Claude to use
def get_knowledge_context(symptom_description: str) -> str:
    """Get formatted knowledge graph context for a symptom"""
    rag_engine = SYEKnowledgeGraphRAG()
    try:
        context = rag_engine.get_rag_context(symptom_description)
        return rag_engine.format_context_for_claude(context)
    finally:
        rag_engine.close()

if __name__ == "__main__":
    # Test the RAG engine
    test_symptom = "API response time is very slow"
    context = get_knowledge_context(test_symptom)
    print(context)