# Module Imports
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

from cache_warmup import warmup_cache
from neo4j_tool import Neo4jKnowledgeGraphTool
from redis_client import RedisClient
from semantic_cache import Neo4jSemanticCache, get_semantic_cache
from tools import is_log_format, logparser_tool, similarity_search_tool

load_dotenv()


# Core Class
class MultiModelClassifier:
  """Multi-model classifier with Neo4j and semantic cache integration."""

  def __init__(self):
    self.openai_api_key = os.getenv("OPENAI_API_KEY")
    self.google_api_key = os.getenv("GOOGLE_API_KEY")
    self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not all([self.openai_api_key, self.google_api_key, self.anthropic_api_key]):
      raise ValueError("Missing required API keys in .env file")

    self.openai_client = OpenAI(api_key=self.openai_api_key)
    self.genai_client = genai.Client(api_key=self.google_api_key)
    self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)

    self.redis_client = RedisClient()
    self.semantic_cache: Optional[Neo4jSemanticCache] = None
    self.neo4j_tool: Optional[Neo4jKnowledgeGraphTool] = None
    self._cache_warmed = False

    self._initialize_semantic_infrastructure()

    print(
      "✅ MultiModelClassifier ready with GPT-5, Gemini 2.5 Pro, Claude 4.5, and Neo4j integration"
    )

  # Initialization
  def _initialize_semantic_infrastructure(self):
    """Set up semantic cache and Neo4j tooling."""
    try:
      self.semantic_cache = get_semantic_cache()
    except Exception as exc:
      print(f"⚠️ Semantic cache unavailable: {exc}")
      self.semantic_cache = None

    try:
      self.neo4j_tool = Neo4jKnowledgeGraphTool()
      self._warmup_cache_once()
    except Exception as exc:
      print(f"⚠️ Neo4j integration disabled: {exc}")
      self.neo4j_tool = None

  def _warmup_cache_once(self):
    """Warm semantic cache with existing Neo4j data."""
    if self._cache_warmed or not self.semantic_cache or not self.neo4j_tool:
      return

    try:
      warmup_cache()
      self._cache_warmed = True
    except Exception as exc:
      print(f"⚠️ Cache warmup skipped: {exc}")

  # Classification Pipeline
  def classify(self, user_input: str) -> Dict[str, Any]:
    print(f"\n{'=' * 60}")
    print("🔍 Starting classification pipeline")
    print(f"{'=' * 60}\n")

    enriched_input = user_input
    parsed_data = None

    if is_log_format(user_input):
      print("📋 Detected log format, parsing with logparser...")
      parsed_data = logparser_tool(user_input)
      enriched_input = self._enrich_with_parsed_data(user_input, parsed_data)
      print(
        f"✅ Parsed: {parsed_data.get('severity')} severity, {len(parsed_data.get('components', []))} components"
      )

    print("\n" + "-" * 60)
    print("🤖 Step 1: Getting GPT-5 first opinion...")
    print("-" * 60)
    gpt_classification = self._call_gpt_for_classification(enriched_input)
    print("✅ GPT-5 opinion received")

    print("\n" + "-" * 60)
    print("🤖 Step 2: Getting Gemini second opinion...")
    print("-" * 60)
    gemini_classification = self._call_gemini_for_classification(enriched_input)
    print("✅ Gemini opinion received")

    print("\n" + "-" * 60)
    print("🤖 Step 3: Claude 4.5 Sonnet making final decision...")
    print("-" * 60)
    final_classification = self._call_claude_for_final_decision(
      enriched_input, gpt_classification, gemini_classification
    )
    print("✅ Claude final decision made")

    classification_id = str(uuid.uuid4())

    symptom = {
      "id": classification_id,
      "text": final_classification["symptom"],
      "confidence": final_classification.get("symptom_confidence", 0.85),
      "created_at": datetime.now().isoformat(),
      "model_consensus": ["gpt", "gemini", "claude"],
    }

    cause = {
      "id": classification_id,
      "text": final_classification["cause"],
      "confidence": final_classification.get("cause_confidence", 0.85),
      "created_at": datetime.now().isoformat(),
      "model_consensus": ["gpt", "gemini", "claude"],
    }

    action = {
      "id": classification_id,
      "text": final_classification["action"],
      "confidence": final_classification.get("action_confidence", 0.85),
      "created_at": datetime.now().isoformat(),
      "model_consensus": ["gpt", "gemini", "claude"],
    }

    semantic_matches = self._gather_semantic_matches(final_classification)
    knowledge_graph_info = self._persist_to_knowledge_graph(
      classification_id, final_classification
    )
    similarity_matches = self._retrieve_similarity_matches(final_classification)

    self.redis_client.store_classification(classification_id, symptom, cause, action)

    print(f"\n{'=' * 60}")
    print(f"✅ Classification stored with ID: {classification_id}")
    print(f"{'=' * 60}\n")

    return {
      "classification_id": classification_id,
      "symptom": symptom,
      "cause": cause,
      "action": action,
      "parsed_data": parsed_data,
      "gpt_opinion": gpt_classification,
      "gemini_opinion": gemini_classification,
      "claude_decision": final_classification,
      "semantic_matches": semantic_matches,
      "knowledge_graph": knowledge_graph_info,
      "similarity_matches": similarity_matches,
    }

  # Knowledge Graph Integration
  def _persist_to_knowledge_graph(
    self, classification_id: str, final: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Write classification results to Neo4j and update cache."""
    if not self.neo4j_tool:
      return {"success": False, "reason": "neo4j_unavailable"}

    graph_payload = self._build_graph_payload(classification_id, final)

    try:
      response = self.neo4j_tool.forward("write_graph", json.dumps(graph_payload))
      data = json.loads(response)
    except Exception as exc:
      print(f"⚠️ Neo4j write error: {exc}")
      return {"success": False, "reason": str(exc)}

    nodes = {
      "symptom": self._lookup_node("Symptom", final["symptom"]),
      "cause": self._lookup_node("Cause", final["cause"]),
      "action": self._lookup_node("Action", final["action"]),
    }

    self._store_nodes_in_cache(nodes, final)

    return {
      "success": data.get("success", False),
      "run_id": data.get("run_id"),
      "nodes_created": data.get("nodes_created", 0),
      "relationships_created": data.get("relationships_created", 0),
      "nodes": nodes,
    }

  def _build_graph_payload(
    self, classification_id: str, final: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Prepare graph payload for Neo4j write."""
    nodes = [
      self._node_payload(classification_id, "symptom", "Symptom", final),
      self._node_payload(classification_id, "cause", "Cause", final),
      self._node_payload(classification_id, "action", "Action", final),
    ]

    relationships = [
      {
        "type": "CAUSES",
        "start_node_id": f"{classification_id}:cause",
        "end_node_id": f"{classification_id}:symptom",
        "properties": {"confidence": final.get("cause_confidence", 0.85)},
      },
      {
        "type": "FIXES",
        "start_node_id": f"{classification_id}:action",
        "end_node_id": f"{classification_id}:cause",
        "properties": {"confidence": final.get("action_confidence", 0.85)},
      },
    ]

    return {"nodes": nodes, "relationships": relationships}

  def _node_payload(
    self, classification_id: str, key: str, label: str, final: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Create individual node payload."""
    confidence_key = f"{key}_confidence"
    text_value = final[key]

    return {
      "id": f"{classification_id}:{key}",
      "label": label,
      "properties": {
        "name": text_value,
        "description": text_value,
        "confidence": final.get(confidence_key, 0.85),
        "classification_id": classification_id,
      },
    }

  def _lookup_node(self, label: str, name: str) -> List[Dict[str, Any]]:
    """Fetch node details from cache/Neo4j."""
    if not self.neo4j_tool:
      return []

    try:
      response = self.neo4j_tool.forward(
        "query_existing", json.dumps({"name": name, "label": label})
      )
      data = json.loads(response)
      return data.get("nodes", [])
    except Exception as exc:
      print(f"⚠️ Failed to lookup {label} node: {exc}")
      return []

  # Cache Helpers
  def _store_nodes_in_cache(
    self, nodes: Dict[str, List[Dict[str, Any]]], final: Dict[str, Any]
  ):
    """Persist knowledge graph nodes into semantic cache."""
    if not self.semantic_cache:
      return

    label_mapping = {"symptom": "Symptom", "cause": "Cause", "action": "Action"}

    for key, label in label_mapping.items():
      node_entries = nodes.get(key) or []
      text_value = final.get(key)

      payload = node_entries or [
        {
          "node_id": None,
          "name": text_value,
          "created_at": datetime.now().isoformat(),
          "times_seen": 1,
        }
      ]

      try:
        self.semantic_cache.store(text_value, payload, label)
      except Exception as exc:
        print(f"⚠️ Unable to store {label} node in cache: {exc}")

  # Helper Functions
  def _gather_semantic_matches(
    self, final: Dict[str, Any]
  ) -> Dict[str, List[Dict[str, Any]]]:
    """Collect semantic cache matches for each category."""
    if not self.semantic_cache:
      return {}

    matches = {}

    for label, key in [
      ("Symptom", "symptom"),
      ("Cause", "cause"),
      ("Action", "action"),
    ]:
      try:
        nodes = self.semantic_cache.check(final[key], label) or []
        if nodes:
          matches[key] = nodes
      except Exception as exc:
        print(f"⚠️ Semantic cache check failed for {label}: {exc}")

    return matches

  def _retrieve_similarity_matches(
    self, final: Dict[str, Any]
  ) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch similarity matches from Redis for quick suggestions."""
    categories = {"symptom": "symptom", "cause": "cause", "action": "action"}

    results: Dict[str, List[Dict[str, Any]]] = {}

    for key, node_type in categories.items():
      try:
        matches = similarity_search_tool(final[key], node_type)
        if matches:
          results[key] = matches
      except Exception as exc:
        print(f"⚠️ Similarity search failed for {node_type}: {exc}")

    return results

  def _enrich_with_parsed_data(
    self, original_input: str, parsed_data: Dict[str, Any]
  ) -> str:
    enrichment = "\n\n[Parsed Log Info]\n"
    enrichment += f"Severity: {parsed_data.get('severity', 'N/A')}\n"
    enrichment += f"Components: {', '.join(parsed_data.get('components', []))}\n"
    enrichment += f"Pattern: {parsed_data.get('pattern', 'N/A')}\n"
    return original_input + enrichment

  def _call_gpt_for_classification(self, user_input: str) -> Dict[str, Any]:
    prompt = f"""You are a production error classification expert.

Given the following production error or observation, classify it into:
1. SYMPTOM: The observable problem (what's wrong)
2. CAUSE: The root cause (why it's happening)
3. ACTION: The remediation step (how to fix it)

If any category is not mentioned or unclear, provide your best inference based on the information given.

Input:
{user_input}

Respond with valid JSON in this exact format:
{{
  "symptom": "description of the symptom",
  "cause": "description of the cause",
  "action": "description of the action"
}}"""

    try:
      response = self.openai_client.responses.create(
        model="gpt-5",
        input=[
          {
            "role": "system",
            "content": [
              {
                "type": "input_text",
                "text": "You are a production error classification expert. Always respond with valid JSON.",
              }
            ],
          },
          {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
        ],
        max_output_tokens=5000,
      )
      content = getattr(response, "output_text", None)

      if not content:
        content_chunks = []
        for item in getattr(response, "output", []) or []:
          if hasattr(item, "content") and item.content:
            for block in item.content:
              if hasattr(block, "text") and block.text:
                content_chunks.append(block.text)

        content = "".join(content_chunks).strip()

      if not content:
        raise ValueError(
          f"GPT-5 response status: {response.status}, incomplete_details: {getattr(response, 'incomplete_details', None)}"
        )

      return json.loads(content)
    except Exception as e:
      print(f"⚠️ GPT-5 error: {e}")
      return {
        "symptom": "Unable to classify symptom",
        "cause": "Unable to determine cause",
        "action": "Unable to suggest action",
      }

  def _call_gemini_for_classification(self, user_input: str) -> Dict[str, Any]:
    prompt = f"""You are a production incident analyzer providing an alternative perspective.

Analyze this production error and classify it into:
1. SYMPTOM: What is the observable problem?
2. CAUSE: What is the underlying root cause?
3. ACTION: What remediation should be taken?

Provide your independent analysis, even if you have a different interpretation.

Input:
{user_input}

Respond with valid JSON in this exact format:
{{
  "symptom": "description of the symptom",
  "cause": "description of the cause",
  "action": "description of the action"
}}"""

    try:
      from google.genai import types

      response = self.genai_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
      )
      content = response.text
      return json.loads(content)
    except Exception as e:
      print(f"⚠️ Gemini error: {e}")
      return {
        "symptom": "Unable to classify symptom",
        "cause": "Unable to determine cause",
        "action": "Unable to suggest action",
      }

  def _call_claude_for_final_decision(
    self, user_input: str, gpt_opinion: Dict[str, Any], gemini_opinion: Dict[str, Any]
  ) -> Dict[str, Any]:
    prompt = f"""You are the final arbitrator for production error classification.

You have received two independent opinions on how to classify a production error.
Your task is to review both opinions, resolve any conflicts, and provide the final classification.

Original Input:
{user_input}

GPT-5 Opinion:
- Symptom: {gpt_opinion.get("symptom", "N/A")}
- Cause: {gpt_opinion.get("cause", "N/A")}
- Action: {gpt_opinion.get("action", "N/A")}

Gemini Opinion:
- Symptom: {gemini_opinion.get("symptom", "N/A")}
- Cause: {gemini_opinion.get("cause", "N/A")}
- Action: {gemini_opinion.get("action", "N/A")}

Analyze both opinions and provide your final decision. Where they agree, confirm. Where they differ, choose the most accurate classification or synthesize a better one.

Respond with valid JSON in this exact format:
{{
  "symptom": "final symptom description",
  "cause": "final cause description",
  "action": "final action description",
  "symptom_confidence": 0.85,
  "cause_confidence": 0.85,
  "action_confidence": 0.85
}}"""

    try:
      response = self.anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
      )
      content = response.content[0].text

      json_match = content
      if "```json" in content:
        json_match = content.split("```json")[1].split("```")[0]
      elif "```" in content:
        json_match = content.split("```")[1].split("```")[0]

      return json.loads(json_match.strip())
    except Exception as e:
      print(f"⚠️ Claude error: {e}")
      return {
        "symptom": gpt_opinion.get("symptom", "Unable to classify"),
        "cause": gpt_opinion.get("cause", "Unable to determine"),
        "action": gpt_opinion.get("action", "Unable to suggest"),
        "symptom_confidence": 0.5,
        "cause_confidence": 0.5,
        "action_confidence": 0.5,
      }
