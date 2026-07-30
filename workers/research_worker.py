"""
workers/research_worker.py

ResearchWorker — the fully-migrated Research AI worker for Project Genesis.

This module subclasses BaseWorker and implements the 5-step lifecycle
(Goal → Plan → Execute → Verify → Learn) while preserving 100% of the
original research_worker.py behaviour:

  ✓ Identical LLM prompt text
  ✓ Identical report Markdown format
  ✓ Identical company_memory.md append format
  ✓ Identical return signature  →  (result_text: str, report_path: Path)

Callers that used the legacy root-level research_worker.py continue to
work unchanged via the backward-compatible proxy in that file.

Phase 2: Research Worker Migration — genesis.py is NOT modified.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from brain import ask_ai
from core import BaseWorker, WorkerIdentity, WorkerReport
from memory import load_company_context


# ──────────────────────────────────────────────────────────────────────────────
# Constants  (identical to original research_worker.py)
# ──────────────────────────────────────────────────────────────────────────────

REPORTS_FOLDER = Path("research_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers  (private — extracted from original, unchanged in behaviour)
# ──────────────────────────────────────────────────────────────────────────────

def _get_next_report_path() -> Path:
    """Return the next sequential research_report_NNN.md path."""
    REPORTS_FOLDER.mkdir(exist_ok=True)
    existing_reports = list(REPORTS_FOLDER.glob("research_report_*.md"))
    next_number = len(existing_reports) + 1
    return REPORTS_FOLDER / f"research_report_{next_number:03}.md"


def _research_product_ideas(target_audience: str) -> str:
    """
    Call the LLM with the Research AI prompt.

    Prompt text is character-for-character identical to the original
    research_worker.py to guarantee zero output regression.
    """
    company_context = load_company_context()

    prompt = f"""
You are the Research AI worker for Project Genesis.

{company_context}

Your assignment is to identify profitable AI product opportunities for this target audience:

{target_audience}

Generate exactly 3 preliminary product hypotheses.

For every product include:

1. Product name
2. Customer problem
3. Proposed AI solution
4. Why customers may pay
5. Difficulty score out of 10
6. Profit potential score out of 10
7. Main risk
8. Validation required

Important rules:

- Do not pretend that you performed live internet research.
- Do not present estimated numbers as verified facts.
- Clearly label every idea as an unvalidated hypothesis.
- Follow the Project Genesis Constitution.
- Use clear Markdown formatting.
"""

    return ask_ai(prompt)


def _save_research_report(target_audience: str, research_result: str) -> Path:
    """
    Write the research report to disk.

    Report format is character-for-character identical to the original
    research_worker.py to guarantee zero format regression.
    """
    report_path = _get_next_report_path()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    complete_report = f"""# Project Genesis Research Report

**Created:** {current_time}

**Prepared by:** Research AI

**Target audience:** {target_audience}

**Status:** Preliminary and unvalidated

---

## Important Notice

This report was generated using AI reasoning and existing company context.

It does not contain verified live market research unless clearly stated.

Customer interviews and external validation are required before development begins.

---

{research_result}

---

## Current Decision

No product has been approved automatically.

Final product selection requires review and approval from Harshit, Founder of Project Genesis.
"""

    report_path.write_text(complete_report, encoding="utf-8")
    return report_path


def _update_company_memory(target_audience: str, report_path: Path) -> None:
    """
    Append a Research Activity entry to company_memory.md.

    Entry format is character-for-character identical to the original
    research_worker.py to guarantee zero memory regression.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    memory_entry = f"""

---

## Research Activity

**Date:** {current_time}

**Research topic:** {target_audience}

**Report location:** {report_path}

**Status:** Research completed. Product ideas remain unvalidated.

**Founder approval:** Pending
"""

    with COMPANY_MEMORY_FILE.open("a", encoding="utf-8") as memory_file:
        memory_file.write(memory_entry)


# ──────────────────────────────────────────────────────────────────────────────
# ResearchWorker
# ──────────────────────────────────────────────────────────────────────────────

class ResearchWorker(BaseWorker):
    """
    Research AI worker — migrated to the BaseWorker lifecycle framework.

    Lifecycle mapping:
      create_plan(task)    →  Validates and normalises the target audience.
      execute(task, plan)  →  Calls LLM, saves report; returns (text, path).
      verify(result)       →  Checks for required sections in the LLM output.
      learn(task, result)  →  Appends Research Activity to company_memory.md.

    The return type of execute() is intentionally a (str, Path) tuple so
    that the legacy run_research_assignment(audience) wrapper can unpack
    it without any adaptation.
    """

    identity = WorkerIdentity(
        name="Research Worker",
        role="Identify profitable AI product opportunities for a target audience.",
        version="2.0.0",
    )

    # ── Lifecycle hooks ────────────────────────────────────────────────

    def create_plan(self, task: Any) -> str:
        """
        Validate the target audience and return it as the plan.

        The original worker did no explicit planning step; this method
        replicates that simplicity while fitting the BaseWorker contract.

        Args:
            task: Target audience string provided by the caller.

        Returns:
            The normalised target audience string.
        """
        target_audience = str(task).strip()
        self.logger.info(
            f"Research plan created — Target audience: '{target_audience}'"
        )
        return target_audience

    def execute(self, task: Any, plan: str) -> tuple[str, Path]:
        """
        Run the LLM research call and save the report to disk.

        Behaviour is identical to the original sequence:
          research_product_ideas(audience) → save_research_report(audience, result)

        Args:
            task: Original task (used only for logging context).
            plan: Normalised target audience (output of create_plan).

        Returns:
            A (result_text, report_path) tuple — identical to the original
            run_research_assignment() return signature.
        """
        self.logger.info(f"Calling LLM for audience: '{plan}'")
        result_text = _research_product_ideas(plan)

        self.logger.info("Saving research report to disk…")
        report_path = _save_research_report(plan, result_text)
        self.logger.info(f"Report saved: {report_path}")

        return result_text, report_path

    def verify(self, result: tuple[str, Path]) -> bool:
        """
        Confirm the LLM output contains the three required sections.

        Per the migration plan: checks for 'Product name', 'Customer problem',
        and 'Main risk' to ensure the model followed the prompt structure.

        Args:
            result: (result_text, report_path) tuple from execute().

        Returns:
            True if all three sections are present; False otherwise.
        """
        result_text, _ = result
        required_sections = ["Product name", "Customer problem", "Main risk"]

        for section in required_sections:
            if section not in result_text:
                self.logger.warning(
                    f"Verification failed — missing section: '{section}'"
                )
                return False

        self.logger.info("Verification passed — all required sections present.")
        return True

    def learn(self, task: Any, result: tuple[str, Path]) -> None:
        """
        Append the Research Activity entry to company_memory.md.

        Behaviour is identical to the original update_company_memory():
        a direct append to company_memory.md so that Genesis and all
        existing callers continue to see the update immediately.

        Note: Phase 3 will introduce the MemoryInterface staging path.
        For Phase 2, the direct write is preserved for 100% parity.

        Args:
            task:   Target audience string (original task).
            result: (result_text, report_path) tuple from execute().

        Returns:
            None — direct write requires no proposal path.
        """
        _, report_path = result
        target_audience = str(task).strip()

        _update_company_memory(target_audience, report_path)
        self.logger.info("Company memory updated.")
        return None
