"""
test_phase4_acquisition.py

Comprehensive Phase 4 Verification Test Suite for AcquisitionWorker.
"""

import sys
from pathlib import Path

# ── 1. IMPORTS TEST ─────────────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core import BaseWorker, WorkerIdentity, WorkerReport
    from workers.acquisition_worker import AcquisitionWorker
    from acquisition_worker import run_acquisition_assignment
    from genesis import WORKER_REGISTRY, should_run_acquisition
    print("✓ All imports passed successfully.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. IDENTITY & INSTANTIATION TEST ───────────────────────────────────────
print("\n=== TEST 2: IDENTITY & LIFECYCLE INSTANTIATION ===")
worker = AcquisitionWorker()
assert issubclass(AcquisitionWorker, BaseWorker), "AcquisitionWorker must inherit from BaseWorker"
assert worker.identity.name == "Acquisition Worker", f"Unexpected worker name: {worker.identity.name}"
assert worker.identity.version == "1.0.0", f"Unexpected version: {worker.identity.version}"
print(f"✓ AcquisitionWorker identity verified: {worker.identity}")

# ── 3. REGISTRY ROUTING TEST ───────────────────────────────────────────────
print("\n=== TEST 3: WORKER REGISTRY INTEGRATION ===")
assert "acquisition" in WORKER_REGISTRY, "Acquisition Worker not found in genesis WORKER_REGISTRY"
assert isinstance(WORKER_REGISTRY["acquisition"], AcquisitionWorker), "Registry item is not an AcquisitionWorker instance"
assert should_run_acquisition("find leads for agency owners"), "should_run_acquisition failed to recognize keyword"
print("✓ WORKER_REGISTRY integration verified.")

# ── 4. LIFECYCLE & REPORT GENERATION TEST ──────────────────────────────────
print("\n=== TEST 4: LIFECYCLE EXECUTION & REPORT GENERATION ===")
test_icp = "Small B2B marketing agencies seeking automated client reporting"
print(f"Executing lifecycle for test ICP: '{test_icp}'...")

report = worker.run_lifecycle(test_icp)
print(f"Report status: {report.status.value}")

assert report.status.value in ("SUCCESS", "PARTIAL"), f"Report failed with status {report.status.value}. Error: {report.error}"
assert report.result is not None, "Report result payload is None"

result_text, report_path = report.result
print(f"Report path: {report_path}")
assert report_path.exists(), f"Report file does not exist on disk: {report_path}"

report_content = report_path.read_text(encoding="utf-8")
assert "Acquisition Report" in report_content, "Missing Acquisition Report title"
assert "Lead" in report_content, "Missing Lead database section"
assert "Fit" in report_content, "Missing Fit Score section"
assert "Outreach" in report_content, "Missing Outreach draft section"
print("✓ Lifecycle execution and Markdown report structure verified.")

# ── 5. BACKWARD-COMPATIBILITY PROXY TEST ───────────────────────────────────
print("\n=== TEST 5: BACKWARD-COMPATIBILITY PROXY ===")
proxy_result, proxy_path = run_acquisition_assignment("Local dental clinics needing appointment reminders")
assert Path(proxy_path).exists(), "Proxy report path does not exist"
print("✓ Proxy run_acquisition_assignment() verified.")

# ── 6. ERROR HANDLING TEST ─────────────────────────────────────────────────
print("\n=== TEST 6: ERROR HANDLING & RESILIENCE ===")
# BaseWorker must catch errors gracefully in run_lifecycle
class FaultyWorker(BaseWorker):
    identity = WorkerIdentity(name="Faulty Worker", role="Test failure handling")
    def create_plan(self, task): raise ValueError("Simulated planning failure")
    def execute(self, task, plan): pass
    def verify(self, result): return True
    def learn(self, task, result): pass

faulty_report = FaultyWorker().run_lifecycle("test task")
assert faulty_report.status.value == "FAILURE", f"Expected FAILURE state, got {faulty_report.status.value}"
assert "Simulated planning failure" in faulty_report.error, "Error message not captured in report"
print("✓ BaseWorker error handling & failure report envelope verified.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 4 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
