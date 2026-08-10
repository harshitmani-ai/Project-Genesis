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
from core.company_dashboard import CompanyDashboard
from core.autopilot import AutoPilotEngine
from core.connector_manager import DEFAULT_CONNECTOR_MANAGER, ConnectorManager
from core.report_manager import ReportManager


COMPANY_MEMORY_FILE = Path("company_memory.md")
REPORTS_FOLDER = Path("research_reports")
REPORT_MANAGER = ReportManager()

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

TASK_QUEUE = TaskQueue("company_memory/task_queue.json")

# ── Company Dashboard ───────────────────────────────────────────────
# Phase 13: Company Operating System dashboard.

DASHBOARD = CompanyDashboard(
    worker_registry=WORKER_REGISTRY,
    skill_manager=SKILL_MANAGER,
    tool_manager=TOOL_MANAGER,
    task_queue=TASK_QUEUE,
    memory_governor=GOVERNOR,
)

# ── Auto-Pilot Engine ───────────────────────────────────────────────
# Phase 14: Autonomous execution loop for task queue automation.

AUTOPILOT = AutoPilotEngine(
    task_queue=TASK_QUEUE,
    executor_fn=lambda: execute_next_task(),
    dashboard=DASHBOARD,
)

# ── Connector Framework ─────────────────────────────────────────────
# Phase V2: Decoupled connector framework for Antigravity, ChatGPT, etc.

CONNECTOR_MANAGER = DEFAULT_CONNECTOR_MANAGER
_connectors_loaded = CONNECTOR_MANAGER.discover()



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


def is_proposal_command(command: str) -> bool:
    """Return True if command is any local proposal management command."""
    cmd = command.lower().strip()
    return ("proposal" in cmd or "proposals" in cmd) and not is_report_command(cmd)


def is_report_command(command: str) -> bool:
    """Return True if command is a request to open, view, or read a specific report file."""
    cmd = command.lower().strip()
    if cmd in {"latest report", "open latest report", "show latest report", "read latest report", "latest"}:
        return True
    triggers = [
        "show report",
        "open report",
        "read report",
        "view report",
        "display report",
        "get report",
    ]
    return any(cmd.startswith(t) for t in triggers)


def extract_report_identifier(command: str) -> tuple[str, int | None]:
    """Extract report identifier (full name, stem, number, or 'latest') and optional choice index."""
    cmd = command.strip()
    cmd_lower = cmd.lower()

    if cmd_lower in {"latest report", "open latest report", "show latest report", "read latest report", "latest"}:
        return "latest", None

    prefixes = [
        "show report",
        "open report",
        "read report",
        "view report",
        "display report",
        "get report",
    ]
    raw = cmd
    for p in prefixes:
        if cmd_lower.startswith(p):
            raw = cmd[len(p):].strip()
            break

    tokens = raw.split()
    if not tokens:
        return "latest", None

    choice_idx = None
    if len(tokens) >= 2 and tokens[-1].isdigit():
        try:
            choice_idx = int(tokens[-1])
            tokens = tokens[:-1]
        except ValueError:
            pass

    identifier = " ".join(tokens).strip()
    return identifier, choice_idx


def extract_proposal_identifier(command: str) -> str:
    """Extract proposal index or filename from command string."""
    cmd = command.strip()
    parts = cmd.split("proposal", 1)
    if len(parts) > 1:
        specifier = parts[1].strip()
        tokens = specifier.split()
        if tokens:
            return tokens[0]
    return ""


def should_review_single_proposal(command: str) -> bool:
    """Return True if command asks to review/show/view a specific proposal (e.g. 'review proposal 1')."""
    cmd = command.lower().strip()
    triggers = ["review proposal", "show proposal", "view proposal", "read proposal"]
    if any(t in cmd for t in triggers):
        id_str = extract_proposal_identifier(cmd)
        if id_str and id_str != "s" and id_str != "all":
            return True
    return False


