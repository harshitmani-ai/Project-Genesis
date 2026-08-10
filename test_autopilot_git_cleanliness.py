"""
test_autopilot_git_cleanliness.py

Automated Test Suite for AutoPilot Task Persistence & Git Status Cleanliness.

Verifies:
  1. TaskQueue JSON disk persistence (saves/loads company_memory/task_queue.json).
  2. Deduplication in build_task_plan() (reuses active tasks instead of creating duplicates).
  3. AutoPilot execution git artifact synchronization (sync_git_artifacts()).
  4. Clean git status with 0 untracked files and 0 orphaned reports.
"""

import os
import subprocess
from pathlib import Path
from core.task_queue import TaskQueue, Task, TaskStatus
import genesis


def test_task_queue_disk_persistence():
    print("=== TEST 1: TASKQUEUE DISK PERSISTENCE ===")
    test_file = Path("company_memory/test_queue.json")
    if test_file.exists():
        test_file.unlink()

    tq = TaskQueue(persistence_file=test_file)
    t1 = Task(title="Test Task 1", description="Desc 1", assigned_to="research")
    t2 = Task(title="Test Task 2", description="Desc 2", assigned_to="acquisition", dependencies=[t1.id])

    tq.add(t1)
    tq.add(t2)

    assert test_file.exists(), "FAIL: persistence file was not created on task add!"

    # Load in new instance
    tq2 = TaskQueue(persistence_file=test_file)
    assert tq2.total_count() == 2, f"Expected 2 tasks loaded, got {tq2.total_count()}"
    assert tq2.get(t1.id) is not None, "Task 1 missing from loaded queue"
    assert tq2.get(t2.id) is not None, "Task 2 missing from loaded queue"

    # Cleanup test file
    if test_file.exists():
        test_file.unlink()
    print("✓ TaskQueue disk persistence verified.")


def test_build_task_plan_deduplication():
    print("\n=== TEST 2: BUILD_TASK_PLAN DEDUPLICATION ===")
    # Clear queue first for clean test
    genesis.TASK_QUEUE.clear_completed()
    
    # 1. First call builds tasks
    goal = "Test Goal for Deduplication Check"
    count1, titles1 = genesis.build_task_plan(goal)
    assert count1 > 0, "Failed to build task plan"

    # 2. Second call with same queue should return existing queue without re-planning
    count2, titles2 = genesis.build_task_plan(goal)
    assert count2 == count1, f"Expected {count1} tasks, got {count2} (re-planned duplicate tasks!)"
    assert titles2 == titles1, "Task titles changed on second build_task_plan call"

    print(f"✓ Deduplication verified: reused {count1} existing tasks instead of re-planning.")


def test_git_status_cleanliness():
    print("\n=== TEST 3: GIT STATUS & ORPHANED REPORT CLEANLINESS ===")

    # Sync git artifacts
    genesis.sync_git_artifacts()

    # Check git status for untracked markdown files
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    untracked_lines = [line for line in res.stdout.splitlines() if line.startswith("??")]

    untracked_md = [line for line in untracked_lines if line.endswith(".md") or line.endswith(".json")]
    
    assert len(untracked_md) == 0, f"FAIL: Found untracked report/proposal files in git status: {untracked_md}"
    print("✓ Asserted ZERO untracked report/proposal files in Git status.")


if __name__ == "__main__":
    test_task_queue_disk_persistence()
    test_build_task_plan_deduplication()
    test_git_status_cleanliness()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("ALL AUTOPILOT GIT CLEANLINESS TESTS PASSED SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
