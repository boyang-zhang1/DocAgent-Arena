"""ExtendAI parsing adapter with page-based parsing."""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from extend_ai import Extend
from extend_ai.core.request_options import RequestOptions

from .base import BaseParseAdapter, PageResult, ParseResult


class ExtendAIParser(BaseParseAdapter):
    """Parser using ExtendAI API with page chunking."""

    def __init__(self, api_key: str, agentic_ocr: bool = False):
        """
        Initialize ExtendAI parser.

        Args:
            api_key: API key for ExtendAI (required).
            agentic_ocr: Enable AI-powered OCR for complex documents (default: False).
                        True = 2 credits/page, False = 2 credits/page (same cost).

        Raises:
            ValueError: If api_key is empty or None.
        """
        if not api_key:
            raise ValueError("ExtendAI API key is required")

        self.client = Extend(
            base_url="https://api.extend.ai",
            token=api_key
        )
        self.agentic_ocr = agentic_ocr
        self.request_options = RequestOptions(
            additional_headers={"x-extend-api-version": "2025-04-21"}
        )

    async def parse_pdf(self, pdf_path: Path, debug_info: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse PDF using ExtendAI SDK and map chunks to pages.

        Args:
            pdf_path: Path to the PDF file
            debug_info: Optional debug configuration for saving request/response

        Returns:
            ParseResult with chunks mapped to pages
        """
        start_time = time.time()

        # Step 1: Upload file using SDK
        with open(pdf_path, "rb") as f:
            upload_response = self.client.file.upload(
                file=f,
                request_options=self.request_options
            )

        file_id = upload_response.file.id

        # Save request parameters if debug mode is enabled
        parse_config = {
            "target": "markdown",
            "chunkingStrategy": {
                "type": "page",
            },
            "blockOptions": {
                "figures": {
                    "enabled": True,
                    "figureImageClippingEnabled": True,
                },
                "tables": {
                    "enabled": True,
                    "targetFormat": "markdown",
                    "tableHeaderContinuationEnabled": False,
                },
                "text": {
                    "signatureDetectionEnabled": True,
                },
            },
            "advancedOptions": {
                "pageRotationEnabled": True,
                "agenticOcrEnabled": self.agentic_ocr,
            },
        }

        if debug_info and debug_info.get("enabled"):
            request_data = {
                "provider": "extendai",
                "pdf_path": str(pdf_path),
                "file_id": file_id,
                "config": parse_config,
            }
            self._save_debug_file(debug_info, "extendai", request_data, "request")

        # Step 2: Parse with page chunking using SDK
        parse_response = self.client.parse(
            file={
                "fileId": file_id,
            },
            config=parse_config,
            request_options=self.request_options
        )

        # Extract chunks from response
        chunks = parse_response.chunks if hasattr(parse_response, 'chunks') else []

        # Save raw response if debug mode is enabled
        if debug_info and debug_info.get("enabled"):
            # Convert chunks to JSON-serializable format using Pydantic serialization
            def serialize_obj(obj):
                """Helper to serialize Pydantic objects or dicts"""
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                elif hasattr(obj, 'dict'):
                    return obj.dict()
                elif isinstance(obj, dict):
                    return obj
                else:
                    return str(obj)

            response_data = {
                "parser_run_id": parse_response.id if hasattr(parse_response, 'id') else None,
                "status": parse_response.status if hasattr(parse_response, 'status') else None,
                "total_chunks": len(chunks),
                "chunks": [serialize_obj(chunk) for chunk in chunks],
                "usage": serialize_obj(parse_response.usage) if hasattr(parse_response, 'usage') else None,
                "metrics": serialize_obj(parse_response.metrics) if hasattr(parse_response, 'metrics') else None,
            }
            self._save_debug_file(debug_info, "extendai", response_data, "response")

        # Map chunks to pages
        pages = self._map_chunks_to_pages(chunks)

        processing_time = time.time() - start_time

        # Extract usage and metrics
        usage = {}
        metrics = {}
        if hasattr(parse_response, 'usage'):
            usage = parse_response.usage.__dict__ if hasattr(parse_response.usage, '__dict__') else {}
        if hasattr(parse_response, 'metrics'):
            metrics = parse_response.metrics.__dict__ if hasattr(parse_response.metrics, '__dict__') else {}

        # Add metadata to usage for cost calculation
        usage["num_pages"] = len(pages)
        usage["agentic_ocr"] = self.agentic_ocr
        usage["mode"] = "agentic-ocr" if self.agentic_ocr else "standard"
        usage["page_count"] = metrics.get("pageCount") or metrics.get("page_count") or len(pages)
        usage["processing_time_ms"] = metrics.get("processingTimeMs") or metrics.get("processing_time_ms") or 0

        parser_run_id = parse_response.id if hasattr(parse_response, 'id') else None
        status = parse_response.status if hasattr(parse_response, 'status') else None

        return ParseResult(
            provider="extendai",
            total_pages=len(pages),
            pages=pages,
            raw_response={
                "total_chunks": len(chunks),
                "parser_run_id": parser_run_id,
                "status": status,
            },
            processing_time=processing_time,
            usage=usage,
        )

    def _map_chunks_to_pages(self, chunks: List[Any]) -> List[PageResult]:
        """
        Map ExtendAI chunks to pages using metadata.

        Args:
            chunks: List of chunks from ExtendAI SDK (can be dict or objects)

        Returns:
            List of PageResult objects with markdown content
        """
        page_map: Dict[int, List[str]] = {}
        page_images: Dict[int, List[str]] = {}
        max_page = 0

        for chunk in chunks:
            # Handle both dict and object responses
            if hasattr(chunk, '__dict__'):
                chunk_dict = chunk.__dict__
            elif isinstance(chunk, dict):
                chunk_dict = chunk
            else:
                continue

            # Get chunk content and metadata
            content = chunk_dict.get("content", "")
            metadata = chunk_dict.get("metadata", {})

            if hasattr(metadata, '__dict__'):
                metadata = metadata.__dict__

            page_range = metadata.get("pageRange") or metadata.get("page_range", {})

            if hasattr(page_range, '__dict__'):
                page_range = page_range.__dict__

            # ExtendAI uses pageRange with start/end
            start_page = page_range.get("start", 1)
            end_page = page_range.get("end", start_page)

            max_page = max(max_page, end_page)

            # If chunk spans multiple pages, add to all pages
            for page_num in range(start_page, end_page + 1):
                if page_num not in page_map:
                    page_map[page_num] = []
                page_map[page_num].append(content)

            # Extract blocks for images and additional metadata
            blocks = chunk_dict.get("blocks", [])
            for block in blocks:
                # Handle both dict and object responses
                if hasattr(block, '__dict__'):
                    block_dict = block.__dict__
                elif isinstance(block, dict):
                    block_dict = block
                else:
                    continue

                block_type = block_dict.get("type", "")
                block_metadata = block_dict.get("metadata", {})

                if hasattr(block_metadata, '__dict__'):
                    block_metadata = block_metadata.__dict__

                block_page = block_metadata.get("page", {})

                if hasattr(block_page, '__dict__'):
                    block_page = block_page.__dict__

                page_num = block_page.get("number", start_page)

                # Extract image URLs if available
                if block_type == "image" or block_type == "figure":
                    # ExtendAI may provide image URLs in block details
                    details = block_dict.get("details", {})
                    if hasattr(details, '__dict__'):
                        details = details.__dict__
                    image_url = details.get("url") or details.get("imageUrl")
                    if image_url:
                        if page_num not in page_images:
                            page_images[page_num] = []
                        page_images[page_num].append(image_url)

        # Ensure we have at least one page
        if not page_map:
            page_map[1] = ["*No content extracted from chunks*"]
            max_page = 1
        else:
            max_page = max(max_page, 1)

        # Convert to PageResult objects
        pages = []
        for page_num in range(1, max_page + 1):
            page_contents = page_map.get(page_num, [])

            # Join content with double newlines
            markdown = "\n\n".join(page_contents) if page_contents else "*No content on this page*"

            pages.append(
                PageResult(
                    page_number=page_num,
                    markdown=markdown.strip(),
                    images=page_images.get(page_num, []),
                    metadata={
                        "chunk_count": len(page_contents),
                        "has_images": len(page_images.get(page_num, [])) > 0,
                    },
                )
            )

        return pages
