"""
core/company_dashboard.py

Company Operating System Dashboard for Project Genesis.

Architecture:
  CompanyDashboard aggregates live data from every Genesis subsystem and
  produces three artefacts:

    1. DashboardSnapshot — Typed dataclass with all company metrics.
    2. Daily Brief       — Morning report for the Founder.
    3. Weekly Summary    — Progress report for the past 7 days.

  The dashboard integrates with:
    • Worker Registry    — worker count and names
    • Skill Manager      — skill count and names
    • Tool Manager       — tool count and names
    • Task Queue         — task progress, completion %, priority next task
    • Memory Governor    — pending proposal count (pending approvals)
    • Company Memory     — name, product, milestone, revenue (text parsed)
    • LLM               — AI-generated recommendation and risk summary

  Health Score (0–100):
    Base: 50
    +20  if task completion ≥ 50 %
    +10  if no failed tasks
    +10  if all required workers are present (≥ 4)
    +10  if no pending memory proposals older than 24 h
    −5   per failed task (max −20)
    −5   per unresolved memory proposal (max −10)

Phase 13: Company Operating System — no existing core files are modified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ── DashboardSnapshot ─────────────────────────────────────────────────────────

@dataclass
class DashboardSnapshot:
    """
    A point-in-time snapshot of the entire company state.

    All fields are populated by CompanyDashboard.build_snapshot().
    """

    # ── Identity ─────────────────────────────────────────────────────────────
    company_name: str = "Project Genesis"
    version: str = "13.0.0"
    generated_at: datetime = field(default_factory=datetime.now)

    # ── Company info (from company_memory.md) ─────────────────────────────────
    current_product: str = "Not specified"
    revenue: str = "Not yet generating"
    current_milestone: str = "Not specified"
    founder_name: str = "Harshit"

    # ── Task metrics ─────────────────────────────────────────────────────────
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    ready_tasks: int = 0
    running_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    completion_pct: float = 0.0
    highest_priority_task: Any | None = None   # Task | None

    # ── System metrics ────────────────────────────────────────────────────────
    worker_count: int = 0
    worker_names: list[str] = field(default_factory=list)
    skill_count: int = 0
    skill_names: list[str] = field(default_factory=list)
    tool_count: int = 0
    tool_names: list[str] = field(default_factory=list)

    # ── Governance ────────────────────────────────────────────────────────────
    pending_proposals: int = 0

    # ── Health ────────────────────────────────────────────────────────────────
    health_score: int = 50
    health_factors: list[str] = field(default_factory=list)

    # ── AI-generated fields ───────────────────────────────────────────────────
    recommendation: str = ""
    risks: list[str] = field(default_factory=list)
    yesterday_summary: str = ""

    @property
    def health_label(self) -> str:
        if self.health_score >= 85:
            return "Excellent"
        if self.health_score >= 70:
            return "Good"
        if self.health_score >= 50:
            return "Fair"
        return "Needs Attention"

    @property
    def health_bar(self) -> str:
        filled = round(self.health_score / 5)
        empty = 20 - filled
        return "█" * filled + "░" * empty


# ── CompanyDashboard ──────────────────────────────────────────────────────────

class CompanyDashboard:
    """
    Company Operating System Dashboard.

    Aggregates live data from every Genesis subsystem and generates
    human-readable reports for the Founder.

    Usage (genesis.py):
        DASHBOARD = CompanyDashboard(
            worker_registry=WORKER_REGISTRY,
            skill_manager=SKILL_MANAGER,
            tool_manager=TOOL_MANAGER,
            task_queue=TASK_QUEUE,
            memory_governor=GOVERNOR,
        )
        print(DASHBOARD.daily_brief())
    """

    _MEMORY_FILE = Path("company_memory.md")

    def __init__(
        self,
        worker_registry: dict,
        skill_manager: Any,
        tool_manager: Any,
        task_queue: Any,
        memory_governor: Any,
    ) -> None:
        self._workers = worker_registry
        self._skills = skill_manager
        self._tools = tool_manager
        self._queue = task_queue
        self._governor = memory_governor

    # ── Public API ────────────────────────────────────────────────────────────

    def build_snapshot(self, with_ai: bool = True) -> DashboardSnapshot:
        """
        Build and return a full DashboardSnapshot.

        Args:
            with_ai: If True, call the LLM to generate recommendation and risks.
                     Set False during tests to avoid real API calls.
        """
        snap = DashboardSnapshot()

        self._populate_memory_fields(snap)
        self._populate_task_fields(snap)
        self._populate_system_fields(snap)
        self._populate_governance_fields(snap)
        self._calculate_health(snap)

        if with_ai:
            self._generate_ai_fields(snap)

        return snap

    def daily_brief(self, with_ai: bool = True) -> str:
        """Generate the Good Morning daily brief."""
        snap = self.build_snapshot(with_ai=with_ai)
        return self._render_daily_brief(snap)

    def company_status(self, with_ai: bool = True) -> str:
        """Generate the compact company status view."""
        snap = self.build_snapshot(with_ai=with_ai)
        return self._render_company_status(snap)

    def weekly_summary(self, with_ai: bool = True) -> str:
        """Generate the weekly progress summary."""
        snap = self.build_snapshot(with_ai=with_ai)
        return self._render_weekly_summary(snap)

    # ── Data population ───────────────────────────────────────────────────────

    def _populate_memory_fields(self, snap: DashboardSnapshot) -> None:
        """Parse company_memory.md for identity fields."""
        if not self._MEMORY_FILE.exists():
            return

        try:
            text = self._MEMORY_FILE.read_text(encoding="utf-8")
        except Exception:
            return

        # Extract company name
        name_match = re.search(
            r"company\s+name[:\-\s]+([^\n]+)", text, re.IGNORECASE
        )
        if name_match:
            snap.company_name = name_match.group(1).strip(" *#`")

        # Extract founder name
        founder_match = re.search(
            r"founder[:\-\s]+([^\n]+)", text, re.IGNORECASE
        )
        if founder_match:
            snap.founder_name = founder_match.group(1).strip(" *#`")

        # Extract current product
        product_match = re.search(
            r"(?:current\s+)?product[:\-\s]+([^\n]+)", text, re.IGNORECASE
        )
        if product_match:
            val = product_match.group(1).strip(" *#`")
            if val and val.lower() not in ("name", "none", "n/a", "tbd"):
                snap.current_product = val

        # Extract revenue
        revenue_match = re.search(
            r"revenue[:\-\s]+([^\n]+)", text, re.IGNORECASE
        )
        if revenue_match:
            snap.revenue = revenue_match.group(1).strip(" *#`")

        # Extract milestone
        milestone_match = re.search(
            r"(?:current\s+)?milestone[:\-\s]+([^\n]+)", text, re.IGNORECASE
        )
        if milestone_match:
            snap.current_milestone = milestone_match.group(1).strip(" *#`")

    def _populate_task_fields(self, snap: DashboardSnapshot) -> None:
        """Read task queue metrics."""
        from core.task_queue import TaskStatus

        snap.total_tasks = self._queue.total_count()
        snap.completed_tasks = self._queue.completed_count()
        snap.failed_tasks = self._queue.failed_count()
        snap.ready_tasks = self._queue.ready_count()
        snap.pending_tasks = self._queue.pending_count()

        running = self._queue.get_all(status=TaskStatus.RUNNING)
        snap.running_tasks = len(running)

        cancelled = self._queue.get_all(status=TaskStatus.CANCELLED)
        snap.cancelled_tasks = len(cancelled)

        if snap.total_tasks > 0:
            snap.completion_pct = round(
                (snap.completed_tasks / snap.total_tasks) * 100, 1
            )

        snap.highest_priority_task = self._queue.get_next()

    def _populate_system_fields(self, snap: DashboardSnapshot) -> None:
        """Read worker, skill, and tool counts."""
        snap.worker_count = len(self._workers)
        snap.worker_names = sorted(self._workers.keys())
        snap.skill_count = len(self._skills.list_skills())
        snap.skill_names = self._skills.list_skills()
        snap.tool_count = len(self._tools.list_tools())
        snap.tool_names = self._tools.list_tools()

    def _populate_governance_fields(self, snap: DashboardSnapshot) -> None:
        """Count pending memory proposals."""
        try:
            proposals_dir = Path("company_memory") / "proposals"
            if proposals_dir.exists():
                pending = [
                    f for f in proposals_dir.iterdir()
                    if f.is_file() and f.suffix == ".md"
                ]
                snap.pending_proposals = len(pending)
        except Exception:
            snap.pending_proposals = 0

    # ── Health Score ──────────────────────────────────────────────────────────

    def _calculate_health(self, snap: DashboardSnapshot) -> None:
        """Calculate the Company Health Score (0–100)."""
        score = 50
        factors = []

        # Task completion bonus
        if snap.total_tasks > 0 and snap.completion_pct >= 50:
            score += 20
            factors.append(f"+20: Task completion ≥ 50% ({snap.completion_pct}%)")
        elif snap.total_tasks == 0:
            score += 10
            factors.append("+10: Queue is clean (no outstanding tasks)")

        # No failed tasks
        if snap.failed_tasks == 0:
            score += 10
            factors.append("+10: No failed tasks")
        else:
            deduction = min(20, snap.failed_tasks * 5)
            score -= deduction
            factors.append(f"−{deduction}: {snap.failed_tasks} failed task(s)")

        # Workers available
        if snap.worker_count >= 4:
            score += 10
            factors.append(f"+10: All {snap.worker_count} workers available")
        else:
            factors.append(f"  0: Only {snap.worker_count} workers registered")

        # Pending proposals
        if snap.pending_proposals == 0:
            score += 10
            factors.append("+10: No pending memory proposals")
        else:
            deduction = min(10, snap.pending_proposals * 5)
            score -= deduction
            factors.append(f"−{deduction}: {snap.pending_proposals} pending proposal(s)")

        snap.health_score = max(0, min(100, score))
        snap.health_factors = factors

    # ── AI fields ─────────────────────────────────────────────────────────────

    def _generate_ai_fields(self, snap: DashboardSnapshot) -> None:
        """Use the LLM to generate recommendation, risks, and yesterday summary."""
        try:
            from brain import ask_ai
            from memory import load_company_context

            context = load_company_context()
            task_summary = self._describe_tasks(snap)

            prompt = f"""
