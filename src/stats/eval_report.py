from typing import Any

from pydantic import BaseModel, Field

from stats.eval_result import EvalResult


class EvalReport(BaseModel):
    results: list[EvalResult] = Field(default_factory=list)
    cutoffs: list[int] = Field(default_factory=list)
    modes: list[str] = Field(default_factory=list)

    def metric_names(self) -> list[str]:
        names: list[str] = ["mrr"]
        for cutoff in self.cutoffs:
            names.extend(
                [
                    f"precision@{cutoff}",
                    f"recall@{cutoff}",
                    f"f1@{cutoff}",
                    f"ndcg@{cutoff}",
                ]
            )
        return names

    def categories(self) -> list[str]:
        seen: list[str] = []
        for result in self.results:
            if not result.expected_empty and result.category not in seen:
                seen.append(result.category)
        return seen

    def positive(self, mode: str, category: str | None = None) -> list[EvalResult]:
        return [
            result
            for result in self.results
            if result.mode == mode
            and not result.expected_empty
            and (category is None or result.category == category)
        ]

    def negative(self, mode: str) -> list[EvalResult]:
        return [
            result
            for result in self.results
            if result.mode == mode and result.expected_empty
        ]

    def macro(self, metric: str, mode: str, category: str | None = None) -> float:
        values: list[float] = [
            result.metrics[metric]
            for result in self.positive(mode, category)
            if metric in result.metrics
        ]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def micro(
        self, cutoff: int, mode: str, category: str | None = None
    ) -> dict[str, float]:
        results: list[EvalResult] = self.positive(mode, category)
        key: str = str(cutoff)
        tp: int = sum(result.tp.get(key, 0) for result in results)
        fp: int = sum(result.fp.get(key, 0) for result in results)
        fn: int = sum(result.fn.get(key, 0) for result in results)
        precision: float = tp / (tp + fp) if (tp + fp) else 0.0
        recall: float = tp / (tp + fn) if (tp + fn) else 0.0
        f1: float = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        return {"precision": precision, "recall": recall, "f1": f1}

    def negatives(self, mode: str) -> dict[str, float]:
        results: list[EvalResult] = self.negative(mode)
        if not results:
            return {"cases": 0.0, "returned_any": 0.0, "false_positive_rate": 0.0}
        returned_any: int = sum(1 for result in results if result.retrieved > 0)
        return {
            "cases": float(len(results)),
            "returned_any": float(returned_any),
            "false_positive_rate": returned_any / len(results),
        }

    def to_dict(self) -> dict[str, Any]:
        overall: dict[str, Any] = {}
        for mode in self.modes:
            overall[mode] = {
                "cases": len(self.positive(mode)),
                "macro": {name: self.macro(name, mode) for name in self.metric_names()},
                "micro": {
                    str(cutoff): self.micro(cutoff, mode) for cutoff in self.cutoffs
                },
            }
        by_category: dict[str, Any] = {}
        for category in self.categories():
            by_category[category] = {}
            for mode in self.modes:
                by_category[category][mode] = {
                    "cases": len(self.positive(mode, category)),
                    "macro": {
                        name: self.macro(name, mode, category)
                        for name in self.metric_names()
                    },
                    "micro": {
                        str(cutoff): self.micro(cutoff, mode, category)
                        for cutoff in self.cutoffs
                    },
                }
        return {
            "cutoffs": self.cutoffs,
            "modes": self.modes,
            "overall": overall,
            "by_category": by_category,
            "negatives": {mode: self.negatives(mode) for mode in self.modes},
            "cases": [result.model_dump(mode="json") for result in self.results],
        }
