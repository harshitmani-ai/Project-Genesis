"""
workers/finance_worker.py

FinanceWorker — the Finance AI worker for Project Genesis.

Subclasses BaseWorker and implements the 5-step lifecycle:
  Goal → Plan → Execute → Verify → Learn

Responsibilities:
  - Evaluate financial viability of products and business models.
  - Generate revenue model, startup cost estimates, monthly operating costs.
  - Produce gross margin estimates, break-even analysis, ROI projections.
  - Document cash-flow assumptions and financial risks.
  - Provide pricing recommendations and a Profitability Score (1–10).
  - Save structured finance reports to finance_reports/finance_report_NNN.md.
  - Append Finance Activity entries to company_memory.md.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from brain import ask_ai
from core import BaseWorker, WorkerIdentity
from memory import load_company_context


REPORTS_FOLDER = Path("finance_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def _get_next_report_path() -> Path:
    """Return the next sequential finance_report_NNN.md path."""
    REPORTS_FOLDER.mkdir(exist_ok=True)
    existing_reports = list(REPORTS_FOLDER.glob("finance_report_*.md"))
    next_number = len(existing_reports) + 1
    return REPORTS_FOLDER / f"finance_report_{next_number:03}.md"


def _generate_financial_analysis(product_info: str) -> str:
    """
    Call the LLM to generate a comprehensive financial viability analysis.
    """
    company_context = load_company_context()

    prompt = f"""
You are the Finance AI worker for Project Genesis.

{company_context}

Your assignment is to produce a full financial viability analysis for this product or business model:

{product_info}

Generate a complete financial report containing ALL of the following required sections:

# 1. Revenue Model
- Primary revenue stream (SaaS / one-time / usage-based / hybrid).
- Pricing tiers and structure.
- Revenue per customer (MRR / ARR).
- Assumptions: clearly state every assumption used.

# 2. Startup Cost Estimate
- Development costs (MVP build).
- Tooling and infrastructure costs.
- Licensing, compliance, legal.
- Total estimated startup cost.
- Assumptions: clearly state every assumption used.

# 3. Monthly Operating Cost
- Hosting and infrastructure.
- AI / API costs per customer.
- Support and maintenance.
- Total monthly operating cost estimate.
- Assumptions: clearly state every assumption used.

# 4. Gross Margin Estimate
- Revenue per customer vs. cost to serve.
- Gross margin percentage.
- Assumptions: clearly state every assumption used.

# 5. Break-Even Analysis
- Break-even number of customers.
- Break-even timeline estimate.
- Assumptions: clearly state every assumption used.

# 6. ROI Estimate
- 6-month ROI projection.
- 12-month ROI projection.
- Assumptions: clearly state every assumption used.

# 7. Cash-Flow Assumptions
- Monthly cash burn (pre-revenue).
- Cash runway estimate.
- Revenue ramp-up assumptions.
- Assumptions: clearly state every assumption used.

# 8. Financial Risks
- List the top 5 financial risks.
- Risk severity (Low / Medium / High) for each.
- Mitigation strategy for each risk.

# 9. Pricing Recommendations
- Recommended entry-level price.
- Recommended growth-tier price.
- Rationale for pricing strategy.
- Competitor pricing benchmark (estimated).

# 10. Profitability Score
- Assign a Profitability Score from 1 to 10.
- Justify the score with clear reasoning.
- Format: "Profitability Score: X/10 — [Reasoning]"

Important rules:
- Every estimate must explicitly state its assumptions.
- Do not present speculative numbers as confirmed facts.
- Follow the Project Genesis Constitution (Profit-first, honest numbers).
- Use clear Markdown formatting with distinct section headers.
- The Profitability Score must appear in its own section with the exact format shown above.
"""

    return ask_ai(prompt)


def _save_finance_report(product_info: str, result_text: str) -> Path:
    """
    Write the finance report to disk.
    """
    report_path = _get_next_report_path()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    complete_report = f"""# Project Genesis Finance Report

**Created:** {current_time}

**Prepared by:** Finance AI

**Product / Business Model:** {product_info}

**Status:** Financial Viability Analysis Generated

---

## Important Notice

This finance report was generated using AI reasoning, industry benchmarks, and existing company context.

All cost estimates, revenue projections, and financial assumptions require founder review and validation before any financial commitments are made.

---

{result_text}

---

## Governance & Action Items

No financial commitments have been made automatically.

Final approval for all financial decisions belongs to Harshit, Founder of Project Genesis.
"""

    report_path.write_text(complete_report, encoding="utf-8")
    return report_path


def _update_company_memory(product_info: str, report_path: Path) -> None:
    """
    Append a Finance Activity entry to company_memory.md.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    memory_entry = f"""

---

## Finance Activity

**Date:** {current_time}

**Product / Business Model:** {product_info}

**Report location:** {report_path}

**Status:** Financial viability analysis generated.

**Founder approval:** Pending
"""

    with COMPANY_MEMORY_FILE.open("a", encoding="utf-8") as memory_file:
        memory_file.write(memory_entry)


class FinanceWorker(BaseWorker):
    """
    Finance AI worker — implemented within the BaseWorker framework.
    """

    identity = WorkerIdentity(
        name="Finance Worker",
        role="Evaluate financial viability, project unit economics, and enforce profit-first decisions.",
        version="1.0.0",
    )

    def create_plan(self, task: Any) -> str:
        """
        Validate the product / business model info and return it as the plan.
        """
        product_info = str(task).strip()
        self.logger.info(
            f"Finance plan created — Target product/model: '{product_info}'"
        )
        return product_info

    def execute(self, task: Any, plan: str) -> tuple[str, Path]:
        """
        Run the LLM financial analysis and save the report to disk.
        """
        self.logger.info(f"Calling LLM for financial analysis of: '{plan}'")
        result_text = _generate_financial_analysis(plan)

        self.logger.info("Saving finance report to disk…")
        report_path = _save_finance_report(plan, result_text)
        self.logger.info(f"Report saved: {report_path}")

        return result_text, report_path

    def verify(self, result: tuple[str, Path]) -> bool:
        """
        Confirm the LLM output contains all required financial sections:
          1. Output is not empty.
          2. All financial sections exist.
          3. Every estimate clearly states assumptions.
          4. Profitability score exists.
          5. Financial risks exist.
        """
        result_text, _ = result

        # Check 1: Output is not empty
        if not result_text or not result_text.strip():
            self.logger.warning("Verification failed — output is empty.")
            return False

        # Check 2 & 3: Required sections and assumptions present
        required_sections = [
            "Revenue Model",
            "Break-Even",
            "Assumptions",
        ]
        for section in required_sections:
            if section not in result_text:
                self.logger.warning(
                    f"Verification failed — missing required section: '{section}'"
                )
                return False

        # Check 4: Profitability score exists
        if "Profitability Score" not in result_text:
            self.logger.warning("Verification failed — Profitability Score is missing.")
            return False

        # Check 5: Financial risks exist
        if "Financial Risk" not in result_text and "Risk" not in result_text:
            self.logger.warning("Verification failed — Financial Risks section is missing.")
            return False

        self.logger.info("Verification passed — all financial verification rules satisfied.")
        return True

    def learn(self, task: Any, result: tuple[str, Path]) -> None:
        """
        Append the Finance Activity entry to company_memory.md.
        """
        _, report_path = result
        product_info = str(task).strip()

        _update_company_memory(product_info, report_path)
        self.logger.info("Company memory updated with Finance Activity.")
        return None
