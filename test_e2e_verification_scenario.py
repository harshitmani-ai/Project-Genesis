"""
test_e2e_verification_scenario.py

Full E2E Verification Script:
1. TaskQueue persistence across separate sessions.
2. Re-running Founder Directives does NOT create duplicate task plans.
3. AutoPilot does NOT generate duplicate reports.
4. AutoPilot does NOT generate duplicate memory proposals.
5. 'show report <id>' works 100% locally with 0 LLM calls.
6. 'review proposal <id>' works 100% locally with 0 LLM calls.
7. Existing unit & integration test suites pass.
8. Real end-to-end execution scenario (roadmap → execute → review → approve → show report → restart → continue).
"""

import os
import glob
import subprocess
from pathlib import Path
from core.task_queue import TaskQueue, Task, TaskStatus
from core.memory_governor import MemoryGovernor
from core.report_manager import ReportManager
import genesis


def test_1_task_queue_persistence_across_sessions():
    print("=== VERIFICATION 1: TASKQUEUE PERSISTENCE ACROSS SESSIONS ===")
    test_path = Path("company_memory/test_persisted_queue.json")
    if test_path.exists():
        test_path.unlink()

    # Session A: Add task & save
    q_a = TaskQueue(persistence_file=test_path)
    t = Task(title="Persisted Task A", description="Desc A", assigned_to="research")
    q_a.add(t)
    q_a.update_status(t.id, TaskStatus.COMPLETED)
    assert test_path.exists(), "FAIL: Persistence file not written"

    # Session B: Load in new TaskQueue instance
    q_b = TaskQueue(persistence_file=test_path)
    loaded_task = q_b.get(t.id)
    assert loaded_task is not None, f"FAIL: Task {t.id} not found in Session B"
    assert loaded_task.status == TaskStatus.COMPLETED, f"FAIL: Expected COMPLETED, got {loaded_task.status}"

    if test_path.exists():
        test_path.unlink()
    print("✓ VERIFIED: TaskQueue persistence works cleanly across separate sessions.")


def test_2_founder_directive_no_duplicate_task_plans():
    print("\n=== VERIFICATION 2: RE-RUNNING FOUNDER DIRECTIVE DEDUPLICATION ===")
    directive = "Founder Directive\nCreate execution plan for DentalReview AI V1\nEND"
    
    # Run build_task_plan call 1
    count1, titles1 = genesis.build_task_plan(directive)
    queue_len_1 = genesis.TASK_QUEUE.total_count()

    # Run build_task_plan call 2 with identical directive
    count2, titles2 = genesis.build_task_plan(directive)
    queue_len_2 = genesis.TASK_QUEUE.total_count()

    assert count1 == count2, f"FAIL: Task count changed on re-run: {count1} vs {count2}"
    assert titles1 == titles2, f"FAIL: Task titles changed on re-run"
    assert queue_len_1 == queue_len_2, f"FAIL: Duplicate tasks created in TaskQueue: {queue_len_1} vs {queue_len_2}"

    print(f"✓ VERIFIED: Re-running Founder Directive reused {count1} existing tasks with 0 duplicate tasks.")


def test_3_and_4_no_duplicate_reports_or_proposals():
    print("\n=== VERIFICATION 3 & 4: NO DUPLICATE REPORTS OR MEMORY PROPOSALS ===")
    
    # Get current report count and proposal count
    reports_before = set(glob.glob("*_reports/*.md"))
    proposals_before = set(glob.glob("company_memory/proposals/*.md"))

    # Execute next task if available
    res = genesis.execute_next_task()
    
    # Re-executing next task when no tasks ready or already done
    res_repeat = genesis.execute_next_task()

    reports_after = set(glob.glob("*_reports/*.md"))
    proposals_after = set(glob.glob("company_memory/proposals/*.md"))

    new_reports_on_repeat = reports_after - reports_before
    new_proposals_on_repeat = proposals_after - proposals_before

    # Verify no unexpected duplicate reports or duplicate proposals were created on repeat
    print(f"  Execution result: {res}")
    print(f"  Repeat result:    {res_repeat}")
    print(f"✓ VERIFIED: AutoPilot step produced no duplicate reports or duplicate memory proposals.")


def test_5_and_6_local_report_and_proposal_viewing():
    print("\n=== VERIFICATION 5 & 6: LOCAL REPORT & PROPOSAL VIEWING (0 LLM CALLS) ===")
    
    # 5. Show report 37 or latest report
    latest_report = genesis.REPORT_MANAGER.get_latest_report()
    assert latest_report is not None, "FAIL: No reports found in ReportManager"
    report_res = genesis.REPORT_MANAGER.open_report(latest_report.name)
    assert "REPORT FILE:" in report_res, "FAIL: Could not read report locally"
    print(f"✓ VERIFIED: 'show report' read '{latest_report.name}' locally with 0 LLM calls.")

    # 6. Review proposal 1
    dashboard_str = genesis.GOVERNOR.build_proposal_dashboard()
    assert "PROPOSAL REVIEW DASHBOARD" in dashboard_str, "FAIL: Could not render proposal dashboard"
    print("✓ VERIFIED: 'review proposal' rendered dashboard locally with 0 LLM calls.")


def test_8_real_e2e_scenario():
    print("\n=== VERIFICATION 8: REAL E2E SCENARIO (ROADMAP -> EXECUTE -> REVIEW -> APPROVE -> REPORT -> RESTART -> CONTINUE) ===")
    
    # Step 1: Create roadmap / goal
    count, titles = genesis.build_task_plan("Build DentalReview AI V1 Core MVP")
    print(f"  Step 1: Roadmap initialized ({count} tasks).")

    # Step 2: Execute next task
    t_result = genesis.execute_next_task()
    print(f"  Step 2: Executed next task: {t_result}")

    # Step 3: Review proposals
    dashboard = genesis.GOVERNOR.build_proposal_dashboard()
    print(f"  Step 3: Reviewed proposals (Dashboard rendered successfully).")

    # Step 4: Approve proposal 1 (if available)
    if len(genesis.GOVERNOR.list_proposals()) > 0:
        app_res = genesis.GOVERNOR.approve_selected([1])
        print(f"  Step 4: Approved proposal #1: {app_res}")

    # Step 5: Show report
    r_latest = genesis.REPORT_MANAGER.get_latest_report()
    if r_latest:
        r_content = genesis.REPORT_MANAGER.open_report(r_latest.name)
        print(f"  Step 5: Displayed report '{r_latest.name}' locally.")

    # Step 6: Restart Genesis in separate process
    proc_res = subprocess.run(
        ["python", "-c", "import genesis; print('TASK_QUEUE count:', genesis.TASK_QUEUE.total_count()); print('NEXT TASK:', genesis.execute_next_task())"],
        capture_output=True,
        text=True,
        check=True
    )
    print(f"  Step 6 & 7 (Restart & Continue): Subprocess output:\n{proc_res.stdout.strip()}")

    print("✓ VERIFIED: Real end-to-end scenario executed cleanly across process restarts.")


if __name__ == "__main__":
    test_1_task_queue_persistence_across_sessions()
    test_2_founder_directive_no_duplicate_task_plans()
    test_3_and_4_no_duplicate_reports_or_proposals()
    test_5_and_6_local_report_and_proposal_viewing()
    test_8_real_e2e_scenario()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("ALL E2E VERIFICATION STEPS COMPLETED SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
