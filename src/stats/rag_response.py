from pydantic import BaseModel

from stats.search_hit import SearchHit


class RagResponse(BaseModel):
    question: str = ""
    answer: str = ""
    model: str = ""
    citations: list[SearchHit] = []
