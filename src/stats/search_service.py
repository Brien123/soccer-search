from typing import Any

from stats.elasticsearch_provider import ElasticsearchProvider
from stats.embedding_provider import EmbeddingProvider
from stats.search_hit import SearchHit
from stats.search_query import SearchQuery
from stats.search_response import SearchResponse


class SearchService:
    def __init__(
        self, provider: ElasticsearchProvider, embeddings: EmbeddingProvider
    ) -> None:
        self._provider: ElasticsearchProvider = provider
        self._embeddings: EmbeddingProvider = embeddings

    def search(
        self, query: SearchQuery, query_vector: list[float] | None = None
    ) -> SearchResponse:
        if query.mode != "keyword":
            raise ValueError("Only keyword search is enabled. RAG modes come later.")
        if query_vector is not None:
            raise ValueError("Vector search is not enabled yet.")
        body: dict[str, Any] = self._build_keyword_body(query)
        raw: dict[str, Any] = self._provider.get_client().search(
            index=self._provider.get_index(), body=body
        )
        return self._to_response(raw, query.mode)

    def health(self) -> dict[str, Any]:
        client: Any = self._provider.get_client()
        info: dict[str, Any] = dict(client.info())
        count: dict[str, Any] = dict(client.count(index=self._provider.get_index()))
        return {
            "elasticsearch": info.get("version", {}),
            "count": count.get("count", 0),
        }

    def _build_keyword_body(self, query: SearchQuery) -> dict[str, Any]:
        must_clauses: list[dict[str, Any]] = []
        filter_clauses: list[dict[str, Any]] = []
        text: str = query.q.strip()
        if text:
            must_clauses.append({"match": {"narrative": {"query": text}}})
        else:
            must_clauses.append({"match_all": {}})
        if query.team:
            filter_clauses.append({"term": {"team": query.team}})
        if query.player:
            filter_clauses.append({"term": {"player": query.player}})
        if query.match_id:
            filter_clauses.append({"term": {"match_id": query.match_id}})
        minute_range: dict[str, Any] = {}
        if query.minute_from is not None:
            minute_range["gte"] = query.minute_from
        if query.minute_to is not None:
            minute_range["lte"] = query.minute_to
        if minute_range:
            filter_clauses.append({"range": {"minute": minute_range}})
        return {
            "size": query.size,
            "from": query.offset,
            "track_total_hits": True,
            "sort": [{"_score": {"order": "desc"}}, {"minute": {"order": "asc"}}],
            "query": {"bool": {"must": must_clauses, "filter": filter_clauses}},
        }

    def _to_response(self, raw: dict[str, Any], mode: str) -> SearchResponse:
        total_value: Any = raw.get("hits", {}).get("total", {}).get("value", 0)
        total: int = int(total_value) if isinstance(total_value, int) else 0
        raw_hits: Any = raw.get("hits", {}).get("hits", [])
        hits: list[SearchHit] = []
        for item in raw_hits:
            source: dict[str, Any] = item.get("_source", {})
            hits.append(
                SearchHit(
                    event_id=source.get("event_id"),
                    match_id=source.get("match_id"),
                    team=source.get("team"),
                    player=source.get("player"),
                    minute=int(source.get("minute", 0)),
                    narrative=str(source.get("narrative", "")),
                    score=float(item.get("_score", 0.0)),
                )
            )
        return SearchResponse(total=total, hits=hits, mode=mode)
