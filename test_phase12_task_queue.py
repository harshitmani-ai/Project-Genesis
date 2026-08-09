"""
test_phase12_task_queue.py

Comprehensive Phase 12 Verification Suite for the Autonomous Task Queue.

Tests:
  1.  Imports verification
  2.  TaskStatus enum — all 6 values
  3.  Task creation — fields, defaults, auto-ID, priority clamping
  4.  Task properties — is_done, duration_ms, status_icon, summary
  5.  TaskResult structure and __str__
  6.  TaskQueue.add() — valid and invalid
  7.  Duplicate task ID prevention
  8.  Dependency resolution — PENDING → READY on completion
  9.  Priority ordering — lower int = higher priority
  10. get_next() — selects highest-priority READY task
  11. update_status() — all transitions + timestamps
  12. record_result() — COMPLETED on success, FAILED on failure
  13. retry_failed() — re-queues failed tasks, refreshes readiness
  14. clear_completed() — removes only COMPLETED tasks
  15. cancel() — marks task CANCELLED
  16. view() — grouped status display
  17. Planner plan_tasks() — mocked LLM returns valid task dicts
  18. Planner plan_tasks() — fallback when LLM fails
  19. build_task_plan() — creates Tasks in TASK_QUEUE with dependency IDs
  20. Task Queue command helpers — all routing functions
  21. TASK_QUEUE instance in genesis.py
  22. Backward compatibility — all prior keyword routes intact
  23. Syntax — all project files
"""

import sys
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

