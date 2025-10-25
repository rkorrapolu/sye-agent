import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import redis
from dotenv import load_dotenv

load_dotenv()

class RedisClient:
  """
  Redis client for storing and retrieving classification data.
  
  Connects to Redis server and provides methods for:
  - Storing classifications (symptom, cause, action)
  - Retrieving classifications by ID
  - Searching for similar entries
  """
  
  def __init__(self):
    """Initialize Redis connection using environment variables."""
    self.host = os.getenv("REDIS_HOST", "localhost")
    self.port = int(os.getenv("REDIS_PORT", "5769"))
    
    self.client = redis.Redis(
      host=self.host,
      port=self.port,
      decode_responses=True
    )
    
    try:
      self.client.ping()
      print(f"✅ Connected to Redis at {self.host}:{self.port}")
    except redis.ConnectionError as e:
      print(f"❌ Failed to connect to Redis: {e}")
      raise
  
  def store_classification(
    self, 
    classification_id: str, 
    symptom: Dict[str, Any], 
    cause: Dict[str, Any], 
    action: Dict[str, Any]
  ) -> bool:
    """
    Store a classification with symptom, cause, and action as separate JSON blobs.
    
    Args:
      classification_id: Unique identifier for this classification
      symptom: Symptom data dictionary
      cause: Cause data dictionary
      action: Action data dictionary
      
    Returns:
      bool: True if successful, False otherwise
    """
    try:
      symptom_key = f"classification:{classification_id}:symptom"
      cause_key = f"classification:{classification_id}:cause"
      action_key = f"classification:{classification_id}:action"
      
      self.client.set(symptom_key, json.dumps(symptom))
      self.client.set(cause_key, json.dumps(cause))
      self.client.set(action_key, json.dumps(action))
      
      metadata_key = f"classification:{classification_id}:metadata"
      metadata = {
        "created_at": datetime.now().isoformat(),
        "symptom_key": symptom_key,
        "cause_key": cause_key,
        "action_key": action_key
      }
      self.client.set(metadata_key, json.dumps(metadata))
      
      return True
    except Exception as e:
      print(f"Error storing classification: {e}")
      return False
  
  def get_classification(self, classification_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete classification by ID.
    
    Args:
      classification_id: Unique identifier for the classification
      
    Returns:
      Dictionary with symptom, cause, action, and metadata, or None if not found
    """
    try:
      symptom_key = f"classification:{classification_id}:symptom"
      cause_key = f"classification:{classification_id}:cause"
      action_key = f"classification:{classification_id}:action"
      metadata_key = f"classification:{classification_id}:metadata"
      
      symptom_data = self.client.get(symptom_key)
      cause_data = self.client.get(cause_key)
      action_data = self.client.get(action_key)
      metadata_data = self.client.get(metadata_key)
      
      if not all([symptom_data, cause_data, action_data]):
        return None
      
      return {
        "classification_id": classification_id,
        "symptom": json.loads(symptom_data),
        "cause": json.loads(cause_data),
        "action": json.loads(action_data),
        "metadata": json.loads(metadata_data) if metadata_data else {}
      }
    except Exception as e:
      print(f"Error retrieving classification: {e}")
      return None
  
  def search_similar(self, text: str, node_type: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for similar entries in Redis based on text and node type.
    
    Args:
      text: Text to search for
      node_type: Type of node (symptom, cause, or action)
      limit: Maximum number of results to return
      
    Returns:
      List of similar entries with id, text, and similarity score
    """
    try:
      pattern = f"classification:*:{node_type}"
      results = []
      
      for key in self.client.scan_iter(match=pattern):
        data_str = self.client.get(key)
        if data_str:
          data = json.loads(data_str)
          stored_text = data.get("text", "")
          
          similarity = self._calculate_similarity(text.lower(), stored_text.lower())
          
          if similarity > 0.3:
            classification_id = key.split(":")[1]
            results.append({
              "id": classification_id,
              "text": stored_text,
              "similarity_score": similarity,
              "data": data
            })
      
      results.sort(key=lambda x: x["similarity_score"], reverse=True)
      return results[:limit]
    except Exception as e:
      print(f"Error searching for similar entries: {e}")
      return []
  
  def _calculate_similarity(self, text1: str, text2: str) -> float:
    """
    Simple word-based similarity calculation.
    
    Args:
      text1: First text string
      text2: Second text string
      
    Returns:
      Similarity score between 0 and 1
    """
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
      return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0