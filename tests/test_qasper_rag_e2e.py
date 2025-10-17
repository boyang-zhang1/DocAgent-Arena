"""
End-to-end RAGRace test with Qasper dataset.

Complete RAGRace workflow - Fair 3-way comparison:
1. Load Qasper paper (original PDF from arxiv + questions with ground truth)
2. Upload SAME PDF to ALL 3 RAG providers (LlamaIndex, LandingAI, Reducto)
3. Query ALL 3 providers with SAME questions
4. Evaluate EACH provider's answers against ground truth using Ragas metrics
5. Compare scores across providers and declare winner

Key Design Decisions:
- Uses ORIGINAL PDF from arxiv (not reconstructed from text)
- ALL providers process SAME PDF format (fair comparison)
- Evaluation metrics: Faithfulness, Factual Correctness, Context Recall
- Default: 1 paper, 3 questions (configurable for cost control)

Test Results Example (1 paper, 3 questions):
- Winner: Reducto (2/3 metrics)
- Reducto: Faithfulness=1.0, Factual_Correctness=0.71, Context_Recall=1.0
- LandingAI: Faithfulness=1.0, Factual_Correctness=0.43, Context_Recall=0.83
- LlamaIndex: Faithfulness=0.0, Factual_Correctness=0.17, Context_Recall=0.0
- Duration: ~2 minutes

Usage:
    # Default test (1 paper, 3 questions)
    pytest tests/test_qasper_rag_e2e.py::TestQasperRAGRace::test_ragrace_3_providers_qasper -v -s -m integration

    # Modify max_papers and max_questions in test code for different scale
"""

import pytest
import os
from pathlib import Path

from src.datasets.loader import DatasetLoader
from src.core.ragas_evaluator import RagasEvaluator, RAGEvaluationSample
from src.adapters.llamaindex_adapter import LlamaIndexAdapter
from src.adapters.landingai_adapter import LandingAIAdapter
from src.adapters.reducto_adapter import ReductoAdapter
from src.adapters.base import Document


