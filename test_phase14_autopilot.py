"""
test_phase14_autopilot.py

Comprehensive Phase 14 Verification Suite for the Autonomous Auto-Pilot Engine.

Tests:
  1.  Imports verification
  2.  AutoPilotStatus enum — all 6 states
  3.  AutoPilotResult structure and __str__
  4.  AutoPilotEngine instantiation
  5.  run() on empty queue → STOPPED with clear message
  6.  run() single successful task → COMPLETED
  7.  run() multi-task pipeline with dependency resolution
  8.  run() stop_on_failure=True → FAILED on task error
  9.  run() stop_on_failure=False → continues past failed task
 10.  run() max_steps limit enforcement → PAUSED
 11.  summary() string output formatting
 12.  Integration with TaskQueue and TaskResult
 13.  Integration with TaskPlanner.plan_tasks() and build_task_plan()
 14.  Integration with CompanyDashboard (snapshot metrics after run)
 15.  should_run_autopilot routing helper — all triggers
 16.  should_show_autopilot routing helper — all status triggers
 17.  AUTOPILOT instance in genesis.py
 18.  Full end-to-end integration: build_task_plan() + run_autopilot_mode()
 19.  Backward compatibility — all 15 routing helpers intact
 20.  Syntax verification — all project files
"""

import sys
import time
from unittest.mock import MagicMock, patch

