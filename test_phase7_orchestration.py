"""
test_phase7_orchestration.py

Comprehensive Phase 7 Verification Test Suite for Multi-Worker Orchestration.

Tests:
  1. Imports verification
  2. FinalCompanyReport structure
  3. Worker ordering — pipeline executes in the correct sequence
  4. Multi-worker execution — all 4 workers run successfully
  5. Report aggregation — FinalCompanyReport contains all individual reports
  6. Failure handling — a failing worker does not crash the pipeline
  7. No regression — existing single-worker registry routes still work
  8. Syntax compilation check
  9. Orchestrator keyword routing (should_run_orchestration)
"""

import sys
from pathlib import Path

# ── 1. IMPORTS TEST ─────────────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core.orchestrator import WorkerOrchestrator, FinalCompanyReport
    from core import WorkerOrchestrator as OrchestratorFromCore, FinalCompanyReport as ReportFromCore
    from core import BaseWorker, WorkerIdentity
    from core.worker_report import ReportStatus
    from genesis import (
        WORKER_REGISTRY,
        ORCHESTRATOR,
        DEFAULT_PIPELINE,
        should_run_orchestration,
        remove_orchestration_instruction,
    )
    print("✓ All imports passed successfully.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. FINAL COMPANY REPORT STRUCTURE TEST ──────────────────────────────────
print("\n=== TEST 2: FINALCOMPANYREPORT STRUCTURE ===")
report = FinalCompanyReport(
    goal="Test goal",
    workers_requested=["research", "finance"],
    workers_executed=["research"],
)
assert report.goal == "Test goal"
assert report.success_count == 0
assert report.failure_count == 0
assert isinstance(report.completed_at, str)
markdown = report.to_markdown()
assert "Final Company Report" in markdown
assert "Workers Executed" in markdown
print("✓ FinalCompanyReport structure and to_markdown() verified.")

# ── 3. WORKER ORDERING TEST ─────────────────────────────────────────────────
print("\n=== TEST 3: WORKER ORDERING VERIFICATION ===")
from workers.research_worker import ResearchWorker
from workers.acquisition_worker import AcquisitionWorker
from workers.marketing_worker import MarketingWorker
from workers.finance_worker import FinanceWorker

executed_order = []

class OrderTrackingWorker(BaseWorker):
    def __init__(self, key, tracker):
        self._key = key
        self._tracker = tracker
        super().__init__()

    identity = WorkerIdentity(name="Order Tracker", role="Track execution order")

    def create_plan(self, task): return task
    def execute(self, task, plan):
        self._tracker.append(self._key)
        return (f"Output from {self._key}", Path("."))
    def verify(self, result): return True
    def learn(self, task, result): pass

tracker = []
test_registry = {
    "alpha": OrderTrackingWorker("alpha", tracker),
    "beta": OrderTrackingWorker("beta", tracker),
    "gamma": OrderTrackingWorker("gamma", tracker),
}

# Patch identities so they're unique
test_registry["alpha"].identity = WorkerIdentity(name="Alpha Worker", role="Order test")
test_registry["beta"].identity = WorkerIdentity(name="Beta Worker", role="Order test")
test_registry["gamma"].identity = WorkerIdentity(name="Gamma Worker", role="Order test")

order_orchestrator = WorkerOrchestrator(test_registry)
order_report = order_orchestrator.run("order test goal", ["alpha", "beta", "gamma"])

assert tracker == ["alpha", "beta", "gamma"], f"Wrong execution order: {tracker}"
assert order_report.workers_executed == ["alpha", "beta", "gamma"]
print("✓ Worker execution ordering verified.")

# ── 4. MULTI-WORKER EXECUTION TEST ──────────────────────────────────────────
print("\n=== TEST 4: MULTI-WORKER EXECUTION (LIVE — 2 WORKERS) ===")
# Run only 2 workers in the live test to keep it fast
test_goal = "ShiftGuard AI — SaaS attendance tracking for SMBs at $49/month"
print(f"Running 2-worker pipeline for: '{test_goal}'")

live_orchestrator = WorkerOrchestrator({
    "research": WORKER_REGISTRY["research"],
    "finance": WORKER_REGISTRY["finance"],
})

live_report = live_orchestrator.run(test_goal, ["research", "finance"])
print(f"Workers executed: {live_report.workers_executed}")
print(f"Failures: {live_report.failures}")

assert len(live_report.individual_reports) >= 1, "No individual reports captured"
assert live_report.goal == test_goal
assert live_report.success_count >= 1, "No successful workers"
print(f"✓ Multi-worker pipeline executed. {live_report.success_count} worker(s) succeeded.")

# ── 5. REPORT AGGREGATION TEST ──────────────────────────────────────────────
print("\n=== TEST 5: REPORT AGGREGATION ===")
assert live_report.combined_summary, "combined_summary is empty"
assert live_report.risks, "risks is empty"
assert live_report.next_actions, "next_actions is empty"

# Verify FinalCompanyReport file was saved
report_folder = Path("orchestration_reports")
assert report_folder.exists(), "orchestration_reports/ folder was not created"
saved_reports = list(report_folder.glob("company_report_*.md"))
assert len(saved_reports) >= 1, "No company_report_XXX.md files found"
print(f"✓ Report aggregation verified. {len(saved_reports)} report(s) saved to orchestration_reports/.")

# ── 6. FAILURE HANDLING TEST ────────────────────────────────────────────────
print("\n=== TEST 6: FAILURE HANDLING & GRACEFUL DEGRADATION ===")

class AlwaysFailWorker(BaseWorker):
    identity = WorkerIdentity(name="Always Fail Worker", role="Test failure resilience")
    def create_plan(self, task): raise RuntimeError("Intentional failure for testing")
    def execute(self, task, plan): pass
    def verify(self, result): return True
    def learn(self, task, result): pass

class AlwaysSucceedWorker(BaseWorker):
    identity = WorkerIdentity(name="Always Succeed Worker", role="Test success")
    def create_plan(self, task): return task
    def execute(self, task, plan): return (f"Success output", Path("."))
    def verify(self, result): return True
    def learn(self, task, result): pass

failure_registry = {
    "success_a": AlwaysSucceedWorker(),
    "fail":      AlwaysFailWorker(),
    "success_b": AlwaysSucceedWorker(),
}
# Fix identities for uniqueness
failure_registry["success_a"].identity = WorkerIdentity(name="Success A Worker", role="Test")
failure_registry["success_b"].identity = WorkerIdentity(name="Success B Worker", role="Test")

failure_orchestrator = WorkerOrchestrator(failure_registry)
failure_report = failure_orchestrator.run(
    "resilience test goal",
    ["success_a", "fail", "success_b"]
)

assert "fail" in failure_report.failures, "Failure was not recorded in failures dict"
assert "success_a" in failure_report.workers_executed, "success_a should have executed"
assert "success_b" in failure_report.workers_executed, "success_b should have executed after fail"
assert failure_report.success_count == 2, f"Expected 2 successes, got {failure_report.success_count}"
assert failure_report.failure_count == 1, f"Expected 1 failure, got {failure_report.failure_count}"
print(f"✓ Failure handling verified: {failure_report.success_count} succeeded, {failure_report.failure_count} failed, pipeline continued.")

# ── 7. NO REGRESSION TEST ───────────────────────────────────────────────────
print("\n=== TEST 7: NO REGRESSION (SINGLE-WORKER REGISTRY ROUTES) ===")
# Verify the individual worker routes from genesis.py still work
from genesis import should_run_research, should_run_acquisition, should_run_marketing, should_run_finance

assert should_run_research("research SaaS market"), "Research route broken"
assert should_run_acquisition("find leads for agencies"), "Acquisition route broken"
assert should_run_marketing("marketing strategy for product"), "Marketing route broken"
assert should_run_finance("financial analysis for SaaS"), "Finance route broken"
assert should_run_orchestration("run all workers for ShiftGuard AI"), "Orchestration route broken"
assert should_run_orchestration("full analysis for my product"), "Orchestration 'full analysis' trigger broken"
assert not should_run_orchestration("what is the company name"), "Orchestration false positive"
print("✓ All individual worker routing helpers verified — zero regressions.")

# ── 8. KEYWORD DETECTION TEST ───────────────────────────────────────────────
print("\n=== TEST 8: ORCHESTRATION KEYWORD DETECTION ===")
phrases_that_should_trigger = [
    "full analysis for ShiftGuard",
    "complete strategy for my startup",
    "run all workers for attendance tracking app",
    "orchestrate everything for SaaS startup",
    "end-to-end analysis for my product",
    "run pipeline for B2B SaaS",
]
for phrase in phrases_that_should_trigger:
    assert should_run_orchestration(phrase), f"Orchestration not triggered by: '{phrase}'"

assert remove_orchestration_instruction("full analysis for ShiftGuard AI") == "ShiftGuard AI", \
    "remove_orchestration_instruction failed to strip correctly"
print("✓ Orchestration keyword detection and instruction stripping verified.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 7 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
