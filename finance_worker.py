"""
finance_worker.py (Compatibility Proxy — Phase 6)

This file is the backward-compatible entry point for the Finance Worker.

It exposes:
  ✓  run_finance_assignment(product_info)  →  (result_text, report_path)
  ✓  python finance_worker.py              →  interactive CLI
"""

from pathlib import Path

from workers.finance_worker import FinanceWorker
from core.worker_report import ReportStatus


REPORTS_FOLDER = Path("finance_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def run_finance_assignment(product_info: str) -> tuple:
    """
    Run a full finance assignment and return (result_text, report_path).
    """
    worker = FinanceWorker()
    report = worker.run_lifecycle(product_info)

    if report.status in (ReportStatus.SUCCESS, ReportStatus.PARTIAL):
        result_text, report_path = report.result
        return result_text, report_path

    raise RuntimeError(
        f"Finance Worker failed: {report.error}"
    )


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Project Genesis — Finance AI")
    print()

    product_info = input(
        "Enter product info or business model to analyse: "
    ).strip()

    if not product_info:
        print("No product info entered.")
        return

    try:
        print()
        print("Finance AI is working...")

        result, report_path = run_finance_assignment(product_info)

        print()
        print("Finance AI Report:")
        print(result)

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Financial analysis completed.")
        print(f"Report saved automatically: {report_path}")
        print("No manual copying is required.")

    except Exception as error:
        print()
        print("Finance AI could not complete the assignment.")
        print("Error:", error)


if __name__ == "__main__":
    main()
