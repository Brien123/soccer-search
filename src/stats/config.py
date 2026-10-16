from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )

    elasticsearch_host: str = "http://localhost:9200"
    index_name: str = "statsbomb_events"
    default_size: int = 10
    max_size: int = 50
    rag_enabled: bool = False
    embedding_model: str = "google/embeddinggemma-2"
