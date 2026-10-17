from typing import Any

import pytest
from fastapi.testclient import TestClient

from stats.config import AppConfig
from tests.conftest import make_hit
from tests.fakes.fake_elasticsearch_client import FakeElasticsearchClient
from tests.fakes.fake_elasticsearch_provider import FakeElasticsearchProvider
from tests.fakes.fake_embedding_provider import FakeEmbeddingProvider
from tests.fakes.fake_llm_provider import FakeLlmProvider


@pytest.fixture
def client(config: AppConfig, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    es_client = FakeElasticsearchClient(
        hits=[make_hit(event_id="evt-1", narrative="Messi scored at 91:43.")],
        total=1,
        count=7573,
    )
    provider = FakeElasticsearchProvider(config, es_client)
    embeddings = FakeEmbeddingProvider()
    llm = FakeLlmProvider(answer="Messi scored late.")

    monkeypatch.setattr("stats.app_factory.ElasticsearchProvider", lambda cfg: provider)
    monkeypatch.setattr("stats.app_factory.EmbeddingProvider", lambda cfg: embeddings)
    monkeypatch.setattr("stats.app_factory.LlmProvider", lambda cfg: llm)

    from stats.app_factory import AppFactory

    app = AppFactory.create_app(config)
    return TestClient(app)


def test_index_returns_both_forms(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "searchForm" in response.text
    assert "ragForm" in response.text
    assert "tabRag" in response.text


def test_api_search_returns_hits(client: TestClient) -> None:
    response = client.get("/api/search", params={"q": "shot", "size": 5})
    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    assert payload["mode"] == "keyword"
    assert len(payload["hits"]) == 1
    assert payload["hits"][0]["narrative"] == "Messi scored at 91:43."


def test_api_search_rejects_bad_size(client: TestClient) -> None:
    response = client.get("/api/search", params={"q": "shot", "size": 999})
    assert response.status_code == 422


def test_api_search_hybrid_mode(client: TestClient) -> None:
    response = client.get(
        "/api/search", params={"q": "late goals", "mode": "hybrid", "size": 5}
    )
    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    assert payload["mode"] == "hybrid"
    assert len(payload["hits"]) == 1


def test_api_search_rejects_bad_mode(client: TestClient) -> None:
    response = client.get("/api/search", params={"q": "shot", "mode": "vector"})
    assert response.status_code == 422


def test_api_health_reports_count(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    assert payload["count"] == 7573
    assert payload["elasticsearch"]["number"] == "8.15.0"


def test_api_rag_returns_answer_and_citations(client: TestClient) -> None:
    response = client.post(
        "/api/rag",
        json={"question": "who scored late goals?", "size": 10},
    )
    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    assert payload["answer"] == "Messi scored late."
    assert payload["model"] == "fake/model"
    assert len(payload["citations"]) == 1


def test_api_rag_rejects_empty_question(client: TestClient) -> None:
    response = client.post("/api/rag", json={"question": ""})
    assert response.status_code == 422
