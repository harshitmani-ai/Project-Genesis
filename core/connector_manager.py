"""
core/connector_manager.py

Generic Connector Framework for Project Genesis (V2 Infrastructure Upgrade).

Architecture:
  The Connector Framework decouples Genesis from external AI models, IDEs, and services
  (e.g., Antigravity SDK, ChatGPT, GitHub, Stripe, Browser Automation). It eliminates
  the Founder as a manual communication bridge, allowing Genesis to send structured tasks
  and receive verified results directly.

  ┌─────────────────────────────────────────────────────────────┐
  │  Project Genesis Core / Task Queue / Task Planner           │
  │       │                                                     │
  │       ▼                                                     │
  │  ConnectorManager.send_task(task)                           │
  │       │                                                     │
  │       ├─► Pending Task Persistence                              │
  │       ├─► Automatic Retry Loop (on network/API failure)     │
  │       ├─► Target Connector (e.g. Antigravity, ChatGPT)      │
  │       │     ├── Live Mode (if API key / SDK configured)     │
  │       │     └── Simulation Mode (with adapter metadata)     │
  │       ├─► Result Verification                               │
  │       └─► Audit Interaction Logging                         │
  └─────────────────────────────────────────────────────────────┘

Components:
  ConnectorStatus  — Lifecycle states for task execution and connectors.
  ConnectorTask    — Structured task payload sent to a connector.
  ConnectorResult  — Standardised return object from a connector.
  BaseConnector    — Abstract base class for all connectors.
  ConnectorManager — Registry, discovery engine, retry orchestrator, and logger.

Phase V2: Connector Framework — Standalone infrastructure upgrade.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


_DEFAULT_CONNECTORS_DIR = Path("connectors")


# ── ConnectorStatus ───────────────────────────────────────────────────────────

class ConnectorStatus(Enum):
    """Lifecycle states for Connector Tasks and Connectors."""
    IDLE       = "idle"       # Connector ready
    PENDING    = "pending"    # Task queued
    CONNECTING = "connecting" # Initiating communication
    SENDING    = "sending"    # Transmitting task payload
    RECEIVING  = "receiving"  # Awaiting response
    COMPLETED  = "completed"  # Execution & verification succeeded
    FAILED     = "failed"     # Unrecoverable error
    RETRYING   = "retrying"   # Attempting automatic retry
    SIMULATED  = "simulated"  # Executed in adapter simulation mode


# ── ConnectorTask ─────────────────────────────────────────────────────────────

@dataclass
class ConnectorTask:
    """
    A structured task payload sent to an external connector.

    Fields:
        connector_name — Target connector name (e.g. "antigravity", "chatgpt").
        action         — Command / method to invoke (e.g. "execute_code", "ask").
        payload        — Dict of input arguments / prompt / options.
        id             — Auto-generated unique UUID4 hex.
        priority       — Integer 1–10 (1 = highest).
        max_retries    — Maximum automatic retry attempts on communication failure.
        retry_count    — Current retry attempt number.
        created_at     — Creation timestamp.
        status         — Current ConnectorStatus.
        context        — Metadata dict.
    """

    connector_name: str
    action: str
    payload: dict = field(default_factory=dict)
    priority: int = 5
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    status: ConnectorStatus = ConnectorStatus.PENDING
    context: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def __post_init__(self) -> None:
        self.priority = max(1, min(10, self.priority))

    def summary(self) -> str:
        return (
            f"[{self.status.value.upper()}] Task '{self.id}' "
            f"→ {self.connector_name}.{self.action} (retry {self.retry_count}/{self.max_retries})"
        )


# ── ConnectorResult ───────────────────────────────────────────────────────────

@dataclass
class ConnectorResult:
    """
    Standardised return object from a connector task execution.

    Fields:
        task_id           — ID of the task executed.
        connector_name    — Name of the connector.
        success           — True if execution & verification succeeded.
        data              — Execution output data / response object.
        error             — Error message if success is False, else None.
        execution_time_ms — Wall-clock execution time.
        mode              — "live" | "simulated"
        retry_attempts    — Number of retries performed.
        timestamp         — Completion timestamp.
    """

    task_id: str
    connector_name: str
    success: bool
    data: Any
    error: str | None = None
    execution_time_ms: float = 0.0
    mode: str = "live"            # "live" | "simulated"
    retry_attempts: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        status_icon = "✓" if self.success else "✗"
        mode_tag = f"[{self.mode.upper()}]"
        return (
            f"{status_icon} {mode_tag} Connector '{self.connector_name}' "
            f"({self.execution_time_ms:.0f}ms)"
            + (f" — Error: {self.error}" if self.error else "")
        )


# ── BaseConnector ─────────────────────────────────────────────────────────────

class BaseConnector(ABC):
    """
    Abstract Base Class for all Genesis connectors.

    Subclasses must implement:
        name         — Unique identifier matching folder / manifest name.
        version      — SemVer string.
        description  — Purpose summary.
        is_live      — True if live credentials/SDK are configured, False if simulation.
        send_task()  — Low-level communication method.
        verify()     — Output verification rule check.
        health_check() — Connection test.

    Base class provides automatic retry handling and task logging.
    """

    name: str = "base_connector"
    version: str = "1.0.0"
    description: str = "Abstract base connector."
    category: str = "General"

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """Return True if live external service is configured, False if simulation mode."""

    @abstractmethod
    def send_task(self, task: ConnectorTask) -> ConnectorResult:
        """
        Execute the task via the connector.

        Args:
            task: ConnectorTask instance containing action and payload.

        Returns:
            A populated ConnectorResult object.
        """

    @abstractmethod
    def verify_result(self, result: ConnectorResult) -> bool:
        """
        Verify that the connector result meets quality and integrity checks.

        Args:
            result: The ConnectorResult returned by send_task.

        Returns:
            True if verification passes, False otherwise.
        """

    @abstractmethod
    def health_check(self) -> bool:
        """Test whether the connector service is reachable / operational."""


# ── ConnectorManager ──────────────────────────────────────────────────────────

class ConnectorManager:
    """
    Central registry, discovery engine, and execution orchestrator for connectors.

    Features:
      - Automatic discovery of connectors from connectors/ folder.
      - Persistence of pending tasks (never loses pending tasks).
      - Automatic retry loop for communication failures.
      - Interaction audit log.
      - Safe fallback to simulation mode when live APIs are unconfigured.

    Usage:
        manager = ConnectorManager()
        manager.discover()
        result = manager.execute(
            connector_name="chatgpt",
            action="ask",
            payload={"prompt": "Explain Quantum Computing"},
        )
    """

    def __init__(self, connectors_dir: Path | None = None) -> None:
        self._connectors_dir = connectors_dir or _DEFAULT_CONNECTORS_DIR
        self._registry: dict[str, BaseConnector] = {}
        self._pending_tasks: dict[str, ConnectorTask] = {}
        self._interaction_log: list[dict] = []
        self._discovery_errors: list[str] = []

    # ── Discovery ─────────────────────────────────────────────────────────────

    def discover(self, connectors_dir: Path | None = None) -> int:
        """
        Scan the connectors directory and dynamically load valid connectors.

        A connector folder is valid when it contains manifest.json and connector.py.
        """
        directory = connectors_dir or self._connectors_dir

        if not directory.exists():
            return 0

        loaded = 0
        for folder in sorted(directory.iterdir()):
            if not folder.is_dir():
                continue

            manifest_path = folder / "manifest.json"
            connector_py = folder / "connector.py"

            if not manifest_path.exists() or not connector_py.exists():
                continue

            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                class_name = manifest_data.get("connector_class", "Connector")
                instance = self._load_connector_module(connector_py, class_name)
                self._register_internal(instance)
                loaded += 1
            except Exception as exc:
                err = f"Failed to load connector '{folder.name}': {type(exc).__name__}: {exc}"
                self._discovery_errors.append(err)

        return loaded

    def _load_connector_module(self, path: Path, class_name: str) -> BaseConnector:
        module_name = f"connectors.{path.parent.name}.connector"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        connector_class = getattr(module, class_name, None)
        if connector_class is None:
            raise AttributeError(f"Class '{class_name}' not found in {path}")
        if not (isinstance(connector_class, type) and issubclass(connector_class, BaseConnector)):
            raise TypeError(f"'{class_name}' in {path} is not a BaseConnector subclass")

        return connector_class()

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, connector: BaseConnector) -> None:
        """Manually register a BaseConnector instance."""
        if not isinstance(connector, BaseConnector):
            raise TypeError(f"Expected BaseConnector instance, got {type(connector).__name__}")
        if connector.name in self._registry:
            raise ValueError(f"Connector '{connector.name}' is already registered.")
        self._registry[connector.name] = connector

    def _register_internal(self, connector: BaseConnector) -> None:
        self._registry[connector.name] = connector

    def deregister(self, name: str) -> None:
        self._registry.pop(name, None)

    # ── Execution with Retry Loop & Task Persistence ──────────────────────────

    def send_task(
        self,
        connector_name: str,
        action: str,
        payload: dict | None = None,
        max_retries: int = 3,
        context: dict | None = None,
    ) -> ConnectorResult:
        """
        Create, persist, and execute a ConnectorTask through the target connector.

        Includes automatic retry logic for failed communication.
        Never loses pending tasks (remains in _pending_tasks until finished).
        """
        task = ConnectorTask(
            connector_name=connector_name,
            action=action,
            payload=payload or {},
            max_retries=max_retries,
            context=context or {},
        )
        return self.execute_task(task)

    def execute_task(self, task: ConnectorTask) -> ConnectorResult:
        """
        Execute a ConnectorTask instance with persistence, retries, and verification.
        """
        start_time = time.perf_counter()

        # Step 1: Persist pending task
        self._pending_tasks[task.id] = task
        task.status = ConnectorStatus.PENDING

        if task.connector_name not in self._registry:
            elapsed = round((time.perf_counter() - start_time) * 1000, 2)
            task.status = ConnectorStatus.FAILED
            result = ConnectorResult(
                task_id=task.id,
                connector_name=task.connector_name,
                success=False,
                data=None,
                error=f"Connector '{task.connector_name}' is not registered. Available: {self.list_connectors()}",
                execution_time_ms=elapsed,
                mode="simulated",
            )
            self._log_interaction(task, result)
            self._pending_tasks.pop(task.id, None)
            return result

        connector = self._registry[task.connector_name]
        last_result: ConnectorResult | None = None

        # Step 2: Execution loop with retries
        for attempt in range(task.max_retries + 1):
            task.retry_count = attempt
            if attempt > 0:
                task.status = ConnectorStatus.RETRYING
                time.sleep(0.05 * (2 ** (attempt - 1)))  # short backoff

            task.status = ConnectorStatus.SENDING

            try:
                result = connector.send_task(task)
                result.retry_attempts = attempt
                last_result = result

                # Step 3: Verification check
                if result.success and connector.verify_result(result):
                    task.status = ConnectorStatus.COMPLETED if result.mode == "live" else ConnectorStatus.SIMULATED
                    elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                    result.execution_time_ms = elapsed
                    self._log_interaction(task, result)
                    self._pending_tasks.pop(task.id, None)  # task completed
                    return result
                else:
                    # Verification failed or connector returned failure
                    if not result.success and not result.error:
                        result.error = "Verification failed or connector returned error"
            except Exception as exc:
                elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                last_result = ConnectorResult(
                    task_id=task.id,
                    connector_name=task.connector_name,
                    success=False,
                    data=None,
                    error=f"{type(exc).__name__}: {exc}",
                    execution_time_ms=elapsed,
                    mode="simulated" if not connector.is_live else "live",
                    retry_attempts=attempt,
                )

        # Step 4: All retry attempts exhausted
        elapsed = round((time.perf_counter() - start_time) * 1000, 2)
        task.status = ConnectorStatus.FAILED
        if last_result is None:
            last_result = ConnectorResult(
                task_id=task.id,
                connector_name=task.connector_name,
                success=False,
                data=None,
                error="Exhausted max retries without result",
                execution_time_ms=elapsed,
                mode="simulated" if not connector.is_live else "live",
                retry_attempts=task.max_retries,
            )
        else:
            last_result.execution_time_ms = elapsed

        self._log_interaction(task, last_result)
        self._pending_tasks.pop(task.id, None)
        return last_result

    # ── Logging & Introspection ───────────────────────────────────────────────

    def _log_interaction(self, task: ConnectorTask, result: ConnectorResult) -> None:
        self._interaction_log.append({
            "task_id": task.id,
            "connector": task.connector_name,
            "action": task.action,
            "success": result.success,
            "mode": result.mode,
            "retries": result.retry_attempts,
            "time_ms": result.execution_time_ms,
            "error": result.error,
            "timestamp": datetime.now().isoformat(),
        })

    def list_connectors(self) -> list[str]:
        return sorted(self._registry.keys())

    def get(self, name: str) -> BaseConnector | None:
        return self._registry.get(name)

    def pending_tasks(self) -> list[ConnectorTask]:
        return list(self._pending_tasks.values())

    def interaction_log(self) -> list[dict]:
        return list(self._interaction_log)

    def connectors_summary(self) -> str:
        if not self._registry:
            return "No connectors registered in ConnectorManager."

        lines = [f"Registered Connectors ({len(self._registry)} total):", ""]
        for name in self.list_connectors():
            conn = self._registry[name]
            mode_str = "LIVE" if conn.is_live else "SIMULATION MODE"
            lines.append(f"  🔌 {conn.name}  v{conn.version}  [{conn.category}]  — {mode_str}")
            lines.append(f"     {conn.description}")
            lines.append(f"     Health Check: {'PASS' if conn.health_check() else 'FAIL'}")
            lines.append("")

        if self._pending_tasks:
            lines.append(f"Pending Tasks ({len(self._pending_tasks)}):")
            for t in self._pending_tasks.values():
                lines.append(f"  ⏳ {t.summary()}")
            lines.append("")

        if self._discovery_errors:
            lines.append("Discovery Errors:")
            for err in self._discovery_errors:
                lines.append(f"  ⚠ {err}")

        return "\n".join(lines).rstrip()


DEFAULT_CONNECTOR_MANAGER = ConnectorManager()
