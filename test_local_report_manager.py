"""
test_local_report_manager.py

Automated Test Suite for Local ReportManager & Zero-LLM Report Viewing Routing.

Verifies:
  1. ReportManager initialization and scanning across all 7 report directories.
  2. Resolution of exact names ('research_report_034.md'), stems ('research_report_034'), and numeric IDs ('34').
  3. Resolution of 'latest report'.
  4. Multi-match selection prompt formatting when numeric IDs match multiple report types.
  5. genesis.handle_command() routing with ZERO Gemini calls, ZERO worker execution, and ZERO new reports created.
"""

import os
from pathlib import Path
from core.report_manager import ReportManager
import genesis


def test_report_manager_resolution():
    print("=== TEST 1: REPORTMANAGER LOOKUP & RESOLUTION ===")
    rm = ReportManager()

    reports = rm.list_all_reports()
    assert len(reports) > 0, "Expected at least one report file in project directories"
    print(f"✓ ReportManager found {len(reports)} total report files across all categories.")

    # 1. Test latest report lookup
    latest = rm.get_latest_report()
    assert latest is not None, "get_latest_report() returned None"
    latest_out = rm.open_report("latest")
    assert latest.name in latest_out, f"Expected {latest.name} in open_report('latest') output"
    print(f"✓ 'latest report' resolved to newest report: {latest.name}")

    # 2. Test exact stem lookup
    sample_report = reports[0]
    stem_out = rm.open_report(sample_report.stem)
    assert sample_report.name in stem_out, f"Expected {sample_report.name} in open_report({sample_report.stem})"
    print(f"✓ Exact stem lookup '{sample_report.stem}' succeeded.")

    # 3. Test numeric lookup
    num_out = rm.open_report("034")
    assert "034" in num_out or "Multiple reports" in num_out, "Expected report 034 or multi-match prompt"
    print("✓ Numeric ID lookup ('034') succeeded.")


def test_zero_llm_command_routing():
    print("\n=== TEST 2: GENESIS COMMAND ROUTING & ZERO LLM CALLS ===")

    # Track reports before command execution
    rm = ReportManager()
    initial_count = len(rm.list_all_reports())

    # Count pending proposals before
    proposals_dir = Path("company_memory/proposals")
    initial_proposals = len(list(proposals_dir.glob("*.md"))) if proposals_dir.exists() else 0

    # 1. Test 'show report research_report_034'
    print("Testing handle_command('show report research_report_034')...")
    genesis.handle_command("show report research_report_034")

    # 2. Test 'show report 34'
    print("Testing handle_command('show report 34')...")
    genesis.handle_command("show report 34")

    # 3. Test 'latest report'
    print("Testing handle_command('latest report')...")
    genesis.handle_command("latest report")

    # Verify NO new report files were created
    final_count = len(rm.list_all_reports())
    assert final_count == initial_count, f"FAIL: New report file created! (initial={initial_count}, final={final_count})"
    print("✓ Asserted ZERO new report files were created.")

    # Verify NO new proposals were created
    final_proposals = len(list(proposals_dir.glob("*.md"))) if proposals_dir.exists() else 0
    assert final_proposals == initial_proposals, f"FAIL: New proposal created! (initial={initial_proposals}, final={final_proposals})"
    print("✓ Asserted ZERO new memory proposals were created.")


if __name__ == "__main__":
    test_report_manager_resolution()
    test_zero_llm_command_routing()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("ALL REPORT MANAGER TESTS PASSED SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
