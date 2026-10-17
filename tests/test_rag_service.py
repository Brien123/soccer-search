from typing import Any

from stats.config import AppConfig
from stats.rag_request import RagRequest
from stats.rag_service import RagService
from stats.search_service import SearchService
from tests.conftest import make_hit
from tests.fakes.fake_elasticsearch_client import FakeElasticsearchClient
from tests.fakes.fake_elasticsearch_provider import FakeElasticsearchProvider
from tests.fakes.fake_embedding_provider import FakeEmbeddingProvider
from tests.fakes.fake_llm_provider import FakeLlmProvider


def _build(
    config: AppConfig, hits: list[dict[str, Any]] | None = None
) -> tuple[RagService, FakeLlmProvider, FakeEmbeddingProvider, FakeElasticsearchClient]:
    client = FakeElasticsearchClient(
        hits=hits
        if hits is not None
        else [make_hit(narrative="Messi scored at 91:43.")],
        total=len(hits) if hits is not None else 1,
    )
    provider = FakeElasticsearchProvider(config, client)
    embeddings = FakeEmbeddingProvider()
    search = SearchService(provider, embeddings)  # type: ignore[arg-type]
    llm = FakeLlmProvider(answer="Messi scored late.")
    rag = RagService(search, embeddings, llm, config)  # type: ignore[arg-type]
    return rag, llm, embeddings, client


def test_ask_returns_answer_and_citations(config: AppConfig) -> None:
    rag, _, _, _ = _build(config)
    response = rag.ask(RagRequest(question="who scored late?", size=10))
    assert response.answer == "Messi scored late."
    assert response.model == "fake/model"
    assert response.question == "who scored late?"
    assert len(response.citations) == 1
    assert response.citations[0].narrative == "Messi scored at 91:43."


def test_ask_embeds_the_question(config: AppConfig) -> None:
    rag, _, embeddings, _ = _build(config)
    rag.ask(RagRequest(question="who scored late?"))
    assert embeddings.encoded_texts == ["who scored late?"]


def test_ask_prompt_contains_events_and_question(config: AppConfig) -> None:
    rag, llm, _, _ = _build(config)
    rag.ask(RagRequest(question="who scored late?"))
    system_prompt, user_prompt = llm.calls[0]
    assert "Answer only from the match events given" in system_prompt
    assert "Messi scored at 91:43." in user_prompt
    assert "Question: who scored late?" in user_prompt


def test_ask_clamps_size_to_max(config: AppConfig) -> None:
    small = config.model_copy(update={"max_size": 3})
    rag, _, _, client = _build(small)
    rag.ask(RagRequest(question="shot", size=10))
    assert client.last_body["size"] == 3


def test_citations_follow_search_order(config: AppConfig) -> None:
    hits = [make_hit(event_id="a"), make_hit(event_id="b")]
    rag, _, _, _ = _build(config, hits=hits)
    response = rag.ask(RagRequest(question="duels"))
    assert [hit.event_id for hit in response.citations] == ["a", "b"]
