from pathlib import Path

from stats.labels_loader import LabelsLoader
from stats.query_loader import QueryLoader


def test_query_loader_reads_cases(tmp_path: Path) -> None:
    path = tmp_path / "queries.jsonl"
    path.write_text(
        '{"id": "q1", "query": "late goals", "intent": {"event_type": "Shot"}}\n'
        '{"id": "q2", "query": "blocks", "category": "semantic"}\n',
        encoding="utf-8",
    )
    cases = QueryLoader(path).load()
    assert [case.id for case in cases] == ["q1", "q2"]
    assert cases[0].intent == {"event_type": "Shot"}
    assert cases[1].category == "semantic"


def test_query_loader_missing_file_returns_empty(tmp_path: Path) -> None:
    assert QueryLoader(tmp_path / "nope.jsonl").load() == []


def test_labels_loader_reads_ids(tmp_path: Path) -> None:
    path = tmp_path / "labels.jsonl"
    path.write_text('{"case_id": "u1", "relevant": ["e1", "e2"]}\n', encoding="utf-8")
    labels = LabelsLoader(path).load()
    assert labels == {"u1": {"e1", "e2"}}


def test_labels_loader_missing_file_returns_empty(tmp_path: Path) -> None:
    assert LabelsLoader(tmp_path / "nope.jsonl").load() == {}
