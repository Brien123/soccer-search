from typing import Any

from stats.elasticsearch_provider import ElasticsearchProvider
from stats.eval_case import EvalCase
from stats.intent_filter import IntentFilter


class GoldSetBuilder:
    def __init__(self, provider: ElasticsearchProvider) -> None:
        self._provider: ElasticsearchProvider = provider

    def build(self, case: EvalCase) -> set[str]:
        if case.expected_empty:
            return set()
        clauses: list[dict[str, Any]] = IntentFilter(case.intent).to_clauses()
        body: dict[str, Any] = {
            "size": case.gold_limit,
            "_source": ["event_id"],
            "query": {"bool": {"filter": clauses}},
        }
        if case.rank_field:
            body["sort"] = [{case.rank_field: {"order": case.rank_order}}]
        raw: dict[str, Any] = self._provider.get_client().search(
            index=self._provider.get_index(), body=body
        )
        hits: list[dict[str, Any]] = raw.get("hits", {}).get("hits", [])
        return {
            str(hit.get("_source", {}).get("event_id"))
            for hit in hits
            if hit.get("_source", {}).get("event_id")
        }
