from typing import Any

from stats.config import AppConfig
from tests.fakes.fake_elasticsearch_client import FakeElasticsearchClient


class FakeElasticsearchProvider:
    def __init__(self, config: AppConfig, client: FakeElasticsearchClient) -> None:
        self._config: AppConfig = config
        self._client: FakeElasticsearchClient = client

    def get_client(self) -> Any:
        return self._client

    def get_index(self) -> str:
        return self._config.index_name
