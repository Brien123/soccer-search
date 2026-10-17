import json
from pathlib import Path


class LabelsLoader:
    def __init__(self, path: Path) -> None:
        self._path: Path = path

    def load(self) -> dict[str, set[str]]:
        if not self._path.exists():
            return {}
        labels: dict[str, set[str]] = {}
        for line in self._path.read_text(encoding="utf-8").splitlines():
            stripped: str = line.strip()
            if not stripped:
                continue
            record: dict[str, object] = json.loads(stripped)
            relevant: list[str] = list(record.get("relevant", []))  # type: ignore[arg-type]
            labels[str(record["case_id"])] = set(relevant)
        return labels
