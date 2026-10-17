import json
from pathlib import Path

from stats.eval_case import EvalCase


class QueryLoader:
    def __init__(self, path: Path) -> None:
        self._path: Path = path

    def load(self) -> list[EvalCase]:
        if not self._path.exists():
            return []
        cases: list[EvalCase] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            stripped: str = line.strip()
            if not stripped:
                continue
            cases.append(EvalCase(**json.loads(stripped)))
        return cases
