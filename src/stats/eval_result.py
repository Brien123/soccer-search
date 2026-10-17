from pydantic import BaseModel, Field


class EvalResult(BaseModel):
    case_id: str
    query: str = ""
    category: str = ""
    mode: str = ""
    expected_empty: bool = False
    retrieved: int = 0
    relevant_total: int = 0
    tp: dict[str, int] = Field(default_factory=dict)
    fp: dict[str, int] = Field(default_factory=dict)
    fn: dict[str, int] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
