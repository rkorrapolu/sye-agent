# Self-Improving Yolo Engine

SYE (Self-Improving Yolo Engine) is designed to demonstrate a self-improving knowledge system that learns from production errors. In this project, “YOLO” means identifying the right context of input, whether logs, text, or images.

SYE is a self-improving AI agent that learns production insights in real time. A loop from input, classification, verification, and graph update.

The agent uses **smolagents**, **Neo4j**, and **Redis** to build a lightweight self-improving knowledge graph that shows:
1. Classification of user input into **Symptom**, **Cause**, and **Action**.  
2. Storing and linking this in Neo4j as a mini knowledge graph.  
3. Simulated self-improvement, the system updates relationships when verified by a user.

## Overview
Every user input (log, message, or observation) is processed by the agent and categorized into one of three types:

- **Symptom** (What’s happening?)  
- **Cause** (Why it happens?)  
- **Action** (How to fix it?)  

After classification, the user verifies or adjusts these categories. The system then updates the knowledge graph, learning stronger patterns for future use.

## Goal

1. **Input** (text log, message)  
2. **smol-agent classification** → Symptom / Cause / Action  
3. **Neo4j graph storage** (create or update nodes & relationships)  
4. **Feedback loop** — user modifies or approves classification  
5. **Graph update** — store user feedback and new connections  

## Setup

### Steps
1. Start Neo4j and Redis via Docker Compose.
2. Run `main.py` to start processing user input.
3. Enter logs or short text.
4. Inspect relationships in the Neo4j browser (`localhost:7474`).
5. Verify or update classifications and rerun.

## Team Breakdown

| Role | Member Tasks | Deliverables |
|------|---------------|--------------|
| **Agent & Logic Dev** | Build smol-agent pipeline for categorization. Define prompt templates for Symptom, Cause, Action. | Classification script (`agent.py`) working with simple text. |
| **Graph Dev** | Integrate Neo4j. Write simple CRUD for nodes and relations (`graph.py`). | Function to insert/update relationships: Symptom → Cause → Action. |
| **Backend/API Dev** | Connect agent + graph via FastAPI or Streamlit for quick I/O testing. | Simple interactive UI endpoint that takes text input and returns graph JSON. |
| **Demo & Feedback Lead** | Handle Redis caching for fast lookup, prepare example inputs, polish the README/demo flow. | Live demo and example queries showing learning from user corrections. |

## Demo Scenario
Input example:  
> “High CPU usage after deploying new model version.”

Agent response →  
- Symptom: “High CPU usage”  
- Cause: “Model update increases load”  
- Action: “Scale up container or optimize inference”  

Neo4j graph shows:
```
(:Symptom {name:"High CPU"})
   -> (:Cause {name:"Model update"})
   -> (:Action {name:"Scale resources"})
```

User corrects if necessary. Agent stores the validated relationship for future predictions.

## Stretch Goals
- Add embeddings for similarity-based lookup.  
- Visualize graph relationships in browser.  
- Cache last N queries in Redis for rapid recall.  
