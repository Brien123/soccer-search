import json
from pathlib import Path

from stats.eval_report import EvalReport
from stats.eval_result import EvalResult
from stats.report_writer import ReportWriter


def make_report() -> EvalReport:
    return EvalReport(
        cutoffs=[2, 4],
        modes=["keyword", "hybrid"],
        results=[
            EvalResult(
                case_id="q1",
                category="structured",
                mode="keyword",
                retrieved=4,
                relevant_total=2,
                tp={"2": 1, "4": 2},
                fp={"2": 1, "4": 2},
                fn={"2": 1, "4": 0},
                metrics={
                    "mrr": 1.0,
                    "precision@2": 0.5,
                    "recall@2": 0.5,
                    "f1@2": 0.5,
                    "ndcg@2": 0.613,
                    "precision@4": 0.5,
                    "recall@4": 1.0,
                    "f1@4": 0.667,
                    "ndcg@4": 0.7,
                },
            ),
            EvalResult(
                case_id="q1",
                category="structured",
                mode="hybrid",
                retrieved=4,
                relevant_total=2,
                tp={"2": 2, "4": 2},
                fp={"2": 0, "4": 2},
                fn={"2": 0, "4": 0},
                metrics={
                    "mrr": 1.0,
                    "precision@2": 1.0,
                    "recall@2": 1.0,
                    "f1@2": 1.0,
                    "ndcg@2": 1.0,
                    "precision@4": 0.5,
                    "recall@4": 1.0,
                    "f1@4": 0.667,
                    "ndcg@4": 0.7,
                },
            ),
            EvalResult(
                case_id="n1",
                category="negative",
                mode="keyword",
                expected_empty=True,
                retrieved=3,
            ),
            EvalResult(
                case_id="n1",
                category="negative",
                mode="hybrid",
                expected_empty=True,
                retrieved=0,
            ),
        ],
    )


def test_macro_and_micro() -> None:
    report = make_report()
    assert report.macro("f1@2", "keyword") == 0.5
    assert report.macro("f1@2", "hybrid") == 1.0
    assert report.micro(2, "keyword")["precision"] == 0.5
    assert report.micro(2, "hybrid")["precision"] == 1.0


def test_negatives_summary() -> None:
    report = make_report()
    assert report.negatives("keyword")["false_positive_rate"] == 1.0
    assert report.negatives("hybrid")["false_positive_rate"] == 0.0


def test_markdown_contains_tables() -> None:
    markdown = ReportWriter(make_report()).to_markdown()
    assert "# Search Evaluation Report" in markdown
    assert "## Overall (macro over queries)" in markdown
    assert "## Overall (micro, pooled counts)" in markdown
    assert "## Negative queries (expected empty)" in markdown
    assert "| keyword |" in markdown


def test_write_emits_files(tmp_path: Path) -> None:
    writer = ReportWriter(make_report())
    md_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    writer.write(md_path, json_path)
    assert md_path.read_text(encoding="utf-8").startswith("# Search Evaluation")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["cutoffs"] == [2, 4]
    assert data["overall"]["keyword"]["micro"]["2"]["precision"] == 0.5
