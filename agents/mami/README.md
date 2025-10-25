# SYE-Agent MAMI: Multi-Model Classifier

Multi-model classifier agent that uses GPT, Gemini, and Claude in consensus to classify production errors into Symptom, Cause, and Action categories.

## Architecture

SYE-Agent MAMI follows a three-stage consensus pipeline:

```
User Input
  ↓
[Conditional] Log Parser (coroot/logparser)
  ↓
GPT-5 (first opinion)
  ↓
Gemini 2.5 Pro (second opinion)
  ↓
Claude 4.5 Sonnet (arbitration)
  ↓
Redis Storage (symptom / cause / action / metadata)
```

- **GPT-5** delivers the initial classification.
- **Gemini 2.5 Pro** provides an independent second opinion.
- **Claude 4.5 Sonnet** compares both opinions, resolves conflicts, and issues the final decision with confidence scores.

## Features

- Multi-model consensus classification (GPT-5 → Gemini 2.5 Pro → Claude 4.5 Sonnet)
- Conditional log parsing via coroot/logparser when log format is detected
- Redis-backed storage of symptom / cause / action JSON blobs
- Similarity search to surface related incidents
- Rich console interface for interactive workflows

## Components

- `agent.py` – `MultiModelClassifier` orchestrates GPT-5, Gemini, and Claude calls, enriches logs, and persists consensus decisions to Redis.
- `tools.py` – utility layer for log parsing (coroot/logparser Docker integration), similarity search, and format detection.
- `redis_client.py` – Redis connector that stores and retrieves classification blobs and supports naive similarity matching.
- `main.py` – Rich-powered CLI for classifying new input or retrieving historical results.
- `example.py` – runnable scenarios demonstrating log/text classification, retrieval, and similarity search.

## Setup

### Prerequisites

- Python 3.12
- Redis running on localhost:5769
- Docker (for logparser tool)
- API keys for OpenAI, Google, and Anthropic

### Setup & Quick Run

```bash
# 1. Install dependencies
uv sync

# 2. Quick docker run
docker build -t sye-agent-mami .
docker run -it -p 5769:5769 -p 7474:7474 -p 7687:7687 --env-file .env sye-agent-mami /usr/local/bin/dev-shell.sh

# 3. Smoke test
uv run python example.py 1

# 4. Interactive CLI
uv run python main.py
```

## Usage

The CLI provides three options:

1. **Classify new input**: Enter production errors or logs
2. **Retrieve classification**: Look up stored classifications by ID
3. **Exit**: Quit the application

### Example Inputs

**Structured log**
```
2024-10-25 10:23:45 ERROR [database] Query timeout after 30s (severity=critical)
```

**Plain text**
```
High CPU usage after deploying new model version. Latency increased to 2s.
```

**Complex scenario**
```
Users report 502 errors, load balancer shows backend timeouts, DB pool nearly exhausted.
```

## Classification Schema

Each classification generates three JSON blobs stored in Redis:

**Symptom**:
```json
{
  "id": "uuid",
  "text": "Observable problem description",
  "confidence": 0.85,
  "created_at": "ISO timestamp",
  "model_consensus": ["gpt", "gemini", "claude"]
}
```

**Cause**:
```json
{
  "id": "uuid",
  "text": "Root cause description",
  "confidence": 0.85,
  "created_at": "ISO timestamp",
  "model_consensus": ["gpt", "gemini", "claude"]
}
```

**Action**:
```json
{
  "id": "uuid",
  "text": "Remediation steps",
  "confidence": 0.85,
  "created_at": "ISO timestamp",
  "model_consensus": ["gpt", "gemini", "claude"]
}
```

## Redis Keys

- `classification:{uuid}:symptom` - Symptom JSON
- `classification:{uuid}:cause` - Cause JSON
- `classification:{uuid}:action` - Action JSON
- `classification:{uuid}:metadata` - Metadata with timestamps
