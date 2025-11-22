# DocAgent-Arena Adapter Reference

## Overview

All RAG providers in DocAgent-Arena implement the `BaseAdapter` interface for standardized comparison. This document provides detailed specifications for each integrated adapter.

## BaseAdapter Interface

All adapters must implement:

```python
class BaseAdapter(ABC):
    def initialize(self, api_key: str, **kwargs) -> None
        """Initialize the RAG provider connection."""

    def ingest_documents(self, documents: List[Document]) -> str
        """Upload documents and return index_id."""

    def query(self, question: str, index_id: str, **kwargs) -> RAGResponse
        """Query the RAG system and return standardized response."""

    def health_check(self) -> bool
        """Check if provider is accessible."""
```

### Data Structures

```python
@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]

@dataclass
class RAGResponse:
    answer: str
    context: List[str]  # Retrieved context chunks
    metadata: Dict[str, Any]
    latency_ms: float
    tokens_used: Optional[int] = None
```

## Integrated Adapters

### LlamaIndex

**Type**: Full RAG Framework

**Description**: Complete RAG framework with built-in vector storage, embeddings, and LLM integration.

**Implementation**:
- **Class**: `LlamaIndexAdapter`
- **Module**: `src.adapters.llamaindex_adapter`
- **Lines of Code**: 253

**Components**:
- PDF Parser: LlamaParse cloud API (markdown format)
- Vector Store: In-memory `SimpleVectorStore`
- Index: `VectorStoreIndex`
- Embeddings: OpenAI `text-embedding-3-small`
- LLM: OpenAI `gpt-4o-mini`
- Query Engine: Built-in with configurable `similarity_top_k`

**Configuration**:
```python
adapter.initialize(
    api_key=openai_api_key,
    llamacloud_api_key=llamaindex_api_key,     # Required for LlamaParse
    embedding_model="text-embedding-3-small",  # Optional
    llm_model="gpt-4o-mini",                   # Optional
    chunk_size=1024,                            # Optional
    chunk_overlap=20,                           # Optional
    top_k=3                                     # Optional
)
```

**Features**:
- ✅ Cloud-based PDF parsing (LlamaParse)
- ✅ Automatic document chunking
- ✅ Semantic retrieval with similarity scores
- ✅ Response synthesis with source nodes
- ✅ Configurable chunk size and overlap
- ✅ Native vector search

**Input Requirements**:
- Requires PDF files via `file_path` metadata
- Validates `.pdf` extension (strict)
- No plain text fallback

**Testing**:
- Unit Tests: 11 (all passing)
- Integration Tests: 3 (all passing)
- Test Coverage: Initialization, ingestion, query, health check

**Pros**:
- Complete out-of-the-box solution
- High-quality PDF extraction (LlamaParse)
- Well-documented framework
- Minimal code required

**Cons**:
- Requires 2 API keys (OpenAI + LlamaIndex Cloud)
- PDF files only (no plain text)
- Less control over chunking strategy
- In-memory only (no persistence in current implementation)

---

### LandingAI ADE (Agentic Document Extraction)

**Type**: Document Preprocessing + RAG Completion

**Description**: Document parsing service with semantic chunking. Adapter adds embedding generation and vector search for complete RAG functionality.

**Implementation**:
- **Class**: `LandingAIAdapter`
- **Module**: `src.adapters.landingai_adapter`
- **Lines of Code**: 462

**Components**:
- Document Parser: LandingAI ADE API
- Embeddings: External (OpenAI)
- Vector Store: In-memory (NumPy)
- LLM: External (OpenAI)
- Retrieval: Cosine similarity search

**Configuration**:
```python
adapter.initialize(
    api_key=landingai_api_key,
    openai_api_key=openai_api_key,             # Required
    base_url="https://api.va.landing.ai",      # Optional (US/EU)
    embedding_model="text-embedding-3-small",  # Optional
    llm_model="gpt-4o-mini",                   # Optional
    top_k=3,                                    # Optional
    model="dpt-2-latest"                        # Optional (parse model)
)
```

**Document Parsing**:
- **8 Chunk Types**: text, table, marginalia, figure, logo, card, attestation, scan_code
- **Grounding Metadata**: Bounding boxes, page numbers for citations
- **Multi-Modal**: Handles text, tables, figures, logos, QR codes, etc.

