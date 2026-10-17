from collections.abc import Callable
from typing import Any

import pytest

from stats.config import AppConfig
from stats.search_service import SearchService
from tests.fakes.fake_elasticsearch_client import FakeElasticsearchClient
from tests.fakes.fake_elasticsearch_provider import FakeElasticsearchProvider
from tests.fakes.fake_embedding_provider import FakeEmbeddingProvider
from tests.fakes.fake_llm_provider import FakeLlmProvider


def make_hit(
    event_id: str = "evt-1",
    match_id: str = "3879600",
    team: str = "Barcelona",
    player: str = "Lionel Messi",
    minute: int = 91,
    narrative: str = "Messi scored a goal.",
    score: float = 3.5,
) -> dict[str, Any]:
    return {
        "_score": score,
        "_source": {
            "event_id": event_id,
            "match_id": match_id,
            "team": team,
            "player": player,
            "minute": minute,
            "narrative": narrative,
        },
    }


@pytest.fixture
def config() -> AppConfig:
    return AppConfig(
        elasticsearch_host="http://test-host:9200",
        index_name="test_index",
        max_size=50,
        embedding_model="test/embedding-model",
        llm_host="http://test-llm:1234/v1",
        llm_model="test/llm-model",
    )


@pytest.fixture
def fake_client() -> FakeElasticsearchClient:
    return FakeElasticsearchClient()


@pytest.fixture
def provider(
    config: AppConfig, fake_client: FakeElasticsearchClient
) -> FakeElasticsearchProvider:
    return FakeElasticsearchProvider(config, fake_client)


@pytest.fixture
def fake_embeddings() -> FakeEmbeddingProvider:
    return FakeEmbeddingProvider()


@pytest.fixture
def fake_llm() -> FakeLlmProvider:
    return FakeLlmProvider()


@pytest.fixture
def search_service(
    provider: FakeElasticsearchProvider,
    fake_embeddings: FakeEmbeddingProvider,
) -> SearchService:
    return SearchService(provider, fake_embeddings)  # type: ignore[arg-type]


@pytest.fixture
def hit_builder() -> Callable[..., dict[str, Any]]:
    return make_hit
