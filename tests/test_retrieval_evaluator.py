from typing import Any

from stats.config import AppConfig
from stats.eval_case import EvalCase
from stats.gold_set_builder import GoldSetBuilder
from stats.metric_calculator import MetricCalculator
from stats.retrieval_evaluator import RetrievalEvaluator
from stats.search_service import SearchService
from tests.fakes.fake_elasticsearch_client import FakeElasticsearchClient
from tests.fakes.fake_elasticsearch_provider import FakeElasticsearchProvider
from tests.fakes.fake_embedding_provider import FakeEmbeddingProvider


def make_hits(event_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {"_score": 1.0, "_source": {"event_id": event_id, "minute": index}}
        for index, event_id in enumerate(event_ids)
    ]


def build_evaluator(event_ids: list[str]) -> RetrievalEvaluator:
    config = AppConfig(index_name="test_index")
    client = FakeElasticsearchClient(hits=make_hits(event_ids))
    provider = FakeElasticsearchProvider(config, client)
    embeddings = FakeEmbeddingProvider()
    service = SearchService(provider, embeddings)  # type: ignore[arg-type]
    return RetrievalEvaluator(
        search_service=service,
        embeddings=embeddings,  # type: ignore[arg-type]
        gold_builder=GoldSetBuilder(provider),  # type: ignore[arg-type]
        metrics=MetricCalculator(),
        cutoffs=[2, 4],
    )


def test_keyword_precision_recall_f1() -> None:
    evaluator = build_evaluator(["e1", "e2", "e3", "e4"])
    case = EvalCase(id="q1", query="late goals", intent={"event_type": "Shot"})
    report = evaluator.evaluate([case], ["keyword"], labels={"q1": {"e1", "e3"}})
    assert report.macro("precision@2", "keyword") == 0.5
    assert report.macro("recall@2", "keyword") == 0.5
    assert report.macro("f1@2", "keyword") == 0.5
    assert report.micro(2, "keyword") == {
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }


def test_oracle_is_perfect() -> None:
    evaluator = build_evaluator(["e1", "e2", "e3", "e4"])
    case = EvalCase(id="q1", query="late goals", intent={"event_type": "Shot"})
    report = evaluator.evaluate([case], ["oracle"], labels={"q1": {"e1", "e3"}})
    assert report.macro("precision@2", "oracle") == 1.0
    assert report.macro("recall@2", "oracle") == 1.0
    assert report.macro("f1@2", "oracle") == 1.0


def test_mrr_and_ndcg() -> None:
    evaluator = build_evaluator(["e1", "e2", "e3", "e4"])
    case = EvalCase(id="q1", query="late goals", intent={"event_type": "Shot"})
    report = evaluator.evaluate([case], ["keyword"], labels={"q1": {"e1", "e3"}})
    result = report.results[0]
    assert result.metrics["mrr"] == 1.0
    assert round(result.metrics["ndcg@2"], 3) == 0.613
    assert result.relevant_total == 2


def test_negative_query_reports_returned() -> None:
    evaluator = build_evaluator(["e1", "e2"])
    case = EvalCase(
        id="n1",
        query="var handball",
        category="negative",
        expected_empty=True,
    )
    report = evaluator.evaluate([case], ["keyword"])
    summary = report.negatives("keyword")
    assert summary["cases"] == 1.0
    assert summary["returned_any"] == 1.0
    assert summary["false_positive_rate"] == 1.0


def test_unlabeled_subjective_is_skipped() -> None:
    evaluator = build_evaluator(["e1"])
    case = EvalCase(id="u1", query="clutch", category="subjective")
    report = evaluator.evaluate([case], ["keyword"])
    assert report.results == []


def test_programmatic_gold_when_no_labels() -> None:
    evaluator = build_evaluator(["e1", "e2"])
    case = EvalCase(id="q1", query="shots", intent={"event_type": "Shot"})
    report = evaluator.evaluate([case], ["keyword"])
    assert report.macro("precision@2", "keyword") == 1.0


def test_hybrid_mode_runs() -> None:
    evaluator = build_evaluator(["e1", "e2"])
    case = EvalCase(id="q1", query="shots", intent={"event_type": "Shot"})
    report = evaluator.evaluate([case], ["hybrid"])
    assert [result.mode for result in report.results] == ["hybrid"]
