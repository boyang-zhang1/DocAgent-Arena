"""Tests for battle mode logic in parsing API."""

import shutil
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.main import app
from backend.api.db import get_db
from backend.api.routers import parsing as parsing_router
from src.adapters.parsing.base import PageResult, ParseResult


@pytest.fixture(autouse=True)
def override_db_dependency():
    """Ensure DB operations are skipped during API tests."""

    async def _override():  # pragma: no cover - trivial dependency override
        return None

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


def _install_dummy_parsers(monkeypatch):
    """Replace external parser SDKs and storage service with deterministic stubs."""

    def _factory(provider_name):
        class _DummyParser:
            def __init__(self, *args, **kwargs):
                self.provider_name = provider_name

            async def parse_pdf(self, pdf_path):  # pragma: no cover - exercised via API call
                return ParseResult(
                    provider=self.provider_name,
                    total_pages=1,
                    pages=[
                        PageResult(
                            page_number=1,
                            markdown=f"## {self.provider_name} summary",
                            images=[],
                            metadata={"source": str(pdf_path)},
                        )
                    ],
                    raw_response={},
                    processing_time=0.01,
                    usage={"num_pages": 1, "parse_mode": "test"},
                )

        return _DummyParser

    monkeypatch.setattr(parsing_router, "LlamaIndexParser", _factory("llamaindex"))
    monkeypatch.setattr(parsing_router, "ReductoParser", _factory("reducto"))

    class _DummyStorage:
        def upload(self, local_path, storage_path):  # pragma: no cover - trivial
            return f"https://storage/{storage_path}"

    monkeypatch.setattr(parsing_router, "SupabaseStorageService", lambda: _DummyStorage())
    monkeypatch.setattr(parsing_router, "load_pricing_config", lambda: {})


def _prepare_temp_pdf(file_id: str) -> None:
    """Copy fixture PDF into parse upload temp directory."""

    src = Path(__file__).resolve().parents[2] / "data/test/temp_pdfs/Low-Back-Guideline.pdf"
    dst = parsing_router.TEMP_DIR / f"{file_id}.pdf"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)


def test_battle_mode_requires_page_number(monkeypatch):
    _install_dummy_parsers(monkeypatch)
    file_id = uuid.uuid4().hex
    _prepare_temp_pdf(file_id)

    client = TestClient(app)
    response = client.post(
        "/api/v1/parse/compare",
        json={"file_id": file_id},
    )

    assert response.status_code == 400
    assert "page" in response.json()["detail"].lower()


def test_battle_mode_returns_assignments(monkeypatch):
    _install_dummy_parsers(monkeypatch)
    file_id = uuid.uuid4().hex
    _prepare_temp_pdf(file_id)

    client = TestClient(app)
    response = client.post(
        "/api/v1/parse/compare",
        json={"file_id": file_id, "page_number": 1, "filename": "sample.pdf"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["battle"]["battle_id"]
    assignments = payload["battle"]["assignments"]
    assert len(assignments) == 2
    assert set(entry["provider"] for entry in assignments) == {"llamaindex", "reducto"}

    results = payload["results"]
    assert set(results.keys()) == {"llamaindex", "reducto"}
    for provider, data in results.items():
        assert data["total_pages"] == 1
        assert data["pages"][0]["markdown"]
