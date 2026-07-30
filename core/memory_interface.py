"""
core/memory_interface.py

Defines MemoryInterface — the formal abstraction layer through which all
Project Genesis workers read company context and propose memory updates.

Design principles:
  - READ PATH:  Delegates to the existing memory.py module so that the
                constitution.md / company_memory.md reading logic is not
                duplicated.  The existing files are untouched.
  - WRITE PATH: Workers submit proposed updates to a staging area
                (company_memory/proposals/) rather than writing directly
                to company_memory.md.  Genesis (the orchestrator) decides
                when to commit staged proposals.
  - ISOLATION:  MemoryInterface is a pure utility class; it holds no
                worker state and can be instantiated by any worker.

Phase 1: Core Infrastructure — No existing files are modified.
"""

from datetime import datetime
from pathlib import Path


# Paths mirror the constants already used in memory.py and research_worker.py.
_CONSTITUTION_FILE   = Path("constitution.md")
_COMPANY_MEMORY_FILE = Path("company_memory.md")
_PROPOSALS_DIR       = Path("company_memory") / "proposals"


class MemoryInterface:
    """
    Formal interface for reading company context and submitting memory
    update proposals.

    Usage:
        memory = MemoryInterface()

        # Read the full company context (constitution + memory).
        context = memory.read_context()

        # Propose a new memory entry (does NOT touch company_memory.md).
        proposal_path = memory.propose_update(
            worker_name="Research Worker",
            topic="HR Tools for SMBs",
            content="Research completed on 2026-07-30. See report_001.md.",
        )
    """

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def read_context(self) -> str:
        """
        Load the full company context for use in LLM prompts.

        Mirrors the behaviour of memory.load_company_context() to keep
        existing prompt injection patterns working without modification.

        Returns:
            A formatted string containing both the company constitution
            and the company memory, ready for prompt injection.

        Raises:
            FileNotFoundError: If constitution.md or company_memory.md
                               cannot be found.
        """
        constitution = _CONSTITUTION_FILE.read_text(encoding="utf-8")
        company_memory = _COMPANY_MEMORY_FILE.read_text(encoding="utf-8")

        return (
            f"\nCOMPANY CONSTITUTION:\n{constitution}"
            f"\nCOMPANY MEMORY:\n{company_memory}\n"
        )

    def read_constitution(self) -> str:
        """Return only the company constitution text."""
        return _CONSTITUTION_FILE.read_text(encoding="utf-8")

    def read_company_memory(self) -> str:
        """Return only the current company memory text."""
        return _COMPANY_MEMORY_FILE.read_text(encoding="utf-8")

    def memory_file_exists(self) -> bool:
        """Return True if company_memory.md exists."""
        return _COMPANY_MEMORY_FILE.exists()

    def constitution_file_exists(self) -> bool:
        """Return True if constitution.md exists."""
        return _CONSTITUTION_FILE.exists()

    # ------------------------------------------------------------------
    # Write operations (staging only — never touches company_memory.md)
    # ------------------------------------------------------------------

    def propose_update(
        self,
        worker_name: str,
        topic: str,
        content: str,
    ) -> Path:
        """
        Save a memory update proposal to the staging area.

        The proposal is written as a Markdown file inside
        company_memory/proposals/.  It is NOT appended to company_memory.md.
        Genesis is responsible for reviewing and committing proposals.

        Args:
            worker_name:  Name of the worker submitting the proposal.
            topic:        Short label describing the subject of the update.
            content:      The Markdown text to be proposed for memory.

        Returns:
            The Path to the saved proposal file.
        """
        _PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Build a safe filename from the worker name and topic.
        safe_topic = "".join(
            c if c.isalnum() or c in "-_" else "_"
            for c in topic.lower().replace(" ", "_")
        )[:40]
        filename = f"proposal_{timestamp}_{safe_topic}.md"
        proposal_path = _PROPOSALS_DIR / filename

        now_formatted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        proposal_text = f"""# Memory Update Proposal

**Worker:** {worker_name}
**Topic:** {topic}
**Proposed at:** {now_formatted}
**Status:** Pending founder review

---

{content}

---

*This proposal was generated automatically.  It requires review and
approval from Harshit before being committed to company_memory.md.*
"""
        proposal_path.write_text(proposal_text, encoding="utf-8")
        return proposal_path

    def list_proposals(self) -> list[Path]:
        """
        Return a sorted list of all pending proposal files.

        Returns an empty list if the proposals directory does not exist.
        """
        if not _PROPOSALS_DIR.exists():
            return []
        return sorted(_PROPOSALS_DIR.glob("proposal_*.md"))
