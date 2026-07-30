from pathlib import Path

from brain import ask_ai
from memory import load_company_context
from workers.research_worker import ResearchWorker
from core.worker_report import ReportStatus


COMPANY_MEMORY_FILE = Path("company_memory.md")
REPORTS_FOLDER = Path("research_reports")

# ── Worker Registry ──────────────────────────────────────────────────────────
# Central lookup table for all migrated workers.
# Phase 3 registers Research Worker only.
# Phase 4 will add ProductEvaluatorWorker, MarketIntelligenceWorker, etc.

WORKER_REGISTRY = {
    "research": ResearchWorker(),
}


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