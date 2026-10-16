from stats.config import AppConfig
from stats.embedding_provider import EmbeddingProvider
from stats.llm_provider import LlmProvider
from stats.rag_request import RagRequest
from stats.rag_response import RagResponse
from stats.search_query import SearchQuery
from stats.search_response import SearchResponse
from stats.search_service import SearchService


class RagService:
    def __init__(
        self,
        search: SearchService,
        embeddings: EmbeddingProvider,
        llm: LlmProvider,
        config: AppConfig,
    ) -> None:
        self._search: SearchService = search
        self._embeddings: EmbeddingProvider = embeddings
        self._llm: LlmProvider = llm
        self._config: AppConfig = config

    def ask(self, request: RagRequest) -> RagResponse:
        query: SearchQuery = SearchQuery(
            q=request.question,
            team=request.team,
            player=request.player,
            match_id=request.match_id,
            minute_from=request.minute_from,
            minute_to=request.minute_to,
            size=min(request.size, self._config.max_size),
            offset=0,
            mode="hybrid",
        )
        context: SearchResponse = self._retrieve(query)
        answer: str = self._llm.generate(
            self._system_prompt(), self._user_prompt(request.question, context)
        )
        return RagResponse(
            question=request.question,
            answer=answer,
            model=self._llm.model_name(),
            citations=context.hits,
        )

    def _retrieve(self, query: SearchQuery) -> SearchResponse:
        vector: list[float] = self._embeddings.encode_query(query.q)
        return self._search.search_hybrid(query, vector)

    def _system_prompt(self) -> str:
        return (
            "You are a football analyst. Answer only from the match events given. "
            "Mention minute, player, and team for each fact. "
            "Never invent dates, competitions, opponents, or scores. "
            "If the events do not answer the question, say so plainly."
        )

    def _user_prompt(self, question: str, context: SearchResponse) -> str:
        lines: list[str] = [f"- {hit.narrative}" for hit in context.hits]
        events: str = "\n".join(lines)
        return f"Match events:\n{events}\n\nQuestion: {question}"
