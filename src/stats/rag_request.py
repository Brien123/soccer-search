from pydantic import BaseModel, Field


class RagRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    size: int = Field(default=5, ge=1, le=10)
    team: str | None = Field(default=None, max_length=100)
    player: str | None = Field(default=None, max_length=100)
    match_id: str | None = Field(default=None, max_length=50)
    minute_from: int | None = Field(default=None, ge=0, le=200)
    minute_to: int | None = Field(default=None, ge=0, le=200)
