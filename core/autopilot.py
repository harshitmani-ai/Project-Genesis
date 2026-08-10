"""
core/autopilot.py

Autonomous Auto-Pilot Engine for Project Genesis.

Architecture:
  The Auto-Pilot Engine orchestrates the continuous, unassisted execution of the
  Autonomous Task Queue (Phase 12), leveraging the Task Planner (Phase 9),
  Skill System (Phase 11), Tool Manager (Phase 10), Memory Governor (Phase 8),
  Worker Orchestrator (Phase 7), and Company Dashboard (Phase 13).

  ┌─────────────────────────────────────────────────────────────┐
  │  Founder: "run autopilot" or "autopilot"                    │
  │       │                                                     │
  │       ▼                                                     │
  │  AutoPilotEngine.run()                                      │
  │       │                                                     │
  │       ├── 1. Refresh TaskQueue readiness                   │
  │       ├── 2. Loop get_next() task until queue empty        │
  │       │      or max_steps reached or unrecoverable failure │
  │       ├── 3. Execute task via execute_next_task()          │
  │       ├── 4. Collect step results                          │
  │       └── 5. Produce AutoPilotResult & update Dashboard     │
  └─────────────────────────────────────────────────────────────┘

Components:
  AutoPilotStatus  — Lifecycle states (IDLE, RUNNING, PAUSED, COMPLETED, FAILED, STOPPED).
  AutoPilotResult  — Standardised summary object of an auto-pilot execution run.
  AutoPilotEngine  — The execution loop engine.

Phase 14: Autonomous Auto-Pilot Engine — No existing core files are modified.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


# ── AutoPilotStatus ───────────────────────────────────────────────────────────

class AutoPilotStatus(Enum):
    """Lifecycle states for the AutoPilotEngine."""
    IDLE      = "idle"       # Ready to start
    RUNNING   = "running"    # Currently executing task queue loop
    PAUSED    = "paused"     # Paused by founder request or max_steps limit
    COMPLETED = "completed"  # All ready tasks executed successfully
    FAILED    = "failed"     # Stopped due to task failure (stop_on_failure=True)
    STOPPED   = "stopped"    # Manually stopped by founder or empty queue


# ── AutoPilotResult ───────────────────────────────────────────────────────────

@dataclass
class AutoPilotResult:
    """
    Standardised summary object returned by AutoPilotEngine.run().

    Fields:
        status            — Final AutoPilotStatus.
        steps_executed    — Number of tasks executed during this run.
        tasks_completed   — Number of tasks that succeeded.
        tasks_failed      — Number of tasks that failed.
        total_time_ms     — Total wall-clock time for the run.
        step_results      — List of individual TaskResult objects.
        message           — Readable summary message.
        stopped_at_task   — ID of task that caused stop (if failed/stopped).
    """

    status: AutoPilotStatus
    steps_executed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_time_ms: float = 0.0
    step_results: list[Any] = field(default_factory=list)
    message: str = ""
    stopped_at_task: str | None = None

    def __str__(self) -> str:
        icon = "✓" if self.status in (AutoPilotStatus.COMPLETED, AutoPilotStatus.IDLE) else "⚠" if self.status == AutoPilotStatus.PAUSED else "✗"
        return (
            f"[{icon}] Auto-Pilot {self.status.value.upper()}: "
            f"{self.tasks_completed}/{self.steps_executed} tasks succeeded "
            f"({self.total_time_ms:.0f}ms) — {self.message}"
        )


# ── AutoPilotEngine ───────────────────────────────────────────────────────────

class AutoPilotEngine:
    """
    Autonomous Execution Engine for Project Genesis.

    Loops through the TaskQueue, automatically executing ready tasks in order
    of priority and dependency, passing context down the pipeline, and updating
    the CompanyDashboard.

    Usage:
        autopilot = AutoPilotEngine(
            task_queue=TASK_QUEUE,
            executor_fn=execute_next_task,
            dashboard=DASHBOARD,
        )
        result = autopilot.run(max_steps=10, stop_on_failure=True)
    """

    def __init__(
        self,
        task_queue: Any,
        executor_fn: Callable[[], Any],
        dashboard: Any | None = None,
    ) -> None:
        self._queue = task_queue
        self._executor_fn = executor_fn
        self._dashboard = dashboard
        self._status = AutoPilotStatus.IDLE
        self._last_result: AutoPilotResult | None = None

    @property
    def status(self) -> AutoPilotStatus:
        """Return current status of the engine."""
        return self._status

    @property
    def last_result(self) -> AutoPilotResult | None:
        """Return the result of the most recent run."""
        return self._last_result

    def run(
        self,
        max_steps: int = 50,
        stop_on_failure: bool = True,
        verbose: bool = False,
    ) -> AutoPilotResult:
        """
        Execute the auto-pilot loop.

        Args:
            max_steps:       Maximum number of tasks to execute in one run.
            stop_on_failure: If True, halt immediately if any task fails.
            verbose:         If True, print live progress updates.

        Returns:
            An AutoPilotResult describing the outcome of the run.
        """
        start_time = time.perf_counter()
        self._status = AutoPilotStatus.RUNNING

        steps_executed = 0
        tasks_completed = 0
        tasks_failed = 0
        step_results = []
        stopped_at_task = None
        final_message = ""

        if self._queue.is_empty():
            self._status = AutoPilotStatus.STOPPED
            elapsed = round((time.perf_counter() - start_time) * 1000, 2)
            result = AutoPilotResult(
                status=AutoPilotStatus.STOPPED,
                steps_executed=0,
                tasks_completed=0,
                tasks_failed=0,
                total_time_ms=elapsed,
                message="Queue is empty. Use 'build <goal>' to queue tasks.",
            )
            self._last_result = result
            return result

        while steps_executed < max_steps:
            self._queue.refresh_readiness()
            next_task = self._queue.get_next()

            if next_task is None:
                # No more READY tasks
                pending = self._queue.pending_count()
                if pending > 0:
                    final_message = f"Paused: {pending} task(s) waiting on dependencies or blocked."
                    self._status = AutoPilotStatus.PAUSED
                else:
                    final_message = "All queue tasks completed successfully!"
                    self._status = AutoPilotStatus.COMPLETED
                break

            if verbose:
                print(f"[Auto-Pilot Step {steps_executed + 1}] Executing: {next_task.title} → {next_task.assigned_to}")

            # Execute step via task execution function
            step_result = self._executor_fn()

            # Handle execution result
            if isinstance(step_result, str):
                # String return indicates queue empty / message
                final_message = step_result
                self._status = AutoPilotStatus.STOPPED
                break

            step_results.append(step_result)
            steps_executed += 1

            if hasattr(step_result, "success") and step_result.success:
                tasks_completed += 1
                if verbose:
                    print(f"  ✓ {step_result}")
            else:
                tasks_failed += 1
                stopped_at_task = getattr(step_result, "task_id", None)
                err_msg = getattr(step_result, "error", "Execution failed")
                if verbose:
                    print(f"  ✗ {step_result}")

                if stop_on_failure:
                    self._status = AutoPilotStatus.FAILED
                    final_message = f"Stopped on task failure: {err_msg}"
                    break

        if steps_executed >= max_steps and self._status == AutoPilotStatus.RUNNING:
            self._status = AutoPilotStatus.PAUSED
            final_message = f"Reached max_steps limit ({max_steps}). Use 'autopilot' to continue."

        elapsed_total = round((time.perf_counter() - start_time) * 1000, 2)

        result = AutoPilotResult(
            status=self._status,
            steps_executed=steps_executed,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            total_time_ms=elapsed_total,
            step_results=step_results,
            message=final_message,
            stopped_at_task=stopped_at_task,
        )

        self._last_result = result
        try:
            from genesis import sync_git_artifacts
            sync_git_artifacts()
        except Exception:
            pass

        return result

    def summary(self) -> str:
        """Return a human-readable string representation of current engine state."""
        if self._last_result is None:
            return (
                f"Auto-Pilot Engine: Status={self._status.value.upper()} | "
                f"Queue tasks: {self._queue.total_count()} total, "
                f"{self._queue.ready_count()} ready"
            )
        return str(self._last_result)