@pytest.mark.integration
class TestQasperRAGRace:
    """Integration test: Complete RAGRace on Qasper papers."""

    @pytest.fixture
    def openai_api_key(self):
        """Get OpenAI API key."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            pytest.skip("OPENAI_API_KEY not set - skipping test")
        return key

    @pytest.fixture
    def landingai_api_key(self):
        """Get LandingAI API key."""
        key = os.getenv("VISION_AGENT_API_KEY")
        if not key:
            pytest.skip("VISION_AGENT_API_KEY not set - skipping test")
        return key

    @pytest.fixture
    def reducto_api_key(self):
        """Get Reducto API key."""
        key = os.getenv("REDUCTO_API_KEY")
        if not key:
            pytest.skip("REDUCTO_API_KEY not set - skipping test")
        return key

    @pytest.fixture
    def ragas_evaluator(self):
        """Initialize Ragas evaluator."""
        config = {
            'model': 'gpt-4o-mini',
            'api_key_env': 'OPENAI_API_KEY',
            'metrics': ['faithfulness', 'factual_correctness', 'context_recall']
        }
        return RagasEvaluator(config)

    def test_ragrace_3_providers_qasper(
        self,
        openai_api_key,
        landingai_api_key,
        reducto_api_key,
        ragas_evaluator
    ):
        """
        Complete RAGRace: 3 providers compete on same Qasper paper.

        Workflow:
        1. Load 1 paper, 3 questions from Qasper
        2. Upload to LlamaIndex (text), LandingAI (PDF), Reducto (PDF)
        3. Query all 3 with same questions
        4. For each question: evaluate all 3 predictions vs ground truth
        5. Compare scores and declare winner

        Args:
            max_papers: Number of papers (default: 1)
            max_questions: Questions per paper (default: 3 for demo)
        """
        max_papers = 1
        max_questions = 3

        print("\n" + "=" * 80)
        print("🏁 RAGRACE: 3-WAY PROVIDER COMPARISON ON QASPER")
        print("=" * 80)

        # Step 1: Load Qasper paper
        print(f"\n📥 Loading Qasper paper ({max_papers} paper, {max_questions} questions)...")
        dataset = DatasetLoader.load_qasper(
            split='train',
            max_papers=max_papers,
            filter_unanswerable=True
        )

        samples = dataset.samples[:max_questions]
        paper_id = samples[0].metadata['paper_id']
        paper_title = samples[0].metadata['paper_title']
        original_pdf_path = Path(samples[0].metadata['pdf_path'])  # ORIGINAL PDF from arxiv!

        print(f"✓ Loaded paper: {paper_id}")
        print(f"  Title: {paper_title[:80]}...")
        print(f"  Original PDF: {original_pdf_path}")
        print(f"  PDF size: {original_pdf_path.stat().st_size} bytes")
        print(f"  Questions: {len(samples)}")

        # Step 2: Initialize ALL 3 RAG providers
        print("\n📦 Initializing ALL 3 RAG providers...")
        adapters = {}

        # LlamaIndex
        adapters['LlamaIndex'] = LlamaIndexAdapter()
        adapters['LlamaIndex'].initialize(api_key=openai_api_key, top_k=3)
        print("  ✓ LlamaIndex initialized")

        # LandingAI
        adapters['LandingAI'] = LandingAIAdapter()
        adapters['LandingAI'].initialize(
            api_key=landingai_api_key,
            openai_api_key=openai_api_key,
            top_k=3
        )
        print("  ✓ LandingAI initialized")

        # Reducto
        adapters['Reducto'] = ReductoAdapter()
        adapters['Reducto'].initialize(
            api_key=reducto_api_key,
            openai_api_key=openai_api_key,
            top_k=3
        )
        print("  ✓ Reducto initialized")

        # Step 3: Upload SAME ORIGINAL PDF to ALL 3 providers
        print(f"\n🔄 Uploading ORIGINAL PDF to ALL 3 providers: {original_pdf_path.name}")
        indices = {}

        # LlamaIndex: Original PDF
        pdf_doc_llama = Document(
            id=paper_id,
            content="",
            metadata={'file_path': str(original_pdf_path), 'title': paper_title}
        )
        indices['LlamaIndex'] = adapters['LlamaIndex'].ingest_documents([pdf_doc_llama])
        print(f"  ✓ LlamaIndex ingested PDF")

        # LandingAI: Original PDF
        pdf_doc_landingai = Document(
            id=paper_id,
            content="",
            metadata={'file_path': str(original_pdf_path), 'title': paper_title}
        )
        indices['LandingAI'] = adapters['LandingAI'].ingest_documents([pdf_doc_landingai])
        print(f"  ✓ LandingAI ingested PDF")

        # Reducto: Original PDF
        pdf_doc_reducto = Document(
            id=paper_id,
            content="",
            metadata={'file_path': str(original_pdf_path), 'title': paper_title}
        )
        indices['Reducto'] = adapters['Reducto'].ingest_documents([pdf_doc_reducto])
        print(f"  ✓ Reducto ingested PDF")

        # Step 4: Query ALL 3 providers with SAME questions
        print(f"\n📝 Querying ALL 3 providers ({len(samples)} questions)...")
        print("=" * 80)

        # Store all samples for evaluation (per provider)
        provider_samples = {name: [] for name in adapters.keys()}

        for i, sample in enumerate(samples, 1):
            question = sample.question
            ground_truth = sample.ground_truth

            print(f"\n❓ Question {i}: {question}")
            print(f"   Ground Truth: {ground_truth[:100]}...")
            print()

            # Query each provider
            for provider_name, adapter in adapters.items():
                response = adapter.query(question, indices[provider_name])

                print(f"   {provider_name}:")
                print(f"     Answer: {response.answer[:100]}...")
                print(f"     Latency: {response.latency_ms:.0f}ms | Chunks: {len(response.context)}")

                # Store for evaluation
                ragas_sample = RAGEvaluationSample(
                    user_input=question,
                    reference=ground_truth,
                    retrieved_contexts=response.context,
                    response=response.answer,
                    metadata={
                        'provider': provider_name,
                        'latency_ms': response.latency_ms,
                        'question_id': sample.metadata['question_id'],
                        'paper_id': paper_id
                    }
                )
                provider_samples[provider_name].append(ragas_sample)

            print("-" * 80)

        # Step 5: Evaluate ALL providers with Ragas
        print("\n" + "=" * 80)
        print("📊 RAGAS EVALUATION - Per Provider")
        print("=" * 80)

        provider_scores = {}
        for provider_name, samples_list in provider_samples.items():
            print(f"\nEvaluating {provider_name}...")
            eval_result = ragas_evaluator.evaluate_samples(samples_list)
            provider_scores[provider_name] = eval_result.scores

            print(f"  {provider_name} Scores:")
            for metric, score in eval_result.scores.items():
                print(f"    {metric}: {score:.4f}")

        # Step 6: Compare and declare winner
        print("\n" + "=" * 80)
        print("🏆 RAGRACE RESULTS - PROVIDER COMPARISON")
        print("=" * 80)

        # Compare by each metric
        metrics = list(next(iter(provider_scores.values())).keys())
        overall_winners = []

        for metric in metrics:
            print(f"\n📊 {metric.upper()}:")
            scores = [(name, provider_scores[name][metric]) for name in adapters.keys()]
            scores.sort(key=lambda x: x[1], reverse=True)

            for rank, (name, score) in enumerate(scores, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
                print(f"  {medal} {name}: {score:.4f}")

            # Track winner for this metric
            overall_winners.append(scores[0][0])

        # Declare overall winner
        print("\n" + "=" * 80)
        print("🎯 OVERALL WINNER")
        print("=" * 80)

        # Count how many metrics each provider won
        from collections import Counter
        winner_counts = Counter(overall_winners)
        final_winner = winner_counts.most_common(1)[0][0]

        print(f"\n🏆 {final_winner} wins {winner_counts[final_winner]}/{len(metrics)} metrics!")
        print("\nMedal count:")
        for provider_name in adapters.keys():
            count = winner_counts[provider_name]
            print(f"  {provider_name}: {count} 🥇")

        # No cleanup needed - using original PDF from arxiv

        print("\n" + "=" * 80)
        print("✅ RAGRACE COMPLETE!")
        print("=" * 80)

        # Assertions
        assert len(provider_scores) == 3, "Should have scores for all 3 providers"
        for provider_name in adapters.keys():
            assert provider_name in provider_scores
            assert len(provider_scores[provider_name]) > 0

        return {
            'winner': final_winner,
            'scores': provider_scores,
            'questions': len(samples)
        }


if __name__ == "__main__":
    """
    Run the RAGRace:

    pytest tests/test_qasper_rag_e2e.py::TestQasperRAGRace::test_ragrace_3_providers_qasper -v -s -m integration
    """
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
