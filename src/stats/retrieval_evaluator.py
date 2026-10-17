from stats.embedding_provider import EmbeddingProvider
from stats.eval_case import EvalCase
from stats.eval_report import EvalReport
from stats.eval_result import EvalResult
from stats.gold_set_builder import GoldSetBuilder
from stats.metric_calculator import MetricCalculator
from stats.search_query import SearchQuery
from stats.search_response import SearchResponse
from stats.search_service import SearchService
from stats.set_relevance_judge import SetRelevanceJudge

ORACLE_MODE: str = "oracle"


class RetrievalEvaluator:
    def __init__(
        self,
        search_service: SearchService,
        embeddings: EmbeddingProvider,
        gold_builder: GoldSetBuilder,
        metrics: MetricCalculator,
        cutoffs: list[int],
    ) -> None:
        self._search: SearchService = search_service
        self._embeddings: EmbeddingProvider = embeddings
        self._gold: GoldSetBuilder = gold_builder
        self._metrics: MetricCalculator = metrics
        self._cutoffs: list[int] = cutoffs

    def evaluate(
        self,
        cases: list[EvalCase],
        modes: list[str],
        labels: dict[str, set[str]] | None = None,
    ) -> EvalReport:
        known_labels: dict[str, set[str]] = labels or {}
        size: int = max(self._cutoffs)
        results: list[EvalResult] = []
        for case in cases:
            relevant: set[str] | None = self._relevant_ids(case, known_labels)
            if relevant is None:
                continue
            judge = SetRelevanceJudge(relevant)
            for mode in modes:
                ids: list[str] = self._retrieve(mode, case, relevant, size)
                flags: list[bool] = [judge.is_relevant(event_id) for event_id in ids]
                results.append(self._score(case, mode, ids, flags, len(relevant)))
        return EvalReport(results=results, cutoffs=self._cutoffs, modes=list(modes))

    def _relevant_ids(
        self, case: EvalCase, labels: dict[str, set[str]]
    ) -> set[str] | None:
        if case.expected_empty:
            return set()
        if case.id in labels:
            return set(labels[case.id])
        if case.intent:
            return self._gold.build(case)
        return None

    def _retrieve(
        self, mode: str, case: EvalCase, relevant: set[str], size: int
    ) -> list[str]:
        if mode == ORACLE_MODE:
            return sorted(relevant)[:size]
        query = SearchQuery(q=case.query, size=size)
        response: SearchResponse
        if mode == "hybrid":
            vector: list[float] = self._embeddings.encode_query(case.query)
            response = self._search.search_hybrid(query, vector)
        else:
            response = self._search.search(query)
        return [hit.event_id for hit in response.hits if hit.event_id is not None]

    def _score(
        self,
        case: EvalCase,
        mode: str,
        ids: list[str],
        flags: list[bool],
        relevant_total: int,
    ) -> EvalResult:
        tp: dict[str, int] = {}
        fp: dict[str, int] = {}
        fn: dict[str, int] = {}
        metrics: dict[str, float] = {"mrr": self._metrics.reciprocal_rank(flags)}
        for cutoff in self._cutoffs:
            true_pos, false_pos, false_neg = self._metrics.counts(
                flags, relevant_total, cutoff
            )
            precision: float = self._metrics.precision(flags, cutoff)
            recall: float = self._metrics.recall(flags, relevant_total, cutoff)
            tp[str(cutoff)] = true_pos
            fp[str(cutoff)] = false_pos
            fn[str(cutoff)] = false_neg
            metrics[f"precision@{cutoff}"] = precision
            metrics[f"recall@{cutoff}"] = recall
            metrics[f"f1@{cutoff}"] = self._metrics.f1(precision, recall)
            metrics[f"ndcg@{cutoff}"] = self._metrics.ndcg(
                flags, relevant_total, cutoff
            )
        return EvalResult(
            case_id=case.id,
            query=case.query,
            category=case.category,
            mode=mode,
            expected_empty=case.expected_empty,
            retrieved=len(ids),
            relevant_total=relevant_total,
            tp=tp,
            fp=fp,
            fn=fn,
            metrics=metrics,
        )
