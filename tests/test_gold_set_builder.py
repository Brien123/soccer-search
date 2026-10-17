from typing import Any

from stats.config import AppConfig
from stats.eval_case import EvalCase
from stats.gold_set_builder import GoldSetBuilder
from tests.fakes.fake_elasticsearch_client import FakeElasticsearchClient
from tests.fakes.fake_elasticsearch_provider import FakeElasticsearchProvider


def make_provider(event_ids: list[str]) -> FakeElasticsearchProvider:
    hits: list[dict[str, Any]] = [
        {"_score": 1.0, "_source": {"event_id": event_id}} for event_id in event_ids
    ]
    client = FakeElasticsearchClient(hits=hits)
    config = AppConfig(index_name="test_index")
    return FakeElasticsearchProvider(config, client)


def test_build_returns_event_ids() -> None:
    provider = make_provider(["e1", "e2"])
    builder = GoldSetBuilder(provider)  # type: ignore[arg-type]
    case = EvalCase(id="q", query="x", intent={"event_type": "Shot"})
    assert builder.build(case) == {"e1", "e2"}


def test_build_expected_empty_short_circuits() -> None:
    provider = make_provider(["e1"])
    builder = GoldSetBuilder(provider)  # type: ignore[arg-type]
    case = EvalCase(id="q", query="x", intent={}, expected_empty=True)
    assert builder.build(case) == set()


def test_build_sends_filter_and_source() -> None:
    provider = make_provider(["e1"])
    client = provider.get_client()
    builder = GoldSetBuilder(provider)  # type: ignore[arg-type]
    builder.build(EvalCase(id="q", query="x", intent={"event_type": "Shot"}))
    body = client.last_body
    assert body["_source"] == ["event_id"]
    assert {"term": {"event_type": "Shot"}} in body["query"]["bool"]["filter"]
