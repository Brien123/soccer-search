from typing import Any

from stats.config import AppConfig


class EmbeddingProvider:
    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._model: Any | None = None

    def is_enabled(self) -> bool:
        return self._config.rag_enabled

    def encode_query(self, text: str) -> list[float]:
        if not self._config.rag_enabled:
            raise RuntimeError("RAG is disabled. Enable it to use vector search.")
        model: Any = self._load_model()
        prefixed: str = f"title: none | text: {text}"
        vector: Any = model.encode(prefixed, normalize_embeddings=True)
        return list(vector.tolist())

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._config.embedding_model)
        return self._model
