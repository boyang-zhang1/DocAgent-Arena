"""Base adapter interface for PDF parsing."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PageResult:
    """Result for a single page of parsed content."""

    page_number: int
    markdown: str
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    """Complete parsing result from a provider."""

    provider: str
    total_pages: int
    pages: List[PageResult]
    raw_response: Dict[str, Any]
    processing_time: float
    usage: Dict[str, Any] = field(default_factory=dict)  # Credits, model info, etc.


class BaseParseAdapter(ABC):
    """Abstract base class for PDF parsing adapters."""

    @abstractmethod
    async def parse_pdf(self, pdf_path: Path, debug_info: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse a PDF file and return structured results.

        Args:
            pdf_path: Path to the PDF file
            debug_info: Optional debug configuration containing:
                - enabled: Whether debug mode is active
                - debug_dir: Directory to save debug files
                - base_filename: Base filename for debug files
                - timestamp: Timestamp string for debug files

        Returns:
            ParseResult containing page-by-page markdown and metadata
        """
        pass

    def _save_debug_file(self, debug_info: Dict[str, Any], provider: str, data: Dict[str, Any], suffix: str) -> None:
        """
        Save debug data to a JSON file.

        Args:
            debug_info: Debug configuration from endpoint
            provider: Provider name (e.g., 'llamaindex', 'reducto')
            data: Data to save as JSON
            suffix: File suffix (e.g., 'request', 'response')
        """
        if not debug_info or not debug_info.get("enabled"):
            return

        debug_dir = debug_info["debug_dir"]
        base_filename = debug_info["base_filename"]
        timestamp = debug_info["timestamp"]

        filename = f"{base_filename}_{provider}_{timestamp}_{suffix}.json"
        filepath = debug_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def serialize_obj(obj):
    """
    Helper to serialize Pydantic objects, dicts, and lists to JSON-serializable format.

    Args:
        obj: Object to serialize (Pydantic model, dict, list, or primitive)

    Returns:
        JSON-serializable version of the object
    """
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, dict):
        return {k: serialize_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_obj(item) for item in obj]
    else:
        return obj
