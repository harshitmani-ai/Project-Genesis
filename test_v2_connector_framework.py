"""
test_v2_connector_framework.py

Comprehensive Verification Suite for Project Genesis V2 Connector Framework.

Tests:
  1.  Imports verification
  2.  ConnectorStatus enum — all 8 states
  3.  ConnectorTask structure, fields, auto-ID, priority clamping
  4.  ConnectorResult structure, fields, and __str__ (live vs simulated)
  5.  BaseConnector abstract base class enforcement
  6.  ConnectorManager manual registration (valid & invalid type checking)
  7.  Duplicate registration prevention & deregistration
  8.  ConnectorManager.discover() auto-discovery from connectors/ directory
  9.  AntigravityConnector send_task, verify_result, health_check, simulation mode
 10.  ChatGPTConnector send_task, verify_result, health_check, simulation mode
 11.  ConnectorManager.send_task() execution, verification, and log recording
 12.  Automatic retry logic on communication failures
 13.  Pending tasks persistence & state tracking
 14.  Unknown connector handling (graceful ConnectorResult failure)
 15.  connectors_summary() formatting
 16.  Task Queue & execute_next_task() integration with assigned_type="connector"
 17.  should_show_connectors routing helper — all triggers
 18.  CONNECTOR_MANAGER instance in genesis.py
 19.  Backward compatibility — all 16 routing helpers across Phases 1–14 + V2
 20.  Syntax verification — all project files
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── 1. IMPORTS VERIFICATION ──────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core.connector_manager import (
        BaseConnector,
        ConnectorManager,
        ConnectorResult,
        ConnectorStatus,
        ConnectorTask,
        DEFAULT_CONNECTOR_MANAGER,
    )
    from core import (
        BaseConnector as BCFromCore,
        ConnectorManager as CMFromCore,
        ConnectorResult as CRFromCore,
        ConnectorStatus as CSFromCore,
        ConnectorTask as CTFromCore,
    )
    from connectors.antigravity.connector import AntigravityConnector
    from connectors.chatgpt.connector import ChatGPTConnector
    from genesis import (
        CONNECTOR_MANAGER,
        should_show_connectors,
        show_connectors,
    )
    print("✓ All imports passed.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. CONNECTORSTATUS ENUM ───────────────────────────────────────────────────
print("\n=== TEST 2: CONNECTORSTATUS ENUM — ALL 8 STATES ===")
assert ConnectorStatus.IDLE.value == "idle"
assert ConnectorStatus.PENDING.value == "pending"
assert ConnectorStatus.CONNECTING.value == "connecting"
assert ConnectorStatus.SENDING.value == "sending"
assert ConnectorStatus.RECEIVING.value == "receiving"
assert ConnectorStatus.COMPLETED.value == "completed"
assert ConnectorStatus.FAILED.value == "failed"
assert ConnectorStatus.RETRYING.value == "retrying"
assert ConnectorStatus.SIMULATED.value == "simulated"
print("✓ All 8 ConnectorStatus states verified.")

# ── 3. CONNECTORTASK STRUCTURE & CLAMPING ─────────────────────────────────────
print("\n=== TEST 3: CONNECTORTASK STRUCTURE & PRIORITY CLAMPING ===")
task = ConnectorTask(
    connector_name="chatgpt",
    action="ask",
    payload={"prompt": "Hello"},
    priority=15,  # Should clamp to 10
)
assert task.connector_name == "chatgpt"
assert task.action == "ask"
assert task.payload == {"prompt": "Hello"}
assert task.priority == 10, f"Expected priority 10, got {task.priority}"
assert isinstance(task.id, str) and len(task.id) == 8
assert "chatgpt.ask" in task.summary()
print(f"✓ ConnectorTask created with auto-ID '{task.id}'. Priority clamped to 10.")

# ── 4. CONNECTORRESULT STRUCTURE & STR ────────────────────────────────────────
print("\n=== TEST 4: CONNECTORRESULT STRUCTURE & __STR__ ===")
res_live = ConnectorResult(
    task_id=task.id,
    connector_name="chatgpt",
    success=True,
    data={"response": "Hi"},
    execution_time_ms=45.0,
    mode="live",
)
assert "✓" in str(res_live)
assert "[LIVE]" in str(res_live)

res_sim = ConnectorResult(
    task_id=task.id,
    connector_name="antigravity",
    success=True,
    data={"status": "simulated"},
    execution_time_ms=12.0,
    mode="simulated",
)
assert "✓" in str(res_sim)
assert "[SIMULATED]" in str(res_sim)
print("✓ ConnectorResult structure and __str__ ([LIVE]/[SIMULATED]) verified.")

# ── 5. BASECONNECTOR ABC ENFORCEMENT ──────────────────────────────────────────
print("\n=== TEST 5: BASECONNECTOR ABC ENFORCEMENT ===")
try:
    BaseConnector()
    assert False, "Should raise TypeError when instantiating ABC directly"
except TypeError as e:
    print(f"✓ BaseConnector ABC enforces abstract methods: {e}")

# ── 6. CONNECTORMANAGER MANUAL REGISTRATION ───────────────────────────────────
print("\n=== TEST 6: CONNECTORMANAGER REGISTRATION ===")
cm = ConnectorManager(connectors_dir=Path("nonexistent_dir"))
ag = AntigravityConnector()
cm.register(ag)
assert "antigravity" in cm.list_connectors()
assert cm.get("antigravity") is ag

try:
    cm.register("not a connector")
    assert False, "Should raise TypeError"
except TypeError as e:
    print(f"✓ Non-BaseConnector rejected: {e}")

# ── 7. DUPLICATE REGISTRATION PREVENTION & DEREGISTRATION ────────────────────
print("\n=== TEST 7: DUPLICATE REGISTRATION PREVENTION & DEREGISTRATION ===")
try:
    cm.register(ag)
    assert False, "Should raise ValueError for duplicate registration"
except ValueError as e:
    print(f"✓ Duplicate connector registration rejected: {e}")

cm.deregister("antigravity")
assert "antigravity" not in cm.list_connectors()
print("✓ Deregister works correctly.")

# ── 8. CONNECTORMANAGER.DISCOVER() ───────────────────────────────────────────
print("\n=== TEST 8: CONNECTORMANAGER.DISCOVER() AUTO-DISCOVERY ===")
cm_disc = ConnectorManager(connectors_dir=Path("connectors"))
count = cm_disc.discover()
assert count == 2, f"Expected 2 connectors, got {count}"
assert "antigravity" in cm_disc.list_connectors()
assert "chatgpt" in cm_disc.list_connectors()
print(f"✓ Auto-discovered {count} connectors: {cm_disc.list_connectors()}")

# ── 9. ANTIGRAVITYCONNECTOR ───────────────────────────────────────────────────
print("\n=== TEST 9: ANTIGRAVITYCONNECTOR SIMULATION MODE & EXECUTION ===")
ag_conn = AntigravityConnector()
assert ag_conn.name == "antigravity"
assert ag_conn.health_check() is True

t_ag = ConnectorTask(connector_name="antigravity", action="execute_code", payload={"code": "print('hello')"})
res_ag = ag_conn.send_task(t_ag)
assert res_ag.success is True
assert res_ag.mode == "simulated"
assert ag_conn.verify_result(res_ag) is True
print(f"✓ AntigravityConnector execution verified (mode={res_ag.mode}).")

# ── 10. CHATGPTCONNECTOR ──────────────────────────────────────────────────────
print("\n=== TEST 10: CHATGPTCONNECTOR SIMULATION MODE & EXECUTION ===")
cg_conn = ChatGPTConnector()
assert cg_conn.name == "chatgpt"
assert cg_conn.health_check() is True

t_cg = ConnectorTask(connector_name="chatgpt", action="ask", payload={"prompt": "Analyze ROI"})
res_cg = cg_conn.send_task(t_cg)
assert res_cg.success is True
assert res_cg.mode == "simulated"
assert cg_conn.verify_result(res_cg) is True
print(f"✓ ChatGPTConnector execution verified (mode={res_cg.mode}).")

# ── 11. CONNECTORMANAGER.SEND_TASK & LOGGING ──────────────────────────────────
print("\n=== TEST 11: CONNECTORMANAGER.SEND_TASK & INTERACTION LOG ===")
cm_exec = ConnectorManager(connectors_dir=Path("connectors"))
cm_exec.discover()

res_exec = cm_exec.send_task("chatgpt", "ask", {"prompt": "Market research"})
assert res_exec.success is True
assert len(cm_exec.interaction_log()) == 1
assert cm_exec.interaction_log()[0]["connector"] == "chatgpt"
print("✓ ConnectorManager.send_task executed and recorded in interaction log.")

# ── 12. AUTOMATIC RETRY LOGIC ON COMMUNICATION FAILURES ──────────────────────
print("\n=== TEST 12: AUTOMATIC RETRY LOGIC ON FAILURES ===")
class FlakyConnector(BaseConnector):
    name = "flaky"
    version = "1.0.0"
    description = "Flaky connector for testing retries."
    category = "Test"
    is_live = False

    def __init__(self):
        self.attempts = 0

    def send_task(self, task: ConnectorTask) -> ConnectorResult:
        self.attempts += 1
        if self.attempts < 3:
            return ConnectorResult(task_id=task.id, connector_name=self.name, success=False, data=None, error="Network glitch", mode="simulated")
        return ConnectorResult(task_id=task.id, connector_name=self.name, success=True, data={"status": "ok"}, mode="simulated")

    def verify_result(self, result: ConnectorResult) -> bool:
        return result.success

    def health_check(self) -> bool:
        return True

flaky = FlakyConnector()
cm_flaky = ConnectorManager(connectors_dir=Path("connectors"))
cm_flaky.register(flaky)

res_flaky = cm_flaky.send_task("flaky", "ping", max_retries=3)
assert res_flaky.success is True
assert res_flaky.retry_attempts == 2  # succeeded on 3rd attempt (attempt index 2)
print(f"✓ Automatic retry loop succeeded on attempt {res_flaky.retry_attempts + 1}.")

# ── 13. PENDING TASKS PERSISTENCE ─────────────────────────────────────────────
print("\n=== TEST 13: PENDING TASKS QUEUE PERSISTENCE ===")

class BlockingConnector(BaseConnector):
    name = "blocking"
    version = "1.0.0"
    description = "Blocking connector."
    category = "Test"
    is_live = False

    def send_task(self, task: ConnectorTask) -> ConnectorResult:
        # Verify task is in pending_tasks during execution
        assert task.id in task_manager_ref._pending_tasks
        return ConnectorResult(task_id=task.id, connector_name=self.name, success=True, data={"status": "ok"}, mode="simulated")

    def verify_result(self, result: ConnectorResult) -> bool:
        return True

    def health_check(self) -> bool:
        return True

blocking = BlockingConnector()
cm_block = ConnectorManager(connectors_dir=Path("connectors"))
task_manager_ref = cm_block
cm_block.register(blocking)

res_block = cm_block.send_task("blocking", "test")
assert res_block.success is True
assert len(cm_block.pending_tasks()) == 0  # removed after completion
print("✓ Pending task persisted during execution and cleared on completion.")

# ── 14. UNKNOWN CONNECTOR HANDLING ───────────────────────────────────────────
print("\n=== TEST 14: UNKNOWN CONNECTOR HANDLING ===")
res_unk = cm_exec.send_task("nonexistent_connector", "test")
assert res_unk.success is False
assert "not registered" in res_unk.error
print("✓ Unknown connector returned graceful ConnectorResult failure.")

# ── 15. CONNECTORS_SUMMARY() FORMATTING ───────────────────────────────────────
print("\n=== TEST 15: CONNECTORS_SUMMARY() FORMATTING ===")
summary = cm_exec.connectors_summary()
assert "Registered Connectors" in summary
assert "antigravity" in summary
assert "chatgpt" in summary
print(f"✓ connectors_summary() output verified:\n{summary[:200]}…")

# ── 16. TASK QUEUE INTEGRATION (assigned_type="connector") ───────────────────
print("\n=== TEST 16: TASK QUEUE INTEGRATION (assigned_type='connector') ===")
import genesis as genesis_mod
from core.task_queue import Task, TaskQueue, TaskResult, TaskStatus

q16 = TaskQueue()
t_conn = Task(
    title="ChatGPT Reasoning Step",
    description="Ask ChatGPT to evaluate product ideas",
    assigned_to="chatgpt",
    assigned_type="connector",
    priority=1,
)
q16.add(t_conn)
q16.refresh_readiness()

genesis_mod.TASK_QUEUE = q16
res_q16 = genesis_mod.execute_next_task()
assert isinstance(res_q16, TaskResult)
assert res_q16.success is True
assert q16.completed_count() == 1
print(f"✓ execute_next_task() executed connector task: {res_q16.task_title} ({res_q16.execution_time_ms:.0f}ms).")

# ── 17. COMMAND ROUTING HELPERS ───────────────────────────────────────────────
print("\n=== TEST 17: COMMAND ROUTING HELPERS ===")
assert should_show_connectors("show connectors")
assert should_show_connectors("list connectors")
assert should_show_connectors("connector status")
assert should_show_connectors("connectors")
assert not should_show_connectors("show memory")
print("✓ should_show_connectors verified for all triggers.")

# ── 18. CONNECTOR_MANAGER INSTANCE IN GENESIS.PY ─────────────────────────────
print("\n=== TEST 18: CONNECTOR_MANAGER INSTANCE IN GENESIS.PY ===")
assert hasattr(genesis_mod, "CONNECTOR_MANAGER")
assert isinstance(genesis_mod.CONNECTOR_MANAGER, ConnectorManager)
assert len(genesis_mod.CONNECTOR_MANAGER.list_connectors()) == 2
print("✓ genesis.CONNECTOR_MANAGER instance verified with 2 auto-discovered connectors.")

# ── 19. BACKWARD COMPATIBILITY — ALL 16 ROUTING HELPERS ──────────────────────
print("\n=== TEST 19: BACKWARD COMPATIBILITY — ALL 16 ROUTING HELPERS ===")
from genesis import (
    should_show_memory, should_show_reports,
    should_show_proposals, should_approve_proposals,
    should_run_research, should_run_acquisition,
    should_run_marketing, should_run_finance,
    should_run_orchestration, should_show_tools,
    should_show_skills, should_show_tasks,
    should_show_dashboard, should_show_weekly_summary,
    should_run_autopilot, should_show_autopilot,
    should_show_connectors,
)
assert should_show_memory("show company memory")
assert should_show_reports("show reports")
assert should_show_proposals("show proposals")
assert should_approve_proposals("approve all proposals")
assert should_run_research("research SaaS market")
assert should_run_acquisition("find leads for agencies")
assert should_run_marketing("marketing strategy for product")
assert should_run_finance("financial analysis for SaaS")
assert should_run_orchestration("run all workers for goal")
assert should_show_tools("show tools")
assert should_show_skills("show skills")
assert should_show_tasks("show tasks")
assert should_show_dashboard("good morning genesis")
assert should_show_weekly_summary("weekly summary")
assert should_run_autopilot("run autopilot")
assert should_show_autopilot("autopilot status")
assert should_show_connectors("show connectors")
print("✓ All 16 routing helpers across Phases 1–14 + V2 verified — zero regressions.")

# ── 20. SYNTAX VERIFICATION — ALL PROJECT FILES ───────────────────────────────
print("\n=== TEST 20: SYNTAX VERIFICATION — ALL PROJECT FILES ===")
import subprocess
files = [
    "genesis.py", "core/__init__.py", "core/connector_manager.py",
    "connectors/antigravity/connector.py", "connectors/chatgpt/connector.py",
    "core/autopilot.py", "core/company_dashboard.py", "core/task_queue.py",
    "core/task_planner.py", "core/skill_manager.py", "core/tool_manager.py",
    "core/memory_governor.py", "core/memory_interface.py", "core/orchestrator.py",
    "core/base_worker.py", "core/logger.py", "core/worker_identity.py",
    "core/worker_report.py", "workers/research_worker.py",
    "workers/acquisition_worker.py", "workers/marketing_worker.py",
    "workers/finance_worker.py", "workers/__init__.py",
    "test_v2_connector_framework.py",
]
proc = subprocess.run([sys.executable, "-m", "py_compile"] + files, capture_output=True, text=True)
if proc.returncode != 0:
    print(f"✗ Syntax errors:\n{proc.stderr}")
    sys.exit(1)
print(f"✓ Syntax clean — {len(files)} files, 0 errors.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL V2 CONNECTOR FRAMEWORK TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
