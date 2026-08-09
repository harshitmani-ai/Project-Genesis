"""
core/orchestrator.py

WorkerOrchestrator — the multi-worker orchestration engine for Project Genesis.

Responsibilities:
  - Execute a sequence of workers to complete one business objective.
  - Pass each worker's result text forward as context for the next worker.
  - Collect every WorkerReport throughout the pipeline.
  - Continue when a worker fails (graceful degradation).
  - Produce a FinalCompanyReport summarising all outputs, failures, and next actions.

Architecture contract:
  - Does NOT modify BaseWorker or any individual worker.
  - Workers are identified by their registry key (e.g. "research", "finance").
  - The orchestrator is fed an external WORKER_REGISTRY dict at construction time
    to maintain full decoupling from genesis.py import order.

Phase 7: Multi-Worker Orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from brain import ask_ai
from core.worker_report import ReportStatus, WorkerReport


# ── FinalCompanyReport ────────────────────────────────────────────────────────

@dataclass
class FinalCompanyReport:
    """
    The consolidated output of a multi-worker orchestration run.

    Fields:
        goal                 — The original founder goal / business objective.
        workers_requested    — Ordered list of worker keys requested.
        workers_executed     — Workers that actually ran (may be a subset on failure).
        individual_reports   — WorkerReport for every worker that ran.
        combined_summary     — AI-synthesised summary of all individual outputs.
        risks                — Aggregated risks across all workers.
        next_actions         — Recommended actions for the Founder.
        failures             — Map of worker_key → error_message for any failures.
        completed_at         — ISO timestamp when the orchestration finished.
    """

    goal: str
    workers_requested: list[str] = field(default_factory=list)
    workers_executed: list[str] = field(default_factory=list)
    individual_reports: list[WorkerReport] = field(default_factory=list)
    combined_summary: str = ""
    risks: str = ""
    next_actions: str = ""
    failures: dict[str, str] = field(default_factory=dict)
    completed_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    # ── Convenience accessors ─────────────────────────────────────────────────

    @property
    def success_count(self) -> int:
        return sum(
            1 for r in self.individual_reports
            if r.status == ReportStatus.SUCCESS
        )

    @property
    def failure_count(self) -> int:
        return len(self.failures)

    @property
    def partial_count(self) -> int:
        return sum(
            1 for r in self.individual_reports
            if r.status == ReportStatus.PARTIAL
        )

    def to_markdown(self) -> str:
        """Render the FinalCompanyReport as a Markdown document."""
        lines = [
            "# Project Genesis — Final Company Report",
            "",
            f"**Completed:** {self.completed_at}",
            f"**Goal:** {self.goal}",
            "",
            "---",
            "",
            "## Workers Executed",
            "",
        ]

        for key in self.workers_requested:
            if key in self.failures:
                lines.append(f"- ❌ **{key.title()} Worker** — FAILED: {self.failures[key]}")
            elif key in self.workers_executed:
                # Find the report
                report = next(
                    (r for r in self.individual_reports if r.worker_name.lower().startswith(key)),
                    None,
                )
                status_icon = "✅" if (report and report.status == ReportStatus.SUCCESS) else "⚠️"
                lines.append(f"- {status_icon} **{key.title()} Worker** — {report.status.value if report else 'UNKNOWN'}")
            else:
                lines.append(f"- ⏭️ **{key.title()} Worker** — SKIPPED")

        lines += [
            "",
            "---",
            "",
            "## Individual Worker Summaries",
            "",
        ]

        for report in self.individual_reports:
            lines.append(f"### {report.worker_name}")
            lines.append(f"**Status:** {report.status.value}")
            lines.append(f"**Task:** {report.task_summary}")
            if report.error:
                lines.append(f"**Error:** {report.error}")
            lines.append("")

        lines += [
            "---",
            "",
            "## Combined Recommendation",
            "",
            self.combined_summary if self.combined_summary else "_No combined summary generated._",
            "",
            "---",
            "",
            "## Consolidated Risks",
            "",
            self.risks if self.risks else "_No risks identified._",
            "",
            "---",
            "",
            "## Next Actions for Founder",
            "",
            self.next_actions if self.next_actions else "_No next actions defined._",
            "",
            "---",
            "",
            "## Governance Notice",
            "",
            "This report was generated automatically by the Genesis Orchestration Engine.",
            "All recommendations require founder review and approval before action.",
            "",
        ]

        if self.failures:
            lines += [
                "---",
                "",
                "## Failure Log",
                "",
            ]
            for worker_key, error in self.failures.items():
                lines.append(f"- **{worker_key.title()} Worker:** {error}")
            lines.append("")

        return "\n".join(lines)


# ── WorkerOrchestrator ────────────────────────────────────────────────────────

ORCHESTRATION_REPORTS_FOLDER = Path("orchestration_reports")


class WorkerOrchestrator:
    """
    Coordinates multiple workers in sequence to fulfil one business objective.

    Design decisions:
      - Continues execution after a worker failure (graceful degradation).
      - Each worker receives the original goal PLUS the accumulated context
        from all previous workers' outputs, so later workers have richer input.
      - Produces a FinalCompanyReport synthesised by the LLM.
    """

    def __init__(self, worker_registry: dict[str, Any]) -> None:
        """
        Args:
            worker_registry: A dict mapping worker keys to instantiated worker objects.
                             Example: {"research": ResearchWorker(), "finance": FinanceWorker()}
        """
        self._registry = worker_registry

    # ── Public API ────────────────────────────────────────────────────────────

    def run(
        self,
        goal: str,
        worker_sequence: list[str],
    ) -> FinalCompanyReport:
        """
        Execute the given list of workers in order and return a FinalCompanyReport.

        Args:
            goal:            The founder's business objective.
            worker_sequence: Ordered list of worker registry keys to run.

        Returns:
            A FinalCompanyReport containing all worker outputs and synthesis.
        """
        print(f"\n[Orchestrator] Starting multi-worker pipeline for goal: '{goal}'")
        print(f"[Orchestrator] Worker sequence: {' → '.join(w.title() for w in worker_sequence)}")
        print()

        final_report = FinalCompanyReport(
            goal=goal,
            workers_requested=list(worker_sequence),
        )

        # Accumulate context across workers.  Each worker gets the goal plus
        # a running summary of what previous workers produced.
        accumulated_context: list[str] = []

        for worker_key in worker_sequence:
            worker = self._registry.get(worker_key)

            if worker is None:
                error_msg = f"Worker key '{worker_key}' not found in registry."
                print(f"[Orchestrator] ⚠ Skipping unknown worker: '{worker_key}'")
                final_report.failures[worker_key] = error_msg
                continue

            # Build the task for this worker: original goal + prior context
            if accumulated_context:
                task_input = (
                    f"{goal}\n\n"
                    f"--- Context from previous workers ---\n"
                    + "\n\n".join(accumulated_context)
                )
            else:
                task_input = goal

            print(f"[Orchestrator] ▶ Running: {worker_key.title()} Worker…")

            worker_report: WorkerReport = worker.run_lifecycle(task_input)
            final_report.individual_reports.append(worker_report)

            if worker_report.status == ReportStatus.FAILURE:
                print(f"[Orchestrator] ✗ {worker_key.title()} Worker FAILED — continuing pipeline.")
                final_report.failures[worker_key] = worker_report.error or "Unknown failure"
                # Do not add failed output to accumulated context — keep quality high.
                continue

            final_report.workers_executed.append(worker_key)
            print(f"[Orchestrator] ✓ {worker_key.title()} Worker COMPLETED.")

            # Extract result text from the worker's report for downstream context.
            result_text = self._extract_result_text(worker_report)
            if result_text:
                accumulated_context.append(
                    f"=== {worker.identity.name} Output ===\n{result_text[:3000]}"
                )

        # Synthesise the combined report using LLM
        print("\n[Orchestrator] Synthesising FinalCompanyReport…")
        self._synthesise_final_report(final_report, accumulated_context)

        # Save the report to disk
        report_path = self._save_final_report(final_report)
        print(f"[Orchestrator] ✓ FinalCompanyReport saved: {report_path}")

        return final_report

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _extract_result_text(self, report: WorkerReport) -> str:
        """
        Extract text content from a WorkerReport's result field.
        Workers return (result_text, report_path) tuples — we want the text.
        """
        result = report.result
        if result is None:
            return ""
        if isinstance(result, tuple) and len(result) >= 1:
            return str(result[0])
        return str(result)

    def _synthesise_final_report(
        self,
        final_report: FinalCompanyReport,
        accumulated_context: list[str],
    ) -> None:
        """
        Use the LLM to generate the combined recommendation, risks, and next actions.
        Updates final_report in place.
        """
        if not accumulated_context:
            final_report.combined_summary = "No worker outputs were available for synthesis."
            final_report.risks = "N/A — no successful worker outputs."
            final_report.next_actions = "Review individual worker failure logs and retry."
            return

        workers_summary = ", ".join(
            f"{k.title()} Worker" for k in final_report.workers_executed
        )
        failure_note = ""
        if final_report.failures:
            failed = ", ".join(f"{k.title()} Worker" for k in final_report.failures)
            failure_note = f"\n\nNote: The following workers FAILED and are excluded from synthesis: {failed}"

        combined_outputs = "\n\n".join(accumulated_context)

        prompt = f"""