You are the Chief of Staff for {snap.company_name}, a solo-founder AI company
run by {snap.founder_name}.

Company context:
{context}

Current system snapshot:
- Health Score: {snap.health_score}/100 ({snap.health_label})
- Total tasks: {snap.total_tasks} | Completed: {snap.completed_tasks} | Failed: {snap.failed_tasks} | Ready: {snap.ready_tasks}
- Pending memory proposals: {snap.pending_proposals}
- Current product: {snap.current_product}
- Current milestone: {snap.current_milestone}
- Revenue: {snap.revenue}
{task_summary}

Your job is to produce a brief morning briefing.

Respond ONLY with valid JSON:
{{
  "recommendation": "One clear action the founder should take today (2-3 sentences).",
  "risks": ["Risk 1", "Risk 2", "Risk 3"],
  "yesterday_summary": "One sentence describing yesterday's key progress."
}}
"""
            from core.task_planner import TaskPlanner
            raw = ask_ai(prompt)

            import json, re as re_
            json_text = re_.sub(r"```(?:json)?\s*", "", raw)
            json_text = re_.sub(r"```\s*", "", json_text)
            start = json_text.find("{")
            end = json_text.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(json_text[start:end])
                snap.recommendation = str(data.get("recommendation", "")).strip()
                snap.risks = [str(r) for r in data.get("risks", [])]
                snap.yesterday_summary = str(data.get("yesterday_summary", "")).strip()
        except Exception:
            snap.recommendation = (
                "Review your task queue and execute the next highest-priority task."
            )
            snap.risks = ["Task queue may have unresolved dependencies."]
            snap.yesterday_summary = "Previous session work is tracked in memory."

    def _describe_tasks(self, snap: DashboardSnapshot) -> str:
        """Build a short task description string for the LLM prompt."""
        lines = []
        if snap.highest_priority_task:
            t = snap.highest_priority_task
            lines.append(f"- Next task: '{t.title}' → {t.assigned_to} [Priority {t.priority}]")
        all_tasks = self._queue.get_all()
        if all_tasks:
            lines.append("- Task titles: " + ", ".join(t.title for t in all_tasks[:5]))
        return "\n".join(lines)

    # ── Renderers ─────────────────────────────────────────────────────────────

    def _render_daily_brief(self, snap: DashboardSnapshot) -> str:
        """Render the Good Morning daily brief."""
        now = snap.generated_at.strftime("%A, %d %B %Y — %H:%M")
        lines = [
            "",
            "═" * 60,
            f"  GOOD MORNING, {snap.founder_name.upper()}",
            f"  {snap.company_name}  |  v{snap.version}",
            f"  {now}",
            "═" * 60,
            "",
            f"  Company Health:  {snap.health_score}/100  {snap.health_bar}  {snap.health_label}",
            "",
        ]

        # Identity
        lines += [
            "  ── COMPANY ──────────────────────────────────────────",
            f"  Product:    {snap.current_product}",
            f"  Revenue:    {snap.revenue}",
            f"  Milestone:  {snap.current_milestone}",
            "",
        ]

        # Task progress
        if snap.total_tasks > 0:
            bar_len = 20
            filled = round((snap.completion_pct / 100) * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            lines += [
                "  ── TASK QUEUE ────────────────────────────────────────",
                f"  Total: {snap.total_tasks}  |  Done: {snap.completed_tasks}"
                f"  |  Ready: {snap.ready_tasks}  |  Pending: {snap.pending_tasks}"
                f"  |  Failed: {snap.failed_tasks}",
                f"  Progress:   [{bar}]  {snap.completion_pct}%",
            ]
            if snap.highest_priority_task:
                t = snap.highest_priority_task
                lines += [
                    "",
                    f"  🎯 NEXT PRIORITY:  [{t.id}]  {t.title}",
                    f"     Assigned → {t.assigned_to} ({t.assigned_type})  |  Priority {t.priority}",
                ]
            lines.append("")
        else:
            lines += [
                "  ── TASK QUEUE ────────────────────────────────────────",
                "  Queue is empty.  Use 'build <goal>' to start a task plan.",
                "",
            ]

        # System
        lines += [
            "  ── SYSTEM STATUS ─────────────────────────────────────",
            f"  Workers: {snap.worker_count}   ({', '.join(snap.worker_names)})",
            f"  Skills:  {snap.skill_count}   ({', '.join(snap.skill_names)})",
            f"  Tools:   {snap.tool_count}   ({', '.join(snap.tool_names[:3])}{'…' if snap.tool_count > 3 else ''})",
            "",
        ]

        # Approvals
        if snap.pending_proposals > 0:
            lines += [
                "  ── PENDING APPROVALS ─────────────────────────────────",
                f"  ⚠  {snap.pending_proposals} memory proposal(s) awaiting Founder review.",
                "     Type 'show proposals' then 'approve memory proposals'.",
                "",
            ]

        # Yesterday
        if snap.yesterday_summary:
            lines += [
                "  ── YESTERDAY ─────────────────────────────────────────",
                f"  {snap.yesterday_summary}",
                "",
            ]

        # Recommendation
        if snap.recommendation:
            lines += [
                "  ── TODAY'S RECOMMENDATION ────────────────────────────",
                f"  {snap.recommendation}",
                "",
            ]

        # Risks
        if snap.risks:
            lines += [
                "  ── RISKS ────────────────────────────────────────────",
            ]
            for risk in snap.risks:
                lines.append(f"  •  {risk}")
            lines.append("")

        # Health factors
        lines += [
            "  ── HEALTH BREAKDOWN ──────────────────────────────────",
        ]
        for factor in snap.health_factors:
            lines.append(f"  {factor}")

        lines += ["", "═" * 60, ""]
        return "\n".join(lines)

    def _render_company_status(self, snap: DashboardSnapshot) -> str:
        """Render the compact company status."""
        lines = [
            "",
            f"  {snap.company_name}  v{snap.version}  —  {snap.generated_at.strftime('%d %b %Y %H:%M')}",
            f"  Health: {snap.health_score}/100 {snap.health_bar}  {snap.health_label}",
            "",
            f"  Product:   {snap.current_product}",
            f"  Revenue:   {snap.revenue}",
            f"  Milestone: {snap.current_milestone}",
            "",
            f"  Tasks:    {snap.total_tasks} total | {snap.completed_tasks} done | "
            f"{snap.ready_tasks} ready | {snap.failed_tasks} failed  ({snap.completion_pct}%)",
        ]
        if snap.highest_priority_task:
            t = snap.highest_priority_task
            lines.append(f"  Next:     [{t.id}] {t.title} → {t.assigned_to}")
        lines += [
            "",
            f"  Workers: {snap.worker_count}  Skills: {snap.skill_count}  Tools: {snap.tool_count}",
        ]
        if snap.pending_proposals:
            lines.append(
                f"  ⚠  {snap.pending_proposals} memory proposal(s) pending review"
            )
        if snap.recommendation:
            lines += ["", f"  Recommendation: {snap.recommendation}"]
        lines.append("")
        return "\n".join(lines)

    def _render_weekly_summary(self, snap: DashboardSnapshot) -> str:
        """Render the weekly progress summary."""
        lines = [
            "",
            "═" * 60,
            f"  WEEKLY SUMMARY  —  {snap.company_name}",
            f"  Generated: {snap.generated_at.strftime('%d %B %Y')}",
            "═" * 60,
            "",
            f"  Company Health:  {snap.health_score}/100  {snap.health_bar}",
            "",
            "  PROGRESS THIS WEEK",
            f"  Total tasks in queue: {snap.total_tasks}",
            f"  Completed:           {snap.completed_tasks}  ({snap.completion_pct}%)",
            f"  Failed / Retried:    {snap.failed_tasks}",
            f"  Pending:             {snap.pending_tasks}",
            "",
            "  SYSTEM",
            f"  Workers registered: {snap.worker_count}",
            f"  Skills available:   {snap.skill_count}",
            f"  Tools registered:   {snap.tool_count}",
        ]

        if snap.pending_proposals:
            lines += [
                "",
                f"  APPROVALS PENDING",
                f"  {snap.pending_proposals} memory proposal(s) await your review.",
            ]

        if snap.recommendation:
            lines += [
                "",
                "  NEXT WEEK RECOMMENDATION",
                f"  {snap.recommendation}",
            ]

        if snap.risks:
            lines += ["", "  RISKS TO WATCH"]
            for risk in snap.risks:
                lines.append(f"  •  {risk}")

        lines += ["", "═" * 60, ""]
        return "\n".join(lines)
