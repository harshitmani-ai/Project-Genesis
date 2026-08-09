"""
core/skill_manager.py

Skill & Plugin System for Project Genesis.

Architecture:
  Skills are self-contained, reusable capabilities that can be dropped into
  the skills/ directory without modifying any core file.  SkillManager
  automatically discovers and loads them at startup.

  ┌─────────────────────────────────────────────────────────────────┐
  │  skills/                     (auto-discovered)                  │
  │    google_review_product/                                       │
  │      manifest.json           (metadata, required_workers)       │
  │      skill.py                (Skill subclass)                   │
  │    customer_validation/                                         │
  │      manifest.json                                              │
  │      skill.py                                                   │
  │    business_evaluation/                                         │
  │      manifest.json                                              │
  │      skill.py                                                   │
  └─────────────────────────────────────────────────────────────────┘

Components:
  Skill          — Abstract base class every skill must subclass.
  SkillManifest  — Typed metadata object loaded from manifest.json.
  SkillResult    — Standardised return object from every skill execution.
  SkillManager   — Discovery, registration, and execution engine.

Execution contract:
  Skills call workers exclusively through WorkerOrchestrator, which itself
  uses the WORKER_REGISTRY.  No skill may import or instantiate a worker
  directly — the Worker Framework must never be bypassed.

Phase 11: Skill & Plugin System — No existing core files are modified.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Default discovery directory ───────────────────────────────────────────────

_DEFAULT_SKILLS_DIR = Path("skills")


# ── SkillManifest ─────────────────────────────────────────────────────────────

@dataclass
class SkillManifest:
    """
    Typed representation of a skill's manifest.json file.

    Fields:
        name             — Unique snake_case identifier (matches folder name).
        version          — SemVer string, e.g. "1.0.0".
        description      — One-sentence human-readable description.
        category         — Grouping label (e.g. "Product Evaluation").
        required_workers — List of WORKER_REGISTRY keys the skill needs.
        required_tools   — List of TOOL_MANAGER tool names the skill needs.
        skill_class      — Name of the Skill subclass inside skill.py.
    """

    name: str
    version: str
    description: str
    category: str
    required_workers: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    skill_class: str = "Skill"

    @classmethod
    def from_dict(cls, data: dict) -> "SkillManifest":
        return cls(
            name=str(data.get("name", "")),
            version=str(data.get("version", "1.0.0")),
            description=str(data.get("description", "")),
            category=str(data.get("category", "General")),
            required_workers=list(data.get("required_workers", [])),
            required_tools=list(data.get("required_tools", [])),
            skill_class=str(data.get("skill_class", "Skill")),
        )

    @classmethod
    def from_file(cls, manifest_path: Path) -> "SkillManifest":
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


# ── SkillResult ───────────────────────────────────────────────────────────────

@dataclass
class SkillResult:
    """
    Standardised return object from every SkillManager.execute() call.

    Fields:
        skill_name        — Name of the executed skill.
        success           — True if execution completed without unrecoverable error.
        output            — Primary result (FinalCompanyReport, text, dict, …).
        error             — Error message if success is False, else None.
        workers_used      — Ordered list of worker keys that were executed.
        execution_time_ms — Wall-clock time for the full skill execution.
        metadata          — Optional extra data (e.g. report paths).
    """

    skill_name: str
    success: bool
    output: Any
    error: str | None = None
    workers_used: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        workers = " → ".join(w.title() for w in self.workers_used) or "none"
        return (
            f"[{status}] Skill: {self.skill_name} "
            f"({self.execution_time_ms:.0f}ms) "
            f"Workers: {workers}"
            + (f" — Error: {self.error}" if self.error else "")
        )


# ── Skill (abstract base) ─────────────────────────────────────────────────────

class Skill(ABC):
    """
    Abstract base class for every Project Genesis skill.

    Subclasses define:
        name             — Unique identifier (must match manifest.json "name").
        version          — SemVer string.
        description      — Human-readable purpose.
        category         — Grouping label.
        required_workers — Workers this skill depends on.
        required_tools   — Tools this skill depends on.

    The execute() method receives:
        goal             — Cleaned founder request string.
        worker_registry  — The live WORKER_REGISTRY dict from genesis.py.
        orchestrator     — The live ORCHESTRATOR instance from genesis.py.
        tool_manager     — The live TOOL_MANAGER instance from genesis.py.

    Skills MUST use the orchestrator to run workers.
    Skills MUST NOT instantiate workers directly.
    """

    name: str = "base_skill"
    version: str = "0.0.0"
    description: str = "Abstract base skill."
    category: str = "General"
    required_workers: list[str] = []
    required_tools: list[str] = []

    @abstractmethod
    def execute(
        self,
        goal: str,
        worker_registry: dict,
        orchestrator: Any,
        tool_manager: Any | None = None,
    ) -> SkillResult:
        """
        Run the skill and return a SkillResult.

        Args:
            goal:            Cleaned founder request.
            worker_registry: Live WORKER_REGISTRY from genesis.py.
            orchestrator:    Live ORCHESTRATOR (WorkerOrchestrator) instance.
            tool_manager:    Optional live TOOL_MANAGER instance.

        Returns:
            A populated SkillResult.
        """


# ── SkillManager ──────────────────────────────────────────────────────────────

class SkillManager:
    """
    Discovery, registration, and execution engine for Project Genesis skills.

    Usage:
        manager = SkillManager()
        manager.discover()                   # scan skills/ dir
        result = manager.execute(
            "google_review_product",
            goal="AI CRM for dentists",
            worker_registry=WORKER_REGISTRY,
            orchestrator=ORCHESTRATOR,
        )
    """

    def __init__(self, skills_dir: Path | None = None) -> None:
        self._skills_dir = skills_dir or _DEFAULT_SKILLS_DIR
        self._registry: dict[str, Skill] = {}
        self._manifests: dict[str, SkillManifest] = {}
        self._discovery_errors: list[str] = []

    # ── Discovery ─────────────────────────────────────────────────────────────

    def discover(self, skills_dir: Path | None = None) -> int:
        """
        Scan the skills directory and dynamically load every valid skill.

        A skill folder is valid when it contains both manifest.json and skill.py.
        Discovery errors are stored (not raised) so a broken skill never
        prevents healthy skills from loading.

        Args:
            skills_dir: Override the default skills/ directory.

        Returns:
            The number of skills successfully loaded.
        """
        directory = skills_dir or self._skills_dir

        if not directory.exists():
            return 0

        loaded = 0
        for skill_folder in sorted(directory.iterdir()):
            if not skill_folder.is_dir():
                continue

            manifest_path = skill_folder / "manifest.json"
            skill_py_path = skill_folder / "skill.py"

            if not manifest_path.exists() or not skill_py_path.exists():
                continue  # Not a valid skill folder — skip silently

            try:
                manifest = SkillManifest.from_file(manifest_path)
                skill_instance = self._load_skill_module(
                    skill_py_path, manifest.skill_class
                )
                self._register_internal(skill_instance, manifest)
                loaded += 1
            except Exception as exc:
                error_msg = (
                    f"Failed to load skill from {skill_folder.name}: "
                    f"{type(exc).__name__}: {exc}"
                )
                self._discovery_errors.append(error_msg)

        return loaded

    def _load_skill_module(self, skill_py: Path, class_name: str) -> Skill:
        """
        Dynamically import skill.py and return an instance of the named class.
        """
        module_name = f"skills.{skill_py.parent.name}.skill"

        spec = importlib.util.spec_from_file_location(module_name, skill_py)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {skill_py}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        skill_class = getattr(module, class_name, None)
        if skill_class is None:
            raise AttributeError(
                f"Class '{class_name}' not found in {skill_py}"
            )
        if not (isinstance(skill_class, type) and issubclass(skill_class, Skill)):
            raise TypeError(
                f"'{class_name}' in {skill_py} is not a Skill subclass"
            )

        return skill_class()

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, skill: Skill, manifest: SkillManifest | None = None) -> None:
        """
        Manually register a skill instance (useful for testing / programmatic use).

        Args:
            skill:    A concrete Skill subclass instance.
            manifest: Optional manifest; auto-built from class attributes if omitted.
        """
        if not isinstance(skill, Skill):
            raise TypeError(
                f"Expected a Skill subclass instance, got {type(skill).__name__}"
            )
        if skill.name in self._registry:
            raise ValueError(
                f"A skill named '{skill.name}' is already registered."
            )
        if manifest is None:
            manifest = SkillManifest(
                name=skill.name,
                version=skill.version,
                description=skill.description,
                category=skill.category,
                required_workers=list(skill.required_workers),
                required_tools=list(skill.required_tools),
                skill_class=type(skill).__name__,
            )
        self._registry[skill.name] = skill
        self._manifests[skill.name] = manifest

    def _register_internal(self, skill: Skill, manifest: SkillManifest) -> None:
        """Internal registration that always succeeds (discovery path)."""
        self._registry[skill.name] = skill
        self._manifests[skill.name] = manifest

    def deregister(self, skill_name: str) -> None:
        """Remove a skill by name (silent if absent)."""
        self._registry.pop(skill_name, None)
        self._manifests.pop(skill_name, None)

    # ── Execution ─────────────────────────────────────────────────────────────

    def execute(
        self,
        skill_name: str,
        goal: str,
        worker_registry: dict,
        orchestrator: Any,
        tool_manager: Any | None = None,
    ) -> SkillResult:
        """
        Execute a registered skill by name.

        Always returns a SkillResult — never raises.
        """
        start = time.perf_counter()

        if skill_name not in self._registry:
            result = SkillResult(
                skill_name=skill_name,
                success=False,
                output=None,
                error=(
                    f"Skill '{skill_name}' is not registered. "
                    f"Available: {self.list_skills()}"
                ),
            )
            return result

        skill = self._registry[skill_name]

        try:
            result = skill.execute(
                goal=goal,
                worker_registry=worker_registry,
                orchestrator=orchestrator,
                tool_manager=tool_manager,
            )
            result.execution_time_ms = round(
                (time.perf_counter() - start) * 1000, 2
            )
        except Exception as exc:
            result = SkillResult(
                skill_name=skill_name,
                success=False,
                output=None,
                error=f"{type(exc).__name__}: {exc}",
                execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
            )

        return result

    # ── Introspection ─────────────────────────────────────────────────────────

    def list_skills(self) -> list[str]:
        """Return a sorted list of registered skill names."""
        return sorted(self._registry.keys())

    def get(self, skill_name: str) -> Skill | None:
        """Return the Skill instance for a given name, or None."""
        return self._registry.get(skill_name)

    def get_manifest(self, skill_name: str) -> SkillManifest | None:
        """Return the SkillManifest for a given skill name, or None."""
        return self._manifests.get(skill_name)

    def skills_summary(self) -> str:
        """Return a human-readable listing of all registered skills."""
        if not self._registry:
            return "No skills registered. Add a skill folder to skills/ to begin."

        lines = [f"Available Skills ({len(self._registry)} total):", ""]
        for name in self.list_skills():
            manifest = self._manifests.get(name)
            if manifest:
                workers = " → ".join(w.title() for w in manifest.required_workers) or "none"
                lines.append(f"  ✦ {manifest.name}  v{manifest.version}  [{manifest.category}]")
                lines.append(f"    {manifest.description}")
                lines.append(f"    Workers: {workers}")
                lines.append("")
        if self._discovery_errors:
            lines.append("Discovery Errors:")
            for err in self._discovery_errors:
                lines.append(f"  ⚠ {err}")
        return "\n".join(lines).rstrip()

    @property
    def discovery_errors(self) -> list[str]:
        """Return any errors encountered during discovery."""
        return list(self._discovery_errors)
