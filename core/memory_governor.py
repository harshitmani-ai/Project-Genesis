"""
core/memory_governor.py

MemoryGovernor — the sole authority for committing memory proposals to
company_memory.md in Project Genesis.

Architecture:
  - Workers NEVER write directly to company_memory.md.
  - Workers use MemoryInterface.propose_update() to stage proposals in
    company_memory/proposals/.
  - MemoryGovernor is the only component that reads proposals and merges
    approved ones into company_memory.md.
  - Every merge is recorded in an audit log (company_memory/audit_log.md)
    to prevent duplicate merges and provide a permanent decision trail.

Responsibilities:
  list_proposals()   — Return all pending proposal files.
  show_proposal()    — Display the content of a specific proposal.
  approve()          — Mark a proposal approved and merge into memory.
  reject()           — Mark a proposal rejected and archive it.
  merge_all()        — Approve and merge every pending proposal at once.

Phase 8: Memory Governance — No existing core files are modified.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

_COMPANY_MEMORY_FILE = Path("company_memory.md")
_PROPOSALS_DIR       = Path("company_memory") / "proposals"
_REJECTED_DIR        = Path("company_memory") / "rejected"
_AUDIT_LOG_FILE      = Path("company_memory") / "audit_log.md"


class MemoryGovernor:
    """
    Sole authority for approving and merging memory proposals into
    company_memory.md.

    Usage:
        governor = MemoryGovernor()

        # List all pending proposals
        proposals = governor.list_proposals()

        # Approve a specific proposal by its filename stem or index
        governor.approve(proposals[0])

        # Reject a proposal
        governor.reject(proposals[1], reason="Outdated data")

        # Approve and merge everything pending
        governor.merge_all()
    """

    # ── Public: Listing ───────────────────────────────────────────────────────

    def list_proposals(self) -> list[Path]:
        """Return a sorted list of all pending proposal files."""
        if not _PROPOSALS_DIR.exists():
            return []
        return sorted(_PROPOSALS_DIR.glob("proposal_*.md"))

    def show_proposal(self, proposal_path: Path) -> str:
        """Return the text content of a proposal file."""
        if not proposal_path.exists():
            return f"Proposal not found: {proposal_path}"
        return proposal_path.read_text(encoding="utf-8")

    def proposals_summary(self) -> str:
        """
        Return a human-readable summary of pending proposals.
        Suitable for printing directly to the Genesis CLI.
        """
        proposals = self.list_proposals()
        if not proposals:
            return "No pending memory proposals."

        lines = [f"Pending Memory Proposals ({len(proposals)} total):", ""]
        for i, path in enumerate(proposals, start=1):
            lines.append(f"  [{i}] {path.name}")
        lines += [
            "",
            "Use 'approve memory proposals' to merge all, or review individually.",
        ]
        return "\n".join(lines)

    # ── Public: Approval ──────────────────────────────────────────────────────

    def approve(self, proposal_path: Path) -> str:
        """
        Merge a single proposal into company_memory.md and archive it.

        Args:
            proposal_path: Path to the proposal file.

        Returns:
            A status message indicating success or reason for skip.
        """
        if not proposal_path.exists():
            return f"Skipped — proposal not found: {proposal_path.name}"

        # Duplicate protection: check audit log
        if self._already_merged(proposal_path):
            return f"Skipped — already merged: {proposal_path.name}"

        content = proposal_path.read_text(encoding="utf-8")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append to company_memory.md
        _COMPANY_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _COMPANY_MEMORY_FILE.open("a", encoding="utf-8") as mem:
            mem.write(f"\n\n---\n\n<!-- Merged from proposal: {proposal_path.name} at {timestamp} -->\n\n")
            # Strip the proposal header — keep only the content section
            mem.write(self._extract_proposal_body(content))
            mem.write("\n")

        # Record in audit log
        self._write_audit_entry(
            action="APPROVED",
            proposal_name=proposal_path.name,
            timestamp=timestamp,
        )

        # Move proposal to a merged subfolder so the proposals/ dir stays clean
        merged_dir = _PROPOSALS_DIR / "merged"
        merged_dir.mkdir(parents=True, exist_ok=True)
        archived_path = merged_dir / proposal_path.name
        proposal_path.rename(archived_path)

        return f"Approved and merged: {proposal_path.name}"

    def merge_all(self) -> list[str]:
        """
        Approve and merge every pending proposal in order.

        Returns:
            A list of status messages, one per proposal.
        """
        proposals = self.list_proposals()
        if not proposals:
            return ["No pending proposals to merge."]

        results = []
        for proposal_path in proposals:
            result = self.approve(proposal_path)
            results.append(result)
        return results

    # ── Public: Rejection ─────────────────────────────────────────────────────

    def reject(self, proposal_path: Path, reason: str = "Rejected by Founder") -> str:
        """
        Reject a proposal and move it to company_memory/rejected/.

        Args:
            proposal_path: Path to the proposal file.
            reason:        Short explanation for the rejection.

        Returns:
            A status message.
        """
        if not proposal_path.exists():
            return f"Skipped — proposal not found: {proposal_path.name}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        _REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        rejected_path = _REJECTED_DIR / proposal_path.name
        proposal_path.rename(rejected_path)

        # Append rejection note to the archived file
        with rejected_path.open("a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n**Rejected at:** {timestamp}\n**Reason:** {reason}\n")

        # Record in audit log
        self._write_audit_entry(
            action="REJECTED",
            proposal_name=proposal_path.name,
            timestamp=timestamp,
            note=reason,
        )

        return f"Rejected: {proposal_path.name} — Reason: {reason}"

    # ── Internal: Audit log ───────────────────────────────────────────────────

    def _already_merged(self, proposal_path: Path) -> bool:
        """Return True if this proposal has already been recorded as merged."""
        if not _AUDIT_LOG_FILE.exists():
            return False
        audit_text = _AUDIT_LOG_FILE.read_text(encoding="utf-8")
        return (f"| APPROVED | {proposal_path.name}" in audit_text)

    def _write_audit_entry(
        self,
        action: str,
        proposal_name: str,
        timestamp: str,
        note: str = "",
    ) -> None:
        """Append a single row to the audit log Markdown table."""
        _AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        if not _AUDIT_LOG_FILE.exists():
            _AUDIT_LOG_FILE.write_text(
                "# Memory Governance Audit Log\n\n"
                "| Action | Proposal | Timestamp | Note |\n"
                "| :----- | :------- | :-------- | :--- |\n",
                encoding="utf-8",
            )

        with _AUDIT_LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(f"| {action} | {proposal_name} | {timestamp} | {note} |\n")

    def _extract_proposal_body(self, proposal_text: str) -> str:
        """
        Extract only the meaningful content from a proposal file,
        stripping the auto-generated header/footer.
        """
        # Find the first horizontal rule after the header, take everything after
        delimiter = "---"
        first_delim = proposal_text.find(delimiter)
        if first_delim == -1:
            return proposal_text.strip()

        body_start = first_delim + len(delimiter)
        # Strip the trailing governance footer line
        body = proposal_text[body_start:].strip()

        # Remove trailing "This proposal was generated..." line
        footer_marker = "*This proposal was generated automatically."
        footer_pos = body.rfind(footer_marker)
        if footer_pos != -1:
            body = body[:footer_pos].strip()

        # Remove trailing delimiter if present
        if body.endswith("---"):
            body = body[:-3].strip()

        return body
