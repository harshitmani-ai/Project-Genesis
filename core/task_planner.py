"""
core/task_planner.py

TaskPlanner — the Intelligent Task Planner for Project Genesis.

Architecture:
  The TaskPlanner sits between the founder's natural language request and the
  Worker Orchestrator. Instead of keyword matching, it uses the LLM to analyse
  intent, select the right workers, determine execution order, and produce a
  structured PlanningReport.

Routing logic:
  ┌───────────────────────────────────────────────────────────────────────┐
  │  Founder request (natural language)                                   │
  │       │                                                               │
  │       ▼                                                               │
  │  TaskPlanner.plan(request)                                            │
  │       │                                                               │
  │       ├── intent: "research"          → ResearchWorker only           │
  │       ├── intent: "acquisition"       → AcquisitionWorker only        │
  │       ├── intent: "marketing"         → MarketingWorker only          │
  │       ├── intent: "finance"           → FinanceWorker only            │
  │       ├── intent: "multi_worker"      → WorkerOrchestrator (sequence) │
  │       ├── intent: "general_question"  → answer_company_question()     │
  │       └── intent: "unknown"           → answer_company_question()     │
  │                                                                       │
  │  Returns: PlanningReport                                              │
  └───────────────────────────────────────────────────────────────────────┘

Design decisions:
  - The LLM returns a structured JSON plan.
  - Robust fallback parsing handles malformed LLM output gracefully.
  - A confidence score (0–100) is returned so genesis.py can decide whether
    to trust the plan or fall back to a general answer.
  - The planner is stateless and can be instantiated anywhere.

Phase 9: Intelligent Task Planner — No existing core files are modified.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from brain import ask_ai
from memory import load_company_context


# ── Constants ────────────────────────────────────────────────────────────────

AVAILABLE_WORKERS = ["research", "acquisition", "marketing", "finance"]

VALID_INTENTS = {
    "research",
    "acquisition",
    "marketing",
    "finance",
    "multi_worker",
    "general_question",
    "unknown",
}

# Minimum confidence level below which genesis.py falls back to a general answer
CONFIDENCE_THRESHOLD = 40


# ── PlanningReport ────────────────────────────────────────────────────────────

@dataclass
class PlanningReport:
    """
    Structured output of a TaskPlanner.plan() call.

    Fields:
        original_request  — The raw founder request as submitted.
        intent            — Classified intent string (see VALID_INTENTS).
        workers_selected  — List of worker keys selected by the planner.
        execution_order   — Ordered list of worker keys to run (may differ
                           from workers_selected if ordering was adjusted).
        reasoning         — Plain-English explanation of the planner's decision.
        confidence_score  — Integer 0–100 expressing the planner's certainty.
        cleaned_input     — The request with any ambiguous preamble removed,
                           ready to be passed directly to a worker.
    """

    original_request: str
    intent: str = "unknown"
    workers_selected: list[str] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)
    reasoning: str = ""
    confidence_score: int = 0
    cleaned_input: str = ""

    def __post_init__(self) -> None:
        if not self.cleaned_input:
            self.cleaned_input = self.original_request
        # Validate intent
        if self.intent not in VALID_INTENTS:
            self.intent = "unknown"
        # Confidence clamp
        self.confidence_score = max(0, min(100, self.confidence_score))

    @property
    def is_actionable(self) -> bool:
        """Return True if the plan can route to at least one worker."""
        return bool(self.execution_order) and self.confidence_score >= CONFIDENCE_THRESHOLD

    @property
    def is_multi_worker(self) -> bool:
        return len(self.execution_order) > 1

    def summary(self) -> str:
        """Return a compact, CLI-friendly summary of the plan."""
        lines = [
            f"[Planner] Intent     : {self.intent}",
            f"[Planner] Confidence : {self.confidence_score}/100",
            f"[Planner] Workers    : {' → '.join(w.title() for w in self.execution_order) or 'None'}",
            f"[Planner] Reasoning  : {self.reasoning}",
        ]
        return "\n".join(lines)


# ── TaskPlanner ───────────────────────────────────────────────────────────────

class TaskPlanner:
    """
    Intelligent Task Planner that uses the LLM to interpret founder intent
    and produce a structured PlanningReport.

    Usage:
        planner = TaskPlanner()
        plan = planner.plan("I want to build an AI product for dentists.")
        if plan.is_actionable:
            # Route to worker(s) based on plan.execution_order
    """

    # ── Public API ────────────────────────────────────────────────────────────

    def plan(self, request: str) -> PlanningReport:
        """
        Analyse the founder's request and return a PlanningReport.

        Args:
            request: The raw, unmodified founder request.

        Returns:
            A PlanningReport with intent, workers, execution order, and confidence.
        """
        if not request or not request.strip():
            return PlanningReport(
                original_request=request,
                intent="unknown",
                reasoning="Empty request received.",
                confidence_score=0,
            )

        try:
            raw_plan = self._call_planner_llm(request)
            report = self._parse_plan(request, raw_plan)
        except Exception as e:
            report = PlanningReport(
                original_request=request,
                intent="general_question",
                reasoning=f"Planner LLM failed — falling back to general answer. Error: {e}",
                confidence_score=20,
            )

        return report

    # ── Internal: LLM call ────────────────────────────────────────────────────

    def _call_planner_llm(self, request: str) -> str:
        """
        Call the LLM with a structured planning prompt and return the raw response.
        """
        company_context = load_company_context()

        prompt = f"""
