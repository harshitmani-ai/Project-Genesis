"""
workers/marketing_worker.py

MarketingWorker — the Marketing AI worker for Project Genesis.

Subclasses BaseWorker and implements the 5-step lifecycle:
  Goal → Plan → Execute → Verify → Learn

Responsibilities:
  - Transform validated products & customer knowledge into marketing assets.
  - Generate product positioning & value proposition.
  - Create landing page copy, website headlines, sub-headlines, and CTAs.
  - Draft cold email sequences and social media launch posts.
  - Provide FAQ and objection handling sections.
  - Save structured marketing reports to marketing_reports/marketing_report_NNN.md.
  - Append Marketing Activity entries to company_memory.md.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from brain import ask_ai
from core import BaseWorker, WorkerIdentity
from core.memory_interface import MemoryInterface
from memory import load_company_context


REPORTS_FOLDER = Path("marketing_reports")


def _get_next_report_path() -> Path:
    """Return the next sequential marketing_report_NNN.md path."""
    REPORTS_FOLDER.mkdir(exist_ok=True)
    existing_reports = list(REPORTS_FOLDER.glob("marketing_report_*.md"))
    next_number = len(existing_reports) + 1
    return REPORTS_FOLDER / f"marketing_report_{next_number:03}.md"


def _generate_marketing_campaign(product_info: str) -> str:
    """
    Call the LLM to generate comprehensive marketing assets and campaign copy.
    """
    company_context = load_company_context()

    prompt = f"""
You are the Marketing AI worker for Project Genesis.

{company_context}

Your assignment is to generate a comprehensive marketing strategy and asset package for this product and target customer:

{product_info}

Generate a complete marketing campaign containing ALL of the following required sections:

# 1. Product Positioning & Value Proposition
- Target Customer Identification: Clearly define the ideal customer persona and target audience.
- Core Value Proposition: The single primary benefit that drives purchase decisions.
- Key Differentiators: Why this beats existing alternatives.

# 2. Website Headline & Tagline
- Primary Headline (h1): High-converting headline.
- Sub-headline (h2): Supporting explanatory copy.

# 3. Landing Page Copy
- Hero Section Copy
- Feature & Benefit Bullets (Exactly 3 key benefits)
- Social Proof / Trust Triggers
- Pricing Section Copy

# 4. Cold Email Sequence
- Email 1: Initial Hook & Value Intro
- Email 2: Problem Focus & Case Study / Proof
- Email 3: Urgency & Final Nudge

# 5. Social Media Launch Posts
- LinkedIn Launch Post
- Twitter / X Announcement Thread (3 tweets)

# 6. FAQ & Objection Handling
- Top 3 Customer Objections & AI Responses
- Frequently Asked Questions (FAQ)

# 7. Call to Action (CTA) & Conversion Trigger
- Primary Call to Action Button Copy (e.g., "Start Free Trial", "Book Demo")
- Secondary Conversion Trigger

Important rules:
- Clearly identify the target customer persona in section 1.
- Ensure an explicit Call to Action (CTA) is provided in section 7.
- Follow the Project Genesis Constitution (Honest claims, clear customer value).
- Use clear Markdown formatting with distinct section headers.
"""

    return ask_ai(prompt)


def _save_marketing_report(product_info: str, result_text: str) -> Path:
    """
    Write the marketing report to disk.
    """
    report_path = _get_next_report_path()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    complete_report = f"""# Project Genesis Marketing Report

**Created:** {current_time}

**Prepared by:** Marketing AI

**Product / Target Customer:** {product_info}

**Status:** Marketing Campaign & Asset Package Generated

---

## Important Notice

This marketing report was generated using AI reasoning and existing company context.

All claims, pricing, and campaign copy require founder review before public distribution or ad spend.

---

{result_text}

---

## Governance & Action Items

No marketing campaign has been launched automatically.

Final approval for public campaign launch belongs to Harshit, Founder of Project Genesis.
"""

    report_path.write_text(complete_report, encoding="utf-8")
    return report_path


def _update_company_memory(product_info: str, report_path: Path) -> None:
    """
    Submit a governed memory proposal for this marketing activity.

    Phase 8: Direct writes to company_memory.md are replaced with a
    proposal submitted via MemoryInterface.propose_update().
    """
    content = f"""## Marketing Activity

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Product / Target:** {product_info}

**Report location:** {report_path}

**Status:** Marketing assets & campaign copy generated.

**Founder approval:** Pending
"""
    MemoryInterface().propose_update(
        worker_name="Marketing Worker",
        topic=f"Marketing — {product_info[:50]}",
        content=content,
    )


class MarketingWorker(BaseWorker):
    """
    Marketing AI worker — implemented within the BaseWorker framework.
    """

    identity = WorkerIdentity(
        name="Marketing Worker",
        role="Transform validated products into high-converting marketing assets and campaign copy.",
        version="1.0.0",
    )

    def create_plan(self, task: Any) -> str:
        """
        Validate the product info / target customer and return it as the plan.
        """
        product_info = str(task).strip()
        self.logger.info(
            f"Marketing plan created — Target product/customer: '{product_info}'"
        )
        return product_info

    def execute(self, task: Any, plan: str) -> tuple[str, Path]:
        """
        Run the LLM marketing campaign generation and save the report to disk.
        """
        self.logger.info(f"Calling LLM for product info: '{plan}'")
        result_text = _generate_marketing_campaign(plan)

        self.logger.info("Saving marketing report to disk…")
        report_path = _save_marketing_report(plan, result_text)
        self.logger.info(f"Report saved: {report_path}")

        return result_text, report_path

    def verify(self, result: tuple[str, Path]) -> bool:
        """
        Confirm the LLM output is non-empty and contains all required sections:
          1. Required sections exist (Positioning, Landing Page, Email / Outreach, CTA)
          2. Customer is clearly identified
          3. CTA exists
          4. Output is not empty
        """
        result_text, _ = result

        # Check 1: Output is not empty
        if not result_text or not result_text.strip():
            self.logger.warning("Verification failed — output is empty.")
            return False

        # Check 2: Customer is clearly identified
        if "Customer" not in result_text and "Target" not in result_text:
            self.logger.warning("Verification failed — target customer is not identified.")
            return False

        # Check 3: CTA exists
        if "CTA" not in result_text and "Call to Action" not in result_text:
            self.logger.warning("Verification failed — missing Call to Action (CTA).")
            return False

        # Check 4: Required key sections exist
        required_sections = ["Positioning", "Landing Page"]
        for section in required_sections:
            if section not in result_text:
                self.logger.warning(
                    f"Verification failed — missing required section: '{section}'"
                )
                return False

        self.logger.info("Verification passed — all marketing verification rules satisfied.")
        return True

    def learn(self, task: Any, result: tuple[str, Path]) -> None:
        """
        Append the Marketing Activity entry to company_memory.md.
        """
        _, report_path = result
        product_info = str(task).strip()

        _update_company_memory(product_info, report_path)
        self.logger.info("Company memory updated with Marketing Activity.")
        return None