def should_approve_single_proposal(command: str) -> bool:
    """Return True if command asks to approve a single proposal (e.g. 'approve proposal 1')."""
    cmd = command.lower().strip()
    if "approve proposal" in cmd or "merge proposal" in cmd:
        id_str = extract_proposal_identifier(cmd)
        if id_str and id_str != "s" and id_str != "all":
            return True
    return False


def should_reject_single_proposal(command: str) -> bool:
    """Return True if command asks to reject a single proposal (e.g. 'reject proposal 2')."""
    cmd = command.lower().strip()
    if "reject proposal" in cmd or "deny proposal" in cmd:
        id_str = extract_proposal_identifier(cmd)
        if id_str and id_str != "s" and id_str != "all":
            return True
    return False


def should_review_all_proposals(command: str) -> bool:
    """Return True if command requests the full Proposal Review Dashboard ('review all proposals')."""
    cmd = command.lower().strip()
    triggers = [
        "review all proposals",
        "proposal dashboard",
        "proposals dashboard",
        "review proposals dashboard",
        "show proposal dashboard",
        "view proposal dashboard",
    ]
    return any(t in cmd for t in triggers)


def should_approve_selected_proposals(command: str) -> bool:
    """Return True if command requests batch approval of selected proposals ('approve selected 1,2,4,5')."""
    cmd = command.lower().strip()
    return "approve selected" in cmd or "approve select" in cmd or "merge selected" in cmd


def should_reject_selected_proposals(command: str) -> bool:
    """Return True if command requests batch rejection of selected proposals ('reject selected 3,6,8')."""
    cmd = command.lower().strip()
    return "reject selected" in cmd or "reject select" in cmd or "deny selected" in cmd


def extract_selected_indices(command: str) -> list[int]:
    """
    Extract a list of 1-based integer proposal indices from a command string.
    Supports 'approve selected 1,2,4,5', 'approve selected 1 2 4 5', 'reject selected 3, 6, 8'.
    """
    import re
    raw_nums = re.findall(r"\d+", command)
    indices = []
    for num_str in raw_nums:
        try:
            val = int(num_str)
            if val > 0 and val not in indices:
                indices.append(val)
        except ValueError:
            pass
    return indices


def should_reject_all_proposals(command: str) -> bool:
    """Return True if command asks to reject all proposals."""
    cmd = command.lower().strip()
    triggers = ["reject all proposals", "reject proposals all", "deny all proposals"]
    return any(t in cmd for t in triggers)


def should_show_proposals(command: str) -> bool:
    proposal_commands = [
        "show proposals",
        "list proposals",
        "pending proposals",
        "memory proposals",
        "show memory proposals",
        "review proposals",
        "proposals",
    ]
    command_lower = command.lower().strip()
    return any(phrase == command_lower or phrase in command_lower for phrase in proposal_commands)


def should_approve_proposals(command: str) -> bool:
    approve_commands = [
        "approve proposals",
        "approve memory proposals",
        "merge proposals",
        "commit proposals",
        "approve all proposals",
    ]
    command_lower = command.lower().strip()
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


