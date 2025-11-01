"""
Benchmarks router - API endpoints for creating and managing benchmark runs.
"""

import tempfile
import yaml
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional

from api.models.benchmark import BenchmarkRequest, BenchmarkResponse
from src.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Simple API key verification.

    For now, just checks that key is present.
    Future: Validate against users table.

    Args:
        x_api_key: API key from header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=403,
            detail="API key required. Include 'X-API-Key' header to trigger benchmarks."
        )
    return x_api_key


@router.post("", response_model=BenchmarkResponse)
async def create_benchmark(
    request: BenchmarkRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create and execute a new benchmark run.

    **NOTE**: This endpoint runs synchronously and may take 1-5+ minutes to complete
    for small benchmarks. Use small values for max_docs/max_questions_per_doc for testing.

    **Authentication**: Requires X-API-Key header.

    **Request Body**:
    ```json
    {
        "dataset": "qasper",
        "split": "train",
        "providers": ["llamaindex"],
        "max_docs": 2,
        "max_questions_per_doc": 3,
        "filter_unanswerable": true
    }
    ```

    **Response**:
    ```json
    {
        "run_id": "run_20251101_143000",
        "status": "completed",
        "message": "Benchmark completed successfully",
        "duration_seconds": 123.45
    }
    ```

    Args:
        request: Benchmark configuration
        api_key: API key from header (verified by dependency)

    Returns:
        BenchmarkResponse with run_id and status

    Raises:
        HTTPException: If benchmark fails
    """
    logger.info(f"Benchmark request received: {request.dataset}, {request.providers}")

    # Generate run_id
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create temporary config file
    config = _create_config_from_request(request)

    try:
        # Write config to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        logger.info(f"Created temp config: {config_path}")

        # Initialize orchestrator
        orchestrator = Orchestrator(config_path)

        # Run benchmark in separate thread to avoid event loop conflict
        # This isolates DbWriter's event loop from FastAPI's event loop
        logger.info(f"Starting benchmark execution in thread pool: {run_id}")
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool,
                orchestrator.run_benchmark
            )

        # Clean up temp file
        Path(config_path).unlink(missing_ok=True)

        logger.info(f"Benchmark completed: {run_id} ({result.duration_seconds:.1f}s)")

        return BenchmarkResponse(
            run_id=result.run_id,
            status="completed",
            message="Benchmark completed successfully",
            duration_seconds=result.duration_seconds
        )

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

        # Clean up temp file
        try:
            Path(config_path).unlink(missing_ok=True)
        except:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Benchmark execution failed: {str(e)}"
        )


def _create_config_from_request(request: BenchmarkRequest) -> dict:
    """
    Create benchmark config dict from API request.

    This mirrors the structure of YAML config files.

    Args:
        request: BenchmarkRequest

    Returns:
        Config dict ready for YAML serialization
    """
    return {
        "benchmark": {
            "dataset": {
                "name": request.dataset,
                "split": request.split,
                "max_docs": request.max_docs,
                "max_questions_per_doc": request.max_questions_per_doc,
                "filter_unanswerable": request.filter_unanswerable,
            },
            "providers": request.providers,
            "provider_configs": {},  # Use defaults from providers.yaml
            "execution": {
                # Conservative defaults for API
                "max_total_workers": 4,
                "max_per_provider_workers": 2,
                "max_ragas_workers": 2,
            },
            "timeouts": {
                "provider_init": 30,
                "document_ingest": 300,
                "query": 60,
                "evaluation": 120,
            },
            "output": {
                "results_dir": "data/results",
                "save_intermediate": True,
                "resume_enabled": False,  # Don't resume API runs
            },
            "evaluation": {
                # Use default RAGAS metrics
                "model": "gpt-4o-mini",
                "metrics": [
                    "faithfulness",
                    "factual_correctness",
                    "context_recall"
                ],
            }
        }
    }
