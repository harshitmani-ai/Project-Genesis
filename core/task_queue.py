"""
core/task_queue.py

Autonomous Task Queue for Project Genesis.

Architecture:
  The Task Queue allows Genesis to decompose a large founder goal into a
  sequence of individually tracked tasks.  Each task is assigned to a specific
  worker or skill, carries dependencies on other tasks, and moves through a
  well-defined lifecycle.

  ┌──────────────────────────────────────────────────────────────┐
  │  Large Goal (founder input)                                  │
  │       │                                                      │
  │       ▼                                                      │
  │  TaskPlanner.plan_tasks()   ← LLM decomposes goal           │
  │       │                                                      │
  │  ┌────▼────────────────────────────────────────────────┐    │
  │  │              TaskQueue                               │    │
  │  │                                                      │    │
  │  │  Task(id, title, assigned_to, priority, deps, ...)  │    │
  │  │  Task(...)                                           │    │
  │  │  Task(...)                                           │    │
  │  └────┬────────────────────────────────────────────────┘    │
  │       │  get_next() → highest priority READY task            │
  │       ▼                                                      │
  │  Worker / Skill execute                                      │
  │       │                                                      │
  │  TaskResult → feeds context into next task                   │
  └──────────────────────────────────────────────────────────────┘

Components:
  TaskStatus  — Lifecycle states for a task.
  Task        — A single unit of work with full tracking metadata.
  TaskResult  — Standardised output from executing a single task.
  TaskQueue   — The ordered, dependency-aware work queue.

Dependency rules:
  A task moves to READY once ALL tasks in its `dependencies` list have
  status COMPLETED.  A task with no dependencies is READY immediately.

Priority ordering:
  Lower integer = higher priority.  Tasks with priority 1 run before
  tasks with priority 5.  Equal-priority tasks are ordered by creation time.

Phase 12: Autonomous Task Queue — No existing core files are modified.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ── TaskStatus ─────────────────────────────────────────────────────────────────

class TaskStatus(Enum):
    """Lifecycle states for a Task."""
    PENDING   = "pending"    # waiting on dependencies
    READY     = "ready"      # dependencies met, can run
    RUNNING   = "running"    # currently executing
    COMPLETED = "completed"  # finished successfully
    FAILED    = "failed"     # execution failed
    CANCELLED = "cancelled"  # removed by founder


# ── TaskResult ─────────────────────────────────────────────────────────────────

@dataclass
class TaskResult:
    """
    Standardised return value from executing a single Task.

    Fields:
        task_id           — ID of the task that was executed.
        task_title        — Human-readable title.
        success           — True if execution completed without error.
        output            — Primary output (WorkerReport, SkillResult, text…).
        error             — Error message if success is False, else None.
        execution_time_ms — Wall-clock time for execution.
    """

    task_id: str
    task_title: str
    success: bool
    output: Any
    error: str | None = None
    execution_time_ms: float = 0.0

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return (
            f"[{status}] Task '{self.task_title}' "
            f"({self.execution_time_ms:.0f}ms)"
            + (f" — {self.error}" if self.error else "")
        )


# ── Task ───────────────────────────────────────────────────────────────────────

@dataclass
class Task:
    """
    A single unit of work in the Task Queue.

    Fields:
        id            — Unique UUID4-based identifier (auto-generated).
        title         — Short, human-readable name.
        description   — Full description passed as the worker/skill goal.
        assigned_to   — Worker key (e.g. "research") or skill name.
        assigned_type — "worker" | "skill"
        priority      — Integer 1–10; 1 = highest priority.
        dependencies  — List of Task IDs that must be COMPLETED first.
        status        — Current TaskStatus.
        created_at    — Timestamp when the Task was created.
        started_at    — Timestamp when execution began (None until then).
        completed_at  — Timestamp when execution finished (None until then).
        result        — TaskResult if completed/failed, else None.
        context       — Arbitrary key/value metadata (e.g. prior task output).
    """

    title: str
    description: str
    assigned_to: str
    assigned_type: str = "worker"   # "worker" | "skill"
    priority: int = 5               # 1 (highest) – 10 (lowest)
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: TaskResult | None = None
    context: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def __post_init__(self) -> None:
        # Clamp priority
        self.priority = max(1, min(10, self.priority))
        # Validate assigned_type
        if self.assigned_type not in ("worker", "skill", "connector"):
            self.assigned_type = "worker"

    @property
    def is_done(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)

    @property
    def duration_ms(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    def status_icon(self) -> str:
        icons = {
            TaskStatus.PENDING:   "⏳",
            TaskStatus.READY:     "🟢",
            TaskStatus.RUNNING:   "⚙",
            TaskStatus.COMPLETED: "✓",
            TaskStatus.FAILED:    "✗",
            TaskStatus.CANCELLED: "✘",
        }
        return icons.get(self.status, "?")

    def summary(self) -> str:
        dep_str = f" (deps: {', '.join(self.dependencies)})" if self.dependencies else ""
        return (
            f"{self.status_icon()} [{self.id}] P{self.priority} "
            f"{self.title} → {self.assigned_to}{dep_str}"
        )


# ── TaskQueue ──────────────────────────────────────────────────────────────────

class TaskQueue:
    """
    Dependency-aware, priority-ordered task queue.

    Usage:
        queue = TaskQueue()
        t1 = Task(title="Research", description="…", assigned_to="research")
        t2 = Task(title="Finance", description="…", assigned_to="finance",
                  dependencies=[t1.id])
        queue.add(t1)
        queue.add(t2)
        queue.refresh_readiness()        # updates PENDING → READY
        next_task = queue.get_next()     # returns t1 (no deps, priority 5)
    """

    def __init__(self) -> None:
        # Ordered insertion dict: task.id → Task
        self._tasks: dict[str, Task] = {}

    # ── Mutation ───────────────────────────────────────────────────────────────

    def add(self, task: Task) -> str:
        """
        Add a task to the queue.

        Auto-promotes to READY if it has no unmet dependencies.
        Returns the task's ID.
        """
        if not isinstance(task, Task):
            raise TypeError(
                f"Expected a Task instance, got {type(task).__name__}"
            )
        if task.id in self._tasks:
            raise ValueError(f"Task ID '{task.id}' already exists in queue.")

        self._tasks[task.id] = task
        self._refresh_task_readiness(task)
        return task.id

    def remove(self, task_id: str) -> bool:
        """Remove a task by ID.  Returns True if removed, False if not found."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def cancel(self, task_id: str) -> bool:
        """Cancel a task (marks as CANCELLED).  Returns False if not found."""
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        return True

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        """
        Update a task's status.  Automatically refreshes downstream readiness.
        """
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task '{task_id}' not found.")
        task.status = status
        if status == TaskStatus.RUNNING and task.started_at is None:
            task.started_at = datetime.now()
        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            task.completed_at = datetime.now()
        # If a task completed, downstream tasks may now be READY
        if status == TaskStatus.COMPLETED:
            self.refresh_readiness()

    def record_result(self, task_id: str, result: TaskResult) -> None:
        """Store the execution result on a task and mark it COMPLETED or FAILED."""
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task '{task_id}' not found.")
        task.result = result
        new_status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.update_status(task_id, new_status)

    # ── Readiness management ──────────────────────────────────────────────────

    def refresh_readiness(self) -> None:
        """
        Scan all PENDING tasks and promote to READY those whose
        dependencies are fully COMPLETED.
        """
        for task in self._tasks.values():
            self._refresh_task_readiness(task)

    def _refresh_task_readiness(self, task: Task) -> None:
        if task.status not in (TaskStatus.PENDING,):
            return
        if not task.dependencies:
            task.status = TaskStatus.READY
            return
        all_done = all(
            self._tasks.get(dep_id, None) is not None
            and self._tasks[dep_id].status == TaskStatus.COMPLETED
            for dep_id in task.dependencies
        )
        if all_done:
            task.status = TaskStatus.READY

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, task_id: str) -> Task | None:
        """Return the Task for a given ID, or None."""
        return self._tasks.get(task_id)

    def get_next(self) -> Task | None:
        """
        Return the highest-priority READY task.
        Tiebreaker: earliest creation time.
        """
        ready = [t for t in self._tasks.values() if t.status == TaskStatus.READY]
        if not ready:
            return None
        return min(ready, key=lambda t: (t.priority, t.created_at))

    def get_all(self, status: TaskStatus | None = None) -> list[Task]:
        """Return tasks in priority order, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: (t.priority, t.created_at))

    def retry_failed(self) -> int:
        """
        Re-queue all FAILED tasks back to PENDING, then refresh readiness.
        Returns the number of tasks re-queued.
        """
        count = 0
        for task in self._tasks.values():
            if task.status == TaskStatus.FAILED:
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.completed_at = None
                task.result = None
                count += 1
        if count > 0:
            self.refresh_readiness()
        return count

    def clear_completed(self) -> int:
        """
        Remove all COMPLETED tasks from the queue.
        Returns the number removed.
        """
        completed_ids = [
            tid for tid, t in self._tasks.items()
            if t.status == TaskStatus.COMPLETED
        ]
        for tid in completed_ids:
            del self._tasks[tid]
        return len(completed_ids)

    def pending_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

    def ready_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.READY)

    def completed_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)

    def failed_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)

    def total_count(self) -> int:
        return len(self._tasks)

    def is_empty(self) -> bool:
        return len(self._tasks) == 0

    # ── Display ───────────────────────────────────────────────────────────────

    def view(self) -> str:
        """Return a human-readable snapshot of the entire queue."""
        if self.is_empty():
            return "Task Queue is empty. Use 'build <goal>' to create a task plan."

        lines = [
            f"Task Queue ({self.total_count()} tasks)",
            f"  Ready: {self.ready_count()}  |  Pending: {self.pending_count()}  "
            f"|  Completed: {self.completed_count()}  |  Failed: {self.failed_count()}",
            "",
        ]

        # Group by status for clarity
        order = [
            TaskStatus.RUNNING,
            TaskStatus.READY,
            TaskStatus.PENDING,
            TaskStatus.FAILED,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
        ]
        for status in order:
            group = self.get_all(status=status)
            if not group:
                continue
            lines.append(f"  {status.value.upper()}")
            for task in group:
                lines.append(f"    {task.summary()}")
                if task.result and not task.result.success and task.result.error:
                    lines.append(f"      Error: {task.result.error[:80]}")
            lines.append("")

        return "\n".join(lines).rstrip()
