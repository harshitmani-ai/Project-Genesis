"""
acquisition_worker.py (Compatibility Proxy — Phase 4)

This file is the backward-compatible entry point for the Acquisition Worker.

It exposes:
  ✓  run_acquisition_assignment(icp)  →  (result_text, report_path)
  ✓  python acquisition_worker.py     →  interactive CLI
"""

from datetime import datetime
from pathlib import Path

from brain import ask_ai
from memory import load_company_context
from workers.acquisition_worker import AcquisitionWorker
from core.worker_report import ReportStatus

REPORTS_FOLDER = Path("acquisition_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def run_acquisition_assignment(target_icp: str) -> tuple:
    """
    Run a full acquisition assignment and return (result_text, report_path).
    """
    worker = AcquisitionWorker()
    report = worker.run_lifecycle(target_icp)

    if report.status in (ReportStatus.SUCCESS, ReportStatus.PARTIAL):
        result_text, report_path = report.result
        return result_text, report_path

    raise RuntimeError(
        f"Acquisition Worker failed: {report.error}"
    )


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Project Genesis — Acquisition AI")
    print()

    icp = input(
        "Enter an Ideal Customer Profile (ICP): "
    ).strip()

    if not icp:
        print("No ICP entered.")
        return

    try:
        print()
        print("Acquisition AI is working...")

        result, report_path = run_acquisition_assignment(icp)

        print()
        print("Acquisition AI Report:")
        print(result)

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Acquisition strategy completed.")
        print(f"Report saved automatically: {report_path}")
        print("No manual copying is required.")

    except Exception as error:
        print()
        print("Acquisition AI could not complete the assignment.")
        print("Error:", error)


if __name__ == "__main__":
    main()
