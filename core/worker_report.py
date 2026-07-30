"""
core/worker_report.py

Defines WorkerReport — the standardised output envelope returned by every
worker after completing a lifecycle run.

Phase 1: Core Infrastructure — No existing files are modified.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ReportStatus(str, Enum):
    """Possible completion states of a worker lifecycle run."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"   # completed with non-fatal issues
    PENDING = "PENDING"   # task accepted but not yet finished


@dataclass
class WorkerReport:
    """
    Standardised output envelope for every worker lifecycle run.

    Attributes:
        worker_name:    Name of the worker that produced this report.
        task_summary:   One-line description of the task that was run.
        status:         Final completion state (ReportStatus enum).
        result:         Primary output payload (raw text, path, dict …).
        metadata:       Optional dict of supplemental key/value data.
        error:          Captured exception or error message, if any.
        completed_at:   ISO-8601 timestamp set when the report is finalised.
    """

    worker_name: str
    task_summary: str
    status: ReportStatus = ReportStatus.PENDING
    result: Any = None
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None
    completed_at: Optional[str] = None

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def mark_success(self, result: Any = None, **metadata_kwargs) -> "WorkerReport":
        """Finalise the report as SUCCESS."""
        self.status = ReportStatus.SUCCESS
        if result is not None:
            self.result = result
        self.metadata.update(metadata_kwargs)
        self._stamp_time()
        return self

    def mark_failure(self, error: str, **metadata_kwargs) -> "WorkerReport":
        """Finalise the report as FAILURE."""
        self.status = ReportStatus.FAILURE
        self.error = error
        self.metadata.update(metadata_kwargs)
        self._stamp_time()
        return self

    def mark_partial(self, result: Any = None, error: str = "", **metadata_kwargs) -> "WorkerReport":
        """Finalise the report as PARTIAL (completed with non-fatal issues)."""
        self.status = ReportStatus.PARTIAL
        if result is not None:
            self.result = result
        if error:
            self.error = error
        self.metadata.update(metadata_kwargs)
        self._stamp_time()
        return self

    # ------------------------------------------------------------------
    # Backward-compatibility helpers
    # ------------------------------------------------------------------

    def as_text(self) -> Optional[str]:
        """
        Return the result as a plain string.

        Converts the result to str if needed, mimicking the raw text
        return signatures of legacy workers (e.g. research_worker.py).
        Returns None if result is None.
        """
        if self.result is None:
            return None
        return str(self.result)

    def as_tuple(self) -> tuple:
        """
        Return (result, metadata) — mirrors legacy (result, report_path) tuples.
        """
        return (self.result, self.metadata)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def summary_lines(self) -> list[str]:
        """Return a human-readable summary as a list of lines."""
        lines = [
            f"Worker  : {self.worker_name}",
            f"Task    : {self.task_summary}",
            f"Status  : {self.status.value}",
        ]
        if self.completed_at:
            lines.append(f"Finished: {self.completed_at}")
        if self.error:
            lines.append(f"Error   : {self.error}")
        return lines

    def __str__(self) -> str:
        return "\n".join(self.summary_lines())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _stamp_time(self) -> None:
        self.completed_at = datetime.now().isoformat(timespec="seconds")