**Supported Input**:
- Requires `document_url` or `file_path` in metadata
- Validates `.pdf` extension for `file_path` (strict)
- Warns for non-PDF URLs (proceeds anyway)
- Does NOT work with plain text content
- Supported formats: PDF, JPEG, PNG, TIFF, BMP, WEBP, JP2, GIF

**Limits**:
- Synchronous: 50 pages, 50MB
- Asynchronous: 1000 pages, 1GB
- Rate limits: 10-25 req/min (plan dependent)

**Features**:
- ✅ Semantic chunking with 8 types
- ✅ Grounding metadata (bounding boxes)
- ✅ Multi-modal document understanding
- ✅ Page-level splitting
- ✅ Async support for large files

**Testing**:
- Unit Tests: 11 (all passing)
- Integration Tests: 3 (all passing)
- Test Coverage: Full end-to-end with real API

**Pros**:
- Excellent document understanding
- Rich metadata for citations
- Strong multi-modal support
- Grounding information

**Cons**:
- Requires actual document files (not plain text)
- Needs external embedding + LLM
- Rate limits on free tier

---

### Reducto

**Type**: Document Preprocessing + RAG Completion

**Description**: Document processing API optimized for RAG workflows. Adapter adds embedding generation and vector search.

**Implementation**:
- **Class**: `ReductoAdapter`
- **Module**: `src.adapters.reducto_adapter`
- **Lines of Code**: 445

**Components**:
- Document Parser: Reducto API
- Embeddings: External (OpenAI)
- Vector Store: In-memory (NumPy)
- LLM: External (OpenAI)
- Retrieval: Cosine similarity search

**Configuration**:
```python
adapter.initialize(
    api_key=reducto_api_key,
    openai_api_key=openai_api_key,             # Required
    embedding_model="text-embedding-3-small",  # Optional
    llm_model="gpt-4o-mini",                   # Optional
    top_k=3,                                    # Optional
    chunk_mode="variable",                      # Optional
    ocr_system="standard",                      # Optional
    summarize_figures=True                      # Optional
)
```

**Document Parsing**:
- **Variable-Size Chunking**: Content-aware chunk boundaries
- **Embedding Optimization**: Special `chunks[].embed` field optimized for embeddings
- **AI Enrichment**: Optional agentic enhancement of content
- **Figure Summarization**: AI-generated summaries of figures

**Supported Input**:
- Requires `document_url` or `file_path` in metadata
- Validates `.pdf` extension for `file_path` (strict)
- Warns for non-PDF URLs (proceeds anyway)
- Supports file upload via `/upload` endpoint
- Supported formats: PDF, DOCX, XLSX, Images

**Configuration Options**:
- `chunk_mode`: "variable", "disabled", etc.
- `embedding_optimized`: true (always enabled in adapter)
- `ocr_system`: "standard" or other OCR engines
- `summarize_figures`: Enable AI figure summaries

**Features**:
- ✅ Embedding-optimized text output
- ✅ Variable-size semantic chunking
- ✅ AI content enrichment
- ✅ Figure summarization
- ✅ Block filtering and confidence scores
- ✅ Async processing with webhooks

**Testing**:
- Unit Tests: 11 (all passing)
- Integration Tests: 4 (all passing, including enriched content)
- Test Coverage: Full end-to-end with real API

**Query Options**:
- `top_k`: Override default retrieval count
- `temperature`: LLM temperature
- `use_enriched`: Use AI-enriched content instead of raw

**Pros**:
- Optimized specifically for RAG
- Embedding-optimized output
- AI enrichment capabilities
- Variable chunking

**Cons**:
- Requires actual document files (not plain text)
- Needs external embedding + LLM
- Credit-based pricing

---

### ExtendAI

**Type**: Document Parsing Service

**Description**: AI-powered document parsing with standard and agentic OCR modes. Provides page-based chunking with figure and table extraction.

**Implementation**:
- **Class**: `ExtendAIParser`
- **Module**: `src.adapters.parsing.extendai_parser`
- **Lines of Code**: 296

**Components**:
- Document Parser: ExtendAI API
- Parsing Modes: standard, agentic-ocr
- Output: Markdown format
- Chunking: Page-based

**Configuration**:
```python
parser.initialize(
    api_key=extendai_api_key,
    mode="standard"  # or "agentic-ocr"
)
```

