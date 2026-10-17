import pytest

from stats.config import AppConfig
from stats.embedding_provider import EmbeddingProvider
from tests.fakes.fake_sentence_model import FakeSentenceModel


def test_encode_query_prefixes_text(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = EmbeddingProvider(config)
    model = FakeSentenceModel()
    monkeypatch.setattr(provider, "_load_model", lambda: model)
    vector = provider.encode_query("late goals")
    assert vector == [0.1, 0.2, 0.3]
    assert model.seen_texts == ["title: none | text: late goals"]
    assert model.seen_normalize is True


def test_encode_query_returns_list(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = EmbeddingProvider(config)
    monkeypatch.setattr(provider, "_load_model", lambda: FakeSentenceModel())
    assert isinstance(provider.encode_query("shot"), list)
