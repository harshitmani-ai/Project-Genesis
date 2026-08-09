"""
core/tool_manager.py

Tool Integration Layer for Project Genesis.

Architecture:
  Every worker that needs to interact with the external world (read files,
  write reports, list directories, search the web) does so exclusively through
  ToolManager.  No worker may perform raw filesystem or network I/O without
  going through this layer.

Components:
  Tool          — Abstract base class that every tool must subclass.
  ToolResult    — Standardised return object from every tool execution.
  ToolManager   — Central registry: register, validate, execute, log tools.

Built-in tools (registered automatically in DEFAULT_TOOL_MANAGER):
  FileReaderTool      — Read a text file and return its content.
  FileWriterTool      — Write text to a file (safety-validated path only).
  DirectoryListerTool — List files in a directory.
  WebSearchTool       — Placeholder for future web search integration.
  ReportExporterTool  — Export a markdown report to a specified folder.

Safety rules (FileWriterTool):
  • Resolved path must remain inside the project working directory.
  • Writing to Python source files (*.py) is blocked.
  • Writing to .git/ internals is blocked.

Logging:
  Every tool call is recorded with tool name, inputs (summarised),
  execution time in ms, and success/failure status.

Phase 10: Tool Integration Layer — BaseWorker and all existing components
are untouched.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ── ToolResult ────────────────────────────────────────────────────────────────

@dataclass
class ToolResult:
    """
    Standardised return object from every ToolManager.execute() call.

    Fields:
        tool_name         — Name of the tool that was called.
        success           — True if execution completed without error.
        output            — The primary result value (str, list, dict, …).
        error             — Error message string if success is False, else None.
        execution_time_ms — Wall-clock execution time in milliseconds.
        metadata          — Optional extra metadata (e.g. path used, byte count).
    """

    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    execution_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return (
            f"[{status}] {self.tool_name} "
            f"({self.execution_time_ms:.1f}ms) "
            f"{'— ' + self.error if self.error else ''}"
        )


# ── Tool (abstract base) ──────────────────────────────────────────────────────

class Tool(ABC):
    """
    Abstract base class for every Project Genesis tool.

    Subclasses must define:
        name        — Unique identifier string (no spaces, snake_case).
        description — Human-readable explanation shown in tool listings.
        execute(**kwargs) — Perform the tool's work and return any value.
    """

    # Subclasses override these at class level.
    name: str = "base_tool"
    description: str = "Abstract base tool."

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        Perform the tool's action.

        Args:
            **kwargs: Tool-specific parameters (documented per subclass).

        Returns:
            The primary result of the action (type varies per tool).

        Raises:
            Any exception — caught and wrapped by ToolManager.execute().
        """


# ── Built-in tools ────────────────────────────────────────────────────────────

class FileReaderTool(Tool):
    """
    Read the full text content of a file.

    kwargs:
        path (str | Path): Path to the file to read.
        encoding (str):    Text encoding, default "utf-8".
    """

    name = "file_reader"
    description = "Read the text content of a file on disk."

    def execute(self, **kwargs: Any) -> str:
        path = Path(kwargs["path"])
        encoding = kwargs.get("encoding", "utf-8")

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")

        return path.read_text(encoding=encoding)


class FileWriterTool(Tool):
    """
    Write text content to a file.

    Safety rules:
      • Target path must be inside the project root (cwd).
      • Writing to *.py source files is blocked.
      • Writing inside .git/ is blocked.

    kwargs:
        path    (str | Path): Destination file path.
        content (str):        Text to write.
        mode    (str):        "w" (overwrite, default) or "a" (append).
        encoding (str):       Text encoding, default "utf-8".
    """

    name = "file_writer"
    description = "Write text content to a file (safety-validated path only)."

    # Project root is locked at import time.
    _PROJECT_ROOT: Path = Path.cwd().resolve()

    # Patterns that can never be written to.
    _BLOCKED_SUFFIXES = {".py", ".pyc"}
    _BLOCKED_FOLDERS = {".git"}

    def execute(self, **kwargs: Any) -> str:
        path = Path(kwargs["path"])
        content = str(kwargs["content"])
        mode = kwargs.get("mode", "w")
        encoding = kwargs.get("encoding", "utf-8")

        resolved = path.resolve()

        # Safety check 1: must stay inside project root
        try:
            resolved.relative_to(self._PROJECT_ROOT)
        except ValueError:
            raise PermissionError(
                f"FileWriterTool: path '{resolved}' is outside the project root "
                f"'{self._PROJECT_ROOT}'. Write blocked."
            )

        # Safety check 2: no Python source file writes
        if resolved.suffix in self._BLOCKED_SUFFIXES:
            raise PermissionError(
                f"FileWriterTool: writing to Python source files (*.py, *.pyc) "
                f"is not allowed. Path: {resolved}"
            )

        # Safety check 3: no .git internals
        for part in resolved.parts:
            if part in self._BLOCKED_FOLDERS:
                raise PermissionError(
                    f"FileWriterTool: writing inside '{part}/' is not allowed. "
                    f"Path: {resolved}"
                )

        # Create parent directories if needed
        resolved.parent.mkdir(parents=True, exist_ok=True)

        with resolved.open(mode, encoding=encoding) as f:
            f.write(content)

        return f"Written {len(content)} characters to {resolved}"


class DirectoryListerTool(Tool):
    """
    List the contents of a directory.

    kwargs:
        path    (str | Path): Directory to list.
        pattern (str):        Glob pattern, default "*".
    """

    name = "directory_lister"
    description = "List files and subdirectories inside a given directory."

    def execute(self, **kwargs: Any) -> list[str]:
        path = Path(kwargs.get("path", "."))
        pattern = kwargs.get("pattern", "*")

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        entries = sorted(path.glob(pattern))
        return [str(e) for e in entries]


