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

    # ── Public: Proposal Review Dashboard & Metadata Extraction ───────────────

    def get_active_product(self) -> str:
        """Dynamically read the active company product from company_memory.md."""
        if not _COMPANY_MEMORY_FILE.exists():
            return "DentalReview AI"
        text = _COMPANY_MEMORY_FILE.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "Current Product:" in line or "Current Target Product:" in line or "Target Product:" in line:
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()
        return "DentalReview AI"

    def parse_proposal_metadata(
        self,
        path: Path,
        index: int,
        all_proposals: list[Path],
    ) -> dict[str, str | bool | int]:
        """
        Parse metadata from a proposal file locally without calling an LLM.

        Returns dict containing:
          index, path, name, worker, topic, date, report_location,
          summary, duplicate_status, is_duplicate, relevance, recommendation
        """
        raw_text = path.read_text(encoding="utf-8")
        lines = raw_text.splitlines()

        worker = "Unknown Worker"
        topic = "General Update"
        date = "Unknown Date"
        report_loc = "N/A"

        for line in lines[:25]:
            l_strip = line.strip()
            if l_strip.startswith("**Worker:**") or l_strip.startswith("Worker:"):
                worker = l_strip.split(":", 1)[1].strip("* ").strip()
            elif l_strip.startswith("**Topic:**") or l_strip.startswith("Topic:"):
                topic = l_strip.split(":", 1)[1].strip("* ").strip()
            elif l_strip.startswith("**Proposed at:**") or l_strip.startswith("Proposed at:") or l_strip.startswith("Date:"):
                date = l_strip.split(":", 1)[1].strip("* ").strip()
            elif l_strip.startswith("**Report location:**") or l_strip.startswith("Report location:") or l_strip.startswith("Report:"):
                report_loc = l_strip.split(":", 1)[1].strip("* ").strip()

        # Generate local 2-3 line summary (max 160 chars) without LLM
        body = self._extract_proposal_body(raw_text)
        substance_lines = []
        for line in body.splitlines():
            line_s = line.strip()
            if line_s and not line_s.startswith("#") and not line_s.startswith("*") and not line_s.startswith("-") and not line_s.startswith("|"):
                substance_lines.append(line_s)
        
        summary_raw = " ".join(substance_lines) if substance_lines else topic
        if len(summary_raw) > 160:
            summary = summary_raw[:157].rstrip() + "..."
        else:
            summary = summary_raw

        # Duplicate Detection
        duplicate_status = "None"
        is_duplicate = False

        if self._already_merged(path):
            duplicate_status = "Already Merged"
            is_duplicate = True
        else:
            # Check sibling proposals created earlier in list
            for prev_idx, prev_path in enumerate(all_proposals[: index - 1], start=1):
                if prev_path.exists():
                    prev_text = prev_path.read_text(encoding="utf-8")
                    if report_loc != "N/A" and report_loc in prev_text:
                        duplicate_status = f"Duplicate of Proposal #{prev_idx}"
                        is_duplicate = True
                        break
                    if topic and len(topic) > 15 and topic in prev_text:
                        duplicate_status = f"Duplicate of Proposal #{prev_idx}"
                        is_duplicate = True
                        break

        # Dynamic Product Relevance & Recommendation Engine
        active_product = self.get_active_product()
        active_keywords = [k.lower() for k in active_product.replace("-", " ").split()]
        if "dentalreview" in active_product.lower():
            active_keywords.extend(["dental", "google review", "review", "clinic"])

        archived_keywords = ["dentishield", "no-show", "waitlist", "scheduling tool"]

        raw_lower = raw_text.lower()
        topic_lower = topic.lower()

        matches_active = any(k in topic_lower or k in raw_lower for k in active_keywords)
        matches_archived = any(k in topic_lower or k in raw_lower for k in archived_keywords) and not matches_active

        if is_duplicate:
            relevance = "DUPLICATE"
            recommendation = "❌ Reject"
        elif matches_archived:
            relevance = "🗂 Archived Product"
            recommendation = "🗂 Archived Product"
        elif matches_active:
            relevance = f"HIGH ({active_product})"
            recommendation = "✅ Approve"
        else:
            relevance = "MEDIUM"
            recommendation = "⚠️ Founder Decision"

        return {
            "index": index,
            "path": path,
            "name": path.name,
            "worker": worker,
            "topic": topic,
            "date": date,
            "report_location": report_loc,
            "summary": summary,
            "duplicate_status": duplicate_status,
            "is_duplicate": is_duplicate,
            "relevance": relevance,
            "recommendation": recommendation,
        }

    def build_proposal_dashboard(self) -> str:
        """
        Scan all pending proposals locally and build a comprehensive
        Proposal Review Dashboard table & footer summary. Zero LLM calls.
        """
        proposals = self.list_proposals()
        if not proposals:
            return "No pending memory proposals found. Company memory is 100% up to date."

        active_product = self.get_active_product()
        meta_list = [self.parse_proposal_metadata(p, i, proposals) for i, p in enumerate(proposals, start=1)]

        approve_ids = [m["index"] for m in meta_list if m["recommendation"] == "✅ Approve"]
        reject_ids = [m["index"] for m in meta_list if m["recommendation"] == "❌ Reject"]
        archived_ids = [m["index"] for m in meta_list if m["recommendation"] == "🗂 Archived Product"]
        needs_review_ids = [m["index"] for m in meta_list if m["recommendation"] == "⚠️ Founder Decision"]

        div_heavy = "═" * 84
        div_thin  = "─" * 84

        lines = [
            div_heavy,
            "                     GENESIS PROPOSAL REVIEW DASHBOARD                     ",
            f"                     Current Active Product: {active_product}",
            div_heavy,
            "",
        ]

        for m in meta_list:
            lines.append(f"[#{m['index']}] {m['name']}")
            lines.append(f"  Worker:       {m['worker']}")
            lines.append(f"  Topic:        {m['topic']}")
            lines.append(f"  Date:         {m['date']}")
            lines.append(f"  Report:       {m['report_location']}")
            lines.append(f"  Summary:      {m['summary']}")
            lines.append(f"  Duplicate:    {m['duplicate_status']}")
            lines.append(f"  Relevance:    {m['relevance']}")
            lines.append(f"  Action:       {m['recommendation']}")
            lines.append(div_thin)

        lines.extend([
            "",
            div_heavy,
            "PROPOSAL REVIEW DASHBOARD SUMMARY",
            div_heavy,
            f"Current Active Product:      {active_product}",
            f"Pending Proposals:           {len(meta_list)}",
            f"Current Product Proposals:   {len(approve_ids)}",
            f"Archived Product Proposals:  {len(archived_ids)}",
            f"Possible Duplicates:         {len(reject_ids)}",
            f"Needs Founder Review:        {len(needs_review_ids)}",
            "Estimated Review Time:       < 1 min (using batch commands)",
            "",
            "RECOMMENDED BATCH ACTIONS:",
            "",
            "Approve (Current Product):",
            f"  approve selected {','.join(str(i) for i in approve_ids)}" if approve_ids else "  [None]",
            "",
            "Reject (Duplicates / Failed):",
            f"  reject selected {','.join(str(i) for i in reject_ids)}" if reject_ids else "  [None]",
            "",
            "Archived Product (Previous Directions — Founder Decision):",
            f"  {archived_ids}" if archived_ids else "  [None]",
            "",
            "Needs Founder Review:",
            f"  {needs_review_ids}" if needs_review_ids else "  [None]",
            "",
            "Use 'approve selected <ids>' or 'reject selected <ids>' to process.",
            div_heavy,
        ])

        return "\n".join(lines)

    # ── Public: Identifier Resolution & Review ─────────────────────────

    def resolve_proposal(self, identifier: str | int | None = None) -> tuple[Path | None, str | None]:
        """
        Resolve a proposal identifier (1-based index or filename/stem) to a Path.

        Returns:
            (proposal_path, None) if resolved successfully.
            (None, error_message) if resolution failed.
        """
        proposals = self.list_proposals()
        if not proposals:
            return None, "No pending memory proposals found."

        if identifier is None or str(identifier).strip() == "":
            return proposals[0], None

        id_str = str(identifier).strip()

        # Case 1: Numeric index (1-based)
        if id_str.isdigit():
            idx = int(id_str)
            if 1 <= idx <= len(proposals):
                return proposals[idx - 1], None
            return None, f"Invalid proposal number '{id_str}'. Available pending proposals: 1 to {len(proposals)}."

        # Case 2: Exact filename or stem match
        for p in proposals:
            if p.name.lower() == id_str.lower() or p.stem.lower() == id_str.lower():
                return p, None

        return None, f"Proposal '{id_str}' not found in pending proposals."

    def review_proposal(self, identifier: str | int | None = None) -> str:
        """
        Return the raw markdown content of a specific proposal locally,
        with zero AI/LLM involvement.
        """
        proposal_path, error = self.resolve_proposal(identifier)
        if error:
            return error

        content = proposal_path.read_text(encoding="utf-8")
        divider = "═" * 80
        return (
            f"\n{divider}\n"
            f"  MEMORY PROPOSAL FILE: {proposal_path.name}\n"
            f"  Path: {proposal_path.resolve()}\n"
            f"{divider}\n\n"
            f"{content}\n"
        )

    def approve_selected(self, indices: list[int]) -> list[str]:
        """Approve a list of 1-based proposal indices in batch."""
        if not indices:
            return ["No proposal indices specified for batch approval."]

        proposals = self.list_proposals()
        if not proposals:
            return ["No pending memory proposals found to approve."]

        results = []
        for idx in indices:
            path, err = self.resolve_proposal(idx)
            if err:
                results.append(f"Index {idx}: {err}")
            else:
                res = self.approve(path)
                results.append(f"Index {idx} ({path.name}): {res}")
        return results

    def reject_selected(self, indices: list[int], reason: str = "Rejected in Batch") -> list[str]:
        """Reject a list of 1-based proposal indices in batch."""
        if not indices:
            return ["No proposal indices specified for batch rejection."]

        proposals = self.list_proposals()
        if not proposals:
            return ["No pending memory proposals found to reject."]

        results = []
        for idx in indices:
            path, err = self.resolve_proposal(idx)
            if err:
                results.append(f"Index {idx}: {err}")
            else:
                res = self.reject(path, reason=reason)
                results.append(f"Index {idx} ({path.name}): {res}")
        return results

    def approve_single(self, identifier: str | int | None = None) -> str:
        """Approve and merge a single proposal by its 1-based index or filename."""
        proposal_path, error = self.resolve_proposal(identifier)
        if error:
            return error
        return self.approve(proposal_path)

    def reject_single(self, identifier: str | int | None = None, reason: str = "Rejected by Founder") -> str:
        """Reject a single proposal by its 1-based index or filename."""
        proposal_path, error = self.resolve_proposal(identifier)
        if error:
            return error
        return self.reject(proposal_path, reason=reason)

    def reject_all(self, reason: str = "Rejected all by Founder") -> list[str]:
        """Reject all pending proposals."""
        proposals = self.list_proposals()
        if not proposals:
            return ["No pending proposals to reject."]

        results = []
        for proposal_path in proposals:
            result = self.reject(proposal_path, reason=reason)
            results.append(result)
        return results


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

        return body


# ── ProposalManager Alias ───────────────────────────────────────────────────
ProposalManager = MemoryGovernor
DEFAULT_PROPOSAL_MANAGER = MemoryGovernor()

