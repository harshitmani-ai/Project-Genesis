from pathlib import Path

from brain import ask_ai
from memory import load_company_context
from workers.research_worker import ResearchWorker
from workers.acquisition_worker import AcquisitionWorker
from workers.marketing_worker import MarketingWorker
from workers.finance_worker import FinanceWorker
from core.worker_report import ReportStatus
from core.orchestrator import WorkerOrchestrator


COMPANY_MEMORY_FILE = Path("company_memory.md")
REPORTS_FOLDER = Path("research_reports")

# ── Worker Registry ──────────────────────────────────────────────────────────
# Central lookup table for all migrated workers.
# Phase 3 registers Research Worker.
# Phase 4 registers Acquisition Worker.
# Phase 5 registers Marketing Worker.
# Phase 6 registers Finance Worker.

WORKER_REGISTRY = {
    "research": ResearchWorker(),
    "acquisition": AcquisitionWorker(),
    "marketing": MarketingWorker(),
    "finance": FinanceWorker(),
}

# ── Orchestration Engine ─────────────────────────────────────────────────────
# Phase 7: Multi-worker orchestration.
# Default pipeline runs all four workers in business-logic order.

ORCHESTRATOR = WorkerOrchestrator(WORKER_REGISTRY)

DEFAULT_PIPELINE = ["research", "acquisition", "marketing", "finance"]


def show_company_memory():
    if not COMPANY_MEMORY_FILE.exists():
        return "Company memory file was not found."

    return COMPANY_MEMORY_FILE.read_text(encoding="utf-8")


def show_research_reports():
    if not REPORTS_FOLDER.exists():
        return "No research reports have been created yet."

    reports = sorted(REPORTS_FOLDER.glob("research_report_*.md"))

    if not reports:
        return "No research reports have been created yet."

    report_list = "\n".join(
        f"- {report.name}" for report in reports
    )

    return f"""Completed Research Reports:

{report_list}
"""


def should_run_research(command):
    research_words = [
        "research",
        "investigate",
        "find product ideas",
        "find business ideas",
        "study market",
        "product opportunities",
    ]

    command_lower = command.lower()

    return any(
        phrase in command_lower
        for phrase in research_words
    )


def should_show_memory(command):
    memory_commands = [
        "show company memory",
        "open company memory",
        "display company memory",
        "read company memory",
    ]

    command_lower = command.lower()

    return any(
        phrase in command_lower
        for phrase in memory_commands
    )


def should_show_reports(command):
    report_commands = [
        "show reports",
        "list reports",
        "show research reports",
        "what reports",
        "completed reports",
        "latest research",
    ]

    command_lower = command.lower()

    return any(
        phrase in command_lower
        for phrase in report_commands
    )


def remove_research_instruction(command):
    phrases = [
        "research",
        "investigate",
        "find product ideas for",
        "find business ideas for",
        "study the market for",
        "study market for",
        "product opportunities for",
    ]

    cleaned_command = command

    for phrase in phrases:
        cleaned_command = cleaned_command.replace(
            phrase,
            "",
        )

        cleaned_command = cleaned_command.replace(
            phrase.title(),
            "",
        )

    return cleaned_command.strip(" :.-")


def should_run_acquisition(command):
    acquisition_words = [
        "acquisition",
        "find leads",
        "lead database",
        "outreach",
        "customer acquisition",
        "acquire customers",
        "icp",
    ]

    command_lower = command.lower()

    return any(
        phrase in command_lower
        for phrase in acquisition_words
    )


def remove_acquisition_instruction(command):
    phrases = [
        "customer acquisition for",
        "acquisition strategy for",
        "acquisition for",
        "find leads for",
        "lead database for",
        "outreach for",
        "acquire customers for",
        "customer acquisition",
        "acquisition",
        "find leads",
        "lead database",
        "outreach",
        "icp",
    ]

    cleaned_command = command

    for phrase in phrases:
        cleaned_command = cleaned_command.replace(
            phrase,
            "",
        )

        cleaned_command = cleaned_command.replace(
            phrase.title(),
            "",
        )

    return cleaned_command.strip(" :.-")


def should_run_marketing(command):
    marketing_words = [
        "marketing",
        "positioning",
        "landing page",
        "cold email",
        "copywriting",
        "campaign",
        "headline",
        "value proposition",
    ]

    command_lower = command.lower()

    return any(
        phrase in command_lower
        for phrase in marketing_words
    )


