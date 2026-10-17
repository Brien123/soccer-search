from typing import Any

from tests.fakes.fake_http_response import FakeHttpResponse


class FakeHttpClient:
    def __init__(self, response: FakeHttpResponse) -> None:
        self._response: FakeHttpResponse = response
        self.last_url: str = ""
        self.last_json: dict[str, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> "FakeHttpClient":
        return self

    def __enter__(self) -> "FakeHttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def post(self, url: str, json: dict[str, Any]) -> FakeHttpResponse:
        self.last_url = url
        self.last_json = json
        return self._response