# ── 1. IMPORTS TEST ─────────────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core.task_queue import Task, TaskQueue, TaskResult, TaskStatus
    from core import (
        Task as TaskFromCore,
        TaskQueue as TQFromCore,
        TaskResult as TRFromCore,
        TaskStatus as TSFromCore,
    )
    from genesis import (
        TASK_QUEUE,
        should_show_tasks, should_run_next_task,
        should_retry_failed, should_clear_completed,
        should_build_task_plan, extract_build_goal,
        build_task_plan, execute_next_task,
    )
    print("✓ All imports passed.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. TASKSTATUS ENUM ────────────────────────────────────────────────────────
print("\n=== TEST 2: TASKSTATUS ENUM — ALL 6 VALUES ===")
assert TaskStatus.PENDING.value == "pending"
assert TaskStatus.READY.value == "ready"
assert TaskStatus.RUNNING.value == "running"
assert TaskStatus.COMPLETED.value == "completed"
assert TaskStatus.FAILED.value == "failed"
assert TaskStatus.CANCELLED.value == "cancelled"
print("✓ All 6 TaskStatus values verified.")

# ── 3. TASK CREATION ──────────────────────────────────────────────────────────
print("\n=== TEST 3: TASK CREATION — FIELDS, DEFAULTS, AUTO-ID ===")
t = Task(
    title="Market Research",
    description="Research the AI dental market",
    assigned_to="research",
    assigned_type="worker",
    priority=1,
)
assert t.title == "Market Research"
assert t.description == "Research the AI dental market"
assert t.assigned_to == "research"
assert t.assigned_type == "worker"
assert t.priority == 1
assert t.dependencies == []
assert t.status == TaskStatus.PENDING
assert isinstance(t.id, str) and len(t.id) == 8
assert isinstance(t.created_at, datetime)
assert t.started_at is None
assert t.completed_at is None
assert t.result is None
print(f"✓ Task created with auto-ID '{t.id}'. Fields verified.")

# Priority clamping
t_low = Task(title="X", description="X", assigned_to="research", priority=99)
assert t_low.priority == 10, f"Priority should clamp to 10, got {t_low.priority}"
t_high = Task(title="X", description="X", assigned_to="research", priority=-5)
assert t_high.priority == 1, f"Priority should clamp to 1, got {t_high.priority}"
print("✓ Priority clamping verified (max=10, min=1).")

# Invalid assigned_type normalisation
t_bad = Task(title="X", description="X", assigned_to="research", assigned_type="invalid")
assert t_bad.assigned_type == "worker"
print("✓ Invalid assigned_type normalised to 'worker'.")

# ── 4. TASK PROPERTIES ────────────────────────────────────────────────────────
print("\n=== TEST 4: TASK PROPERTIES ===")
t_done = Task(title="Done", description="X", assigned_to="research")
t_done.status = TaskStatus.COMPLETED
assert t_done.is_done is True

t_cancel = Task(title="Cancelled", description="X", assigned_to="research")
t_cancel.status = TaskStatus.CANCELLED
assert t_cancel.is_done is True

t_run = Task(title="Running", description="X", assigned_to="research")
t_run.status = TaskStatus.RUNNING
assert t_run.is_done is False

# duration_ms
t_timed = Task(title="Timed", description="X", assigned_to="research")
t_timed.started_at = datetime(2026, 1, 1, 12, 0, 0)
t_timed.completed_at = datetime(2026, 1, 1, 12, 0, 1)
assert abs(t_timed.duration_ms - 1000.0) < 1

# status_icon
assert t_done.status_icon() == "✓"
assert t_cancel.status_icon() == "✘"
assert t_run.status_icon() == "⚙"

# summary
summary = t.summary()
assert "Market Research" in summary
assert "research" in summary
print("✓ is_done, duration_ms, status_icon, summary() all verified.")

# ── 5. TASKRESULT STRUCTURE ───────────────────────────────────────────────────
print("\n=== TEST 5: TASKRESULT STRUCTURE ===")
tr_ok = TaskResult(
    task_id="abc12345",
    task_title="Financial Analysis",
    success=True,
    output="Report data",
    execution_time_ms=250.0,
)
assert "✓" in str(tr_ok)
assert "Financial Analysis" in str(tr_ok)

tr_fail = TaskResult(
    task_id="abc12345",
    task_title="Broken Task",
    success=False,
    output=None,
    error="API timeout",
)
assert "✗" in str(tr_fail)
assert "API timeout" in str(tr_fail)
print("✓ TaskResult __str__ (✓/✗) verified.")

# ── 6. TASKQUEUE ADD (VALID & INVALID) ────────────────────────────────────────
print("\n=== TEST 6: TASKQUEUE.ADD() — VALID & INVALID ===")
q = TaskQueue()
t1 = Task(title="Task 1", description="first", assigned_to="research")
task_id = q.add(t1)
assert task_id == t1.id
assert q.total_count() == 1

try:
    q.add("not a task")
    assert False, "Should raise TypeError"
except TypeError as e:
    print(f"✓ Non-Task rejected: {e}")

# ── 7. DUPLICATE TASK ID PREVENTION ──────────────────────────────────────────
print("\n=== TEST 7: DUPLICATE TASK ID PREVENTION ===")
try:
    q.add(t1)  # same ID, same task
    assert False, "Should raise ValueError"
except ValueError as e:
    print(f"✓ Duplicate task ID rejected: {e}")

# ── 8. DEPENDENCY RESOLUTION ─────────────────────────────────────────────────
print("\n=== TEST 8: DEPENDENCY RESOLUTION — PENDING → READY ===")
q2 = TaskQueue()
parent = Task(title="Parent", description="X", assigned_to="research")
child = Task(
    title="Child", description="Y", assigned_to="finance",
    dependencies=[parent.id]
)
q2.add(parent)
q2.add(child)
q2.refresh_readiness()

# Parent has no deps → READY; child has unmet dep → PENDING
assert parent.status == TaskStatus.READY, f"Parent should be READY, got {parent.status}"
assert child.status == TaskStatus.PENDING, f"Child should be PENDING, got {child.status}"

# Complete the parent → child should become READY
q2.update_status(parent.id, TaskStatus.COMPLETED)
assert child.status == TaskStatus.READY, f"Child should be READY after parent completes, got {child.status}"
print("✓ Dependency resolution: PENDING → READY when parent completes.")

# ── 9. PRIORITY ORDERING ──────────────────────────────────────────────────────
print("\n=== TEST 9: PRIORITY ORDERING ===")
q3 = TaskQueue()
t_p3 = Task(title="P3", description="X", assigned_to="marketing", priority=3)
t_p1 = Task(title="P1", description="X", assigned_to="research", priority=1)
t_p5 = Task(title="P5", description="X", assigned_to="finance", priority=5)
for t in [t_p3, t_p1, t_p5]:
    q3.add(t)
q3.refresh_readiness()

ordered = q3.get_all(status=TaskStatus.READY)
assert ordered[0].priority == 1, f"First should be P1, got P{ordered[0].priority}"
assert ordered[1].priority == 3
assert ordered[2].priority == 5
print("✓ Tasks ordered by priority (P1 → P3 → P5).")

# ── 10. GET_NEXT() ────────────────────────────────────────────────────────────
print("\n=== TEST 10: GET_NEXT() — HIGHEST PRIORITY READY TASK ===")
next_t = q3.get_next()
assert next_t is not None
assert next_t.priority == 1
assert next_t.title == "P1"
print(f"✓ get_next() returns highest priority: '{next_t.title}' (P{next_t.priority})")

# Empty queue
empty_q = TaskQueue()
assert empty_q.get_next() is None
print("✓ get_next() returns None on empty queue.")

# ── 11. UPDATE_STATUS() + TIMESTAMPS ─────────────────────────────────────────
print("\n=== TEST 11: UPDATE_STATUS() AND TIMESTAMPS ===")
q4 = TaskQueue()
t_ts = Task(title="Timed", description="X", assigned_to="research")
q4.add(t_ts)
q4.refresh_readiness()
assert t_ts.started_at is None

q4.update_status(t_ts.id, TaskStatus.RUNNING)
assert t_ts.started_at is not None, "started_at should be set on RUNNING"
assert t_ts.status == TaskStatus.RUNNING

q4.update_status(t_ts.id, TaskStatus.COMPLETED)
assert t_ts.completed_at is not None, "completed_at should be set on COMPLETED"
print("✓ RUNNING sets started_at; COMPLETED sets completed_at.")

# ── 12. RECORD_RESULT() ───────────────────────────────────────────────────────
print("\n=== TEST 12: RECORD_RESULT() — COMPLETED / FAILED ===")
q5 = TaskQueue()
t_success = Task(title="Success", description="X", assigned_to="research")
t_fail = Task(title="Failure", description="X", assigned_to="finance")
q5.add(t_success)
q5.add(t_fail)
q5.refresh_readiness()

res_ok = TaskResult(task_id=t_success.id, task_title="Success", success=True, output="ok")
q5.record_result(t_success.id, res_ok)
assert t_success.status == TaskStatus.COMPLETED
assert t_success.result is res_ok

res_fail = TaskResult(task_id=t_fail.id, task_title="Failure", success=False, output=None, error="boom")
q5.record_result(t_fail.id, res_fail)
assert t_fail.status == TaskStatus.FAILED
print("✓ record_result() → COMPLETED on success, FAILED on failure.")

# ── 13. RETRY_FAILED() ────────────────────────────────────────────────────────
print("\n=== TEST 13: RETRY_FAILED() ===")
count = q5.retry_failed()
assert count == 1, f"Expected 1 retry, got {count}"
assert t_fail.status == TaskStatus.READY, f"After retry, should be READY: {t_fail.status}"
assert t_fail.result is None, "Result should be cleared on retry"
print(f"✓ retry_failed() re-queued {count} task(s). Status: {t_fail.status.value}")

# ── 14. CLEAR_COMPLETED() ────────────────────────────────────────────────────
print("\n=== TEST 14: CLEAR_COMPLETED() ===")
before = q5.total_count()
cleared = q5.clear_completed()
assert cleared == 1, f"Expected 1 cleared, got {cleared}"
assert q5.total_count() == before - 1
# t_success should be gone
assert q5.get(t_success.id) is None
print(f"✓ clear_completed() removed {cleared} task(s). Queue now has {q5.total_count()} tasks.")

# ── 15. CANCEL() ─────────────────────────────────────────────────────────────
print("\n=== TEST 15: CANCEL() ===")
q6 = TaskQueue()
t_cancel_test = Task(title="To Cancel", description="X", assigned_to="research")
q6.add(t_cancel_test)
q6.refresh_readiness()
result_cancel = q6.cancel(t_cancel_test.id)
assert result_cancel is True
assert t_cancel_test.status == TaskStatus.CANCELLED
assert t_cancel_test.completed_at is not None
print("✓ cancel() sets status to CANCELLED and sets completed_at.")

# ── 16. VIEW() ────────────────────────────────────────────────────────────────
print("\n=== TEST 16: VIEW() — GROUPED STATUS DISPLAY ===")
view_q = TaskQueue()
view_q.add(Task(title="Ready A", description="X", assigned_to="research"))
dep_task = Task(title="Pending B", description="Y", assigned_to="finance")
view_q.add(Task(title="Ready Parent", description="X", assigned_to="marketing"))
dep_task_id = Task(title="Pending C", description="Z", assigned_to="acquisition",
                   dependencies=["fake_dep_id"]).id
view_q.refresh_readiness()

view_output = view_q.view()
assert "Task Queue" in view_output
assert "READY" in view_output
print(f"✓ view() output verified:\n{view_output[:200]}…")

# Empty queue view
empty_q_view = TaskQueue()
assert "empty" in empty_q_view.view().lower()
print("✓ Empty queue view message correct.")

# ── 17. PLANNER PLAN_TASKS() — VALID LLM RESPONSE ────────────────────────────
print("\n=== TEST 17: PLANNER PLAN_TASKS() — VALID LLM RESPONSE ===")
from core.task_planner import TaskPlanner

mock_task_list = json.dumps([
    {"title": "Market Research", "description": "Research AI dental market",
     "assigned_to": "research", "assigned_type": "worker", "priority": 1, "dependencies": []},
    {"title": "Financial Analysis", "description": "Model financials for dental AI",
     "assigned_to": "finance", "assigned_type": "worker", "priority": 2,
     "dependencies": ["Market Research"]},
])

planner = TaskPlanner()
with patch("core.task_planner.ask_ai", return_value=mock_task_list):
    tasks = planner.plan_tasks("AI product for dentists", available_workers=["research", "finance"])

assert len(tasks) == 2
assert tasks[0]["title"] == "Market Research"
assert tasks[0]["assigned_to"] == "research"
assert tasks[1]["dependencies"] == ["Market Research"]
print(f"✓ plan_tasks() returned {len(tasks)} tasks from mocked LLM.")

# ── 18. PLANNER PLAN_TASKS() — FALLBACK WHEN LLM FAILS ─────────────────────
print("\n=== TEST 18: PLANNER PLAN_TASKS() — FALLBACK ON LLM FAILURE ===")
with patch("core.task_planner.ask_ai", side_effect=Exception("LLM error")):
    fallback_tasks = planner.plan_tasks("AI product for dentists")

assert len(fallback_tasks) >= 1, "Fallback should return at least 1 task"
assert fallback_tasks[0]["assigned_to"] in ["research", "finance", "acquisition", "marketing"]
print(f"✓ plan_tasks() fallback returned {len(fallback_tasks)} default tasks.")

# ── 19. BUILD_TASK_PLAN() — TASKS ADDED TO TASK_QUEUE ────────────────────────
print("\n=== TEST 19: BUILD_TASK_PLAN() — CREATES TASKS IN TASK_QUEUE ===")
# Use a fresh queue so we don't pollute global TASK_QUEUE
from core.task_queue import TaskQueue as TQ2
fresh_q = TQ2()

mock_tasks = json.dumps([
    {"title": "Research Phase", "description": "Research dental AI",
     "assigned_to": "research", "assigned_type": "worker", "priority": 1, "dependencies": []},
    {"title": "Finance Phase", "description": "Model financials",
     "assigned_to": "finance", "assigned_type": "worker", "priority": 2,
     "dependencies": ["Research Phase"]},
])

# Patch PLANNER.plan_tasks inside genesis.py
import genesis as genesis_module
original_planner = genesis_module.PLANNER
original_queue = genesis_module.TASK_QUEUE
genesis_module.TASK_QUEUE = fresh_q

with patch.object(genesis_module.PLANNER, "plan_tasks", return_value=[
    {"title": "Research Phase", "description": "Research dental AI",
     "assigned_to": "research", "assigned_type": "worker", "priority": 1, "dependencies": []},
    {"title": "Finance Phase", "description": "Model financials",
     "assigned_to": "finance", "assigned_type": "worker", "priority": 2,
     "dependencies": ["Research Phase"]},
]):
    count, titles = build_task_plan("AI product for dentists")

genesis_module.TASK_QUEUE = original_queue  # restore

assert count == 2, f"Expected 2 tasks, got {count}"
assert "Research Phase" in titles
assert "Finance Phase" in titles
assert fresh_q.total_count() == 2

# Dependency IDs should be properly resolved (not title strings)
finance_task = [t for t in fresh_q.get_all() if t.title == "Finance Phase"][0]
research_task = [t for t in fresh_q.get_all() if t.title == "Research Phase"][0]
assert research_task.id in finance_task.dependencies, \
    "Finance Phase should depend on Research Phase's ID, not its title"
print(f"✓ build_task_plan() created {count} tasks with correct dependency IDs.")

# ── 20. TASK QUEUE COMMAND HELPERS ────────────────────────────────────────────
print("\n=== TEST 20: TASK QUEUE COMMAND ROUTING HELPERS ===")
assert should_show_tasks("show tasks")
assert should_show_tasks("show task queue")
assert should_show_tasks("view tasks")
assert not should_show_tasks("show memory")

assert should_run_next_task("next task")
assert should_run_next_task("run next task")
assert not should_run_next_task("show memory")

assert should_retry_failed("retry failed tasks")
assert should_retry_failed("retry failed")
assert not should_retry_failed("show tasks")

assert should_clear_completed("clear completed tasks")
assert should_clear_completed("clear completed")
assert not should_clear_completed("show tasks")

assert should_build_task_plan("build an AI product for dentists")
assert should_build_task_plan("break down my goal")
assert should_build_task_plan("plan tasks for AI scheduling")
assert not should_build_task_plan("show tasks")

# extract_build_goal
assert extract_build_goal("build an AI CRM for dentists") == "an AI CRM for dentists"
assert extract_build_goal("plan tasks for a SaaS product") == "a SaaS product"
print("✓ All task queue routing helpers verified.")

# ── 21. TASK_QUEUE INSTANCE IN GENESIS.PY ────────────────────────────────────
print("\n=== TEST 21: TASK_QUEUE INSTANCE IN GENESIS.PY ===")
assert isinstance(TASK_QUEUE, TaskQueue), "TASK_QUEUE is not a TaskQueue instance"
print("✓ TASK_QUEUE instance verified in genesis.py.")

# ── 22. BACKWARD COMPATIBILITY ────────────────────────────────────────────────
print("\n=== TEST 22: BACKWARD COMPATIBILITY — ALL KEYWORD ROUTES ===")
from genesis import (
    should_show_memory, should_show_reports,
    should_show_proposals, should_approve_proposals,
    should_run_research, should_run_acquisition,
    should_run_marketing, should_run_finance,
    should_run_orchestration, should_show_tools,
    should_show_skills, should_show_tasks,
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
print("✓ All 12 existing + 1 new routing helpers verified — zero regressions.")

# ── 23. SYNTAX ────────────────────────────────────────────────────────────────
print("\n=== TEST 23: SYNTAX — ALL PROJECT FILES ===")
import subprocess
files = [
    "genesis.py", "core/__init__.py", "core/task_queue.py", "core/task_planner.py",
    "core/skill_manager.py", "core/tool_manager.py", "core/memory_governor.py",
    "core/memory_interface.py", "core/orchestrator.py", "core/base_worker.py",
    "core/logger.py", "core/worker_identity.py", "core/worker_report.py",
    "workers/research_worker.py", "workers/acquisition_worker.py",
    "workers/marketing_worker.py", "workers/finance_worker.py", "workers/__init__.py",
    "skills/google_review_product/skill.py", "skills/customer_validation/skill.py",
    "skills/business_evaluation/skill.py",
    "test_phase12_task_queue.py",
]
proc = subprocess.run([sys.executable, "-m", "py_compile"] + files, capture_output=True, text=True)
if proc.returncode != 0:
    print(f"✗ Syntax errors:\n{proc.stderr}")
    sys.exit(1)
print(f"✓ Syntax clean — {len(files)} files, 0 errors.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 12 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
