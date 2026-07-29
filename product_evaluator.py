from datetime import datetime
from pathlib import Path

from brain import ask_ai
from memory import load_company_context


RESEARCH_FOLDER = Path("research_reports")
EVALUATION_FOLDER = Path("product_evaluations")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def load_research_reports():
    if not RESEARCH_FOLDER.exists():
        raise FileNotFoundError(
            "The research_reports folder does not exist."
        )

    report_paths = sorted(
        RESEARCH_FOLDER.glob("research_report_*.md")
    )

    if not report_paths:
        raise FileNotFoundError(
            "No research reports were found."
        )

    reports = []

    for report_path in report_paths:
        report_content = report_path.read_text(
            encoding="utf-8"
        )

        reports.append(
            f"""
========================================
REPORT FILE: {report_path.name}
========================================

{report_content}
"""
        )

    return "\n".join(reports), report_paths


def evaluate_products(research_content):
    company_context = load_company_context()

    prompt = f"""
You are the Product Evaluation AI for Project Genesis.

Your job is to compare the product hypotheses contained in the
company's existing research reports.

{company_context}

RESEARCH REPORTS:

{research_content}

Evaluate every distinct product hypothesis using exactly these factors:

1. Customer Pain — maximum 25 points
2. Willingness to Pay — maximum 20 points
3. MVP Speed — maximum 20 points
4. Development Simplicity — maximum 15 points
5. Low Validation Cost — maximum 10 points
6. Strategic Fit for Project Genesis — maximum 10 points

Maximum total score: 100 points.

Important scoring rules:

- Higher scores are always better.
- A technically difficult product should receive a lower
  Development Simplicity score.
- A slow product should receive a lower MVP Speed score.
- An expensive validation process should receive a lower
  Low Validation Cost score.
- Do not invent verified market statistics.
- Do not pretend live internet research was performed.
- Treat all products as unvalidated hypotheses.
- Consider the founder's practical experience with HR,
  attendance, employee documentation and small-business operations.
- Use only information supported by the research reports and
  company context.
- Do not automatically approve a product.
- Final approval belongs to Harshit, Founder of Project Genesis.

Your report must include:

# Product Evaluation Report

## Evaluation Method

Briefly explain the scoring method.

## Complete Ranking

Create a Markdown table containing:

- Rank
- Product
- Customer Pain score
- Willingness to Pay score
- MVP Speed score
- Development Simplicity score
- Low Validation Cost score
- Strategic Fit score
- Total score out of 100

Check that every total equals the sum of its factor scores.

## Top Three Opportunities

Explain the strengths, risks and validation requirements
for the three highest-ranked products.

## Recommended Product to Validate First

Recommend exactly one product for validation.

Clearly explain:

- Why it ranked first
- Why it is suitable for the first product
- What could cause it to fail
- The cheapest real-world validation test
- What evidence is required before development begins

## Products Not Recommended Yet

Briefly explain why the remaining products should be postponed.

## Final Decision Status

State clearly:

Recommendation only.
No product has been approved.
Founder approval is pending.
"""

    return ask_ai(prompt)


def get_next_evaluation_path():
    EVALUATION_FOLDER.mkdir(exist_ok=True)

    existing_evaluations = list(
        EVALUATION_FOLDER.glob(
            "product_evaluation_*.md"
        )
    )

    next_number = len(existing_evaluations) + 1

    return EVALUATION_FOLDER / (
        f"product_evaluation_{next_number:03}.md"
    )


def save_evaluation_report(
    evaluation_result,
    report_paths,
):
    evaluation_path = get_next_evaluation_path()

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    source_files = "\n".join(
        f"- {path.name}"
        for path in report_paths
    )

    complete_report = f"""# Project Genesis Product Evaluation

**Created:** {current_time}

**Prepared by:** Product Evaluation AI

**Status:** Recommendation only — founder approval pending

## Research Sources

{source_files}

---

{evaluation_result}

---

## Governance Notice

This evaluation does not approve a product automatically.

No development should begin until Harshit reviews the
recommendation and gives founder approval.
"""

    evaluation_path.write_text(
        complete_report,
        encoding="utf-8",
    )

    return evaluation_path


def update_company_memory(
    evaluation_path,
    report_count,
):
    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    memory_entry = f"""

---

## Product Evaluation Activity

**Date:** {current_time}

**Research reports reviewed:** {report_count}

**Evaluation report:** {evaluation_path}

**Status:** Product comparison completed.

**Product approval:** Pending founder decision.
"""

    with COMPANY_MEMORY_FILE.open(
        "a",
        encoding="utf-8",
    ) as memory_file:
        memory_file.write(memory_entry)


def run_product_evaluation():
    print()
    print(
        "Product Evaluation AI: "
        "Reading all research reports..."
    )

    research_content, report_paths = (
        load_research_reports()
    )

    print(
        f"Product Evaluation AI: "
        f"{len(report_paths)} reports loaded."
    )

    print(
        "Product Evaluation AI: "
        "Comparing product opportunities..."
    )

    evaluation_result = evaluate_products(
        research_content
    )

    evaluation_path = save_evaluation_report(
        evaluation_result,
        report_paths,
    )

    update_company_memory(
        evaluation_path,
        len(report_paths),
    )

    return (
        evaluation_result,
        evaluation_path,
        len(report_paths),
    )


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Project Genesis — Product Evaluation AI")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        result, evaluation_path, report_count = (
            run_product_evaluation()
        )

        print()
        print(result)

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Product Evaluation Status")
        print(
            f"✓ {report_count} research reports reviewed"
        )
        print("✓ Product hypotheses compared")
        print("✓ Ranking created")
        print(
            f"✓ Evaluation saved: {evaluation_path}"
        )
        print("✓ Company memory updated")
        print("✓ Founder approval is still required")

    except Exception as error:
        print()
        print(
            "Product Evaluation AI could not "
            "complete the assignment."
        )
        print("Error:", error)


if __name__ == "__main__":
    main()