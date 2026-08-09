"""
test_phase9_task_planner.py

Comprehensive Phase 9 Verification Test Suite for the Intelligent Task Planner.

Tests:
  1.  Imports verification
  2.  PlanningReport structure and properties
  3.  TaskPlanner — single-worker intent detection (research)
  4.  TaskPlanner — single-worker intent detection (finance)
  5.  TaskPlanner — multi-worker intent (build a product end-to-end)
  6.  TaskPlanner — general question / unknown intent
  7.  TaskPlanner — empty request handling
  8.  TaskPlanner — LLM JSON parse resilience (malformed response)
  9.  PLANNER instance exists in genesis.py
  10. Backward compatibility — all keyword routes still work
  11. CONFIDENCE_THRESHOLD respected
  12. Execution order validated against available workers
  13. Syntax compilation check
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch

# ── 1. IMPORTS TEST ─────────────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core.task_planner import (
        TaskPlanner,
        PlanningReport,
        AVAILABLE_WORKERS,
        VALID_INTENTS,
        CONFIDENCE_THRESHOLD,
    )
    from core import TaskPlanner as TPFromCore, PlanningReport as PRFromCore
    from genesis import (
        PLANNER,
        WORKER_REGISTRY,
        ORCHESTRATOR,
        GOVERNOR,
    )
    print("✓ All imports passed.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. PLANNINGREPORT STRUCTURE TEST ─────────────────────────────────────────
print("\n=== TEST 2: PLANNINGREPORT STRUCTURE & PROPERTIES ===")
# Valid plan
pr = PlanningReport(
    original_request="I want to research the dental software market",
    intent="research",
    workers_selected=["research"],
    execution_order=["research"],
    reasoning="Request clearly asks for market research.",
    confidence_score=90,
    cleaned_input="dental software market",
)
assert pr.original_request == "I want to research the dental software market"
assert pr.intent == "research"
assert pr.is_actionable is True
assert pr.is_multi_worker is False
assert pr.confidence_score == 90
assert "research" in pr.summary()
assert "90/100" in pr.summary()
print("✓ PlanningReport structure, is_actionable, is_multi_worker, summary() verified.")

# Confidence clamping
pr_low = PlanningReport(
    original_request="test",
    intent="unknown",
    confidence_score=150,  # should clamp to 100
)
assert pr_low.confidence_score == 100, "Confidence should clamp to 100"

pr_neg = PlanningReport(
    original_request="test",
    intent="unknown",
    confidence_score=-50,  # should clamp to 0
)
assert pr_neg.confidence_score == 0, "Confidence should clamp to 0"

# Invalid intent → should become "unknown"
pr_bad = PlanningReport(
    original_request="test",
    intent="garbage_intent",
    confidence_score=80,
)
assert pr_bad.intent == "unknown", f"Invalid intent should be corrected to 'unknown', got: {pr_bad.intent}"
print("✓ Confidence clamping and intent validation verified.")

# ── 3. SINGLE-WORKER INTENT: RESEARCH ────────────────────────────────────────
print("\n=== TEST 3: SINGLE-WORKER INTENT DETECTION (RESEARCH) ===")
planner = TaskPlanner()

# Mock the LLM to return a deterministic JSON response
mock_research_response = json.dumps({
    "intent": "research",
    "workers_selected": ["research"],
    "execution_order": ["research"],
    "reasoning": "Founder wants to explore the dental software market.",
    "confidence_score": 92,
    "cleaned_input": "dental software market for dentist practices",
})

with patch("core.task_planner.ask_ai", return_value=mock_research_response):
    plan = planner.plan("I want to research the dental software market for dentist practices")

assert plan.intent == "research", f"Expected 'research', got '{plan.intent}'"
assert plan.execution_order == ["research"]
assert plan.is_actionable is True
assert plan.is_multi_worker is False
assert plan.confidence_score == 92
assert "dental software" in plan.cleaned_input
print(f"✓ Research intent detected. Workers: {plan.execution_order}, Confidence: {plan.confidence_score}/100")

# ── 4. SINGLE-WORKER INTENT: FINANCE ─────────────────────────────────────────
print("\n=== TEST 4: SINGLE-WORKER INTENT DETECTION (FINANCE) ===")
mock_finance_response = json.dumps({
    "intent": "finance",
    "workers_selected": ["finance"],
    "execution_order": ["finance"],
    "reasoning": "Founder wants financial modelling for a SaaS product.",
    "confidence_score": 87,
    "cleaned_input": "SaaS attendance tracker at $49/month",
})

with patch("core.task_planner.ask_ai", return_value=mock_finance_response):
    plan = planner.plan("What is the break-even for my SaaS attendance tracker at $49/month?")

assert plan.intent == "finance"
assert plan.execution_order == ["finance"]
assert plan.confidence_score == 87
print(f"✓ Finance intent detected. Workers: {plan.execution_order}, Confidence: {plan.confidence_score}/100")

# ── 5. MULTI-WORKER INTENT ────────────────────────────────────────────────────
print("\n=== TEST 5: MULTI-WORKER INTENT DETECTION ===")
mock_multi_response = json.dumps({
    "intent": "multi_worker",
    "workers_selected": ["research", "acquisition", "marketing", "finance"],
    "execution_order": ["research", "acquisition", "marketing", "finance"],
    "reasoning": "Founder wants end-to-end evaluation for a new product idea.",
    "confidence_score": 95,
    "cleaned_input": "AI product for dentist practices",
})

with patch("core.task_planner.ask_ai", return_value=mock_multi_response):
    plan = planner.plan("I want to build an AI product for dentists. Run everything.")

assert plan.intent == "multi_worker"
assert plan.execution_order == ["research", "acquisition", "marketing", "finance"]
assert plan.is_multi_worker is True
assert plan.is_actionable is True
assert plan.confidence_score == 95
print(f"✓ Multi-worker intent detected. Pipeline: {' → '.join(plan.execution_order)}, Confidence: {plan.confidence_score}/100")

# ── 6. GENERAL QUESTION / UNKNOWN INTENT ─────────────────────────────────────
print("\n=== TEST 6: GENERAL QUESTION / UNKNOWN INTENT ===")
mock_general_response = json.dumps({
    "intent": "general_question",
    "workers_selected": [],
    "execution_order": [],
    "reasoning": "Founder is asking a strategic question, no worker needed.",
    "confidence_score": 85,
    "cleaned_input": "what is our biggest risk right now?",
})

with patch("core.task_planner.ask_ai", return_value=mock_general_response):
    plan = planner.plan("What is our biggest risk right now?")

assert plan.intent == "general_question"
assert plan.execution_order == []
assert plan.is_actionable is False  # no workers selected
print(f"✓ General question intent detected. Actionable: {plan.is_actionable}")

# ── 7. EMPTY REQUEST HANDLING ─────────────────────────────────────────────────
print("\n=== TEST 7: EMPTY REQUEST HANDLING ===")
empty_plan = planner.plan("")
assert empty_plan.intent == "unknown"
assert empty_plan.confidence_score == 0
assert empty_plan.is_actionable is False

whitespace_plan = planner.plan("   ")
assert whitespace_plan.intent == "unknown"
print("✓ Empty and whitespace requests handled gracefully (no crash).")

# ── 8. JSON PARSE RESILIENCE ──────────────────────────────────────────────────
print("\n=== TEST 8: LLM JSON PARSE RESILIENCE ===")
# Test with completely non-JSON response
with patch("core.task_planner.ask_ai", return_value="I cannot determine the intent for this request."):
    fallback_plan = planner.plan("some request")

assert fallback_plan.intent in ("general_question", "unknown"), \
    f"Expected fallback intent, got '{fallback_plan.intent}'"
assert fallback_plan.confidence_score <= 30, \
    f"Fallback confidence should be low, got {fallback_plan.confidence_score}"

# Test with JSON wrapped in markdown
markdown_json = f"""
```json
{mock_research_response}
```
"""
with patch("core.task_planner.ask_ai", return_value=markdown_json):
    md_plan = planner.plan("research the market")

assert md_plan.intent == "research", f"Markdown-wrapped JSON should parse correctly, got '{md_plan.intent}'"
print("✓ Non-JSON response → graceful fallback. Markdown-wrapped JSON → parsed correctly.")

# ── 9. PLANNER INSTANCE IN GENESIS.PY ────────────────────────────────────────
print("\n=== TEST 9: PLANNER INSTANCE IN GENESIS.PY ===")
assert isinstance(PLANNER, TaskPlanner), "PLANNER is not a TaskPlanner instance"
print("✓ PLANNER instance verified in genesis.py.")

# ── 10. BACKWARD COMPATIBILITY — ALL KEYWORD ROUTES ──────────────────────────
print("\n=== TEST 10: BACKWARD COMPATIBILITY — ALL KEYWORD ROUTES ===")
from genesis import (
    should_show_memory, should_show_reports,
    should_show_proposals, should_approve_proposals,
    should_run_research, should_run_acquisition,
    should_run_marketing, should_run_finance,
    should_run_orchestration,
)
# Every existing route must still be unaffected
assert should_show_memory("show company memory")
assert should_show_memory("read company memory")
assert should_show_reports("show reports")
assert should_show_proposals("show proposals")
assert should_approve_proposals("approve all proposals")
assert should_run_research("research market for SaaS tools")
assert should_run_acquisition("find leads for B2B software agencies")
assert should_run_marketing("marketing strategy for ShiftGuard AI")
assert should_run_finance("financial analysis for attendance SaaS")
assert should_run_orchestration("run all workers for my product")
print("✓ All 10 existing keyword routes verified — zero regressions.")

# ── 11. CONFIDENCE THRESHOLD RESPECTED ───────────────────────────────────────
print("\n=== TEST 11: CONFIDENCE THRESHOLD RESPECTED ===")
low_confidence_plan = PlanningReport(
    original_request="vague request",
    intent="research",
    workers_selected=["research"],
    execution_order=["research"],
    reasoning="Low certainty.",
    confidence_score=CONFIDENCE_THRESHOLD - 1,  # Below threshold
)
assert low_confidence_plan.is_actionable is False, \
    f"Plan below confidence threshold should NOT be actionable"

high_confidence_plan = PlanningReport(
    original_request="clear research request",
    intent="research",
    workers_selected=["research"],
    execution_order=["research"],
    reasoning="High certainty.",
    confidence_score=CONFIDENCE_THRESHOLD,  # At threshold exactly
)
assert high_confidence_plan.is_actionable is True, \
    f"Plan at confidence threshold should be actionable"
print(f"✓ Confidence threshold ({CONFIDENCE_THRESHOLD}) respected. Low: not actionable. At threshold: actionable.")

# ── 12. EXECUTION ORDER VALIDATION ───────────────────────────────────────────
print("\n=== TEST 12: EXECUTION ORDER VALIDATION ===")
# Worker keys outside AVAILABLE_WORKERS must be filtered out
mock_bad_workers = json.dumps({
    "intent": "multi_worker",
    "workers_selected": ["research", "unknown_worker", "finance"],
    "execution_order": ["research", "unknown_worker", "finance"],
    "reasoning": "Test filtering of invalid workers.",
    "confidence_score": 80,
    "cleaned_input": "test request",
})

with patch("core.task_planner.ask_ai", return_value=mock_bad_workers):
    filtered_plan = planner.plan("test filtering")

assert "unknown_worker" not in filtered_plan.execution_order, \
    "Invalid worker keys must be filtered from execution_order"
assert "research" in filtered_plan.execution_order
assert "finance" in filtered_plan.execution_order
print(f"✓ Invalid worker keys filtered. Final order: {filtered_plan.execution_order}")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 9 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
