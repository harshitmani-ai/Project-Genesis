"""
marketing_worker.py (Compatibility Proxy — Phase 5)

This file is the backward-compatible entry point for the Marketing Worker.

It exposes:
  ✓  run_marketing_assignment(product_info)  →  (result_text, report_path)
  ✓  python marketing_worker.py             →  interactive CLI
"""

from datetime import datetime
from pathlib import Path

from brain import ask_ai
from memory import load_company_context
from workers.marketing_worker import MarketingWorker
from core.worker_report import ReportStatus

REPORTS_FOLDER = Path("marketing_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def run_marketing_assignment(product_info: str) -> tuple:
    """
    Run a full marketing assignment and return (result_text, report_path).
    """
    worker = MarketingWorker()
    report = worker.run_lifecycle(product_info)

    if report.status in (ReportStatus.SUCCESS, ReportStatus.PARTIAL):
        result_text, report_path = report.result
        return result_text, report_path

    raise RuntimeError(
        f"Marketing Worker failed: {report.error}"
    )


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Project Genesis — Marketing AI")
    print()

    product_info = input(
        "Enter product info or target customer: "
    ).strip()

    if not product_info:
        print("No product info entered.")
        return

    try:
        print()
        print("Marketing AI is working...")

        result, report_path = run_marketing_assignment(product_info)

        print()
        print("Marketing AI Report:")
        print(result)

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Marketing strategy completed.")
        print(f"Report saved automatically: {report_path}")
        print("No manual copying is required.")

    except Exception as error:
        print()
        print("Marketing AI could not complete the assignment.")
        print("Error:", error)


if __name__ == "__main__":
    main()