class WebSearchTool(Tool):
    """
    Placeholder web search tool.

    Full implementation deferred to Phase 11 or when a search API key is
    configured.  Returns a structured placeholder result so workers that
    request web searches fail gracefully rather than crashing.

    kwargs:
        query (str): The search query string.
    """

    name = "web_search"
    description = (
        "Search the web for information. "
        "[PLACEHOLDER — Full integration in future phase.]"
    )

    def execute(self, **kwargs: Any) -> dict:
        query = str(kwargs.get("query", "")).strip()
        return {
            "status": "placeholder",
            "query": query,
            "message": (
                "Web search is not yet connected to a live API. "
                "This tool will be fully implemented in a future phase. "
                "For now, use company memory and existing worker outputs."
            ),
            "results": [],
        }


class ReportExporterTool(Tool):
    """
    Export a markdown report string to a specified folder.

    kwargs:
        content     (str):        Markdown text to write.
        folder      (str | Path): Destination folder (created if absent).
        filename    (str):        Filename for the report.
        encoding    (str):        Text encoding, default "utf-8".
    """

    name = "report_exporter"
    description = "Export a markdown report to a specified project folder."

    # Delegate safety to FileWriterTool
    _writer = FileWriterTool()

    def execute(self, **kwargs: Any) -> str:
        content = str(kwargs["content"])
        folder = Path(kwargs.get("folder", "exports"))
        filename = str(kwargs.get("filename", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"))
        encoding = kwargs.get("encoding", "utf-8")

        destination = folder / filename
        return self._writer.execute(path=destination, content=content, encoding=encoding)


# ── ToolManager ───────────────────────────────────────────────────────────────

class ToolManager:
    """
    Central registry for all Project Genesis tools.

    Responsibilities:
      - register(tool)          — Add a Tool to the registry.
      - execute(name, **kwargs) — Run a registered tool by name; return ToolResult.
      - list_tools()            — Return sorted list of registered tool names.
      - tool_summary()          — Return a human-readable registry listing.
      - execution_log           — Read-only list of all ToolResult entries.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Tool] = {}
        self._log: list[ToolResult] = []

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the manager.

        Args:
            tool: Any object subclassing Tool.

        Raises:
            TypeError:  If tool is not a Tool subclass instance.
            ValueError: If a tool with the same name is already registered.
        """
        if not isinstance(tool, Tool):
            raise TypeError(
                f"Expected a Tool subclass instance, got {type(tool).__name__}"
            )
        if tool.name in self._registry:
            raise ValueError(
                f"A tool named '{tool.name}' is already registered. "
                "Use a unique name or deregister the existing tool first."
            )
        self._registry[tool.name] = tool

    def deregister(self, tool_name: str) -> None:
        """Remove a tool from the registry by name (silent if absent)."""
        self._registry.pop(tool_name, None)

    # ── Execution ─────────────────────────────────────────────────────────────

    def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """
        Execute a registered tool by name and return a ToolResult.

        Always returns a ToolResult — never raises.  Errors are captured
        in ToolResult.error with success=False.

        Args:
            tool_name: Registered name of the tool to run.
            **kwargs:  Tool-specific parameters passed through to Tool.execute().

        Returns:
            A populated ToolResult object.
        """
        start = time.perf_counter()

        if tool_name not in self._registry:
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Tool '{tool_name}' is not registered. Available: {self.list_tools()}",
                execution_time_ms=0.0,
            )
            self._log.append(result)
            return result

        tool = self._registry[tool_name]

        try:
            output = tool.execute(**kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            result = ToolResult(
                tool_name=tool_name,
                success=True,
                output=output,
                error=None,
                execution_time_ms=round(elapsed_ms, 2),
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"{type(exc).__name__}: {exc}",
                execution_time_ms=round(elapsed_ms, 2),
            )

        self._log.append(result)
        return result

    # ── Introspection ─────────────────────────────────────────────────────────

    def list_tools(self) -> list[str]:
        """Return a sorted list of registered tool names."""
        return sorted(self._registry.keys())

    def tool_summary(self) -> str:
        """Return a human-readable listing of all registered tools."""
        if not self._registry:
            return "No tools registered."

        lines = [f"Registered Tools ({len(self._registry)} total):", ""]
        for name in self.list_tools():
            tool = self._registry[name]
            lines.append(f"  • {name:<24} — {tool.description}")
        return "\n".join(lines)

    def get_log(self) -> list[ToolResult]:
        """Return a copy of the full execution log."""
        return list(self._log)

    def log_summary(self) -> str:
        """Return a human-readable execution log summary."""
        if not self._log:
            return "No tool executions recorded."

        lines = [f"Tool Execution Log ({len(self._log)} entries):", ""]
        for entry in self._log:
            lines.append(f"  {entry}")
        return "\n".join(lines)

    @property
    def execution_log(self) -> list[ToolResult]:
        """Read-only view of the execution log."""
        return list(self._log)


# ── Default Tool Manager (singleton-style, module-level) ──────────────────────

def _build_default_manager() -> ToolManager:
    """Construct a ToolManager pre-loaded with all built-in tools."""
    manager = ToolManager()
    for tool in [
        FileReaderTool(),
        FileWriterTool(),
        DirectoryListerTool(),
        WebSearchTool(),
        ReportExporterTool(),
    ]:
        manager.register(tool)
    return manager


DEFAULT_TOOL_MANAGER: ToolManager = _build_default_manager()
"""
Module-level default instance pre-loaded with all built-in tools.

Workers and other components that need tools should import this:

    from core.tool_manager import DEFAULT_TOOL_MANAGER
    result = DEFAULT_TOOL_MANAGER.execute("file_reader", path="company_memory.md")
"""
