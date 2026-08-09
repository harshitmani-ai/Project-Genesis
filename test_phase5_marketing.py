"""
test_phase5_marketing.py

Comprehensive Phase 5 Verification Test Suite for MarketingWorker.
"""

import sys
from pathlib import Path

# ── 1. IMPORTS TEST ─────────────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core import BaseWorker, WorkerIdentity, WorkerReport
    from workers.marketing_worker import MarketingWorker
    from marketing_worker import run_marketing_assignment
    from genesis import WORKER_REGISTRY, should_run_marketing
    print("✓ All imports passed successfully.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. IDENTITY & INSTANTIATION TEST ───────────────────────────────────────
print("\n=== TEST 2: IDENTITY & LIFECYCLE INSTANTIATION ===")
worker = MarketingWorker()
assert issubclass(MarketingWorker, BaseWorker), "MarketingWorker must inherit from BaseWorker"
assert worker.identity.name == "Marketing Worker", f"Unexpected worker name: {worker.identity.name}"
assert worker.identity.version == "1.0.0", f"Unexpected version: {worker.identity.version}"
print(f"✓ MarketingWorker identity verified: {worker.identity}")

# ── 3. REGISTRY ROUTING TEST ───────────────────────────────────────────────
print("\n=== TEST 3: WORKER REGISTRY INTEGRATION ===")
assert "marketing" in WORKER_REGISTRY, "Marketing Worker not found in genesis WORKER_REGISTRY"
assert isinstance(WORKER_REGISTRY["marketing"], MarketingWorker), "Registry item is not a MarketingWorker instance"
assert should_run_marketing("generate marketing assets for ShiftGuard AI"), "should_run_marketing failed to recognize keyword"
print("✓ WORKER_REGISTRY integration verified.")

# ── 4. LIFECYCLE & REPORT GENERATION TEST ──────────────────────────────────
print("\n=== TEST 4: LIFECYCLE EXECUTION & REPORT GENERATION ===")
test_product = "ShiftGuard AI — Automated employee attendance tracking and fraud prevention for SMBs"
print(f"Executing lifecycle for test product: '{test_product}'...")

report = worker.run_lifecycle(test_product)
print(f"Report status: {report.status.value}")

assert report.status.value in ("SUCCESS", "PARTIAL"), f"Report failed with status {report.status.value}. Error: {report.error}"
assert report.result is not None, "Report result payload is None"

result_text, report_path = report.result
print(f"Report path: {report_path}")
assert report_path.exists(), f"Report file does not exist on disk: {report_path}"

report_content = report_path.read_text(encoding="utf-8")
assert "Marketing Report" in report_content, "Missing Marketing Report title"
assert "Positioning" in report_content, "Missing Positioning section"
assert "Landing Page" in report_content, "Missing Landing Page section"
assert "CTA" in report_content or "Call to Action" in report_content, "Missing Call to Action section"
print("✓ Lifecycle execution and Markdown report structure verified.")

# ── 5. BACKWARD-COMPATIBILITY PROXY TEST ───────────────────────────────────
print("\n=== TEST 5: BACKWARD-COMPATIBILITY PROXY ===")
proxy_result, proxy_path = run_marketing_assignment("FactoryVoice AI — Voice-based HR assistant for shop floor workers")
assert Path(proxy_path).exists(), "Proxy report path does not exist"
print("✓ Proxy run_marketing_assignment() verified.")

# ── 6. ERROR HANDLING & FAILURE ENVELOPE TEST ─────────────────────────────
print("\n=== TEST 6: ERROR HANDLING & RESILIENCE ===")
class FaultyMarketingWorker(BaseWorker):
    identity = WorkerIdentity(name="Faulty Marketing Worker", role="Test failure handling")
    def create_plan(self, task): raise ValueError("Simulated marketing planning failure")
    def execute(self, task, plan): pass
    def verify(self, result): return True
    def learn(self, task, result): pass

faulty_report = FaultyMarketingWorker().run_lifecycle("test product")
assert faulty_report.status.value == "FAILURE", f"Expected FAILURE state, got {faulty_report.status.value}"
assert "Simulated marketing planning failure" in faulty_report.error, "Error message not captured in report"
print("✓ BaseWorker error handling & failure report envelope verified.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 5 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
