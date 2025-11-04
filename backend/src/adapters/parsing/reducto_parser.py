"""Reducto parsing adapter with chunk-to-page mapping."""

import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List

from reducto import Reducto

from .base import BaseParseAdapter, PageResult, ParseResult


class ReductoParser(BaseParseAdapter):
    """Parser using Reducto API with semantic chunking."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize Reducto parser.

        Args:
            api_key: API key for Reducto. If None, reads from REDUCTO_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("REDUCTO_API_KEY")
        if not self.api_key:
            raise ValueError("Reducto API key not provided")

        # Set API key in environment for Reducto client
        os.environ["REDUCTO_API_KEY"] = self.api_key

    async def parse_pdf(self, pdf_path: Path) -> ParseResult:
        """
        Parse PDF using Reducto and map chunks to pages.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ParseResult with chunks mapped to pages
        """
        start_time = time.time()

        # Initialize Reducto client
        client = Reducto()

        # Upload file
        upload_response = client.upload(file=pdf_path)

        # Parse with optimal settings for structured content
        result = client.parse.run(
            input=upload_response,
            enhance={
                "agentic": [],
                "summarize_figures": True,  # Add AI summaries for figures
            },
            retrieval={
                "chunking": {"chunk_mode": "variable"},  # Semantic chunking
                "embedding_optimized": True,
                "filter_blocks": [],
            },
            formatting={
                "add_page_markers": True,  # Important for page mapping
                "table_output_format": "dynamic",  # Best table format
                "merge_tables": False,  # Keep tables separate
            },
            settings={
                "ocr_system": "standard",
                "timeout": 900,
            },
        )

        # Debug: Save raw result structure
        import json
        debug_file_raw = Path("/Users/zby/data/RAGRace/data/temp/reducto_raw_result.json")
        try:
            with open(debug_file_raw, 'w') as f:
                result_info = {
                    "result_type": str(type(result)),
                    "has_result_attr": hasattr(result, 'result'),
                }
                if hasattr(result, '__dict__'):
                    result_info["result_dict_keys"] = list(result.__dict__.keys())
                if isinstance(result, dict):
                    result_info["dict_keys"] = list(result.keys())
                    result_info["result_value"] = result[:500] if len(str(result)) > 500 else result
                else:
                    result_info["result_str"] = str(result)[:500]

                json.dump(result_info, f, indent=2, default=str)
        except Exception as e:
            print(f"Debug raw result save failed: {e}")

        # Extract chunks from result - handle Reducto ParseResponse object
        if hasattr(result, 'result'):
            # result is a ParseResponse object with a result attribute
            result_data = result.result
            if hasattr(result_data, 'chunks'):
                # result_data is a ResultFullResult object with chunks attribute
                chunks = result_data.chunks
            elif isinstance(result_data, dict):
                chunks = result_data.get("chunks", [])
            else:
                chunks = []
        else:
            result_data = result
            chunks = result_data.get("chunks", []) if isinstance(result_data, dict) else []

        # Map chunks to pages using block metadata
        pages = self._map_chunks_to_pages(chunks)

        processing_time = time.time() - start_time

        return ParseResult(
            provider="reducto",
            total_pages=len(pages),
            pages=pages,
            raw_response={
                "total_chunks": len(chunks),
            },
            processing_time=processing_time,
        )

    def _map_chunks_to_pages(self, chunks: List[Dict[str, Any]]) -> List[PageResult]:
        """
        Map Reducto chunks to pages using block metadata.

        Reducto chunks don't natively have page numbers, but the blocks
        within each chunk contain page information. We use this to group
        chunks by page.

        Args:
            chunks: List of chunks from Reducto API

        Returns:
            List of PageResult objects, one per page
        """
        import json
        from pathlib import Path

        # Debug: Save raw chunks for inspection
        debug_file = Path("/Users/zby/data/RAGRace/data/temp/reducto_debug.json")
        try:
            with open(debug_file, 'w') as f:
                json.dump({
                    "total_chunks": len(chunks),
                    "first_chunk_keys": list(chunks[0].keys()) if chunks else [],
                    "first_chunk_sample": chunks[0] if chunks else None,
                    "chunks_preview": chunks[:2] if len(chunks) >= 2 else chunks
                }, f, indent=2, default=str)
        except Exception as e:
            print(f"Debug save failed: {e}")

        page_map: Dict[int, List[str]] = defaultdict(list)
        page_images: Dict[int, List[str]] = defaultdict(list)
        max_page = 0

        for chunk in chunks:
            # Convert Pydantic object to dict if needed
            if hasattr(chunk, '__dict__'):
                chunk_dict = chunk.__dict__ if hasattr(chunk, '__dict__') else {}
            elif isinstance(chunk, dict):
                chunk_dict = chunk
            else:
                continue

            # Get content (prefer enriched, fallback to embed, then content)
            content = (
                chunk_dict.get("enriched")
                or chunk_dict.get("embed")
                or chunk_dict.get("content")
                or ""
            )

            if not content:
                continue

            # Extract page numbers from blocks
            blocks = chunk_dict.get("blocks", [])
            if not blocks:
                # If no blocks, try to use chunk-level metadata
                chunk_page = chunk_dict.get("page", 1)
                page_map[chunk_page].append(content)
                max_page = max(max_page, chunk_page)
                continue

            # Get page numbers from all blocks in this chunk
            chunk_pages = set()
            for block in blocks:
                # Convert block to dict if it's a Pydantic object
                if hasattr(block, '__dict__'):
                    block_dict = block.__dict__
                elif isinstance(block, dict):
                    block_dict = block
                else:
                    continue

                # Try different possible page number fields
                # First check bbox which should have page number
                bbox = block_dict.get("bbox", {})
                if hasattr(bbox, '__dict__'):
                    bbox = bbox.__dict__
                page_num = bbox.get("page") if isinstance(bbox, dict) else None

                if page_num is None:
                    page_num = block_dict.get("page") or block_dict.get("page_number") or block_dict.get("page_idx")

                if page_num is not None and page_num >= 0:  # Reducto uses -1 for special blocks
                    # Convert to int if string
                    if isinstance(page_num, str):
                        try:
                            page_num = int(page_num)
                        except ValueError:
                            continue

                    chunk_pages.add(page_num)
                    max_page = max(max_page, page_num)

                # Extract image URLs if available
                block_type = block_dict.get("type") or block_dict.get("block_type")
                if block_type == "Image":
                    image_url = block_dict.get("url") or block_dict.get("image_url")
                    if image_url and page_num and page_num >= 0:
                        page_images[page_num].append(image_url)

            # If chunk spans multiple pages, add to all of them
            # If no page info, add to page 1
            if not chunk_pages:
                chunk_pages.add(1)

            for page_num in chunk_pages:
                page_map[page_num].append(content)

        # Ensure we have at least one page
        if not page_map:
            page_map[1] = ["*No content extracted - check Reducto API response format*"]
            max_page = 1
        else:
            max_page = max(max_page, 1)

        # Convert to PageResult objects
        pages = []
        for page_num in range(1, max_page + 1):
            page_content = page_map.get(page_num, [])
            markdown = "\n\n".join(page_content) if page_content else "*No content on this page*"

            pages.append(
                PageResult(
                    page_number=page_num,
                    markdown=markdown,
                    images=page_images.get(page_num, []),
                    metadata={
                        "chunk_count": len(page_content),
                        "has_images": len(page_images.get(page_num, [])) > 0,
                    },
                )
            )

        return pages
