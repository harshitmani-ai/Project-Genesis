"""
test_phase6_finance.py

Comprehensive Phase 6 Verification Test Suite for FinanceWorker.
"""

import sys
from pathlib import Path

# ── 1. IMPORTS TEST ─────────────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core import BaseWorker, WorkerIdentity, WorkerReport
    from workers.finance_worker import FinanceWorker
    from finance_worker import run_finance_assignment
    from genesis import WORKER_REGISTRY, should_run_finance
    print("✓ All imports passed successfully.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. IDENTITY & INSTANTIATION TEST ───────────────────────────────────────
print("\n=== TEST 2: IDENTITY & LIFECYCLE INSTANTIATION ===")
worker = FinanceWorker()
assert issubclass(FinanceWorker, BaseWorker), "FinanceWorker must inherit from BaseWorker"
assert worker.identity.name == "Finance Worker", f"Unexpected worker name: {worker.identity.name}"
assert worker.identity.version == "1.0.0", f"Unexpected version: {worker.identity.version}"
print(f"✓ FinanceWorker identity verified: {worker.identity}")

# ── 3. REGISTRY ROUTING TEST ───────────────────────────────────────────────
print("\n=== TEST 3: WORKER REGISTRY INTEGRATION ===")
assert "finance" in WORKER_REGISTRY, "Finance Worker not found in genesis WORKER_REGISTRY"
assert isinstance(WORKER_REGISTRY["finance"], FinanceWorker), "Registry item is not a FinanceWorker instance"
assert should_run_finance("run financial analysis for ShiftGuard AI"), "should_run_finance failed to recognize keyword"
assert should_run_finance("what is the roi for this product"), "should_run_finance failed to recognize 'roi'"
assert should_run_finance("break-even point for SaaS"), "should_run_finance failed to recognize 'break-even'"
print("✓ WORKER_REGISTRY integration and keyword detection verified.")

# ── 4. LIFECYCLE & REPORT GENERATION TEST ──────────────────────────────────
print("\n=== TEST 4: LIFECYCLE EXECUTION & REPORT GENERATION ===")
test_product = "ShiftGuard AI — SaaS attendance tracking for SMBs, priced at $49/month per location"
print(f"Executing lifecycle for: '{test_product}'...")

report = worker.run_lifecycle(test_product)
print(f"Report status: {report.status.value}")

assert report.status.value in ("SUCCESS", "PARTIAL"), f"Report failed with status {report.status.value}. Error: {report.error}"
assert report.result is not None, "Report result payload is None"

result_text, report_path = report.result
print(f"Report path: {report_path}")
assert report_path.exists(), f"Report file does not exist on disk: {report_path}"

report_content = report_path.read_text(encoding="utf-8")
assert "Finance Report" in report_content, "Missing Finance Report title"
assert "Revenue Model" in report_content, "Missing Revenue Model section"
assert "Break-Even" in report_content, "Missing Break-Even Analysis section"
assert "Profitability Score" in report_content, "Missing Profitability Score section"
assert "Risk" in report_content, "Missing Financial Risks section"
assert "Assumptions" in report_content, "Missing Assumptions"
print("✓ Lifecycle execution and Markdown report structure verified.")

# ── 5. BACKWARD-COMPATIBILITY PROXY TEST ───────────────────────────────────
print("\n=== TEST 5: BACKWARD-COMPATIBILITY PROXY ===")
proxy_result, proxy_path = run_finance_assignment(
    "FactoryVoice AI — Voice HR assistant for factory workers, $29/month per 50 workers"
)
assert Path(proxy_path).exists(), "Proxy report path does not exist"
print("✓ Proxy run_finance_assignment() verified.")

# ── 6. ERROR HANDLING & FAILURE ENVELOPE TEST ─────────────────────────────
print("\n=== TEST 6: ERROR HANDLING & RESILIENCE ===")
class FaultyFinanceWorker(BaseWorker):
    identity = WorkerIdentity(name="Faulty Finance Worker", role="Test failure handling")
    def create_plan(self, task): raise ValueError("Simulated finance planning failure")
    def execute(self, task, plan): pass
    def verify(self, result): return True
    def learn(self, task, result): pass

faulty_report = FaultyFinanceWorker().run_lifecycle("test product")
assert faulty_report.status.value == "FAILURE", f"Expected FAILURE state, got {faulty_report.status.value}"
assert "Simulated finance planning failure" in faulty_report.error, "Error message not captured in report"
print("✓ BaseWorker error handling & failure report envelope verified.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 6 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
