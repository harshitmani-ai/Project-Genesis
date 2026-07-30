"""
core/worker_identity.py

Defines WorkerIdentity — the immutable identity record for every worker
in the Project Genesis hub-and-spoke framework.

Phase 1: Core Infrastructure — No existing files are modified.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class WorkerIdentity:
    """
    Immutable identity descriptor for a Project Genesis worker.

    Attributes:
        name:        Human-readable worker name (e.g. "Research Worker").
        role:        One-line description of the worker's primary role.
        version:     Semantic version string (e.g. "1.0.0").
        created_at:  ISO-8601 timestamp of when this identity was created.
    """

    name: str
    role: str
    version: str = "1.0.0"
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def __str__(self) -> str:
        return (
            f"[{self.name} v{self.version}] "
            f"Role: {self.role} | "
            f"Created: {self.created_at}"
        )
