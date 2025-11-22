"""Unstructured.io parsing adapter."""

import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError

from .base import BaseParseAdapter, PageResult, ParseResult


class UnstructuredParser(BaseParseAdapter):
    """Parser using Unstructured.io Cloud API."""

    def __init__(
        self,
        api_key: str,
        strategy: str = "fast",
        vlm_model: str = None,
        vlm_model_provider: str = None,
    ):
        """
        Initialize Unstructured.io parser.

        Args:
            api_key: API key for Unstructured.io (required).
            strategy: Processing strategy - "fast", "hi_res", "auto", or "vlm" (default: "fast").
                     - fast: Rule-based extraction (~100x faster)
                     - hi_res: Model-based with layout analysis
                     - auto: Adaptive routing per page
                     - vlm: Vision Language Model for diagrams/slides
            vlm_model: VLM model to use (required if strategy is "vlm").
                      Examples: "gpt-4o", "claude-sonnet-4-20250514"
            vlm_model_provider: VLM provider (required if strategy is "vlm").
                               Examples: "openai", "anthropic", "bedrock", "vertexai"

        Raises:
            ValueError: If api_key is empty or None, or if strategy is invalid,
                       or if VLM parameters are missing when strategy is "vlm".
        """
        if not api_key:
            raise ValueError("Unstructured.io API key is required")

        valid_strategies = ["fast", "hi_res", "auto", "vlm"]
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy '{strategy}'. Must be one of: {valid_strategies}")

        # Validate VLM parameters
        if strategy == "vlm":
            if not vlm_model:
                raise ValueError("vlm_model is required when strategy is 'vlm'")
            if not vlm_model_provider:
                raise ValueError("vlm_model_provider is required when strategy is 'vlm'")

        self.api_key = api_key
        self.strategy = strategy
        self.vlm_model = vlm_model
        self.vlm_model_provider = vlm_model_provider
        self.client = UnstructuredClient(api_key_auth=api_key)

    async def parse_pdf(self, pdf_path: Path, debug_info: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse PDF using Unstructured.io API and map elements to pages.

        Args:
            pdf_path: Path to the PDF file
            debug_info: Optional debug configuration for saving request/response

        Returns:
            ParseResult with elements mapped to pages
        """
        start_time = time.time()

        # Read PDF file
        with open(pdf_path, "rb") as f:
            file_content = f.read()

        # Create partition request
        req_params = {
            "files": shared.Files(
                content=file_content,
                file_name=pdf_path.name,
            ),
            "strategy": self.strategy,
            # Request coordinate data for better metadata
            "coordinates": True,
            # Use UUIDs for cleaner element IDs
            "unique_element_ids": True,
        }

        # Add VLM parameters if using VLM strategy
        if self.strategy == "vlm":
            req_params["vlm_model"] = self.vlm_model
            req_params["vlm_model_provider"] = self.vlm_model_provider

        req = shared.PartitionParameters(**req_params)

        # Save request parameters if debug mode is enabled
        if debug_info and debug_info.get("enabled"):
            request_data = {
                "provider": "unstructuredio",
                "pdf_path": str(pdf_path),
                "config": {
                    "strategy": self.strategy,
                    "coordinates": True,
                    "unique_element_ids": True,
                    "vlm_model": self.vlm_model if self.strategy == "vlm" else None,
                    "vlm_model_provider": self.vlm_model_provider if self.strategy == "vlm" else None,
                },
            }
            self._save_debug_file(debug_info, "unstructuredio", request_data, "request")

        # Execute partition
        try:
            res = self.client.general.partition(request={"partition_parameters": req})
        except SDKError as e:
            raise Exception(f"Unstructured.io API error: {str(e)}") from e

        # Extract elements from response
        elements = res.elements if hasattr(res, 'elements') else []

        # Save raw response if debug mode is enabled
        if debug_info and debug_info.get("enabled"):
            # Convert elements to JSON-serializable format
            def serialize_element(element):
                """Helper to serialize element objects"""
                if hasattr(element, 'model_dump'):
                    return element.model_dump()
                elif hasattr(element, 'dict'):
                    return element.dict()
                elif isinstance(element, dict):
                    return element
                else:
                    return {
                        "type": getattr(element, 'type', None),
                        "text": getattr(element, 'text', None),
                        "element_id": getattr(element, 'element_id', None),
                    }

            response_data = {
                "total_elements": len(elements),
                "elements": [serialize_element(element) for element in elements],
            }
            self._save_debug_file(debug_info, "unstructuredio", response_data, "response")

        # Map elements to pages
        pages = self._map_elements_to_pages(elements)

        processing_time = time.time() - start_time

        # Calculate usage/credits
        total_pages = len(pages)
        usage = {
            "num_pages": total_pages,
            "strategy": self.strategy,
            "mode": self.strategy,  # For consistency with pricing config
            "total_elements": len(elements),
        }

        # Add VLM model info if using VLM strategy
        if self.strategy == "vlm":
            usage["vlm_model"] = self.vlm_model
            usage["vlm_model_provider"] = self.vlm_model_provider

        return ParseResult(
            provider="unstructuredio",
            total_pages=total_pages,
            pages=pages,
            raw_response={
                "total_elements": len(elements),
                "strategy": self.strategy,
            },
            processing_time=processing_time,
            usage=usage,
        )

    def _map_elements_to_pages(self, elements: List[Any]) -> List[PageResult]:
        """
        Map Unstructured.io elements to pages and convert to markdown.

        Args:
            elements: List of Element objects from Unstructured.io API

        Returns:
            List of PageResult objects with markdown content
        """
        page_map: Dict[int, List[str]] = defaultdict(list)
        page_raw_elements: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        page_metadata_map: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            "element_types": defaultdict(int),
            "has_tables": False,
        })
        max_page = 0

        for element in elements:
            # Extract element data - handle both dict and object formats
            if isinstance(element, dict):
                element_type = element.get('type', 'Unknown')
            else:
                element_type = getattr(element, 'type', 'Unknown')

            # Extract text properly - handle both dict and object formats
            if element:
                if isinstance(element, dict):
                    text = element.get('text', '')
                else:
                    text = getattr(element, 'text', '')
            else:
                text = ""

            # Skip empty elements and page breaks
            if not text.strip() or element_type == 'PageBreak':
                continue

            # Get page number from metadata - handle both dict and object formats
            if isinstance(element, dict):
                metadata = element.get('metadata', None)
            else:
                metadata = getattr(element, 'metadata', None)
            page_num = 1  # Default to page 1 if no metadata

            if metadata:
                if hasattr(metadata, 'page_number'):
                    page_num = metadata.page_number or 1
                elif hasattr(metadata, '__dict__') and 'page_number' in metadata.__dict__:
                    page_num = metadata.__dict__['page_number'] or 1
                elif isinstance(metadata, dict) and 'page_number' in metadata:
                    page_num = metadata['page_number'] or 1

            # Store raw element for debugging (convert to dict if needed)
            if isinstance(element, dict):
                raw_element = element
            else:
                # Convert object to dict representation
                raw_element = {
                    'type': element_type,
                    'text': text,
                    'metadata': metadata.__dict__ if hasattr(metadata, '__dict__') else (metadata if isinstance(metadata, dict) else {})
                }
            page_raw_elements[page_num].append(raw_element)

            # Format content based on element type for formatted view
            formatted_text = self._format_element(element, element_type, text)

            # Add to page map
            page_map[page_num].append(formatted_text)
            max_page = max(max_page, page_num)

            # Track metadata
            page_metadata_map[page_num]["element_types"][element_type] += 1
            if element_type == "Table":
                page_metadata_map[page_num]["has_tables"] = True

        # Ensure we have at least one page
        if not page_map:
            page_map[1] = ["*No content extracted*"]
            max_page = 1

        # Convert to PageResult objects
        pages = []
        for page_num in range(1, max_page + 1):
            page_elements = page_map.get(page_num, [])
            raw_elements = page_raw_elements.get(page_num, [])

            # Formatted markdown for rendering
            markdown = "\n\n".join(page_elements) if page_elements else "*No content on this page*"

            # Raw structured response for debugging
            import json
            if raw_elements:
                raw_response = "\n\n".join([json.dumps(elem, indent=2) for elem in raw_elements])
            else:
                raw_response = "*No elements on this page*"

            # Get metadata for this page
            page_meta = page_metadata_map.get(page_num, {})
            element_types = dict(page_meta.get("element_types", {}))

            pages.append(
                PageResult(
                    page_number=page_num,
                    markdown=markdown.strip(),  # FORMATTED for rendering
                    images=[],  # Unstructured.io doesn't return image URLs in plain text mode
                    metadata={
                        "element_count": len(page_elements),
                        "element_types": element_types,
                        "has_tables": page_meta.get("has_tables", False),
                        "raw_response": raw_response,  # RAW for "Original Structured Response" section
                    },
                )
            )

        return pages

    def _format_element(self, element: Any, element_type: str, text: str) -> str:
        """
        Format element content based on its type.

        Args:
            element: The element object
            element_type: Type of the element
            text: Raw text content

        Returns:
            Formatted markdown text
        """
        # Handle tables specially - try to get HTML representation
        if element_type == "Table":
            # Extract metadata - handle both dict and object formats
            if isinstance(element, dict):
                metadata = element.get('metadata', None)
            else:
                metadata = getattr(element, 'metadata', None)
            if metadata:
                # Try to get HTML table representation
                html_table = None
                if hasattr(metadata, 'text_as_html'):
                    html_table = metadata.text_as_html
                elif hasattr(metadata, '__dict__') and 'text_as_html' in metadata.__dict__:
                    html_table = metadata.__dict__['text_as_html']
                elif isinstance(metadata, dict) and 'text_as_html' in metadata:
                    html_table = metadata['text_as_html']

                if html_table:
                    return html_table

            # Fallback to text representation
            return text

        # Format titles as headers
        if element_type == "Title":
            return f"# {text}"

        # Format narrative text and list items normally
        return text