def remove_marketing_instruction(command):
    phrases = [
        "marketing strategy for",
        "marketing campaign for",
        "marketing assets for",
        "marketing for",
        "landing page for",
        "cold email for",
        "positioning for",
        "marketing",
        "landing page",
        "cold email",
        "positioning",
        "campaign",
    ]

    cleaned_command = command

    for phrase in phrases:
        cleaned_command = cleaned_command.replace(
            phrase,
            "",
        )

        cleaned_command = cleaned_command.replace(
            phrase.title(),
            "",
        )

    return cleaned_command.strip(" :.-")


def should_run_finance(command):
    finance_words = [
        "finance",
        "financial",
        "revenue model",
        "break-even",
        "break even",
        "profitability",
        "roi",
        "pricing strategy",
        "unit economics",
        "cash flow",
        "startup cost",
    ]

    command_lower = command.lower()

    return any(
        phrase in command_lower
        for phrase in finance_words
    )


def remove_finance_instruction(command):
    phrases = [
        "financial analysis for",
        "finance analysis for",
        "finance report for",
        "finance for",
        "financial viability of",
        "analyse finances for",
        "analyze finances for",
        "financial viability",
        "financial analysis",
        "financial",
        "finance",
        "revenue model for",
        "profitability of",
    ]

    cleaned_command = command

    for phrase in phrases:
        cleaned_command = cleaned_command.replace(
            phrase,
            "",
        )

        cleaned_command = cleaned_command.replace(
            phrase.title(),
            "",
        )

    return cleaned_command.strip(" :.-")


def should_run_orchestration(command):
    orchestration_words = [
        "full analysis",
        "complete analysis",
        "full strategy",
        "complete strategy",
        "run all workers",
        "run pipeline",
        "orchestrate",
        "full pipeline",
        "end-to-end",
        "end to end",
        "all workers",
        "full company report",
    ]

    command_lower = command.lower()

    return any(
        phrase in command_lower
        for phrase in orchestration_words
    )


def remove_orchestration_instruction(command):
    phrases = [
        "run all workers for",
        "full analysis for",
        "complete analysis for",
        "full strategy for",
        "complete strategy for",
        "orchestrate for",
        "run pipeline for",
        "end-to-end analysis for",
        "end to end analysis for",
        "run all workers",
        "full analysis",
        "complete analysis",
        "full strategy",
        "complete strategy",
        "orchestrate",
        "run pipeline",
        "all workers",
        "full company report",
        "full pipeline",
    ]

    cleaned_command = command

    for phrase in phrases:
        cleaned_command = cleaned_command.replace(
            phrase,
            "",
        )

        cleaned_command = cleaned_command.replace(
            phrase.title(),
            "",
        )

    return cleaned_command.strip(" :.-")


def answer_company_question(command):
    company_context = load_company_context()

    prompt = f"""
You are Project Genesis, Harshit's AI company partner.

Use the company information below when answering.

{company_context}

Founder request:
{command}

Rules:

- Give an honest answer.
- Do not claim that work was completed unless it really was.
- Do not approve products or major decisions without founder approval.
- Keep the answer practical and clear.
- Focus on moving Project Genesis toward its first successful product and paying customer.
"""

    return ask_ai(prompt)


