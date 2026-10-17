from typing import Any

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    query: str
    category: str = "structured"
    intent: dict[str, Any] = Field(default_factory=dict)
    expected_empty: bool = False
    gold_limit: int = 50
    rank_field: str | None = None
    rank_order: str = "desc"
    notes: str = ""
