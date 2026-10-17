import math


class MetricCalculator:
    def counts(
        self, flags: list[bool], relevant_total: int, k: int
    ) -> tuple[int, int, int]:
        top: list[bool] = flags[:k]
        tp: int = sum(1 for flag in top if flag)
        fp: int = len(top) - tp
        fn: int = max(relevant_total - tp, 0)
        return tp, fp, fn

    def precision(self, flags: list[bool], k: int) -> float:
        top: list[bool] = flags[:k]
        if not top:
            return 0.0
        tp: int = sum(1 for flag in top if flag)
        return tp / len(top)

    def recall(self, flags: list[bool], relevant_total: int, k: int) -> float:
        if relevant_total <= 0:
            return 0.0
        tp: int = sum(1 for flag in flags[:k] if flag)
        return tp / relevant_total

    def f1(self, precision: float, recall: float) -> float:
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    def reciprocal_rank(self, flags: list[bool]) -> float:
        for index, flag in enumerate(flags, start=1):
            if flag:
                return 1.0 / index
        return 0.0

    def ndcg(self, flags: list[bool], relevant_total: int, k: int) -> float:
        dcg: float = sum(
            1.0 / math.log2(index + 1)
            for index, flag in enumerate(flags[:k], start=1)
            if flag
        )
        ideal: int = min(relevant_total, k)
        idcg: float = sum(1.0 / math.log2(index + 1) for index in range(1, ideal + 1))
        if idcg == 0:
            return 0.0
        return dcg / idcg