# ── 1. IMPORTS VERIFICATION ──────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core.autopilot import AutoPilotEngine, AutoPilotResult, AutoPilotStatus
    from core import (
        AutoPilotEngine as APEFromCore,
        AutoPilotResult as APRFromCore,
        AutoPilotStatus as APSFromCore,
    )
    from genesis import (
        AUTOPILOT,
        should_run_autopilot,
        should_show_autopilot,
        run_autopilot_mode,
    )
    print("✓ All imports passed.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. AUTOPILOTSTATUS ENUM ───────────────────────────────────────────────────
print("\n=== TEST 2: AUTOPILOTSTATUS ENUM — ALL 6 STATES ===")
assert AutoPilotStatus.IDLE.value == "idle"
assert AutoPilotStatus.RUNNING.value == "running"
assert AutoPilotStatus.PAUSED.value == "paused"
assert AutoPilotStatus.COMPLETED.value == "completed"
assert AutoPilotStatus.FAILED.value == "failed"
assert AutoPilotStatus.STOPPED.value == "stopped"
print("✓ All 6 AutoPilotStatus states verified.")

# ── 3. AUTOPILOTRESULT STRUCTURE & STR ───────────────────────────────────────
print("\n=== TEST 3: AUTOPILOTRESULT STRUCTURE & __STR__ ===")
res_ok = AutoPilotResult(
    status=AutoPilotStatus.COMPLETED,
    steps_executed=3,
    tasks_completed=3,
    tasks_failed=0,
    total_time_ms=120.0,
    message="All tasks completed successfully!",
)
assert res_ok.status == AutoPilotStatus.COMPLETED
assert res_ok.steps_executed == 3
assert res_ok.tasks_completed == 3
assert "✓" in str(res_ok)
assert "COMPLETED" in str(res_ok)

res_fail = AutoPilotResult(
    status=AutoPilotStatus.FAILED,
    steps_executed=2,
    tasks_completed=1,
    tasks_failed=1,
    total_time_ms=85.0,
    message="Stopped on task failure",
    stopped_at_task="task123",
)
assert "✗" in str(res_fail)
assert "FAILED" in str(res_fail)
assert res_fail.stopped_at_task == "task123"
print("✓ AutoPilotResult structure and __str__ (✓/✗) verified.")

# ── 4. AUTOPILOTENGINE INSTANTIATION ─────────────────────────────────────────
print("\n=== TEST 4: AUTOPILOTENGINE INSTANTIATION ===")
mock_queue = MagicMock()
mock_queue.is_empty.return_value = True
mock_queue.total_count.return_value = 0
mock_queue.ready_count.return_value = 0

engine = AutoPilotEngine(
    task_queue=mock_queue,
    executor_fn=lambda: "done",
)
assert engine.status == AutoPilotStatus.IDLE
assert engine.last_result is None
print("✓ AutoPilotEngine instantiated in IDLE state.")

# ── 5. RUN ON EMPTY QUEUE ─────────────────────────────────────────────────────
print("\n=== TEST 5: RUN ON EMPTY QUEUE ===")
res_empty = engine.run()
assert res_empty.status == AutoPilotStatus.STOPPED
assert res_empty.steps_executed == 0
assert "empty" in res_empty.message.lower()
print(f"✓ Empty queue run returned STOPPED: '{res_empty.message}'")

# ── 6. RUN SINGLE SUCCESSFUL TASK ─────────────────────────────────────────────
print("\n=== TEST 6: RUN SINGLE SUCCESSFUL TASK ===")
from core.task_queue import Task, TaskQueue, TaskResult, TaskStatus

q6 = TaskQueue()
t1 = Task(title="Task 1", description="desc", assigned_to="research")
q6.add(t1)
q6.refresh_readiness()

def mock_executor_success():
    next_task = q6.get_next()
    if next_task is None:
        return "empty"
    tr = TaskResult(
        task_id=next_task.id,
        task_title=next_task.title,
        success=True,
        output="result ok",
        execution_time_ms=10.0,
    )
    q6.record_result(next_task.id, tr)
    return tr

engine6 = AutoPilotEngine(task_queue=q6, executor_fn=mock_executor_success)
res6 = engine6.run()
assert res6.status == AutoPilotStatus.COMPLETED
assert res6.steps_executed == 1
assert res6.tasks_completed == 1
assert res6.tasks_failed == 0
print(f"✓ Single task run: {res6}")

# ── 7. RUN MULTI-TASK PIPELINE WITH DEPENDENCY RESOLUTION ─────────────────────
print("\n=== TEST 7: RUN MULTI-TASK PIPELINE WITH DEPENDENCY RESOLUTION ===")
q7 = TaskQueue()
parent = Task(title="Parent Task", description="p", assigned_to="research", priority=1)
child = Task(title="Child Task", description="c", assigned_to="finance", priority=2, dependencies=[parent.id])
q7.add(parent)
q7.add(child)

def mock_executor_pipeline():
    q7.refresh_readiness()
    t = q7.get_next()
    if t is None:
        return "empty"
    tr = TaskResult(
        task_id=t.id,
        task_title=t.title,
        success=True,
        output=f"output for {t.title}",
        execution_time_ms=15.0,
    )
    q7.record_result(t.id, tr)
    return tr

engine7 = AutoPilotEngine(task_queue=q7, executor_fn=mock_executor_pipeline)
res7 = engine7.run()
assert res7.status == AutoPilotStatus.COMPLETED
assert res7.steps_executed == 2
assert res7.tasks_completed == 2
assert q7.completed_count() == 2
print(f"✓ Pipeline run executed {res7.steps_executed} tasks in order: Parent → Child.")

# ── 8. RUN STOP_ON_FAILURE=TRUE ───────────────────────────────────────────────
print("\n=== TEST 8: RUN STOP_ON_FAILURE=TRUE ===")
q8 = TaskQueue()
t8_1 = Task(title="Failing Task", description="f", assigned_to="research")
t8_2 = Task(title="Subsequent Task", description="s", assigned_to="finance")
q8.add(t8_1)
q8.add(t8_2)

step_count = 0
def mock_executor_fail():
    global step_count
    q8.refresh_readiness()
    t = q8.get_next()
    if t is None:
        return "empty"
    step_count += 1
    success = (step_count != 1)  # first fails
    tr = TaskResult(
        task_id=t.id,
        task_title=t.title,
        success=success,
        output=None if not success else "ok",
        error="API error" if not success else None,
    )
    q8.record_result(t.id, tr)
    return tr

engine8 = AutoPilotEngine(task_queue=q8, executor_fn=mock_executor_fail)
res8 = engine8.run(stop_on_failure=True)
assert res8.status == AutoPilotStatus.FAILED
assert res8.steps_executed == 1
assert res8.tasks_failed == 1
assert res8.stopped_at_task == t8_1.id
print(f"✓ stop_on_failure=True halted loop after 1 failure.")

# ── 9. RUN STOP_ON_FAILURE=FALSE ──────────────────────────────────────────────
print("\n=== TEST 9: RUN STOP_ON_FAILURE=FALSE ===")
q9 = TaskQueue()
t9_1 = Task(title="Failing Task 1", description="f1", assigned_to="research")
t9_2 = Task(title="Success Task 2", description="s2", assigned_to="finance")
q9.add(t9_1)
q9.add(t9_2)

step_count_9 = 0
def mock_executor_continue():
    global step_count_9
    q9.refresh_readiness()
    t = q9.get_next()
    if t is None:
        return "empty"
    step_count_9 += 1
    success = (step_count_9 != 1)
    tr = TaskResult(
        task_id=t.id,
        task_title=t.title,
        success=success,
        output="ok" if success else None,
        error="minor error" if not success else None,
    )
    q9.record_result(t.id, tr)
    return tr

engine9 = AutoPilotEngine(task_queue=q9, executor_fn=mock_executor_continue)
res9 = engine9.run(stop_on_failure=False)
assert res9.steps_executed == 2
assert res9.tasks_completed == 1
assert res9.tasks_failed == 1
print(f"✓ stop_on_failure=False executed both tasks ({res9.tasks_completed} ok, {res9.tasks_failed} fail).")

# ── 10. MAX_STEPS LIMIT ENFORCEMENT ───────────────────────────────────────────
print("\n=== TEST 10: MAX_STEPS LIMIT ENFORCEMENT ===")
q10 = TaskQueue()
for i in range(5):
    q10.add(Task(title=f"Task {i}", description="d", assigned_to="research"))

def mock_executor_limit():
    q10.refresh_readiness()
    t = q10.get_next()
    if t is None:
        return "empty"
    tr = TaskResult(task_id=t.id, task_title=t.title, success=True, output="ok")
    q10.record_result(t.id, tr)
    return tr

engine10 = AutoPilotEngine(task_queue=q10, executor_fn=mock_executor_limit)
res10 = engine10.run(max_steps=3)
assert res10.status == AutoPilotStatus.PAUSED
assert res10.steps_executed == 3
assert "max_steps" in res10.message
print(f"✓ max_steps=3 enforced → PAUSED after 3 tasks.")

# ── 11. SUMMARY() OUTPUT FORMATTING ───────────────────────────────────────────
print("\n=== TEST 11: SUMMARY() OUTPUT FORMATTING ===")
summary_str = engine10.summary()
assert isinstance(summary_str, str) and len(summary_str) > 10
assert "3/3" in summary_str or "PAUSED" in summary_str
print(f"✓ summary() output: '{summary_str}'")

# ── 12. TASKQUEUE AND TASKRESULT INTEGRATION ──────────────────────────────────
print("\n=== TEST 12: TASKQUEUE AND TASKRESULT INTEGRATION ===")
assert res7.step_results[0].task_title == "Parent Task"
assert res7.step_results[1].task_title == "Child Task"
print("✓ Step results contain exact TaskResult objects.")

# ── 13. TASKPLANNER AND BUILD_TASK_PLAN INTEGRATION ──────────────────────────
print("\n=== TEST 13: TASKPLANNER AND BUILD_TASK_PLAN INTEGRATION ===")
import genesis as genesis_mod
from core.task_queue import TaskQueue as TQFresh

fresh_q = TQFresh()
genesis_mod.TASK_QUEUE = fresh_q
genesis_mod.DASHBOARD._queue = fresh_q
genesis_mod.AUTOPILOT = AutoPilotEngine(
    task_queue=fresh_q,
    executor_fn=lambda: genesis_mod.execute_next_task(),
    dashboard=genesis_mod.DASHBOARD,
)

with patch.object(genesis_mod.PLANNER, "plan_tasks", return_value=[
    {"title": "Research Market", "description": "Research SaaS", "assigned_to": "research", "assigned_type": "worker", "priority": 1, "dependencies": []},
    {"title": "Model Financials", "description": "Model cashflow", "assigned_to": "finance", "assigned_type": "worker", "priority": 2, "dependencies": ["Research Market"]},
]):
    count, titles = genesis_mod.build_task_plan("AI tool for dentists")

assert count == 2
assert fresh_q.total_count() == 2
print(f"✓ build_task_plan created {count} tasks for Auto-Pilot execution.")

# ── 14. COMPANYDASHBOARD METRICS AFTER AUTO-PILOT RUN ────────────────────────
print("\n=== TEST 14: COMPANYDASHBOARD METRICS AFTER RUN ===")
mock_worker = MagicMock()
mock_report = MagicMock()
from core.worker_report import ReportStatus
mock_report.status = ReportStatus.SUCCESS
mock_report.output = "Market study complete"
mock_worker.run_lifecycle.return_value = mock_report

genesis_mod.WORKER_REGISTRY["research"] = mock_worker
genesis_mod.WORKER_REGISTRY["finance"] = mock_worker

res14 = genesis_mod.AUTOPILOT.run(max_steps=2)
assert res14.steps_executed == 2
assert res14.tasks_completed == 2

snap14 = genesis_mod.DASHBOARD.build_snapshot(with_ai=False)
assert snap14.completed_tasks == 2
assert snap14.completion_pct == 100.0
print(f"✓ Dashboard updated after Auto-Pilot run: {snap14.completed_tasks}/{snap14.total_tasks} completed ({snap14.completion_pct}%).")

# ── 15. SHOULD_RUN_AUTOPILOT ROUTING HELPER ──────────────────────────────────
print("\n=== TEST 15: SHOULD_RUN_AUTOPILOT ROUTING HELPER ===")
assert should_run_autopilot("autopilot")
assert should_run_autopilot("run autopilot")
assert should_run_autopilot("start autopilot")
assert should_run_autopilot("auto run")
assert should_run_autopilot("auto pilot")
assert not should_run_autopilot("show memory")
assert not should_run_autopilot("autopilot status")
print("✓ should_run_autopilot verified for all triggers.")

# ── 16. SHOULD_SHOW_AUTOPILOT ROUTING HELPER ─────────────────────────────────
print("\n=== TEST 16: SHOULD_SHOW_AUTOPILOT ROUTING HELPER ===")
assert should_show_autopilot("autopilot status")
assert should_show_autopilot("show autopilot")
assert should_show_autopilot("status autopilot")
assert not should_show_autopilot("run autopilot")
print("✓ should_show_autopilot verified for all status triggers.")

# ── 17. AUTOPILOT INSTANCE IN GENESIS.PY ──────────────────────────────────────
print("\n=== TEST 17: AUTOPILOT INSTANCE IN GENESIS.PY ===")
assert hasattr(genesis_mod, "AUTOPILOT")
assert isinstance(genesis_mod.AUTOPILOT, AutoPilotEngine)
print("✓ genesis.AUTOPILOT instance verified.")

# ── 18. END-TO-END INTEGRATION: BUILD + RUN_AUTOPILOT_MODE ───────────────────
print("\n=== TEST 18: END-TO-END INTEGRATION (BUILD + AUTOPILOT MODE) ===")
fresh_q18 = TQFresh()
genesis_mod.TASK_QUEUE = fresh_q18
genesis_mod.DASHBOARD._queue = fresh_q18
genesis_mod.AUTOPILOT = AutoPilotEngine(
    task_queue=fresh_q18,
    executor_fn=lambda: genesis_mod.execute_next_task(),
    dashboard=genesis_mod.DASHBOARD,
)

with patch.object(genesis_mod.PLANNER, "plan_tasks", return_value=[
    {"title": "Target Discovery", "description": "Find dental practices", "assigned_to": "acquisition", "assigned_type": "worker", "priority": 1, "dependencies": []},
]):
    genesis_mod.build_task_plan("AI Dental Review Tool")

res18 = genesis_mod.run_autopilot_mode(max_steps=5)
assert res18.tasks_completed == 1
print(f"✓ End-to-end run_autopilot_mode() completed task successfully: {res18.message}")

# ── 19. BACKWARD COMPATIBILITY — ALL 15 ROUTING HELPERS ──────────────────────
print("\n=== TEST 19: BACKWARD COMPATIBILITY — ALL 15 ROUTING HELPERS ===")
from genesis import (
    should_show_memory, should_show_reports,
    should_show_proposals, should_approve_proposals,
    should_run_research, should_run_acquisition,
    should_run_marketing, should_run_finance,
    should_run_orchestration, should_show_tools,
    should_show_skills, should_show_tasks,
    should_show_dashboard, should_show_weekly_summary,
    should_run_autopilot, should_show_autopilot,
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
print("✓ All 15 routing helpers across Phases 1–14 verified — zero regressions.")

# ── 20. SYNTAX VERIFICATION — ALL PROJECT FILES ──────────────────────────────
print("\n=== TEST 20: SYNTAX VERIFICATION — ALL PROJECT FILES ===")
import subprocess
files = [
    "genesis.py", "core/__init__.py", "core/autopilot.py",
    "core/company_dashboard.py", "core/task_queue.py", "core/task_planner.py",
    "core/skill_manager.py", "core/tool_manager.py", "core/memory_governor.py",
    "core/memory_interface.py", "core/orchestrator.py", "core/base_worker.py",
    "core/logger.py", "core/worker_identity.py", "core/worker_report.py",
    "workers/research_worker.py", "workers/acquisition_worker.py",
    "workers/marketing_worker.py", "workers/finance_worker.py",
    "workers/__init__.py",
    "skills/google_review_product/skill.py", "skills/customer_validation/skill.py",
    "skills/business_evaluation/skill.py",
    "test_phase14_autopilot.py",
]
proc = subprocess.run(
    [sys.executable, "-m", "py_compile"] + files,
    capture_output=True, text=True,
)
if proc.returncode != 0:
    print(f"✗ Syntax errors:\n{proc.stderr}")
    sys.exit(1)
print(f"✓ Syntax clean — {len(files)} files, 0 errors.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 14 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
