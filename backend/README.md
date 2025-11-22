# DocAgent Arena Backend

FastAPI backend for PDF parsing and battle mode.

## Overview

Provides two main services:
1. **Parsing API** - PDF parsing with 5 providers, battle mode, SSE streaming, and comparison endpoints
2. **Battle System** - Blind A/B testing with 12+ configurations and database persistence

## Prerequisites

- Python 3.11+
- API keys for parsers (OpenAI required)
- PostgreSQL database (optional, for battle history)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Setup database (optional, for battles)
prisma generate
prisma db push

# Start API server
uvicorn main:app --reload

# API docs at http://localhost:8000/docs
```

## Project Structure

```
backend/
├── main.py                 # FastAPI entry point
├── api/
│   ├── routers/
│   │   └── parsing.py      # Battle + parsing endpoints
│   └── models/             # Pydantic schemas
│
├── src/
│   ├── adapters/
│   │   ├── parsing/        # Parsing adapters (5 providers)
│   │   │   ├── llamaindex_parser.py
│   │   │   ├── reducto_parser.py
│   │   │   ├── landingai_parser.py
│   │   │   ├── extendai_parser.py
│   │   │   └── unstructured_parser.py
│   │   └── base.py         # Base adapter interfaces
│
├── config/
│   └── parsing_pricing.yaml    # Pricing configuration
│
├── prisma/
│   ├── schema.prisma       # Database schema
│   └── migrations/         # Database migrations
│
└── tests/                  # Unit + integration tests
```

## API Endpoints

### Parsing & Battle

```python
# Upload PDF
POST /api/v1/parsing/upload
multipart/form-data: file

# Get page count
POST /api/v1/parsing/page-count
{ file_id: str }

# Parse PDF (full or battle mode)
POST /api/v1/parsing/compare
{
  file_id: str,
  page_number: int | None,  # Set for battle mode
  providers: list[str],      # Empty = random selection for battle
  api_keys: dict,
  configs: dict
}

# Parse PDF with SSE streaming (real-time progress)
POST /api/v1/parsing/compare-stream
{
  file_id: str,
  providers: list[str],
  api_keys: dict,
  configs: dict
}

# Submit battle feedback
POST /api/v1/parsing/battle-feedback
{
  battle_id: str,
  preferred_labels: list[str],
  comment: str
}

# Get battle history
GET /api/v1/parsing/battles?limit=10&offset=0

# Get battle detail
GET /api/v1/parsing/battles/{battle_id}
```

## Parsing Adapters

All implement `BaseParseAdapter`:

```python
class BaseParseAdapter(ABC):
    @abstractmethod
    async def parse_pdf(self, pdf_path: Path) -> ParseResult:
        """Parse PDF and return structured result."""
```

### LlamaIndex Parser

```python
from src.adapters.parsing.llamaindex_parser import LlamaIndexParser

parser = LlamaIndexParser(
    api_key="llx-...",
    parse_mode="parse_page_with_llm",  # or parse_page_with_agent
    model="openai-gpt-4-1-mini"        # or anthropic-sonnet-4.0
)
result = await parser.parse_pdf(Path("document.pdf"))
```

**Pricing**: $0.001 per credit, 3-90 credits/page depending on mode

### Reducto Parser

```python
from src.adapters.parsing.reducto_parser import ReductoParser

parser = ReductoParser(
    api_key="red-...",
    mode="standard",           # or complex
    summarize_figures=True
)
result = await parser.parse_pdf(Path("document.pdf"))
```

**Pricing**: $0.015 per credit, 1-2 credits/page

### LandingAI Parser

```python
from src.adapters.parsing.landingai_parser import LandingAIParser

parser = LandingAIParser(
    api_key="va-...",
    model="dpt-2-latest"       # or dpt-2-mini
)
result = await parser.parse_pdf(Path("document.pdf"))
```

**Pricing**: $0.01 per credit, 1.5-3 credits/page

### ExtendAI Parser

```python
from src.adapters.parsing.extendai_parser import ExtendAIParser

parser = ExtendAIParser(
    api_key="ext-...",
    mode="standard"            # or agentic-ocr
)
result = await parser.parse_pdf(Path("document.pdf"))
```

**Pricing**: $0.01 per credit, 2 credits/page (flat rate for both modes)

### Unstructured.io Parser

```python
from src.adapters.parsing.unstructured_parser import UnstructuredParser

parser = UnstructuredParser(
    api_key="uns-...",
    strategy="hi_res",         # fast, hi_res, auto, vlm-gpt4o, vlm-claude
    coordinates=True
)
result = await parser.parse_pdf(Path("document.pdf"))
```

**Pricing**: $0.03 per credit, 1 credit/page (flat rate across all strategies)

## Database Setup

```bash
# Generate Prisma client
prisma generate

# Apply migrations
prisma db push

# View data in Prisma Studio
prisma studio
```

**Battle Schema**:
- `ParseBattleRun` - Battle metadata
- `BattleProviderResult` - Per-provider results
- `BattleFeedback` - User preferences

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional parsing providers
LLAMAINDEX_API_KEY=llx-...
REDUCTO_API_KEY=red-...
VISION_AGENT_API_KEY=va-...
EXTENDAI_API_KEY=ext-...
UNSTRUCTURED_API_KEY=uns-...

# Optional database (for battles)
DATABASE_URL=postgresql://...
```

## Testing

```bash
# Unit tests (fast, no API calls)
pytest tests/ -v -k "not integration"

# Integration tests (real APIs, costs money)
pytest tests/ -v -m integration

# Specific adapter
pytest tests/test_llamaindex_parser.py -v
```

## Development

### Adding New Parser

1. Create adapter in `src/adapters/parsing/yourparser.py`
2. Implement `BaseParseAdapter` interface
3. Add pricing to `config/parsing_pricing.yaml`
4. Write tests in `tests/test_yourparser.py`
5. Update documentation

See [Development Guide](../docs/DEVELOPMENT.md) for details.

## API Documentation

Start the server and visit:
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Import errors
```bash
# Ensure you're in backend/ directory
cd backend
python -c "import src.adapters.parsing"
```

### Database connection errors
```bash
# Check DATABASE_URL in .env
# Test connection
prisma db push
```

### Parser API errors
```bash
# Verify API keys in .env
# Test with curl:
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

## License

Part of the DocAgent Arena project (MIT License).
