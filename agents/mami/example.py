#!/usr/bin/env python3
"""
Example usage of the MultiModelClassifier
"""

import json
from agent import MultiModelClassifier
from redis_client import RedisClient

def example_log_classification():
    """Example: Classify a production log entry"""
    print("\n" + "="*60)
    print("Example 1: Log Entry Classification")
    print("="*60 + "\n")
    
    classifier = MultiModelClassifier()
    
    log_input = """2024-10-25 10:23:45 ERROR [database] Query timeout after 30s
Connection pool exhausted, 50/50 connections in use
Blocked on: SELECT * FROM orders WHERE status = 'pending'"""
    
    result = classifier.classify(log_input)
    
    print("\n📊 Classification Object:")
    print(f"  Classification ID: {result['classification_id']}")
    
    print("\n  Symptom:")
    print(f"    Text: {result['symptom']['text']}")
    print(f"    Confidence: {result['symptom']['confidence']}")
    print(f"    Models: {', '.join(result['symptom']['model_consensus'])}")
    
    print("\n  Cause:")
    print(f"    Text: {result['cause']['text']}")
    print(f"    Confidence: {result['cause']['confidence']}")
    print(f"    Models: {', '.join(result['cause']['model_consensus'])}")
    
    print("\n  Action:")
    print(f"    Text: {result['action']['text']}")
    print(f"    Confidence: {result['action']['confidence']}")
    print(f"    Models: {', '.join(result['action']['model_consensus'])}")
    
    print("\n  Model Opinions:")
    print("\n    GPT-5 Response:")
    print(f"      {json.dumps(result['gpt_opinion'], indent=6)}")
    print("\n    Gemini Response:")
    print(f"      {json.dumps(result['gemini_opinion'], indent=6)}")
    print("\n    Claude Final Decision:")
    print(f"      {json.dumps(result.get('claude_decision', {}), indent=6)}")

def example_text_classification():
    """Example: Classify plain text error description"""
    print("\n" + "="*60)
    print("Example 2: Plain Text Classification")
    print("="*60 + "\n")
    
    classifier = MultiModelClassifier()
    
    text_input = "High CPU usage after deploying new model version. Latency increased from 100ms to 2000ms."
    
    result = classifier.classify(text_input)
    
    print("\n📊 Classification Object:")
    print(f"  Classification ID: {result['classification_id']}")
    
    print("\n  Symptom:")
    print(f"    Text: {result['symptom']['text']}")
    print(f"    Confidence: {result['symptom']['confidence']}")
    print(f"    Models: {', '.join(result['symptom']['model_consensus'])}")
    
    print("\n  Cause:")
    print(f"    Text: {result['cause']['text']}")
    print(f"    Confidence: {result['cause']['confidence']}")
    print(f"    Models: {', '.join(result['cause']['model_consensus'])}")
    
    print("\n  Action:")
    print(f"    Text: {result['action']['text']}")
    print(f"    Confidence: {result['action']['confidence']}")
    print(f"    Models: {', '.join(result['action']['model_consensus'])}")
    
    print("\n  Model Opinions:")
    print("\n    GPT-5 Response:")
    print(f"      {json.dumps(result['gpt_opinion'], indent=6)}")
    print("\n    Gemini Response:")
    print(f"      {json.dumps(result['gemini_opinion'], indent=6)}")
    print("\n    Claude Final Decision:")
    print(f"      {json.dumps(result.get('claude_decision', {}), indent=6)}")

def example_retrieve_classification(classification_id: str):
    """Example: Retrieve a stored classification"""
    print("\n" + "="*60)
    print("Example 3: Retrieve Stored Classification")
    print("="*60 + "\n")
    
    redis_client = RedisClient()
    result = redis_client.get_classification(classification_id)
    
    if result:
        print(f"✅ Found classification: {classification_id}")
        print(f"\n  Symptom: {result['symptom']['text']}")
        print(f"  Cause: {result['cause']['text']}")
        print(f"  Action: {result['action']['text']}")
        print(f"\n  Created at: {result['metadata'].get('created_at', 'N/A')}")
    else:
        print(f"❌ Classification not found: {classification_id}")

def example_similarity_search():
    """Example: Search for similar classifications"""
    print("\n" + "="*60)
    print("Example 4: Similarity Search")
    print("="*60 + "\n")
    
    from tools import similarity_search_tool
    
    search_text = "database query timeout"
    results = similarity_search_tool(search_text, "symptom")
    
    if results:
        print(f"Found {len(results)} similar symptoms:")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result['text']}")
            print(f"     Similarity: {result['similarity_score']:.2f}")
            print(f"     ID: {result['id']}")
    else:
        print("No similar entries found")

if __name__ == "__main__":
    import sys
    
    print("SYE-Agent MAMI: Example Usage")
    print("="*60)
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        
        if example_num == "1":
            example_log_classification()
        elif example_num == "2":
            example_text_classification()
        elif example_num == "3":
            if len(sys.argv) > 2:
                example_retrieve_classification(sys.argv[2])
            else:
                print("Usage: python example.py 3 <classification_id>")
        elif example_num == "4":
            example_similarity_search()
        else:
            print(f"Unknown example: {example_num}")
            print("Available examples: 1, 2, 3, 4")
    else:
        print("\nUsage: python example.py <example_number>")
        print("\nAvailable examples:")
        print("  1 - Log entry classification")
        print("  2 - Plain text classification")
        print("  3 - Retrieve stored classification (requires classification_id)")
        print("  4 - Similarity search")
        print("\nExample: python example.py 1")

