import json
from pathlib import Path
from typing import Any

from stats.eval_report import EvalReport


class ReportWriter:
    def __init__(self, report: EvalReport) -> None:
        self._report: EvalReport = report

    def to_markdown(self) -> str:
        data: dict[str, Any] = self._report.to_dict()
        cutoffs: list[int] = data["cutoffs"]
        lines: list[str] = ["# Search Evaluation Report", ""]
        lines.extend(self._overall_macro(cutoffs, data))
        lines.extend(self._overall_micro(cutoffs, data))
        lines.extend(self._by_category(cutoffs, data))
        lines.extend(self._negatives(data))
        return "\n".join(lines) + "\n"

    def _metric_header(self, cutoffs: list[int]) -> list[str]:
        header: list[str] = ["mode", "cases"]
        for cutoff in cutoffs:
            header.extend(
                [f"P@{cutoff}", f"R@{cutoff}", f"F1@{cutoff}", f"nDCG@{cutoff}"]
            )
        header.append("MRR")
        return header

    def _macro_row(self, mode: str, entry: dict[str, Any], cutoffs: list[int]) -> str:
        macro: dict[str, float] = entry["macro"]
        row: list[str] = [mode, str(entry["cases"])]
        for cutoff in cutoffs:
            row.extend(
                [
                    f"{macro[f'precision@{cutoff}']:.3f}",
                    f"{macro[f'recall@{cutoff}']:.3f}",
                    f"{macro[f'f1@{cutoff}']:.3f}",
                    f"{macro[f'ndcg@{cutoff}']:.3f}",
                ]
            )
        row.append(f"{macro['mrr']:.3f}")
        return "| " + " | ".join(row) + " |"

    def _overall_macro(self, cutoffs: list[int], data: dict[str, Any]) -> list[str]:
        header: list[str] = self._metric_header(cutoffs)
        lines: list[str] = ["## Overall (macro over queries)", ""]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for mode in data["modes"]:
            lines.append(self._macro_row(mode, data["overall"][mode], cutoffs))
        lines.append("")
        return lines

    def _overall_micro(self, cutoffs: list[int], data: dict[str, Any]) -> list[str]:
        header: list[str] = ["mode", "cases"]
        for cutoff in cutoffs:
            header.extend([f"P@{cutoff}", f"R@{cutoff}", f"F1@{cutoff}"])
        lines: list[str] = ["## Overall (micro, pooled counts)", ""]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for mode in data["modes"]:
            entry: dict[str, Any] = data["overall"][mode]
            row: list[str] = [mode, str(entry["cases"])]
            for cutoff in cutoffs:
                micro: dict[str, float] = entry["micro"][str(cutoff)]
                row.extend(
                    [
                        f"{micro['precision']:.3f}",
                        f"{micro['recall']:.3f}",
                        f"{micro['f1']:.3f}",
                    ]
                )
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        return lines

    def _by_category(self, cutoffs: list[int], data: dict[str, Any]) -> list[str]:
        primary: int = cutoffs[0]
        header: list[str] = ["category", "mode", "cases", "P", "R", "F1"]
        lines: list[str] = [f"## By category (at k={primary})", ""]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for category, modes in data["by_category"].items():
            for mode, entry in modes.items():
                micro: dict[str, float] = entry["micro"][str(primary)]
                row: list[str] = [
                    category,
                    mode,
                    str(entry["cases"]),
                    f"{micro['precision']:.3f}",
                    f"{micro['recall']:.3f}",
                    f"{micro['f1']:.3f}",
                ]
                lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        return lines

    def _negatives(self, data: dict[str, Any]) -> list[str]:
        header: list[str] = ["mode", "cases", "returned_any", "false_positive_rate"]
        lines: list[str] = ["## Negative queries (expected empty)", ""]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for mode, entry in data["negatives"].items():
            row: list[str] = [
                mode,
                str(int(entry["cases"])),
                str(int(entry["returned_any"])),
                f"{entry['false_positive_rate']:.3f}",
            ]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        return lines

    def write(self, md_path: Path, json_path: Path) -> None:
        md_path.write_text(self.to_markdown(), encoding="utf-8")
        json_path.write_text(
            json.dumps(self._report.to_dict(), indent=2), encoding="utf-8"
        )
