from typing import Any

import pytest

from stats.config import AppConfig
from stats.llm_provider import LlmProvider
from tests.fakes.fake_http_client import FakeHttpClient
from tests.fakes.fake_http_response import FakeHttpResponse


def _install_client(monkeypatch: pytest.MonkeyPatch, client: FakeHttpClient) -> None:
    monkeypatch.setattr("stats.llm_provider.httpx.Client", client)


def test_generate_returns_content(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeHttpResponse(
        {"choices": [{"message": {"content": "Messi scored at 91:43."}}]}
    )
    _install_client(monkeypatch, FakeHttpClient(response))
    provider = LlmProvider(config)
    answer = provider.generate("system", "user")
    assert answer == "Messi scored at 91:43."


def test_generate_strips_think_blocks(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeHttpResponse(
        {"choices": [{"message": {"content": "<think>hidden</think>Visible answer."}}]}
    )
    _install_client(monkeypatch, FakeHttpClient(response))
    provider = LlmProvider(config)
    assert provider.generate("s", "u") == "Visible answer."


def test_generate_raises_on_empty_content(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeHttpResponse(
        {"choices": [{"message": {"content": "<think>only reasoning</think>"}}]}
    )
    _install_client(monkeypatch, FakeHttpClient(response))
    provider = LlmProvider(config)
    with pytest.raises(RuntimeError, match="empty"):
        provider.generate("s", "u")


def test_generate_raises_on_no_choices(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_client(monkeypatch, FakeHttpClient(FakeHttpResponse({"choices": []})))
    provider = LlmProvider(config)
    with pytest.raises(RuntimeError, match="no choices"):
        provider.generate("s", "u")


def test_generate_sends_model_and_url(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeHttpResponse({"choices": [{"message": {"content": "ok"}}]})
    client = FakeHttpClient(response)
    _install_client(monkeypatch, client)
    provider = LlmProvider(config)
    provider.generate("sys", "usr")
    assert client.last_url == "http://test-llm:1234/v1/chat/completions"
    payload: dict[str, Any] = client.last_json
    assert payload["model"] == "test/llm-model"
    assert payload["messages"][0] == {"role": "system", "content": "sys"}
    assert payload["messages"][1] == {"role": "user", "content": "usr"}


def test_model_name_returns_config_value(config: AppConfig) -> None:
    assert LlmProvider(config).model_name() == "test/llm-model"
