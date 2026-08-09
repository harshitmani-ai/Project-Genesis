"""
core/__init__.py

Public API for the Project Genesis core framework package.

Importing `core` exposes the five foundational building blocks needed to
build a compliant worker.  Workers in future phases will use:

    from core import BaseWorker, WorkerIdentity, WorkerReport, WorkerLogger, MemoryInterface

Phase 1: Core Infrastructure — No existing files are modified.
Phase 7: Adds WorkerOrchestrator and FinalCompanyReport for multi-worker orchestration.
Phase 8: Adds MemoryGovernor for governed memory writes.
"""

from core.base_worker import BaseWorker
from core.logger import LogLevel, WorkerLogger
from core.memory_governor import MemoryGovernor
from core.memory_interface import MemoryInterface
from core.orchestrator import FinalCompanyReport, WorkerOrchestrator
from core.worker_identity import WorkerIdentity
from core.worker_report import ReportStatus, WorkerReport

__all__ = [
    "BaseWorker",
    "FinalCompanyReport",
    "MemoryGovernor",
    "LogLevel",
    "WorkerLogger",
    "MemoryInterface",
    "WorkerIdentity",
    "WorkerOrchestrator",
    "ReportStatus",
    "WorkerReport",
]

__version__ = "1.0.0"
