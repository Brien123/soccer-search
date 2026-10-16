from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    q: str = Field(default="", min_length=0, max_length=500)
    team: str | None = Field(default=None, max_length=100)
    player: str | None = Field(default=None, max_length=100)
    match_id: str | None = Field(default=None, max_length=50)
    minute_from: int | None = Field(default=None, ge=0, le=200)
    minute_to: int | None = Field(default=None, ge=0, le=200)
    size: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0, le=10000)
    mode: str = Field(default="keyword", max_length=20)
