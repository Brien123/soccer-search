from pydantic import BaseModel

from stats.search_hit import SearchHit


class SearchResponse(BaseModel):
    total: int = 0
    hits: list[SearchHit] = []
    mode: str = "keyword"
