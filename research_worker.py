"""
research_worker.py  (Compatibility Proxy — Phase 2)

This file is the backward-compatible entry point for the Research Worker.

It preserves 100% of the original public interface so that all existing
callers (genesis.py, direct CLI use, and any future imports) continue to
work without any modification:

  ✓  run_research_assignment(audience)  →  (result_text, report_path)
  ✓  python research_worker.py          →  interactive CLI (unchanged)

All actual logic now lives in workers/research_worker.py (ResearchWorker).
This file simply delegates to that class and unpacks the WorkerReport into
the legacy return signature.

Phase 2: Research Worker Migration — genesis.py is NOT modified.

Rollback: Restore this file from backups/research_worker_<timestamp>.backup
          and delete workers/ to fully revert Phase 2.
"""

# ── Imports preserved from the original for any code that does:
#    from research_worker import REPORTS_FOLDER, COMPANY_MEMORY_FILE, etc.
from datetime import datetime
from pathlib import Path

from brain import ask_ai
from memory import load_company_context

# ── Phase 2: delegate to the new worker class ──────────────────────────────
from workers.research_worker import ResearchWorker
from core.worker_report import ReportStatus

# ── Constants (preserved — referenced by genesis.py and other callers) ──────
REPORTS_FOLDER = Path("research_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


# ──────────────────────────────────────────────────────────────────────────────
# Public API  (100% backward-compatible signatures)
# ──────────────────────────────────────────────────────────────────────────────

def run_research_assignment(target_audience: str) -> tuple:
    """
    Run a full research assignment and return (result_text, report_path).

    This function preserves the original return signature exactly.
    Internally it delegates to ResearchWorker.run_lifecycle() so that
    the new BaseWorker lifecycle (logging, verification, learn step) runs
    while the caller receives the same tuple it always has.

    Args:
        target_audience: The audience or industry to research.

    Returns:
        (result_text: str, report_path: Path)  — identical to original.

    Raises:
        RuntimeError: If the worker lifecycle fails (mirrors the original
                      behaviour where an uncaught exception would propagate).
    """
    worker = ResearchWorker()
    report = worker.run_lifecycle(target_audience)

    if report.status in (ReportStatus.SUCCESS, ReportStatus.PARTIAL):
        # report.result is the (text, path) tuple returned by execute()
        result_text, report_path = report.result
        return result_text, report_path

    # Lifecycle failed — raise so callers see the same exception-based
    # error surface as the original code.
    raise RuntimeError(
        f"Research Worker failed: {report.error}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Legacy helper functions
# (Preserved so that any code importing them directly still works)
# ──────────────────────────────────────────────────────────────────────────────

def get_next_report_path() -> Path:
    """Preserved for backward compatibility. Delegates to internal helper."""
    from workers.research_worker import _get_next_report_path
    return _get_next_report_path()


def research_product_ideas(target_audience: str) -> str:
    """Preserved for backward compatibility. Delegates to internal helper."""
    from workers.research_worker import _research_product_ideas
    return _research_product_ideas(target_audience)


def save_research_report(target_audience: str, research_result: str) -> Path:
    """Preserved for backward compatibility. Delegates to internal helper."""
    from workers.research_worker import _save_research_report
    return _save_research_report(target_audience, research_result)


def update_company_memory(target_audience: str, report_path: Path) -> None:
    """Preserved for backward compatibility. Delegates to internal helper."""
    from workers.research_worker import _update_company_memory
    _update_company_memory(target_audience, report_path)


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point  (100% identical behaviour to original)
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Project Genesis — Research AI")
    print()

    audience = input(
        "Enter a target audience or industry: "
    ).strip()

    if not audience:
        print("No target audience entered.")
        return

    try:
        print()
        print("Research AI is working...")

        result, report_path = run_research_assignment(audience)

        print()
        print("Research AI Report:")
        print(result)

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Research completed.")
        print(f"Report saved automatically: {report_path}")
        print("No manual copying is required.")

    except Exception as error:
        print()
        print("Research AI could not complete the assignment.")
        print("Error:", error)


if __name__ == "__main__":
    main()