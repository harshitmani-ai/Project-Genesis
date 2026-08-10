"""
core/report_manager.py

ReportManager — local zero-LLM engine for opening, reading, and listing report
files directly from disk in Project Genesis.

Features:
  - Searches all report directories (research_reports, acquisition_reports,
    marketing_reports, finance_reports, orchestration_reports,
    product_evaluations, market_reports).
  - Supports exact filename matching, numeric ID resolution (e.g., '34' -> '*_034.md'),
    and 'latest report' lookup.
  - Multi-match disambiguation prompt when multiple reports match a numeric ID.
  - 100% local operation with ZERO Gemini/LLM calls and ZERO worker execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


class ReportManager:
    """
    Local Report Manager for reading report files directly from disk.
    Zero Gemini calls, zero worker execution, zero file generation.
    """

    def __init__(self, project_root: str | Path = "."):
        self.project_root = Path(project_root)
        self.report_dirs = [
            self.project_root / "research_reports",
            self.project_root / "acquisition_reports",
            self.project_root / "marketing_reports",
            self.project_root / "finance_reports",
            self.project_root / "orchestration_reports",
            self.project_root / "product_evaluations",
            self.project_root / "market_reports",
        ]

    def list_all_reports(self) -> List[Path]:
        """Return a list of all report Markdown files sorted by modification time (newest first)."""
        reports: List[Path] = []
        for r_dir in self.report_dirs:
            if r_dir.exists() and r_dir.is_dir():
                reports.extend(r_dir.glob("*.md"))

        # Sort by mtime descending (newest first)
        reports.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        return reports

    def get_latest_report(self) -> Path | None:
        """Return the newest report file across all report directories."""
        reports = self.list_all_reports()
        return reports[0] if reports else None

    def find_matching_reports(self, identifier: str) -> List[Path]:
        """
        Locate all report files matching an identifier.
        Identifier can be:
          - 'latest' -> returns latest report
          - Exact filename stem or path (e.g., 'research_report_034', 'research_report_034.md')
          - Numeric ID (e.g., '34' or '034' -> matches '*_034.md' or '*_34.md')
        """
        raw_id = identifier.strip().lower()
        if not raw_id:
            return []

        if raw_id == "latest":
            latest = self.get_latest_report()
            return [latest] if latest else []

        all_reports = self.list_all_reports()
        matches: List[Path] = []

        # 1. Check exact filename match
        for r in all_reports:
            if r.name.lower() == raw_id or r.stem.lower() == raw_id:
                matches.append(r)
        if matches:
            return matches

        # 2. Check numeric ID match (e.g., '34', '034')
        clean_num = raw_id.lstrip("0")
        if not clean_num:
            clean_num = "0"

        if clean_num.isdigit():
            padded_3 = f"{int(clean_num):03d}"
            padded_2 = f"{int(clean_num):02d}"

            for r in all_reports:
                stem = r.stem.lower()
                if (
                    f"_{padded_3}" in stem
                    or f"_{clean_num}" in stem
                    or f"_{padded_2}" in stem
                    or stem.endswith(padded_3)
                    or stem.endswith(clean_num)
                ):
                    if r not in matches:
                        matches.append(r)
            if matches:
                return matches

        # 3. Substring matching fallback
        for r in all_reports:
            if raw_id in r.name.lower():
                matches.append(r)

        return matches

    def open_report(self, identifier: str, choice_index: int | None = None) -> str:
        """
        Open and return the contents of a report file with zero LLM calls.
        If multiple reports match a numeric ID and choice_index is None,
        returns a selection prompt listing all matching choices.
        """
        raw_id = identifier.strip()

        # Handle 'latest report' case directly
        if raw_id.lower() in {"latest", "latest report", "newest", "newest report"}:
            raw_id = "latest"

        matches = self.find_matching_reports(raw_id)

        if not matches:
            recent = [r.name for r in self.list_all_reports()[:10]]
            return (
                f"Error: Report '{raw_id}' not found.\n"
                f"Available recent reports:\n"
                + "\n".join(f"  - {name}" for name in recent)
            )

        selected_file: Path | None = None

        if len(matches) == 1:
            selected_file = matches[0]
        elif choice_index is not None and 1 <= choice_index <= len(matches):
            selected_file = matches[choice_index - 1]
        else:
            # Multiple matches found — prompt founder to select
            out = [
                f"Multiple reports match '{raw_id}'. Please select a report:\n"
            ]
            for idx, m in enumerate(matches, 1):
                out.append(f"  [{idx}] {m.parent.name}/{m.name}")
            out.append(
                f"\nType 'show report {raw_id} <number>' (e.g. 'show report {raw_id} 1') to select."
            )
            return "\n".join(out)

        if not selected_file.exists():
            return f"Error: File '{selected_file}' does not exist on disk."

        try:
            content = selected_file.read_text(encoding="utf-8")
        except Exception as err:
            return f"Error reading report '{selected_file.name}': {err}"

        header = [
            "═" * 80,
            f"  REPORT FILE: {selected_file.name}",
            f"  Path: {selected_file}",
            f"  Category: {selected_file.parent.name}",
            "═" * 80,
            "",
        ]

        return "\n".join(header) + content
