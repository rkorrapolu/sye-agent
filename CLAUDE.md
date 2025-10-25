# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SYE (Self-Improving Yolo Engine) is a self-improving AI agent that learns production insights in real time through a feedback loop. The system:

1. Classifies user input (logs, text, messages) into **Symptom**, **Cause**, and **Action**
2. Stores relationships in Neo4j as a knowledge graph
3. Allows user verification/correction of classifications
4. Updates the graph based on feedback to improve future predictions

## Architecture

The system follows a simple pipeline:
- **Input** → **smolagents classification** → **Neo4j storage** → **User feedback** → **Graph update**

Key components mentioned in README:
- **smolagents** for AI-powered classification
- **Neo4j** for knowledge graph storage and relationships
- **Redis** for caching and fast lookup
- **FastAPI or Streamlit** for user interface (planned)

## Development Setup

### Prerequisites
- Docker Compose (for Neo4j and Redis)
- Python environment

### Getting Started
1. Start infrastructure: `docker-compose up` (Neo4j + Redis)
2. Run main application: `python main.py`
3. Access Neo4j browser at `localhost:7474` for graph visualization

## Code Organization

This appears to be an early-stage project with the following planned structure:
- `agent.py` - smolagents pipeline for text classification
- `graph.py` - Neo4j CRUD operations for nodes and relationships  
- `main.py` - Main application entry point
- API layer (FastAPI/Streamlit) for user interaction

## Code Style Guidelines

Based on `.cursor/rules/code-style.mdc`:

### Function Organization
- Group related functions with section comments (e.g., `/** Core Functions **/`)
- Keep related functionality together in cohesive functions
- Avoid over-splitting into many tiny helper functions

### Comments Policy
- Avoid obvious comments that restate code
- Only comment complex business logic or non-obvious decisions
- Self-documenting code through clear naming is preferred

### Python Specific
- Group related functions and classes without extra newlines
- Keep error handling and validation logic grouped together

## Demo Flow

Example input: "High CPU usage after deploying new model version"

Expected classification:
- **Symptom**: "High CPU usage"
- **Cause**: "Model update increases load" 
- **Action**: "Scale up container or optimize inference"

Neo4j stores as: `(:Symptom) -> (:Cause) -> (:Action)` relationships

## Future Enhancements
- Embeddings for similarity-based lookup
- Graph relationship visualization
- Redis caching for rapid query recall