"""
Database writer service for persisting benchmark results to Supabase.

Provides sync wrapper functions around async Prisma operations for use
in the synchronous Orchestrator execution flow.

Strategy: Try DB write first, fall back to file-based persistence on error.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from prisma import Prisma
from src.core.schemas import DocumentData, QuestionData, ProviderResult

logger = logging.getLogger(__name__)


class DbWriter:
    """
    Synchronous wrapper for async Prisma database operations.

    Uses asyncio.run() to execute async operations in sync context.
    Handles connection management and error recovery gracefully.
    """

    def __init__(self):
        """Initialize DB writer with persistent event loop."""
        self.prisma: Optional[Prisma] = None
        self.connected = False
        self.loop = None
        self._connect()

    def _connect(self) -> bool:
        """
        Connect to database.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Create persistent event loop for all async operations
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.prisma = Prisma()
            self.loop.run_until_complete(self.prisma.connect())
            self.connected = True
            logger.info("✓ Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            logger.warning("Benchmark will proceed with file-based persistence only")
            self.connected = False
            if self.loop:
                self.loop.close()
                self.loop = None
            return False

    def _disconnect(self):
        """Disconnect from database."""
        if self.prisma and self.connected:
            try:
                self.loop.run_until_complete(self.prisma.disconnect())
                self.loop.close()
                self.connected = False
                self.loop = None
                logger.info("✓ Database connection closed")
            except Exception as e:
                logger.error(f"Error disconnecting from database: {e}")

    def __del__(self):
        """Cleanup on object destruction."""
        self._disconnect()

    def _run_async(self, coro):
        """
        Run async coroutine in the persistent event loop.

        Args:
            coro: Async coroutine to run

        Returns:
            Result of coroutine
        """
        if not self.loop:
            raise RuntimeError("Event loop not initialized")
        return self.loop.run_until_complete(coro)

    def create_benchmark_run(
        self,
        run_id: str,
        config: Dict[str, Any],
        dataset_name: str,
        dataset_split: str,
        providers: List[str],
        num_docs: int = 0,
        num_questions_total: int = 0
    ) -> bool:
        """
        Create a new benchmark run record with status='RUNNING'.

        Args:
            run_id: Unique run identifier (e.g., "run_20251101_143000")
            config: Full benchmark configuration dict
            dataset_name: Dataset name (e.g., "qasper")
            dataset_split: Split name (e.g., "train", "validation")
            providers: List of provider names
            num_docs: Number of documents (may be updated on completion)
            num_questions_total: Total questions (may be updated on completion)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            async def _create():
                return await self.prisma.benchmarkrun.create(
                    data={
                        "runId": run_id,
                        "datasetName": dataset_name,
                        "datasetSplit": dataset_split,
                        "providers": providers,
                        "numDocs": num_docs,
                        "numQuestionsTotal": num_questions_total,
                        "status": "RUNNING",
                        "config": json.dumps(config),  # Serialize to JSON string
                        "startedAt": datetime.utcnow(),
                    }
                )

            result = self._run_async(_create())
            logger.info(f"✓ Created BenchmarkRun: {run_id} (DB ID: {result.id})")
            return True

        except Exception as e:
            logger.error(f"Failed to create benchmark run {run_id}: {e}")
            return False

    def save_provider_result(
        self,
        run_id: str,
        doc_data: DocumentData,
        questions_data: List[QuestionData],
        provider_result: ProviderResult
    ) -> bool:
        """
        Save provider result along with document and question data.

        This performs a complete transaction:
        1. Upsert Document
        2. Upsert Questions
        3. Create ProviderResult
        4. Create QuestionResults

        Args:
            run_id: Benchmark run ID
            doc_data: Document metadata
            questions_data: List of questions for this document
            provider_result: Provider result with question answers

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            async def _save():
                # 1. Find BenchmarkRun record
                benchmark_run = await self.prisma.benchmarkrun.find_unique(
                    where={"runId": run_id}
                )
                if not benchmark_run:
                    raise ValueError(f"BenchmarkRun not found: {run_id}")

                # 2. Upsert Document
                document = await self.prisma.document.upsert(
                    where={
                        "docId_datasetName": {
                            "docId": doc_data.doc_id,
                            "datasetName": doc_data.metadata.get("dataset", "unknown"),
                        }
                    },
                    data={
                        "create": {
                            "docId": doc_data.doc_id,
                            "datasetName": doc_data.metadata.get("dataset", "unknown"),
                            "docTitle": doc_data.doc_title,
                            "pdfPath": str(doc_data.pdf_path) if doc_data.pdf_path else None,
                            "pdfUrl": None,  # TODO: Upload to Supabase Storage
                            "pdfSizeBytes": doc_data.pdf_size_bytes,
                            "metadata": json.dumps(doc_data.metadata),
                        },
                        "update": {},  # Don't update if exists
                    }
                )

                # 3. Upsert Questions (batch)
                question_db_ids = {}
                for question_data in questions_data:
                    question = await self.prisma.question.upsert(
                        where={
                            "questionId_documentId": {
                                "questionId": question_data.question_id,
                                "documentId": document.id,
                            }
                        },
                        data={
                            "create": {
                                "questionId": question_data.question_id,
                                "documentId": document.id,
                                "question": question_data.question,
                                "groundTruth": question_data.ground_truth,
                                "metadata": json.dumps(question_data.metadata),
                            },
                            "update": {},  # Don't update if exists
                        }
                    )
                    question_db_ids[question_data.question_id] = question.id

                # 4. Create ProviderResult
                # Parse timestamps
                started_at = None
                completed_at = None
                if provider_result.timestamp_start:
                    started_at = datetime.fromisoformat(provider_result.timestamp_start)
                if provider_result.timestamp_end:
                    completed_at = datetime.fromisoformat(provider_result.timestamp_end)

                provider_db_result = await self.prisma.providerresult.create(
                    data={
                        "runId": benchmark_run.id,
                        "documentId": document.id,
                        "provider": provider_result.provider,
                        "status": "SUCCESS" if provider_result.status == "success" else "ERROR",
                        "error": provider_result.error,
                        "indexId": provider_result.index_id,
                        "aggregatedScores": json.dumps(provider_result.aggregated_scores),
                        "durationSeconds": provider_result.duration_seconds,
                        "startedAt": started_at,
                        "completedAt": completed_at,
                    }
                )

                # 5. Create QuestionResults (batch)
                for question_result in provider_result.questions:
                    question_db_id = question_db_ids.get(question_result.question_id)
                    if not question_db_id:
                        logger.warning(f"Question {question_result.question_id} not found in DB, skipping")
                        continue

                    await self.prisma.questionresult.create(
                        data={
                            "providerResultId": provider_db_result.id,
                            "questionId": question_db_id,
                            "responseAnswer": question_result.response_answer,
                            "responseContext": question_result.response_context,
                            "responseLatencyMs": question_result.response_latency_ms,
                            "responseMetadata": json.dumps(question_result.response_metadata),
                            "evaluationScores": json.dumps(question_result.evaluation_scores),
                        }
                    )

                return True

            success = self._run_async(_save())
            logger.info(
                f"✓ Saved to DB: {provider_result.provider} on {doc_data.doc_id} "
                f"({len(provider_result.questions)} questions)"
            )
            return success

        except Exception as e:
            logger.error(
                f"Failed to save provider result ({provider_result.provider} on {doc_data.doc_id}): {e}"
            )
            return False

    def complete_benchmark_run(
        self,
        run_id: str,
        duration_seconds: float,
        num_docs: int,
        num_questions_total: int
    ) -> bool:
        """
        Mark benchmark run as completed.

        Args:
            run_id: Run identifier
            duration_seconds: Total execution time
            num_docs: Final document count
            num_questions_total: Final question count

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            async def _complete():
                return await self.prisma.benchmarkrun.update(
                    where={"runId": run_id},
                    data={
                        "status": "COMPLETED",
                        "completedAt": datetime.utcnow(),
                        "durationSeconds": duration_seconds,
                        "numDocs": num_docs,
                        "numQuestionsTotal": num_questions_total,
                    }
                )

            result = self._run_async(_complete())
            logger.info(f"✓ Completed BenchmarkRun: {run_id} ({duration_seconds:.1f}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to complete benchmark run {run_id}: {e}")
            return False

    def fail_benchmark_run(self, run_id: str, error_message: str) -> bool:
        """
        Mark benchmark run as failed.

        Args:
            run_id: Run identifier
            error_message: Error description

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            async def _fail():
                return await self.prisma.benchmarkrun.update(
                    where={"runId": run_id},
                    data={
                        "status": "FAILED",
                        "errorMessage": error_message,
                        "completedAt": datetime.utcnow(),
                    }
                )

            result = self._run_async(_fail())
            logger.info(f"✓ Marked BenchmarkRun as FAILED: {run_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to mark benchmark run as failed {run_id}: {e}")
            return False
