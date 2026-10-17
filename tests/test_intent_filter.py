from stats.intent_filter import IntentFilter


def test_term_field_clause() -> None:
    clauses = IntentFilter({"event_type": "Shot"}).to_clauses()
    assert {"term": {"event_type": "Shot"}} in clauses


def test_boolean_field_coerced() -> None:
    clauses = IntentFilter({"is_goal": True}).to_clauses()
    assert {"term": {"is_goal": True}} in clauses


def test_range_fields() -> None:
    clauses = IntentFilter({"minute_from": 85}).to_clauses()
    assert {"range": {"minute": {"gte": 85}}} in clauses


def test_xg_range_field() -> None:
    clauses = IntentFilter({"xg_min": 0.3}).to_clauses()
    assert {"range": {"xg": {"gte": 0.3}}} in clauses


def test_unknown_key_is_ignored() -> None:
    clauses = IntentFilter({"unknown": "x"}).to_clauses()
    assert clauses == []


def test_multiple_fields_produce_multiple_clauses() -> None:
    clauses = IntentFilter(
        {"event_type": "Pass", "is_key_pass": True, "minute_from": 10}
    ).to_clauses()
    assert len(clauses) == 3
