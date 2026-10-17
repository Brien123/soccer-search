from typing import Any

BOOLEAN_FIELDS: frozenset[str] = frozenset(
    {
        "is_goal",
        "is_key_pass",
        "is_goal_assist",
        "is_through_ball",
        "is_cross",
        "under_pressure",
    }
)
TERM_FIELDS: frozenset[str] = frozenset(
    {"event_type", "team", "player", "match_id", "outcome"}
)
RANGE_FIELDS: dict[str, tuple[str, str]] = {
    "minute_from": ("minute", "gte"),
    "minute_to": ("minute", "lte"),
    "xg_min": ("xg", "gte"),
    "xg_max": ("xg", "lte"),
    "location_x_min": ("location_x", "gte"),
    "location_x_max": ("location_x", "lte"),
    "location_y_min": ("location_y", "gte"),
    "location_y_max": ("location_y", "lte"),
}


class IntentFilter:
    def __init__(self, intent: dict[str, Any]) -> None:
        self._intent: dict[str, Any] = intent

    def to_clauses(self) -> list[dict[str, Any]]:
        clauses: list[dict[str, Any]] = []
        for key, value in self._intent.items():
            clause: dict[str, Any] | None = self._to_clause(key, value)
            if clause is not None:
                clauses.append(clause)
        return clauses

    def _to_clause(self, key: str, value: Any) -> dict[str, Any] | None:
        if key in TERM_FIELDS:
            return {"term": {key: value}}
        if key in BOOLEAN_FIELDS:
            return {"term": {key: bool(value)}}
        if key in RANGE_FIELDS:
            field, operator = RANGE_FIELDS[key]
            return {"range": {field: {operator: value}}}
        return None
