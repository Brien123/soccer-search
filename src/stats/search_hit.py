from pydantic import BaseModel


class SearchHit(BaseModel):
    event_id: str | None = None
    match_id: str | None = None
    team: str | None = None
    player: str | None = None
    minute: int = 0
    narrative: str = ""
    score: float = 0.0
