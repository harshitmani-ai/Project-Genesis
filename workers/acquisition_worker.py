"""
workers/acquisition_worker.py

AcquisitionWorker — the Customer Acquisition AI worker for Project Genesis.

Subclasses BaseWorker and implements the 5-step lifecycle:
  Goal → Plan → Execute → Verify → Learn

Responsibilities:
  - Accept an Ideal Customer Profile (ICP).
  - Build a structured lead database.
  - Score every lead from 1–10 based on acquisition fit.
  - Generate personalized outreach drafts.
  - Track follow-up sequence strategies.
  - Save structured acquisition reports to acquisition_reports/acquisition_report_NNN.md.
  - Append Acquisition Activity entries to company_memory.md.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from brain import ask_ai
from core import BaseWorker, WorkerIdentity
from memory import load_company_context


REPORTS_FOLDER = Path("acquisition_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def _get_next_report_path() -> Path:
    """Return the next sequential acquisition_report_NNN.md path."""
    REPORTS_FOLDER.mkdir(exist_ok=True)
    existing_reports = list(REPORTS_FOLDER.glob("acquisition_report_*.md"))
    next_number = len(existing_reports) + 1
    return REPORTS_FOLDER / f"acquisition_report_{next_number:03}.md"


def _generate_acquisition_strategy(icp: str) -> str:
    """
    Call the LLM to generate an acquisition strategy and lead database.
    """
    company_context = load_company_context()

    prompt = f"""
You are the Acquisition AI worker for Project Genesis.

{company_context}

Your assignment is to build a customer acquisition plan and structured lead database for this Ideal Customer Profile (ICP):

{icp}

Generate exactly 3 structured lead profile segments / targets.

For every lead segment include:

1. Lead Segment / Target Profile Name
2. Key Decision-Maker Title
3. Primary Pain Point
4. Strategic Value Proposition
5. Acquisition Fit Score out of 10
6. Personalized Outreach Draft (Cold Email / Message)
7. Channel Strategy & Follow-up Sequence (Step 1, Step 2, Step 3)
8. Expected Conversion Barriers

Important rules:
- Do not pretend live internet research was performed if data is simulated.
- Follow the Project Genesis Constitution (Honest value, low acquisition cost, customer obsession).
- Use clear Markdown formatting.
- Include explicit Fit Scores out of 10 for every lead segment.
"""

    return ask_ai(prompt)


def _save_acquisition_report(icp: str, result_text: str) -> Path:
    """
    Write the acquisition report to disk.
    """
    report_path = _get_next_report_path()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    complete_report = f"""# Project Genesis Acquisition Report

**Created:** {current_time}

**Prepared by:** Acquisition AI

**Ideal Customer Profile (ICP):** {icp}

**Status:** Acquisition Strategy & Lead Database Generated

---

## Important Notice

This acquisition report was generated using AI reasoning and existing company context.

Outreach drafts and channel strategies require founder review and validation before launching campaigns.

---

{result_text}

---

## Governance & Action Items

No campaign has been launched automatically.

Final approval for outreach campaigns belongs to Harshit, Founder of Project Genesis.
"""

    report_path.write_text(complete_report, encoding="utf-8")
    return report_path


def _update_company_memory(icp: str, report_path: Path) -> None:
    """
    Append an Acquisition Activity entry to company_memory.md.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    memory_entry = f"""

---

## Acquisition Activity

**Date:** {current_time}

**Target ICP:** {icp}

**Report location:** {report_path}

**Status:** Lead database & campaign generated.

**Founder approval:** Pending
"""

    with COMPANY_MEMORY_FILE.open("a", encoding="utf-8") as memory_file:
        memory_file.write(memory_entry)


class AcquisitionWorker(BaseWorker):
    """
    Acquisition AI worker — implemented within the BaseWorker framework.
    """

    identity = WorkerIdentity(
        name="Acquisition Worker",
        role="Build structured lead database and generate personalized acquisition campaigns.",
        version="1.0.0",
    )

    def create_plan(self, task: Any) -> str:
        """
        Validate the Ideal Customer Profile (ICP) and return it as the plan.
        """
        icp = str(task).strip()
        self.logger.info(
            f"Acquisition plan created — Target ICP: '{icp}'"
        )
        return icp

    def execute(self, task: Any, plan: str) -> tuple[str, Path]:
        """
        Run the LLM acquisition strategy call and save the report to disk.
        """
        self.logger.info(f"Calling LLM for ICP: '{plan}'")
        result_text = _generate_acquisition_strategy(plan)

        self.logger.info("Saving acquisition report to disk…")
        report_path = _save_acquisition_report(plan, result_text)
        self.logger.info(f"Report saved: {report_path}")

        return result_text, report_path

    def verify(self, result: tuple[str, Path]) -> bool:
        """
        Confirm the LLM output contains the required acquisition sections.
        """
        result_text, _ = result
        required_keywords = ["Lead", "Fit", "Outreach"]

        for keyword in required_keywords:
            if keyword not in result_text:
                self.logger.warning(
                    f"Verification failed — missing keyword/section: '{keyword}'"
                )
                return False

        self.logger.info("Verification passed — all required acquisition sections present.")
        return True

    def learn(self, task: Any, result: tuple[str, Path]) -> None:
        """
        Append the Acquisition Activity entry to company_memory.md.
        """
        _, report_path = result
        icp = str(task).strip()

        _update_company_memory(icp, report_path)
        self.logger.info("Company memory updated with Acquisition Activity.")
        return None
