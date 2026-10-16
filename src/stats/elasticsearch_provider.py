from elasticsearch import Elasticsearch

from stats.config import AppConfig


class ElasticsearchProvider:
    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._client: Elasticsearch | None = None

    def get_client(self) -> Elasticsearch:
        if self._client is None:
            self._client = Elasticsearch(self._config.elasticsearch_host)
        return self._client

    def get_index(self) -> str:
        return self._config.index_name
