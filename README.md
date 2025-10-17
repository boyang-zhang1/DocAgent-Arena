# RAGRace

A comprehensive platform for comparing and benchmarking different RAG (Retrieval-Augmented Generation) APIs and services.

## Overview

RAGRace provides a standardized framework to evaluate and compare RAG providers using unified interfaces and automated scoring. The platform supports multiple providers with a consistent `BaseAdapter` interface for fair, apples-to-apples comparison.

**Current Status**: 3 RAG providers integrated with 54 passing tests (44 unit + 10 integration).

## Integrated Providers

| Provider | Type | Key Features | Status |
|----------|------|--------------|--------|
| **[LlamaIndex](docs/ADAPTERS.md#llamaindex)** | Full RAG Framework | VectorStoreIndex, built-in embeddings | ✅ Tested |
| **[LandingAI](docs/ADAPTERS.md#landingai-ade-agentic-document-extraction)** | Doc Preprocessing | 8 chunk types, grounding metadata | ✅ Tested |
| **[Reducto](docs/ADAPTERS.md#reducto)** | Doc Preprocessing | Embedding-optimized, AI enrichment | ✅ Tested |

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/RAGRace.git
cd RAGRace

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env
OPENAI_API_KEY=your_openai_key_here
VISION_AGENT_API_KEY=your_landingai_key_here  # For LandingAI
REDUCTO_API_KEY=your_reducto_key_here          # For Reducto
```

### Basic Usage

```python
from src.adapters import LlamaIndexAdapter, Document
import os

# Initialize adapter
adapter = LlamaIndexAdapter()
adapter.initialize(api_key=os.getenv("OPENAI_API_KEY"))

# Prepare documents
docs = [
    Document(
        id="doc1",
        content="Your document text here...",
        metadata={"source": "example"}
    )
]

# Ingest documents
index_id = adapter.ingest_documents(docs)

# Query
response = adapter.query("What is this document about?", index_id)

# Get results
print(f"Answer: {response.answer}")
print(f"Context chunks: {len(response.context)}")
print(f"Latency: {response.latency_ms:.2f}ms")
```

## Running Tests

```bash
# Run unit tests (fast, no API calls)
pytest tests/ -v -k "not integration"

# Run integration tests (real API calls, costs money)
pytest tests/ -v -m integration -s
```

## Project Structure

```
RAGRace/
├── src/
│   ├── adapters/          # RAG provider adapters
│   │   ├── base.py        # BaseAdapter interface
│   │   ├── llamaindex_adapter.py
│   │   ├── landingai_adapter.py
│   │   └── reducto_adapter.py
│   ├── core/              # Scoring and evaluation
│   └── datasets/          # Dataset loaders
├── tests/                 # Unit and integration tests
├── config/                # Provider configurations
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # System architecture
│   ├── ADAPTERS.md        # Adapter specifications
│   └── DEVELOPMENT.md     # Development guide
└── data/                  # Datasets and results
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Adapter Reference](docs/ADAPTERS.md)** - Detailed adapter specs and comparison
- **[Development Guide](docs/DEVELOPMENT.md)** - How to add new providers
- **[Project Plan](local_docs/PROJECT_PLAN.md)** - Development roadmap (AI continuity)

## Key Features

- ✅ **Standardized Interface**: All providers implement `BaseAdapter` for fair comparison
- ✅ **Comprehensive Testing**: 54 tests with real API validation
- ✅ **Multiple Providers**: LlamaIndex, LandingAI, Reducto (more coming)
- ✅ **Dataset Support**: SQuAD 2.0 loader with Ragas evaluation
- ✅ **Web Research**: Uses Playwright MCP to read actual API documentation

## Development

Want to add a new RAG provider? Follow the **NO IMAGINATION** rule:

1. Research actual API docs with web-research-gatherer subagent
2. Implement adapter based on real documentation
3. Write unit + integration tests
4. Update documentation

See **[Development Guide](docs/DEVELOPMENT.md)** for detailed instructions.

## Contributing

Contributions welcome! Please:
- Follow the existing adapter patterns
- Base implementations on actual API documentation
- Include both unit and integration tests
- Update documentation

## License

MIT License

## Contact

For questions or issues, please open a GitHub issue.
