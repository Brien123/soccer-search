from typing import Any


class FakeElasticsearchClient:
    def __init__(
        self,
        hits: list[dict[str, Any]] | None = None,
        total: int | None = None,
        count: int = 0,
        version_number: str = "8.15.0",
    ) -> None:
        self._hits: list[dict[str, Any]] = hits or []
        self._total: int = total if total is not None else len(self._hits)
        self._count: int = count
        self._version_number: str = version_number
        self.last_body: dict[str, Any] = {}
        self.last_index: str = ""

    def search(self, index: str, body: dict[str, Any]) -> dict[str, Any]:
        self.last_index = index
        self.last_body = body
        return {
            "hits": {
                "total": {"value": self._total, "relation": "eq"},
                "hits": self._hits,
            }
        }

    def count(self, index: str) -> dict[str, Any]:
        return {"count": self._count}

    def info(self) -> dict[str, Any]:
        return {"version": {"number": self._version_number}}
