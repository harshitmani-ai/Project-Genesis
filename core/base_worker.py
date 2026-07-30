"""
core/base_worker.py

Defines BaseWorker — the abstract base class for every worker in the
Project Genesis hub-and-spoke framework.

Architecture:
  - Workers subclass BaseWorker and implement the four abstract hook methods:
      create_plan()  →  plan the task
      execute()      →  run the task
      verify()       →  validate the output
      learn()        →  propose memory updates

  - Callers invoke run_lifecycle(task) which orchestrates the 5-step flow:
      Goal → Plan → Execute → Verify → Learn

  - Each step is logged via WorkerLogger.
  - The method returns a WorkerReport regardless of success or failure,
    so callers always receive a structured, inspectable result.

Phase 1: Core Infrastructure — No existing files are modified.
"""

from abc import ABC, abstractmethod
from typing import Any

from core.logger import WorkerLogger
from core.memory_interface import MemoryInterface
from core.worker_identity import WorkerIdentity
from core.worker_report import ReportStatus, WorkerReport


class BaseWorker(ABC):
    """
    Abstract base class for all Project Genesis workers.

    Subclasses MUST implement:
        create_plan(task)   — Return a plan dict or description string.
        execute(task, plan) — Perform the actual work; return the raw result.
        verify(result)      — Validate the result; return True if valid.
        learn(task, result) — Propose memory updates; return proposal path or None.

    Subclasses SHOULD set `identity` in __init__ before calling super().__init__()
    or by overriding the class-level identity attribute.
    """

    # ------------------------------------------------------------------
    # Identity — subclasses override this.
    # ------------------------------------------------------------------
    identity: WorkerIdentity = WorkerIdentity(
        name="BaseWorker",
        role="Abstract base — do not instantiate directly.",
    )

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        self.logger = WorkerLogger(self.identity.name)
        self.memory = MemoryInterface()

    # ------------------------------------------------------------------
    # Abstract lifecycle hooks — subclasses implement these.
    # ------------------------------------------------------------------

    @abstractmethod
    def create_plan(self, task: Any) -> Any:
        """
        Analyse the task and return a plan.

        Args:
            task: The task object or description passed by the orchestrator.

        Returns:
            A plan in any form the subclass finds useful (dict, str, …).
        """

    @abstractmethod
    def execute(self, task: Any, plan: Any) -> Any:
        """
        Carry out the planned work.

        Args:
            task: Original task description.
            plan: Output of create_plan().

        Returns:
            The primary result of the work (text, Path, dict, …).
        """

    @abstractmethod
    def verify(self, result: Any) -> bool:
        """
        Validate the output produced by execute().

        Args:
            result: Output of execute().

        Returns:
            True if the result is acceptable; False otherwise.
        """

    @abstractmethod
    def learn(self, task: Any, result: Any) -> Any:
        """
        Propose memory updates based on the completed task.

        Implementations should call self.memory.propose_update() to stage
        new knowledge rather than writing directly to company_memory.md.

        Args:
            task:   Original task description.
            result: Output of execute().

        Returns:
            The proposal Path if a proposal was written, or None.
        """

    # ------------------------------------------------------------------
    # Lifecycle orchestrator — callers invoke this.
    # ------------------------------------------------------------------

    def run_lifecycle(self, task: Any) -> WorkerReport:
        """
        Execute the full 5-step worker lifecycle and return a WorkerReport.

        Steps:
            1. Goal    — Log the accepted task.
            2. Plan    — Call create_plan(task).
            3. Execute — Call execute(task, plan).
            4. Verify  — Call verify(result).
            5. Learn   — Call learn(task, result).

        Any unhandled exception causes the report to be marked FAILURE.
        A failed verify() causes the report to be marked PARTIAL.

        Args:
            task: Task description or object provided by the orchestrator.

        Returns:
            A fully populated WorkerReport.
        """
        report = WorkerReport(
            worker_name=self.identity.name,
            task_summary=str(task),
        )

        try:
            # ── Step 1: Goal ───────────────────────────────────────────
            self.logger.info(f"Task accepted: {task}")

            # ── Step 2: Plan ───────────────────────────────────────────
            self.logger.info("Creating plan…")
            plan = self.create_plan(task)
            self.logger.debug(f"Plan: {plan}")

            # ── Step 3: Execute ────────────────────────────────────────
            self.logger.info("Executing task…")
            result = self.execute(task, plan)

            # ── Step 4: Verify ─────────────────────────────────────────
            self.logger.info("Verifying result…")
            is_valid = self.verify(result)

            if not is_valid:
                self.logger.warning("Verification failed — result may be incomplete.")
                report.mark_partial(
                    result=result,
                    error="Verification failed — result may be incomplete.",
                )
                # Still attempt the learn step even on partial success.
                self._run_learn_step(task, result, report)
                return report

            # ── Step 5: Learn ──────────────────────────────────────────
            self.logger.info("Proposing memory updates…")
            self._run_learn_step(task, result, report)

            report.mark_success(result=result)
            self.logger.info("Lifecycle completed successfully.")

        except Exception as error:
            error_msg = f"{type(error).__name__}: {error}"
            self.logger.error(f"Lifecycle failed — {error_msg}")
            report.mark_failure(error=error_msg)

        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_learn_step(
        self,
        task: Any,
        result: Any,
        report: WorkerReport,
    ) -> None:
        """Run the learn() hook and attach any proposal path to the report."""
        try:
            proposal_path = self.learn(task, result)
            if proposal_path is not None:
                report.metadata["proposal_path"] = str(proposal_path)
                self.logger.info(f"Memory proposal staged: {proposal_path}")
        except Exception as learn_error:
            # A learn() failure should never mask the main result.
            self.logger.warning(
                f"learn() step failed (non-fatal): {learn_error}"
            )
            report.metadata["learn_error"] = str(learn_error)
