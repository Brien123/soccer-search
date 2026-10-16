import os

from elasticsearch import Elasticsearch


class StatsbombIndexBuilder:
    def __init__(self, host: str, index: str) -> None:
        self._host: str = host
        self._index: str = index

    def build_settings(self) -> dict[str, object]:
        return {
            "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
            "mappings": {
                "properties": {
                    "event_id": {"type": "keyword"},
                    "match_id": {"type": "keyword"},
                    "team": {"type": "keyword"},
                    "player": {"type": "keyword"},
                    "event_type": {"type": "keyword"},
                    "outcome": {"type": "keyword"},
                    "minute": {"type": "integer"},
                    "second": {"type": "integer"},
                    "period": {"type": "integer"},
                    "is_goal": {"type": "boolean"},
                    "is_key_pass": {"type": "boolean"},
                    "is_goal_assist": {"type": "boolean"},
                    "is_through_ball": {"type": "boolean"},
                    "is_cross": {"type": "boolean"},
                    "under_pressure": {"type": "boolean"},
                    "xg": {"type": "float"},
                    "location_x": {"type": "float"},
                    "location_y": {"type": "float"},
                    "narrative": {"type": "text", "analyzer": "english"},
                    "narrative_vector": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        }

    def rebuild(self) -> None:
        client: Elasticsearch = Elasticsearch(self._host)
        if client.indices.exists(index=self._index):
            client.indices.delete(index=self._index)
        client.indices.create(index=self._index, **self.build_settings())
        print(
            f"Successfully created Elasticsearch index: "
            f"'{self._index}' with 768 vector dimensions."
        )


def build_from_env() -> StatsbombIndexBuilder:
    host: str = os.environ.get("ELASTICSEARCH_HOST", "http://localhost:9200")
    index: str = os.environ.get("INDEX_NAME", "statsbomb_events")
    return StatsbombIndexBuilder(host=host, index=index)


if __name__ == "__main__":
    build_from_env().rebuild()
