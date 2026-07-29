from datetime import datetime
from pathlib import Path

from brain import ask_ai
from memory import load_company_context


REPORTS_FOLDER = Path("research_reports")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def get_next_report_path():
    REPORTS_FOLDER.mkdir(exist_ok=True)

    existing_reports = list(
        REPORTS_FOLDER.glob("research_report_*.md")
    )

    next_number = len(existing_reports) + 1

    return REPORTS_FOLDER / f"research_report_{next_number:03}.md"


def research_product_ideas(target_audience):
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


def save_research_report(target_audience, research_result):
    report_path = get_next_report_path()

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

    report_path.write_text(
        complete_report,
        encoding="utf-8",
    )

    return report_path


def update_company_memory(target_audience, report_path):
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


def run_research_assignment(target_audience):
    result = research_product_ideas(target_audience)
    report_path = save_research_report(target_audience, result)
    update_company_memory(target_audience, report_path)
    return result, report_path


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