**Parsing Modes**:
- **standard**: Fast parsing with basic OCR
- **agentic-ocr**: Advanced parsing with AI-enhanced OCR for complex layouts

**Document Processing**:
- **Chunking**: Page-level granularity
- **Output Format**: Markdown with preserved structure
- **Figure Extraction**: Identifies and extracts figures with descriptions
- **Table Handling**: Preserves table structure in markdown

**Supported Input**:
- Accepts PDF files via file upload
- Base64 encoded documents supported
- Maximum file size: Check API limits

**Features**:
- ✅ Dual parsing modes (standard/agentic)
- ✅ Page-based chunking
- ✅ Figure and table extraction
- ✅ Markdown output format
- ✅ Cost-effective pricing ($0.02/page flat rate)

**Pricing**:
- Both modes: $0.02 per page (2 credits @ $0.01/credit)
- No mode-based price variation

**Pros**:
- Simple, predictable pricing
- Clean markdown output
- Fast processing (standard mode)
- Enhanced accuracy (agentic mode)

**Cons**:
- Fewer configuration options
- Page-level chunking only
- Limited metadata compared to competitors

---

### Unstructured.io

**Type**: Enterprise Document Preprocessing

**Description**: Production-ready document processing with multiple strategy modes and VLM support. Provides element-based parsing with rich metadata.

**Implementation**:
- **Class**: `UnstructuredParser`
- **Module**: `src.adapters.parsing.unstructured_parser`
- **Lines of Code**: 341

**Components**:
- Document Parser: Unstructured.io API
- Parsing Strategies: fast, hi_res, auto, vlm-gpt4o, vlm-claude
- Output: Element-based JSON
- Chunking: Element-level or custom

**Configuration**:
```python
parser.initialize(
    api_key=unstructured_api_key,
    strategy="hi_res",  # fast, hi_res, auto, vlm-gpt4o, vlm-claude
    hi_res_model_name=None,  # Optional for hi_res mode
    coordinates=True,         # Include element coordinates
    encoding="utf-8"          # Output encoding
)
```

**Parsing Strategies**:
- **fast**: Quick text extraction without layout analysis (~30s)
- **hi_res**: OCR-based with layout detection (~60s)
- **auto**: Automatic strategy selection based on content
- **vlm-gpt4o**: GPT-4 Vision for complex documents
- **vlm-claude**: Claude Vision for complex documents

**Document Processing**:
- **Element Types**: Title, Text, ListItem, Table, Image, Header, Footer, etc.
- **Metadata**: Coordinates, page numbers, element IDs, detection confidence
- **Output Format**: JSON with structured elements or markdown
- **Chunking**: Configurable by element type and size

**Supported Input**:
- PDF files via file upload
- Multiple file formats supported
- Large document support

**Features**:
- ✅ 5 parsing strategies (flexibility for any use case)
- ✅ VLM support (GPT-4o and Claude)
- ✅ Rich element-level metadata
- ✅ Coordinate-based grounding
- ✅ Production-ready enterprise features
- ✅ Consistent pricing across all modes

**Pricing**:
- All strategies: $0.03 per page (flat rate)
- No strategy-based price variation
- VLM modes same price as standard modes

**Limits**:
- Check API documentation for file size limits
- Rate limits vary by plan

**Pros**:
- Most parsing strategy options (5 modes)
- VLM support for challenging documents
- Rich metadata for citations
- Enterprise-grade reliability
- Consistent pricing regardless of mode

**Cons**:
- Higher base price ($0.03/page)
- More complex configuration options
- VLM modes can be slower

---

## Comparison Matrix

