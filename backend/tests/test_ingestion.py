"""Tests for the PubMed ingestion pipeline."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.vector_store import get_vector_store
from app.main import app
from app.services.ingestion_service import ingest

client = TestClient(app)


class FakeCollection:
    def __init__(self, existing_ids=None):
        self.ids = set(existing_ids or [])

    def count(self):
        return len(self.ids)

    def get(self, ids):
        return {"ids": [chunk_id for chunk_id in ids if chunk_id in self.ids]}


class FakeVectorStore:
    def __init__(self, existing_ids=None):
        self._collection = FakeCollection(existing_ids)
        self.added = []

    def add_texts(self, texts, metadatas, ids):
        self.added.append({"texts": texts, "metadatas": metadatas, "ids": ids})
        self._collection.ids.update(ids)


def test_ingestion_status():
    fake_store = FakeVectorStore()
    app.dependency_overrides[get_vector_store] = lambda: fake_store
    try:
        response = client.get("/api/v1/ingestion/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["document_count"] == 0
    assert data["collection"] == "pubmed_abstracts"


@patch("app.routers.ingestion.ingestion_service.ingest", return_value=2)
def test_ingest_endpoint_success(mock_ingest):
    fake_store = FakeVectorStore()
    app.dependency_overrides[get_vector_store] = lambda: fake_store
    try:
        response = client.post(
            "/api/v1/ingestion/ingest",
            json={"query": "diabetes", "max_results": 10},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["documents_ingested"] == 2
    mock_ingest.assert_called_once()


def test_ingest_requires_email():
    fake_store = FakeVectorStore()

    try:
        ingest("diabetes", 1, fake_store, email="")
    except ValueError as exc:
        assert "PUBMED_EMAIL" in str(exc)
    else:
        raise AssertionError("ingest should require PUBMED_EMAIL")


@patch("app.services.ingestion_service.time.sleep", return_value=None)
@patch("app.services.ingestion_service.seeding._chunk")
@patch("app.services.ingestion_service.seeding._fetch_abstract")
@patch("app.services.ingestion_service.seeding._fetch_full_text")
@patch("app.services.ingestion_service.seeding._search")
def test_ingest_fetches_chunks_and_skips_existing(
    mock_search,
    mock_full_text,
    mock_abstract,
    mock_chunk,
    _mock_sleep,
):
    fake_store = FakeVectorStore(existing_ids={"123_chunk_0"})
    mock_search.return_value = ["123", "123", "456"]
    mock_full_text.side_effect = lambda pmid: {
        "pmid": pmid,
        "full_text": f"record {pmid}",
        "source": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "is_full_text": False,
    }
    mock_abstract.return_value = None
    mock_chunk.side_effect = lambda doc: [{
        "text": doc["full_text"],
        "metadata": {
            "pmid": doc["pmid"],
            "source": doc["source"],
            "is_full_text": doc["is_full_text"],
            "chunk_index": 0,
        },
    }]

    count = ingest("diabetes", 10, fake_store, email="user@example.com", ncbi_api_key="key")

    assert count == 1
    assert fake_store.added[0]["ids"] == ["456_chunk_0"]
    assert mock_search.call_args.args == ("diabetes", 10)
