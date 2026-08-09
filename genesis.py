from pathlib import Path

from brain import ask_ai
from memory import load_company_context
from workers.research_worker import ResearchWorker
from workers.acquisition_worker import AcquisitionWorker
from workers.marketing_worker import MarketingWorker
from workers.finance_worker import FinanceWorker
from core.worker_report import ReportStatus
from core.orchestrator import WorkerOrchestrator
from core.memory_governor import MemoryGovernor
from core.task_planner import TaskPlanner
from core.tool_manager import DEFAULT_TOOL_MANAGER
from core.skill_manager import SkillManager
from core.task_queue import Task, TaskQueue, TaskResult, TaskStatus


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

# ── Memory Governor ───────────────────────────────────────────────────────────
# Phase 8: Sole authority for committing memory proposals to company_memory.md.

GOVERNOR = MemoryGovernor()

# ── Task Planner ────────────────────────────────────────────────────────────
# Phase 9: Intelligent intent routing for natural language requests.

PLANNER = TaskPlanner()

# ── Tool Manager ────────────────────────────────────────────────────────────
# Phase 10: Shared tool registry accessible to all components.

TOOL_MANAGER = DEFAULT_TOOL_MANAGER

# ── Skill Manager ───────────────────────────────────────────────────────────
# Phase 11: Auto-discovers and loads skills from skills/ at startup.

SKILL_MANAGER = SkillManager()
_discovered = SKILL_MANAGER.discover()

# ── Task Queue ───────────────────────────────────────────────────────────
# Phase 12: Autonomous task queue for breaking large goals into tracked steps.

TASK_QUEUE = TaskQueue()


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


def show_proposals():
    """Return a human-readable summary of pending memory proposals."""
    return GOVERNOR.proposals_summary()


def should_show_proposals(command):
    proposal_commands = [
        "show proposals",
        "list proposals",
        "pending proposals",
        "memory proposals",
        "show memory proposals",
        "review proposals",
    ]
    command_lower = command.lower()
    return any(phrase in command_lower for phrase in proposal_commands)


def should_approve_proposals(command):
    approve_commands = [
        "approve proposals",
        "approve memory proposals",
        "merge proposals",
        "commit proposals",
        "approve all proposals",
    ]
    command_lower = command.lower()
    return any(phrase in command_lower for phrase in approve_commands)


def show_tools():
    """Return a human-readable listing of all registered tools."""
    return TOOL_MANAGER.tool_summary()


def should_show_tools(command):
    tool_commands = [
        "show tools",
        "list tools",
        "available tools",
        "what tools",
        "show tool registry",
    ]
    command_lower = command.lower()
    return any(phrase in command_lower for phrase in tool_commands)


def show_skills():
    """Return a human-readable listing of all discovered skills."""
    return SKILL_MANAGER.skills_summary()


def should_show_skills(command):
    skill_commands = [
        "show skills",
        "list skills",
        "available skills",
        "what skills",
        "show skill registry",
    ]
    command_lower = command.lower()
    return any(phrase in command_lower for phrase in skill_commands)


def should_run_skill(command):
    """Return the skill name if the command explicitly requests a skill, else None."""
    command_lower = command.lower()
    for skill_name in SKILL_MANAGER.list_skills():
        if skill_name.replace("_", " ") in command_lower or skill_name in command_lower:
            return skill_name
    return None


