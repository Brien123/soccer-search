import pytest
from pydantic import ValidationError

from stats.rag_request import RagRequest
from stats.search_hit import SearchHit
from stats.search_query import SearchQuery
from stats.search_response import SearchResponse


def test_search_query_defaults() -> None:
    query = SearchQuery()
    assert query.q == ""
    assert query.size == 10
    assert query.offset == 0
    assert query.mode == "keyword"
    assert query.team is None


def test_search_query_rejects_size_above_max() -> None:
    with pytest.raises(ValidationError):
        SearchQuery(size=51)


def test_search_query_rejects_negative_minute() -> None:
    with pytest.raises(ValidationError):
        SearchQuery(minute_from=-1)


def test_search_query_rejects_long_text() -> None:
    with pytest.raises(ValidationError):
        SearchQuery(q="a" * 501)


def test_rag_request_requires_question() -> None:
    with pytest.raises(ValidationError):
        RagRequest(question="")


def test_rag_request_default_size() -> None:
    assert RagRequest(question="who scored?").size == 5


def test_rag_request_rejects_size_above_ten() -> None:
    with pytest.raises(ValidationError):
        RagRequest(question="who scored?", size=11)


def test_search_hit_defaults() -> None:
    hit = SearchHit()
    assert hit.event_id is None
    assert hit.minute == 0
    assert hit.score == 0.0


def test_search_response_defaults() -> None:
    response = SearchResponse()
    assert response.total == 0
    assert response.hits == []
    assert response.mode == "keyword"