You are the Task Planner for Project Genesis, Harshit's AI company.

Your job is to read the founder's request and produce a structured execution plan.

{company_context}

Available Workers (in priority order for multi-worker pipelines):
- research      → Market research, product ideas, opportunity analysis
- acquisition   → Lead generation, ICP building, outreach campaigns
- marketing     → Marketing strategy, landing page copy, email sequences
- finance       → Financial modelling, ROI, break-even, pricing strategy

Intent categories:
- research          → Founder wants to explore a market, find product ideas, validate opportunities
- acquisition       → Founder wants to find leads, customers, or run outreach
- marketing         → Founder wants marketing copy, campaigns, or positioning
- finance           → Founder wants financial modelling, pricing, or profitability analysis
- multi_worker      → Founder has a full business goal that needs multiple workers
- general_question  → Founder is asking a question about the company or strategy (no worker needed)
- unknown           → The request is unclear or cannot be mapped to any worker

Multi-worker rule: If the request involves building, launching, or evaluating a new product or business idea end-to-end, select multiple workers and set intent to "multi_worker".

Confidence scoring rules:
- 85–100: The request clearly maps to one or more workers.
- 60–84: The request likely maps, but some ambiguity exists.
- 40–59: Moderate uncertainty — might be a general question.
- 0–39: Cannot confidently determine — treat as general question.

Founder request:
{request}

Respond with ONLY a valid JSON object. No explanation. No markdown. No extra text.

Required JSON format:
{{
  "intent": "one of: research | acquisition | marketing | finance | multi_worker | general_question | unknown",
  "workers_selected": ["list", "of", "worker", "keys"],
  "execution_order": ["ordered", "list", "of", "worker", "keys"],
  "reasoning": "One or two sentences explaining why these workers were selected.",
  "confidence_score": 85,
  "cleaned_input": "The founder request stripped of meta-language, ready to pass to workers."
}}
"""

        return ask_ai(prompt)

    # ── Internal: Response parsing ────────────────────────────────────────────

    def _parse_plan(self, request: str, raw_response: str) -> PlanningReport:
        """
        Parse the LLM's JSON response into a PlanningReport.
        Falls back gracefully if JSON is malformed.
        """
        # Try to extract JSON block from the response
        json_text = self._extract_json(raw_response)

        try:
            data = json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            # LLM returned non-JSON — fall back to general question
            return PlanningReport(
                original_request=request,
                intent="general_question",
                reasoning="Planner could not parse structured response — treating as general question.",
                confidence_score=25,
                cleaned_input=request,
            )

        # Sanitise: filter worker keys to only valid ones
        workers_selected = [
            w for w in data.get("workers_selected", [])
            if w in AVAILABLE_WORKERS
        ]
        execution_order = [
            w for w in data.get("execution_order", [])
            if w in AVAILABLE_WORKERS
        ]

        # If execution_order is empty but workers_selected is not, use workers_selected
        if not execution_order and workers_selected:
            execution_order = workers_selected

        # Derive intent from execution_order if not provided
        intent = str(data.get("intent", "unknown")).lower()
        if intent not in VALID_INTENTS:
            if len(execution_order) > 1:
                intent = "multi_worker"
            elif len(execution_order) == 1:
                intent = execution_order[0]
            else:
                intent = "general_question"

        # If intent is a single worker name, set the execution order
        if intent in AVAILABLE_WORKERS and not execution_order:
            execution_order = [intent]
            workers_selected = [intent]

        confidence = int(data.get("confidence_score", 50))
        reasoning = str(data.get("reasoning", "")).strip()
        cleaned_input = str(data.get("cleaned_input", request)).strip()

        if not cleaned_input:
            cleaned_input = request

        return PlanningReport(
            original_request=request,
            intent=intent,
            workers_selected=workers_selected,
            execution_order=execution_order,
            reasoning=reasoning,
            confidence_score=confidence,
            cleaned_input=cleaned_input,
        )

    def _extract_json(self, text: str) -> str:
        """
        Extract the first JSON object from an LLM response.
        Handles cases where the LLM wraps JSON in markdown code blocks.
        """
        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*", "", text)

        # Find the outermost { ... } block
        start = text.find("{")
        if start == -1:
            return text.strip()

        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

        return text[start:].strip()