def remove_skill_instruction(command, skill_name):
    """Strip the skill name trigger from the command to get the clean goal."""
    import re
    cleaned = re.sub(re.escape(skill_name.replace("_", " ")), "", command, flags=re.IGNORECASE)
    cleaned = re.sub(re.escape(skill_name), "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" :.-")


# ── Phase 12: Task Queue helpers ──────────────────────────────────────────────

def should_show_tasks(command):
    task_commands = [
        "show tasks",
        "list tasks",
        "show task queue",
        "view tasks",
        "task queue",
        "show queue",
    ]
    return any(phrase in command.lower() for phrase in task_commands)


def should_run_next_task(command):
    next_commands = [
        "next task",
        "run next task",
        "execute next task",
        "run next",
    ]
    return any(phrase in command.lower() for phrase in next_commands)


def should_retry_failed(command):
    retry_commands = [
        "retry failed",
        "retry failed tasks",
        "re-run failed",
    ]
    return any(phrase in command.lower() for phrase in retry_commands)


def should_clear_completed(command):
    clear_commands = [
        "clear completed",
        "clear completed tasks",
        "remove completed",
        "clean queue",
    ]
    return any(phrase in command.lower() for phrase in clear_commands)


def should_build_task_plan(command):
    build_commands = [
        "build ",
        "plan tasks for",
        "create task plan",
        "break down",
        "decompose",
        "queue tasks for",
    ]
    return any(phrase in command.lower() for phrase in build_commands)


def extract_build_goal(command):
    """Extract the goal from a 'build <goal>' command."""
    import re
    prefixes = [
        r"^build\s+",
        r"^plan tasks for\s+",
        r"^create task plan for\s+",
        r"^break down\s+",
        r"^decompose\s+",
        r"^queue tasks for\s+",
    ]
    text = command.strip()
    for pattern in prefixes:
        cleaned = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
        if cleaned and cleaned != text:
            return cleaned
    return text


def build_task_plan(goal):
    """
    Ask the TaskPlanner to decompose goal, create Tasks, and load the queue.
    Returns (task_count, task_titles_list).
    """
    task_dicts = PLANNER.plan_tasks(
        goal,
        available_workers=list(WORKER_REGISTRY.keys()),
        available_skills=SKILL_MANAGER.list_skills(),
    )

    if not task_dicts:
        return 0, []

    # First pass: create tasks without dependency IDs (just titles)
    title_to_task: dict[str, Task] = {}
    for tdict in task_dicts:
        task = Task(
            title=tdict["title"],
            description=tdict["description"],
            assigned_to=tdict["assigned_to"],
            assigned_type=tdict.get("assigned_type", "worker"),
            priority=tdict.get("priority", 5),
            dependencies=[],  # filled in second pass
        )
        title_to_task[tdict["title"]] = task

    # Second pass: resolve title-based deps to task IDs
    for tdict in task_dicts:
        task = title_to_task[tdict["title"]]
        for dep_title in tdict.get("dependencies", []):
            dep_task = title_to_task.get(dep_title)
            if dep_task:
                task.dependencies.append(dep_task.id)

    # Add to queue
    for task in title_to_task.values():
        TASK_QUEUE.add(task)
    TASK_QUEUE.refresh_readiness()

    return len(title_to_task), list(title_to_task.keys())


def execute_next_task():
    """
    Execute the highest-priority READY task from TASK_QUEUE.
    Returns a descriptive string of what happened.
    """
    import time

    TASK_QUEUE.refresh_readiness()
    task = TASK_QUEUE.get_next()

    if task is None:
        if TASK_QUEUE.is_empty():
            return "Task Queue is empty. Use 'build <goal>' to create a task plan."
        pending = TASK_QUEUE.pending_count()
        if pending > 0:
            return f"No READY tasks — {pending} task(s) are waiting for dependencies."
        return "All tasks are complete or failed."

    TASK_QUEUE.update_status(task.id, TaskStatus.RUNNING)

    start = time.perf_counter()
    output = None
    error = None
    success = False

    try:
        # Build context from completed tasks
        context_parts = []
        for completed_task in TASK_QUEUE.get_all(status=TaskStatus.COMPLETED):
            if completed_task.result and completed_task.result.output:
                out = completed_task.result.output
                if hasattr(out, "combined_summary"):
                    context_parts.append(f"[{completed_task.title}]: {out.combined_summary[:200]}")

        context_prefix = ""
        if context_parts:
            context_prefix = "Prior context:\n" + "\n".join(context_parts) + "\n\n"

        full_goal = context_prefix + task.description

        if task.assigned_type == "skill":
            skill_result = SKILL_MANAGER.execute(
                task.assigned_to,
                goal=full_goal,
                worker_registry=WORKER_REGISTRY,
                orchestrator=ORCHESTRATOR,
                tool_manager=TOOL_MANAGER,
            )
            success = skill_result.success
            output = skill_result
            error = skill_result.error
        else:
            # Worker execution
            if task.assigned_to not in WORKER_REGISTRY:
                raise KeyError(f"Worker '{task.assigned_to}' not found in registry.")
            worker_report = WORKER_REGISTRY[task.assigned_to].run_lifecycle(full_goal)
            from core.worker_report import ReportStatus
            success = worker_report.status == ReportStatus.SUCCESS
            output = worker_report
            error = worker_report.error if not success else None

    except Exception as exc:
        success = False
        error = f"{type(exc).__name__}: {exc}"

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    task_result = TaskResult(
        task_id=task.id,
        task_title=task.title,
        success=success,
        output=output,
        error=error,
        execution_time_ms=elapsed_ms,
    )

    TASK_QUEUE.record_result(task.id, task_result)

    return task_result


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

    # ── Tool Registry ──────────────────────────────────────────────────────
    if should_show_tools(command):
        print()
        print(show_tools())
        return

    # ── Task Queue ─────────────────────────────────────────────────────────
    if should_show_tasks(command):
        print()
        print(TASK_QUEUE.view())
        return

    if should_run_next_task(command):
        print()
        result = execute_next_task()
        if isinstance(result, str):
            print(result)
        else:
            print(result)
            if result.success:
                print()
                print("Genesis Status")
                print(f"✓ Task '{result.task_title}' completed ({result.execution_time_ms:.0f}ms)")
                print(f"✓ {TASK_QUEUE.ready_count()} task(s) ready to run")
                print(f"✓ {TASK_QUEUE.pending_count()} task(s) waiting on dependencies")
            else:
                print()
                print("Genesis Status")
                print(f"✗ Task '{result.task_title}' failed")
                print(f"  Error: {result.error}")
                print("  Use 'retry failed tasks' to re-queue.")
        return

    if should_retry_failed(command):
        count = TASK_QUEUE.retry_failed()
        print()
        print(f"Genesis — re-queued {count} failed task(s) back to PENDING.")
        print(TASK_QUEUE.view())
        return

    if should_clear_completed(command):
        count = TASK_QUEUE.clear_completed()
        print()
        print(f"Genesis — cleared {count} completed task(s) from queue.")
        return

    if should_build_task_plan(command):
        goal = extract_build_goal(command)
        print()
        print(f"Genesis — generating task plan for: {goal}")
        print("Asking Task Planner to decompose goal…")
        task_count, titles = build_task_plan(goal)
        if task_count == 0:
            print("Task Planner could not generate tasks. Try a more specific goal.")
            return
        print()
        print(f"✓ Created {task_count} tasks:")
        for i, title in enumerate(titles, 1):
            print(f"  {i}. {title}")
        print()
        print(TASK_QUEUE.view())
        print()
        print("Genesis Status")
        print(f"✓ {task_count} tasks queued. Use 'next task' to start execution.")
        return

    # ── Skill Registry ─────────────────────────────────────────────────────
    if should_show_skills(command):
        print()
        print(show_skills())
        return

    skill_name = should_run_skill(command)
    if skill_name:
        goal = remove_skill_instruction(command, skill_name)
        if not goal:
            goal = input(
                f"What goal should the '{skill_name}' skill work on? "
            ).strip()
        if not goal:
            print(f"Skill '{skill_name}' cancelled.")
            return

        print()
        print(f"Genesis — running Skill: {skill_name}")
        print(f"Goal: {goal}")

        skill_result = SKILL_MANAGER.execute(
            skill_name,
            goal=goal,
            worker_registry=WORKER_REGISTRY,
            orchestrator=ORCHESTRATOR,
            tool_manager=TOOL_MANAGER,
        )

        print()
        print(skill_result)

        if skill_result.success and hasattr(skill_result.output, "combined_summary"):
            final_report = skill_result.output
            print()
            print("═" * 60)
            print(f"SKILL REPORT — {skill_name.replace('_', ' ').title()}")
            print("═" * 60)
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
        print(f"✓ Skill '{skill_name}' completed")
        print(f"✓ Workers used: {', '.join(skill_result.workers_used)}")
        print("✓ Founder approval is still required")
        return

    # ── Memory Governance ──────────────────────────────────────────────────
    if should_show_proposals(command):
        print()
        print(show_proposals())
        return

    if should_approve_proposals(command):
        print()
        print("Memory Governor — merging all approved proposals…")
        results = GOVERNOR.merge_all()
        for result in results:
            print(f"  {result}")
        print()
        print("Genesis Status")
        print("✓ All pending memory proposals processed.")
        print("✓ Merged proposals are now part of company_memory.md.")
        print("✓ Audit log updated in company_memory/audit_log.md.")
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

    # ── Intelligent Task Planner ────────────────────────────────────────────
    # Phase 9: All unmatched requests pass through the TaskPlanner.
    # Existing keyword routes above take priority; the planner handles
    # natural-language requests that don't match any keyword pattern.

    plan = PLANNER.plan(command)

    print()
    print(plan.summary())
    print()

    if not plan.is_actionable:
        # Planner is not confident enough — answer as a general company question
        response = answer_company_question(command)
        print("Genesis:")
        print(response)
        return

    if plan.is_multi_worker:
        # Run the full orchestration pipeline with the planner-selected sequence
        print(f"Genesis Orchestration Engine — starting planned pipeline…")
        print(f"Goal: {plan.cleaned_input}")

        final_report = ORCHESTRATOR.run(plan.cleaned_input, plan.execution_order)

        print()
        print("═" * 60)
        print("FINAL COMPANY REPORT")
        print("═" * 60)
        print()
        print(f"Workers executed: {', '.join(w.title() for w in final_report.workers_executed)}")
        if final_report.failures:
            print(f"Workers failed:   {', '.join(w.title() for w in final_report.failures)}")
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
        print(f"✓ Planner-orchestrated pipeline completed — {final_report.success_count} workers succeeded")
        if final_report.failure_count:
            print(f"⚠ {final_report.failure_count} worker(s) failed — check FinalCompanyReport")
        print("✓ FinalCompanyReport saved to orchestration_reports/")
        print("✓ Founder approval is still required")
        return

    # Single-worker plan
    worker_key = plan.execution_order[0]
    if worker_key not in WORKER_REGISTRY:
        response = answer_company_question(command)
        print("Genesis:")
        print(response)
        return

    print(f"Genesis — routing to {worker_key.title()} Worker…")
    report = WORKER_REGISTRY[worker_key].run_lifecycle(plan.cleaned_input)

    if report.status == ReportStatus.FAILURE:
        print()
        print("Genesis Status")
        print(f"✗ {worker_key.title()} Worker failed.")
        print(f"Error: {report.error}")
        return

    result, report_path = report.result
    print()
    print(f"{worker_key.title()} Worker Result:")
    print(result)
    print()
    print("Genesis Status")
    print(f"✓ {worker_key.title()} AI completed the assignment")
    print(f"✓ Report saved: {report_path}")
    print("✓ Memory proposal submitted for Founder review")
    print("✓ Founder approval is still required")


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