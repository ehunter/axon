# Axon

**Brain Bank Discovery System** — An AI-powered assistant that helps neuroscience researchers find the ideal brain tissue samples for their studies.

## Overview

Axon is a conversational RAG (Retrieval-Augmented Generation) system that combines:
- A comprehensive database of brain tissue samples from multiple brain banks
- Semantic search powered by vector embeddings
- Expert neuroscience knowledge from research papers
- An intelligent chat agent that understands research needs

## Features

- **Intelligent Sample Discovery** — Describe your research needs in plain language
-  **Expert Knowledge** — RAG system enriched with neuroscience literature
- **Conversational Interface** — Natural back-and-forth like ChatGPT
- **Multi-Source Data** — Unified access to multiple brain bank databases
- **Continuous Learning** — System improves as more papers are ingested

## Quick Start

```bash
# Clone and setup
cd axon
uv sync  # or: pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python scripts/setup_db.py

# Import NIH brain bank data
python scripts/import_nih.py data/imports/nih_samples.csv

# Start chatting
axon chat
```

## Development

```bash
# Run API server
uvicorn axon.api.main:app --reload

# Run tests
pytest

# Database migrations
alembic upgrade head
```

## Architecture

See [PLAN.md](./PLAN.md) for detailed architecture documentation.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL with pgvector
- **AI**: Claude API (Anthropic), OpenAI Embeddings
- **RAG**: LangChain
- **Terminal UI**: Rich, Prompt Toolkit

## License

Proprietary — All rights reserved

---

*Helping neuroscientists find the samples they need, faster.*