def sync_git_artifacts() -> None:
    """Automatically stage generated report files, proposals, and queue persistence in Git so status stays clean."""
    import glob
    import subprocess
    patterns = [
        "research_reports/*.md",
        "acquisition_reports/*.md",
        "marketing_reports/*.md",
        "finance_reports/*.md",
        "orchestration_reports/*.md",
        "company_memory/proposals/*.md",
        "company_memory/audit_log.md",
        "company_memory.md",
        "company_memory/task_queue.json",
    ]
    files_to_add = []
    for pat in patterns:
        files_to_add.extend(glob.glob(pat))
    if files_to_add:
        try:
            subprocess.run(["git", "add"] + files_to_add, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def build_task_plan(goal):
    """
    Ask the TaskPlanner to decompose goal, create Tasks, and load the queue.
    If the queue is not empty, reuse existing tasks to prevent duplicate task planning.
    Returns (task_count, task_titles_list).
    """
    # Deduplication check: reuse existing tasks if queue is not empty
    if not TASK_QUEUE.is_empty():
        all_tasks = TASK_QUEUE.get_all()
        return len(all_tasks), [t.title for t in all_tasks]

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
    sync_git_artifacts()

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
        elif task.assigned_type == "connector":
            conn_result = CONNECTOR_MANAGER.send_task(
                connector_name=task.assigned_to,
                action="execute",
                payload={"goal": full_goal},
            )
            success = conn_result.success
            output = conn_result
            error = conn_result.error
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
    sync_git_artifacts()

    return task_result


# ── Phase 13: Company Dashboard helpers ──────────────────────────────────────

def should_show_dashboard(command):
    """Return True for any explicit morning / dashboard / status greeting commands."""
    cmd = command.lower().strip()
    if is_proposal_command(cmd) or "founder directive" in cmd or cmd.startswith("founder directive"):
        return False

    exact_triggers = {
        "good morning genesis",
        "good morning",
        "morning genesis",
        "company status",
        "show dashboard",
        "dashboard",
        "today",
        "show status",
        "company overview",
        "what's our status",
        "how are we doing",
        "status",
    }
    if cmd in exact_triggers:
        return True

    prefix_triggers = [
        "good morning",
        "company status",
        "show dashboard",
        "company overview",
        "what's our status",
        "how are we doing",
    ]
    return any(cmd.startswith(prefix) for prefix in prefix_triggers)


def should_show_weekly_summary(command):
    weekly_triggers = [
        "weekly summary",
        "weekly report",
        "week summary",
        "this week",
        "show weekly",
    ]
    cmd = command.lower().strip()
    return any(trigger in cmd for trigger in weekly_triggers)


# ── Phase 14: Auto-Pilot helpers ─────────────────────────────────────────────

def should_run_autopilot(command):
    triggers = [
        "autopilot",
        "run autopilot",
        "start autopilot",
        "auto run",
        "auto pilot",
    ]
    cmd = command.lower().strip()
    return any(trigger == cmd or trigger in cmd for trigger in triggers) and not should_show_autopilot(command)


def should_show_autopilot(command):
    triggers = [
        "autopilot status",
        "show autopilot",
        "status autopilot",
    ]
    cmd = command.lower().strip()
    return any(trigger in cmd for trigger in triggers)


def should_show_connectors(command):
    triggers = [
        "show connectors",
        "list connectors",
        "connector status",
        "connectors",
    ]
    cmd = command.lower().strip()
    return any(trigger in cmd for trigger in triggers)


def show_connectors():
    return CONNECTOR_MANAGER.connectors_summary()



def run_autopilot_mode(max_steps=50):
    """Run the Auto-Pilot loop and output results to the founder."""
    print()
    print("═" * 60)
    print("  GENESIS AUTO-PILOT ENGINE  —  AUTONOMOUS EXECUTION MODE")
    print("═" * 60)
    print()

    result = AUTOPILOT.run(max_steps=max_steps, stop_on_failure=True, verbose=True)

    print()
    print("═" * 60)
    print(f"AUTO-PILOT SUMMARY: {result.status.value.upper()}")
    print(f"Executed: {result.tasks_completed}/{result.steps_executed} tasks succeeded ({result.total_time_ms:.0f}ms)")
    print(f"Message:  {result.message}")
    print("═" * 60)
    print()

    return result


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
    # ── Dashboard (Phase 13) ────────────────────────────────────────────────
    # Check weekly summary FIRST (it's a sub-case of "today"/"this week")
    if should_show_weekly_summary(command):
        print()
        print(DASHBOARD.weekly_summary(with_ai=True))
        return

    # ── Auto-Pilot (Phase 14) ───────────────────────────────────────────────
    if should_show_autopilot(command):
        print()
        print(AUTOPILOT.summary())
        return

    if should_run_autopilot(command):
        run_autopilot_mode()
        return

    if should_show_dashboard(command):
        print()
        print(DASHBOARD.daily_brief(with_ai=True))
        return


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

    # ── Connector Framework (V2 Upgrade) ───────────────────────────────────
    if should_show_connectors(command):
        print()
        print(show_connectors())
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

    # ── Memory Governance (Local ProposalManager — Zero LLM Calls) ─────────
    if should_review_all_proposals(command):
        print()
        print(GOVERNOR.build_proposal_dashboard())
        return

    if should_approve_selected_proposals(command):
        indices = extract_selected_indices(command)
        print()
        print(f"ProposalManager — approving selected proposals {indices}...")
        results = GOVERNOR.approve_selected(indices)
        for res in results:
            print(f"  {res}")
        return

    if should_reject_selected_proposals(command):
        indices = extract_selected_indices(command)
        print()
        print(f"ProposalManager — rejecting selected proposals {indices}...")
        results = GOVERNOR.reject_selected(indices)
        for res in results:
            print(f"  {res}")
        return

    if should_review_single_proposal(command):
        proposal_id = extract_proposal_identifier(command)
        print()
        print(GOVERNOR.review_proposal(proposal_id))
        return




    if should_approve_single_proposal(command):
        proposal_id = extract_proposal_identifier(command)
        print()
        print("ProposalManager — approving proposal...")
        res = GOVERNOR.approve_single(proposal_id)
        print(f"  {res}")
        return

    if should_reject_single_proposal(command):
        proposal_id = extract_proposal_identifier(command)
        print()
        print("ProposalManager — rejecting proposal...")
        res = GOVERNOR.reject_single(proposal_id)
        print(f"  {res}")
        return

    if should_reject_all_proposals(command):
        print()
        print("ProposalManager — rejecting all pending proposals...")
        results = GOVERNOR.reject_all()
        for result in results:
            print(f"  {result}")
        return

    if should_show_proposals(command):
        print()
        print(show_proposals())
        return

    if should_approve_proposals(command):
        print()
        print("ProposalManager — merging all approved proposals…")
        results = GOVERNOR.merge_all()
        for result in results:
            print(f"  {result}")
        print()
        print("Genesis Status")
        print("✓ All pending memory proposals processed.")
        print("✓ Merged proposals are now part of company_memory.md.")
        print("✓ Audit log updated in company_memory/audit_log.md.")
        return

    if is_proposal_command(command):
        # Fallback for any other proposal command: handle locally with 0 LLM calls
        print()
    if is_report_command(command):
        identifier, choice_idx = extract_report_identifier(command)
        print()
        print(REPORT_MANAGER.open_report(identifier, choice_index=choice_idx))
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


def is_system_command(command: str) -> bool:
    """Return True if command is a single-line system, governance, status, or task command."""
    cmd = command.lower().strip()
    if "founder directive" in cmd or cmd.startswith("founder directive"):
        return False
    return (
        is_proposal_command(cmd)
        or is_report_command(cmd)
        or should_review_all_proposals(cmd)
        or should_approve_selected_proposals(cmd)
        or should_reject_selected_proposals(cmd)
        or should_show_dashboard(cmd)
        or should_show_weekly_summary(cmd)
        or should_show_autopilot(cmd)
        or should_run_autopilot(cmd)
        or should_show_memory(cmd)
        or should_show_reports(cmd)
        or should_show_tools(cmd)
        or should_show_connectors(cmd)
        or should_show_tasks(cmd)
        or should_run_next_task(cmd)
        or should_retry_failed(cmd)
        or should_clear_completed(cmd)
        or should_show_skills(cmd)
    )



def get_multiline_input():
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

    # Execute system/governance commands immediately on Enter
    if is_system_command(first_line):
        return first_line

    # If single-line entry ends with explicit END marker
    if first_line.endswith(" END") or first_line.endswith("\tEND"):
        return first_line[:-3].strip()

    # Multiline directive: collect all lines until 'END' is typed on a new line
    lines = [first_line]
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
    print("Type 'END' on a new line to send multiline messages.")
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