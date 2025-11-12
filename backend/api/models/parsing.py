"""
Request and response models for parsing API endpoints.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProviderCost(BaseModel):
    """Cost breakdown for a single provider."""

    provider: str
    credits: float
    usd_per_credit: float
    total_usd: float
    details: Dict[str, Any] = {}


class CostComparisonResponse(BaseModel):
    """Response with cost breakdown for all providers."""

    file_id: str
    costs: Dict[str, ProviderCost]
    total_usd: float


class LlamaIndexConfig(BaseModel):
    """Configuration for LlamaIndex parsing."""

    parse_mode: str = Field(
        default="parse_page_with_agent",
        description="Parse mode: parse_page_with_agent or parse_page_with_llm"
    )
    model: str = Field(
        default="openai-gpt-4-1-mini",
        description="Model to use for parsing"
    )


class ReductoConfig(BaseModel):
    """Configuration for Reducto parsing."""

    mode: str = Field(
        default="standard",
        description="Mode: standard (1 credit/page) or complex (2 credits/page)"
    )
    summarize_figures: bool = Field(
        default=False,
        description="Enable VLM enhancement for complex pages"
    )


class LandingAIConfig(BaseModel):
    """Configuration for LandingAI parsing."""

    model: str = Field(
        default="dpt-2",
        description="Model to use (currently only dpt-2 is available)"
    )


class BattleAssignment(BaseModel):
    """Mapping between a blind label and the actual provider."""

    label: str
    provider: str


class BattleMetadata(BaseModel):
    """Battle-specific metadata returned with parse results."""

    battle_id: str
    assignments: List[BattleAssignment]


class ParseCompareRequest(BaseModel):
    """
    Request model for comparing PDF parsing across providers.

    Example:
        {
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "providers": ["llamaindex", "reducto"],
            "configs": {
                "llamaindex": {"parse_mode": "parse_page_with_agent", "model": "openai-gpt-4-1-mini"},
                "reducto": {"mode": "standard", "summarize_figures": false}
            }
        }
    """

    file_id: str = Field(..., description="UUID of uploaded file")
    providers: Optional[List[str]] = Field(
        default=None,
        description="List of parser providers to compare. Empty or omitted triggers battle mode.",
    )
    configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional configurations for each provider"
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Specific page to parse (1-indexed). Required for battle mode.",
    )
    filename: Optional[str] = Field(
        default=None,
        description="Original filename to help audit stored uploads",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "providers": ["llamaindex", "reducto"],
                "configs": {
                    "llamaindex": {"parse_mode": "parse_page_with_agent", "model": "openai-gpt-4-1-mini"},
                    "reducto": {"mode": "standard", "summarize_figures": False}
                },
                "page_number": 3,
                "filename": "document.pdf"
            }
        }


class PageCountRequest(BaseModel):
    """Request model for getting page count of an uploaded PDF."""

    file_id: str = Field(..., description="UUID of uploaded file")


class PageCountResponse(BaseModel):
    """Response model for page count."""

    file_id: str = Field(..., description="UUID of the file")
    page_count: int = Field(..., description="Number of pages in the PDF")
    filename: str = Field(..., description="Original filename")


class UploadResponse(BaseModel):
    """
    Response model for file upload.

    Example:
        {
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "document.pdf"
        }
    """

    file_id: str = Field(..., description="UUID for uploaded file")
    filename: str = Field(..., description="Original filename")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "document.pdf",
            }
        }


class PageData(BaseModel):
    """Data for a single parsed page."""

    page_number: int
    markdown: str
    images: List[str] = []
    metadata: Dict[str, Any] = {}


class ProviderParseResult(BaseModel):
    """Parsing result from a single provider."""

    total_pages: int
    pages: List[PageData]
    processing_time: float
    usage: Dict[str, Any] = {}


class ParseCompareResponse(BaseModel):
    """
    Response model for parse comparison.

    Example:
        {
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "results": {
                "llamaindex": {
                    "total_pages": 5,
                    "pages": [...],
                    "processing_time": 12.5
                },
                "reducto": {
                    "total_pages": 5,
                    "pages": [...],
                    "processing_time": 8.3
                }
            }
        }
    """

    file_id: str = Field(..., description="UUID of the parsed file")
    results: Dict[str, ProviderParseResult] = Field(
        ..., description="Parsing results keyed by provider name"
    )
    battle: Optional[BattleMetadata] = Field(
        default=None,
        description="Battle-specific metadata when providers were chosen automatically",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "results": {
                    "llamaindex": {
                        "total_pages": 5,
                        "pages": [
                            {
                                "page_number": 1,
                                "markdown": "# Introduction\n\nThis is page 1...",
                                "images": [],
                                "metadata": {},
                            }
                        ],
                        "processing_time": 12.5,
                    }
                },
            }
        }


class BattlePreference(str, Enum):
    """Possible user selections for battle outcomes."""

    A_BETTER = "A_BETTER"
    B_BETTER = "B_BETTER"
    BOTH_GOOD = "BOTH_GOOD"
    BOTH_BAD = "BOTH_BAD"


class BattleFeedbackRequest(BaseModel):
    """User feedback payload for a completed battle."""

    battle_id: str = Field(..., description="Identifier returned from battle parse")
    preference: Optional[BattlePreference] = Field(
        default=None,
        description="Which side performed better (deprecated once preferred_labels is provided)",
    )
    preferred_labels: Optional[List[str]] = Field(
        default=None,
        description="List of blind labels rated as better (e.g., ['A'])",
    )
    comment: Optional[str] = Field(default=None, description="Optional rationale")


class BattleFeedbackResponse(BaseModel):
    """API response after storing battle feedback."""

    battle_id: str
    preferred_labels: List[str]
    comment: Optional[str]
    assignments: List[BattleAssignment]


class BattleHistoryItem(BaseModel):
    """Summary of a single battle for history list."""

    battle_id: str
    original_name: str
    page_number: int
    created_at: str
    winner: Optional[str] = None  # Provider name that won, or "tie", "none"
    preferred_labels: Optional[List[str]] = None


class BattleHistoryResponse(BaseModel):
    """Paginated list of battle history."""

    battles: List[BattleHistoryItem]
    total: int
    page: int
    limit: int


class BattleProviderDetail(BaseModel):
    """Provider result details for battle detail view."""

    provider: str
    label: str
    content: ProviderParseResult
    cost_usd: Optional[float] = None
    cost_credits: Optional[float] = None


class BattleDetailResponse(BaseModel):
    """Complete battle details for detail view."""

    battle_id: str
    original_name: str
    page_number: int
    upload_file_id: str
    storage_url: Optional[str] = None
    storage_path: Optional[str] = None
    created_at: str
    providers: List[BattleProviderDetail]
    feedback: Optional[Dict[str, Any]] = None
    assignments: List[BattleAssignment]