You are Genesis, Harshit's AI company partner.

A multi-worker orchestration pipeline has completed for the following founder goal:

GOAL: {final_report.goal}

Workers executed successfully: {workers_summary}{failure_note}

Below are the condensed outputs from each worker:

{combined_outputs}

Based on the above, produce three clearly separated sections:

## Combined Recommendation
A concise, actionable synthesis of all worker outputs. What should Harshit do first?

## Consolidated Risks
Top 5 combined risks across all dimensions (market, technical, financial, acquisition, marketing).

## Next Actions for Founder
A numbered list of the 5 most important immediate next steps Harshit should take.

Rules:
- Be direct, specific, and honest.
- Do not fabricate numbers not present in the worker outputs.
- Follow the Project Genesis Constitution (profit-first, honest value).
"""

        try:
            synthesis = ask_ai(prompt)
            # Parse out the three sections
            final_report.combined_summary = self._extract_section(
                synthesis, "Combined Recommendation"
            )
            final_report.risks = self._extract_section(
                synthesis, "Consolidated Risks"
            )
            final_report.next_actions = self._extract_section(
                synthesis, "Next Actions for Founder"
            )
        except Exception as e:
            final_report.combined_summary = f"Synthesis failed: {e}"
            final_report.risks = "Could not extract — see combined_summary."
            final_report.next_actions = "Review individual worker reports."

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a named Markdown section from a block of text."""
        marker = f"## {section_name}"
        start = text.find(marker)
        if start == -1:
            return text  # Return full text if section not found

        content_start = start + len(marker)
        # Find the next ## heading
        next_section = text.find("\n## ", content_start)
        if next_section == -1:
            return text[content_start:].strip()
        return text[content_start:next_section].strip()

    def _save_final_report(self, final_report: FinalCompanyReport) -> Path:
        """Write the FinalCompanyReport Markdown to disk."""
        ORCHESTRATION_REPORTS_FOLDER.mkdir(exist_ok=True)
        existing = list(ORCHESTRATION_REPORTS_FOLDER.glob("company_report_*.md"))
        next_number = len(existing) + 1
        report_path = ORCHESTRATION_REPORTS_FOLDER / f"company_report_{next_number:03}.md"

        report_path.write_text(final_report.to_markdown(), encoding="utf-8")
        return report_path
