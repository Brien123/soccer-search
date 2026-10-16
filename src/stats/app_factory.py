from pathlib import Path

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from stats.config import AppConfig
from stats.elasticsearch_provider import ElasticsearchProvider
from stats.embedding_provider import EmbeddingProvider
from stats.llm_provider import LlmProvider
from stats.rag_request import RagRequest
from stats.rag_response import RagResponse
from stats.rag_service import RagService
from stats.search_query import SearchQuery
from stats.search_response import SearchResponse
from stats.search_service import SearchService


class AppFactory:
    @staticmethod
    def create_app(config: AppConfig | None = None) -> FastAPI:
        effective_config: AppConfig = config or AppConfig()
        provider: ElasticsearchProvider = ElasticsearchProvider(effective_config)
        embeddings: EmbeddingProvider = EmbeddingProvider(effective_config)
        service: SearchService = SearchService(provider, embeddings)
        llm: LlmProvider = LlmProvider(effective_config)
        rag: RagService = RagService(service, embeddings, llm, effective_config)
        base_dir: Path = Path(__file__).resolve().parent
        templates: Jinja2Templates = Jinja2Templates(
            directory=str(base_dir / "templates")
        )
        app: FastAPI = FastAPI(title="StatsBomb Search")

        def get_service() -> SearchService:
            return service

        def get_config() -> AppConfig:
            return effective_config

        def get_rag() -> RagService:
            return rag

        app.mount(
            "/static",
            StaticFiles(directory=str(base_dir / "static")),
            name="static",
        )

        @app.get("/", response_class=HTMLResponse)
        def index(request: Request) -> HTMLResponse:
            return templates.TemplateResponse(request, "index.html", {})

        @app.get("/api/health")
        def api_health(svc: SearchService = Depends(get_service)) -> dict[str, object]:
            return svc.health()

        @app.get("/api/search")
        def api_search(
            q: str = Query(default=""),
            team: str | None = Query(default=None),
            player: str | None = Query(default=None),
            match_id: str | None = Query(default=None),
            minute_from: int | None = Query(default=None),
            minute_to: int | None = Query(default=None),
            size: int = Query(default=10, ge=1, le=50),
            offset: int = Query(default=0, ge=0),
            svc: SearchService = Depends(get_service),
            cfg: AppConfig = Depends(get_config),
        ) -> SearchResponse:
            clamped_size: int = min(size, cfg.max_size)
            query: SearchQuery = SearchQuery(
                q=q,
                team=team,
                player=player,
                match_id=match_id,
                minute_from=minute_from,
                minute_to=minute_to,
                size=clamped_size,
                offset=offset,
                mode="keyword",
            )
            return svc.search(query)

        @app.post("/api/rag")
        def api_rag(
            request: RagRequest, rag_svc: RagService = Depends(get_rag)
        ) -> RagResponse:
            return rag_svc.ask(request)

        return app
