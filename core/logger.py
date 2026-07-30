"""
core/logger.py

Defines WorkerLogger — a lightweight, structured logger used by every
worker in the Project Genesis framework.

Design decisions:
  - No external dependencies (stdlib only).
  - Each log entry is prefixed with a timestamp and the worker's name so
    that log streams from multiple workers can be distinguished at a glance.
  - Output goes to stdout so it integrates naturally with the existing
    print-based CLI in genesis.py.
  - Log level filtering is supported but kept simple (DEBUG/INFO/WARNING/ERROR).

Phase 1: Core Infrastructure — No existing files are modified.
"""

from datetime import datetime
from enum import IntEnum


class LogLevel(IntEnum):
    DEBUG   = 10
    INFO    = 20
    WARNING = 30
    ERROR   = 40


class WorkerLogger:
    """
    Lightweight structured logger for Project Genesis workers.

    Usage:
        logger = WorkerLogger("Research Worker")
        logger.info("Starting research assignment…")
        logger.warning("No target audience provided.")
        logger.error("LLM request failed.")
    """

    # Default minimum level printed to stdout.
    DEFAULT_LEVEL: LogLevel = LogLevel.INFO

    def __init__(
        self,
        worker_name: str,
        min_level: LogLevel = DEFAULT_LEVEL,
    ) -> None:
        """
        Args:
            worker_name:  Name shown in every log line prefix.
            min_level:    Minimum severity to emit. Messages below this
                          level are silently discarded.
        """
        self.worker_name = worker_name
        self.min_level = min_level
        self._history: list[str] = []

    # ------------------------------------------------------------------
    # Public logging methods
    # ------------------------------------------------------------------

    def debug(self, message: str) -> None:
        self._emit(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self._emit(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self._emit(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self._emit(LogLevel.ERROR, message)

    # ------------------------------------------------------------------
    # History / inspection helpers
    # ------------------------------------------------------------------

    def get_history(self) -> list[str]:
        """Return a copy of all emitted log lines (at any level)."""
        return list(self._history)

    def clear_history(self) -> None:
        """Discard all stored log lines."""
        self._history.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _emit(self, level: LogLevel, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_tag = level.name.ljust(7)           # e.g. "INFO   "
        line = f"[{timestamp}] [{level_tag}] [{self.worker_name}] {message}"
        self._history.append(line)
        if level >= self.min_level:
            print(line)