def handle_command(command):
    if should_show_memory(command):
        print()
        print(show_company_memory())
        return

    if should_show_reports(command):
        print()
        print(show_research_reports())
        return

    if should_run_research(command):
        target = remove_research_instruction(command)

        if not target:
            target = input(
                "What audience or problem should Research AI study? "
            ).strip()

        if not target:
            print("Research assignment cancelled.")
            return

        # ── Route through Worker Framework ───────────────────────────
        report = WORKER_REGISTRY["research"].run_lifecycle(target)

        if report.status == ReportStatus.FAILURE:
            print()
            print("Genesis Status")
            print("✗ Research Worker failed.")
            print(f"Error: {report.error}")
            return

        result, report_path = report.result

        print()
        print("Research Result:")
        print(result)

        print()
        print("Genesis Status")
        print("✓ Research AI completed the assignment")
        print(f"✓ Report saved: {report_path}")
        print("✓ Company memory updated")
        print("✓ Founder approval is still required")
        return

    if should_run_acquisition(command):
        icp = remove_acquisition_instruction(command)

        if not icp:
            icp = input(
                "What Ideal Customer Profile (ICP) should Acquisition AI target? "
            ).strip()

        if not icp:
            print("Acquisition assignment cancelled.")
            return

        # ── Route through Worker Framework ───────────────────────────
        report = WORKER_REGISTRY["acquisition"].run_lifecycle(icp)

        if report.status == ReportStatus.FAILURE:
            print()
            print("Genesis Status")
            print("✗ Acquisition Worker failed.")
            print(f"Error: {report.error}")
            return

        result, report_path = report.result

        print()
        print("Acquisition Strategy Result:")
        print(result)

        print()
        print("Genesis Status")
        print("✓ Acquisition AI completed the assignment")
        print(f"✓ Report saved: {report_path}")
        print("✓ Company memory updated")
        print("✓ Founder approval is still required")
        return

    if should_run_marketing(command):
        product_info = remove_marketing_instruction(command)

        if not product_info:
            product_info = input(
                "What product or target customer should Marketing AI focus on? "
            ).strip()

        if not product_info:
            print("Marketing assignment cancelled.")
            return

        # ── Route through Worker Framework ───────────────────────────
        report = WORKER_REGISTRY["marketing"].run_lifecycle(product_info)

        if report.status == ReportStatus.FAILURE:
            print()
            print("Genesis Status")
            print("✗ Marketing Worker failed.")
            print(f"Error: {report.error}")
            return

        result, report_path = report.result

        print()
        print("Marketing Strategy Result:")
        print(result)

        print()
        print("Genesis Status")
        print("✓ Marketing AI completed the assignment")
        print(f"✓ Report saved: {report_path}")
        print("✓ Company memory updated")
        print("✓ Founder approval is still required")
        return

    if should_run_finance(command):
        product_info = remove_finance_instruction(command)

        if not product_info:
            product_info = input(
                "What product or business model should Finance AI evaluate? "
            ).strip()

        if not product_info:
            print("Finance assignment cancelled.")
            return

        # ── Route through Worker Framework ───────────────────────────
        report = WORKER_REGISTRY["finance"].run_lifecycle(product_info)

        if report.status == ReportStatus.FAILURE:
            print()
            print("Genesis Status")
            print("✗ Finance Worker failed.")
            print(f"Error: {report.error}")
            return

        result, report_path = report.result

        print()
        print("Finance Analysis Result:")
        print(result)

        print()
        print("Genesis Status")
        print("✓ Finance AI completed the assignment")
        print(f"✓ Report saved: {report_path}")
        print("✓ Company memory updated")
        print("✓ Founder approval is still required")
        return

    if should_run_orchestration(command):
        goal = remove_orchestration_instruction(command)

        if not goal:
            goal = input(
                "What is the business objective for the full Genesis pipeline? "
            ).strip()

        if not goal:
            print("Orchestration cancelled.")
            return

        print()
        print("Genesis Orchestration Engine — starting full pipeline…")
        print(f"Goal: {goal}")

        final_report = ORCHESTRATOR.run(goal, DEFAULT_PIPELINE)

        print()
        print("═" * 60)
        print("FINAL COMPANY REPORT")
        print("═" * 60)
        print()
        print(f"Workers executed: {', '.join(w.title() for w in final_report.workers_executed)}")
        if final_report.failures:
            print(f"Workers failed: {', '.join(w.title() for w in final_report.failures)}")
        print()
        print("Combined Recommendation:")
        print(final_report.combined_summary)
        print()
        print("Consolidated Risks:")
        print(final_report.risks)
        print()
        print("Next Actions for Founder:")
        print(final_report.next_actions)
        print()
        print("Genesis Status")
        print(f"✓ Orchestration pipeline completed — {final_report.success_count} workers succeeded")
        if final_report.failure_count:
            print(f"⚠ {final_report.failure_count} worker(s) failed — check FinalCompanyReport")
        print("✓ FinalCompanyReport saved to orchestration_reports/")
        print("✓ Founder approval is still required")
        return

    response = answer_company_question(command)

    print()
    print("Genesis:")
    print(response)


def get_multiline_input():
    lines = []
    first_line = input("Harshit: ").strip()

    if not first_line:
        return ""

    if first_line.lower() in {
        "exit",
        "quit",
        "close",
        "stop",
    }:
        return first_line

    if first_line == "END":
        return ""

    lines.append(first_line)

    while True:
        line = input("... ")
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Project Genesis")
    print("Welcome back, Harshit.")
    print()
    print("Speak naturally to your company.")
    print("Type 'END' on a new line to send your message.")
    print("Type 'exit' when you want to stop.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    while True:
        print()
        command = get_multiline_input()

        if not command:
            continue

        if command.lower() in {
            "exit",
            "quit",
            "close",
            "stop",
        }:
            print()
            print("Genesis: Company session closed.")
            break

        try:
            handle_command(command)

        except Exception as error:
            print()
            print("Genesis could not complete the request.")
            print("Error:", error)


if __name__ == "__main__":
    main()