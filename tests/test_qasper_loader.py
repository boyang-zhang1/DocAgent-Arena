"""Test Qasper dataset loader."""

import pytest
from src.datasets.loader import DatasetLoader


def test_qasper_load_minimal():
    """Test loading a minimal sample of Qasper dataset (2 papers for speed)."""
    dataset = DatasetLoader.load_qasper(
        split='train',
        max_papers=2,
        filter_unanswerable=True
    )

    # Verify dataset structure
    assert dataset.dataset_name == 'Qasper'
    assert len(dataset) > 0, "Should have at least some samples"

    # Verify at least 1 paper downloaded
    assert dataset.metadata['downloaded_papers'] >= 1, \
        "At least 1 paper should download successfully"

    # Verify sample structure
    sample = dataset.samples[0]
    assert sample.question, "Question should not be empty"
    assert sample.context, "Context (PDF text) should not be empty"
    assert sample.ground_truth, "Ground truth answer should not be empty"

    # Verify metadata
    assert 'paper_id' in sample.metadata
    assert 'question_id' in sample.metadata
    assert 'paper_title' in sample.metadata
    assert 'pdf_path' in sample.metadata

    # Verify context is raw PDF text (should be reasonably long)
    assert len(sample.context) > 1000, \
        "PDF text should be substantial (>1000 chars)"

    print(f"\n✓ Test passed: {len(dataset)} samples from {dataset.metadata['downloaded_papers']} papers")
    print(f"  Questions: {dataset.metadata['total_questions']}")
    print(f"  Samples created: {dataset.metadata['samples_created']}")
    print(f"  Failed downloads: {dataset.metadata['failed_downloads']}")


def test_qasper_sample_content():
    """Test that Qasper samples have reasonable content."""
    dataset = DatasetLoader.load_qasper(split='train', max_papers=1)

    if len(dataset) == 0:
        pytest.skip("No samples available (download may have failed)")

    sample = dataset.samples[0]

    # Question should be a proper sentence
    assert len(sample.question.split()) >= 3, "Question should have multiple words"

    # PDF context should contain typical paper elements
    context_lower = sample.context.lower()
    # Check for common paper elements (at least one should be present)
    paper_indicators = ['abstract', 'introduction', 'method', 'conclusion', 'reference', 'figure']
    has_indicator = any(indicator in context_lower for indicator in paper_indicators)
    assert has_indicator, "PDF text should contain typical paper sections"

    # Ground truth should be non-trivial
    assert len(sample.ground_truth.split()) >= 2, "Answer should have at least 2 words"

    print(f"\n✓ Sample content validation passed")
    print(f"  Question: {sample.question[:100]}...")
    print(f"  Answer: {sample.ground_truth[:100]}...")
    print(f"  Context length: {len(sample.context)} chars")
