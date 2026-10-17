from typing import Any


class FakeHttpResponse:
    def __init__(self, payload: dict[str, Any], status: int = 200) -> None:
        self._payload: dict[str, Any] = payload
        self._status: int = status

    def raise_for_status(self) -> None:
        if self._status >= 400:
            raise RuntimeError(f"HTTP {self._status}")

    def json(self) -> dict[str, Any]:
        return self._payload
