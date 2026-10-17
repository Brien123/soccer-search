from typing import Any

import pytest

from stats.search_query import SearchQuery
from stats.search_service import SearchService
from tests.conftest import make_hit
from tests.fakes.fake_elasticsearch_client import FakeElasticsearchClient


def test_keyword_body_uses_match_clause(
    search_service: SearchService, fake_client: FakeElasticsearchClient
) -> None:
    search_service.search(SearchQuery(q="late goals", size=5))
    body: dict[str, Any] = fake_client.last_body
    assert fake_client.last_index == "test_index"
    assert body["size"] == 5
    must: list[dict[str, Any]] = body["query"]["bool"]["must"]
    assert {"match": {"narrative": {"query": "late goals"}}} in must


def test_keyword_body_empty_text_uses_match_all(
    search_service: SearchService, fake_client: FakeElasticsearchClient
) -> None:
    search_service.search(SearchQuery(q="   "))
    body: dict[str, Any] = fake_client.last_body
    assert body["query"]["bool"]["must"] == [{"match_all": {}}]


def test_keyword_body_adds_all_filters(
    search_service: SearchService, fake_client: FakeElasticsearchClient
) -> None:
    query = SearchQuery(
        q="shot",
        team="Barcelona",
        player="Lionel Messi",
        match_id="3879600",
        minute_from=75,
        minute_to=95,
    )
    search_service.search(query)
    filters: list[dict[str, Any]] = fake_client.last_body["query"]["bool"]["filter"]
    assert {"term": {"team": "Barcelona"}} in filters
    assert {"term": {"player": "Lionel Messi"}} in filters
    assert {"term": {"match_id": "3879600"}} in filters
    assert {"range": {"minute": {"gte": 75, "lte": 95}}} in filters


def test_keyword_body_skips_empty_filters(
    search_service: SearchService, fake_client: FakeElasticsearchClient
) -> None:
    search_service.search(SearchQuery(q="shot"))
    filters: list[dict[str, Any]] = fake_client.last_body["query"]["bool"]["filter"]
    assert filters == []


def test_search_rejects_non_keyword_mode(search_service: SearchService) -> None:
    with pytest.raises(ValueError, match="keyword"):
        search_service.search(SearchQuery(q="shot", mode="hybrid"))


def test_to_response_maps_hits(search_service: SearchService) -> None:
    raw: dict[str, Any] = {
        "hits": {
            "total": {"value": 42},
            "hits": [make_hit(event_id="evt-9", minute=88, score=4.2)],
        }
    }
    response = search_service._to_response(raw, "keyword")
    assert response.total == 42
    assert response.mode == "keyword"
    assert len(response.hits) == 1
    hit = response.hits[0]
    assert hit.event_id == "evt-9"
    assert hit.minute == 88
    assert hit.score == 4.2


def test_hybrid_body_has_knn_and_match(
    search_service: SearchService, fake_client: FakeElasticsearchClient
) -> None:
    vector: list[float] = [0.5] * 768
    search_service.search_hybrid(SearchQuery(q="late goals", size=3), vector)
    body: dict[str, Any] = fake_client.last_body
    should: list[dict[str, Any]] = body["query"]["bool"]["should"]
    knn = next(clause["knn"] for clause in should if "knn" in clause)
    assert knn["field"] == "narrative_vector"
    assert knn["query_vector"] == vector
    assert knn["k"] == 3
    assert any("match" in clause for clause in should)


def test_hybrid_keeps_filters(
    search_service: SearchService, fake_client: FakeElasticsearchClient
) -> None:
    search_service.search_hybrid(SearchQuery(q="goal", team="Barcelona"), [0.0] * 768)
    filters: list[dict[str, Any]] = fake_client.last_body["query"]["bool"]["filter"]
    assert {"term": {"team": "Barcelona"}} in filters


def test_hybrid_response_mode(
    search_service: SearchService, fake_client: FakeElasticsearchClient
) -> None:
    response = search_service.search_hybrid(SearchQuery(q="goal"), [0.0] * 768)
    assert response.mode == "hybrid"


def test_health_reports_version_and_count(provider: Any, fake_embeddings: Any) -> None:
    client = FakeElasticsearchClient(count=7573, version_number="8.15.0")
    provider._client = client
    service = SearchService(provider, fake_embeddings)
    health = service.health()
    assert health["count"] == 7573
    assert health["elasticsearch"]["number"] == "8.15.0"