| Feature | LlamaIndex | LandingAI | Reducto | ExtendAI | Unstructured.io |
|---------|-----------|-----------|---------|----------|----------------|
| **Type** | Full RAG | Doc Preprocessing | Doc Preprocessing | Parsing Service | Enterprise Preprocessing |
| **PDF Parser** | LlamaParse Cloud | LandingAI ADE | Reducto API | ExtendAI API | Unstructured.io API |
| **Parsing Modes** | 3 modes | 2 modes | 2 modes | 2 modes | 5 strategies |
| **Embeddings** | Built-in (OpenAI) | External (OpenAI) | External (OpenAI) | N/A | N/A |
| **Vector Store** | Built-in | Adapter (NumPy) | Adapter (NumPy) | N/A | N/A |
| **LLM** | Built-in (OpenAI) | External (OpenAI) | External (OpenAI) | N/A | N/A |
| **Chunking** | Fixed-size | 8 semantic types | Variable-size | Page-based | Element-based |
| **Input** | PDF only | PDF only | PDF only | PDF | PDF + multiple formats |
| **Grounding** | ❌ No | ✅ Bounding boxes | ✅ Bounding boxes | ⚠️ Limited | ✅ Coordinates |
| **Multi-Modal** | Limited | ✅ 8 types | ✅ Good | ✅ Figures/Tables | ✅ Rich elements |
| **AI Enrichment** | ❌ No | ❌ No | ✅ Yes | ✅ Agentic mode | ❌ No |
| **VLM Support** | ❌ No | ❌ No | ❌ No | ❌ No | ✅ GPT-4o/Claude |
| **Embedding Optimization** | ❌ No | ❌ No | ✅ Yes | N/A | N/A |
| **Async Support** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Output Format** | Markdown | JSON + chunks | JSON + chunks | Markdown | JSON + elements |
| **Pricing (per page)** | $0.003-$0.090 | $0.015-$0.030 | $0.015-$0.030 | $0.02 (flat) | $0.03 (flat) |
| **Code Complexity** | Low | Medium | Medium | Low | Medium |
| **API Keys Required** | 2 (OpenAI + LlamaIndex) | 2 (LandingAI + OpenAI) | 2 (Reducto + OpenAI) | 1 (ExtendAI) | 1 (Unstructured.io) |

## Performance Characteristics

### Query Latency (Integration Tests)

**Test Setup**: 1 dummy PDF, 2 queries, top_k=2

| Adapter | Query 1 Latency | Query 2 Latency | Avg Latency |
|---------|----------------|-----------------|-------------|
| LlamaIndex | ~2000ms | ~2000ms | ~2000ms |
| LandingAI | ~1100ms | ~1250ms | ~1175ms |
| Reducto | ~830ms | ~1800ms | ~1315ms |

**Note**: Latencies include document parsing (first call), embedding generation, and LLM response.

### Answer Quality (Dummy PDF Test)

| Adapter | Answer Quality | Notes |
|---------|---------------|-------|
| LlamaIndex | N/A | Not tested with same document |
| LandingAI | Low | Could not answer simple questions |
| Reducto | Good | Correctly identified "dummy PDF" |

**Note**: Test used a minimal dummy PDF with limited content.

## Usage Examples

### Basic Usage Pattern

All adapters follow the same pattern:

```python
from src.adapters import LlamaIndexAdapter, LandingAIAdapter, ReductoAdapter
from src.adapters.base import Document

# 1. Initialize
adapter = LlamaIndexAdapter()  # or LandingAIAdapter, ReductoAdapter
adapter.initialize(api_key=api_key, openai_api_key=openai_key)  # openai_key for LandingAI/Reducto

# 2. Health check
assert adapter.health_check()

# 3. Ingest documents
docs = [Document(id="1", content="Your text", metadata={})]
index_id = adapter.ingest_documents(docs)

# 4. Query
response = adapter.query("Your question?", index_id, top_k=3)

# 5. Get results
print(response.answer)
print(f"Retrieved {len(response.context)} chunks")
print(f"Latency: {response.latency_ms:.2f}ms")
```

### Document Preprocessing Adapters (LandingAI, Reducto)

For document preprocessing providers, documents MUST have file reference:

```python
docs = [Document(
    id="doc1",
    content="",  # Not used
    metadata={
        "document_url": "https://example.com/file.pdf"  # OR
        "file_path": "/path/to/local/file.pdf"
    }
)]
```

## Environment Variables

```bash
# LlamaIndex
OPENAI_API_KEY=your_openai_key
LLAMAINDEX_API_KEY=your_llamaindex_cloud_key

# LandingAI
VISION_AGENT_API_KEY=your_landingai_key
OPENAI_API_KEY=your_openai_key

# Reducto
REDUCTO_API_KEY=your_reducto_key
OPENAI_API_KEY=your_openai_key

# ExtendAI
EXTENDAI_API_KEY=your_extendai_key

# Unstructured.io
UNSTRUCTURED_API_KEY=your_unstructured_key
```
