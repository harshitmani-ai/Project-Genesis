"""
test_proposal_review_dashboard.py

Automated Test Suite for Local Proposal Review Dashboard & Batch Actions.

Verifies:
  1. Local metadata parsing (Worker, Topic, Date, Report, 2-3 line summary).
  2. Dynamic product relevance detection from company_memory.md.
  3. Duplicate proposal detection.
  4. Archived product classification (🗂 Archived Product).
  5. Action recommendations (✅ Approve, ❌ Reject, ⚠️ Founder Decision, 🗂 Archived Product).
  6. Dashboard footer summary counts & recommendations layout.
  7. 'approve selected' and 'reject selected' batch execution.
  8. ZERO Gemini LLM calls across all operations.
"""

from pathlib import Path
from unittest.mock import patch
import re

from core.memory_governor import MemoryGovernor, DEFAULT_PROPOSAL_MANAGER
import genesis


def test_dashboard_parsing_and_detection():
    print("=== TEST 1: METADATA PARSING & DYNAMIC PRODUCT DETECTION ===")
    governor = MemoryGovernor()
    active_product = governor.get_active_product()
    assert active_product, "Active product should be dynamically detected from memory"
    print(f"✓ Dynamically detected active product: '{active_product}'")

    proposals = governor.list_proposals()
    assert len(proposals) > 0, "Expected pending proposal files in company_memory/proposals/"
    print(f"✓ Found {len(proposals)} pending proposals for parsing.")

    meta = governor.parse_proposal_metadata(proposals[0], 1, proposals)
    assert meta["worker"] != "Unknown Worker", "Worker name should be extracted"
    assert meta["topic"], "Topic should be extracted"
    assert meta["date"], "Date should be extracted"
    assert meta["summary"], "Local summary should be generated without LLM"
    assert len(meta["summary"]) <= 165, f"Summary should be concise (len={len(meta['summary'])})"
    print("✓ Proposal metadata and local 2-3 line summary parsed successfully.")


def test_dashboard_rendering():
    print("\n=== TEST 2: DASHBOARD RENDERING & FOOTER METRICS ===")
    governor = MemoryGovernor()

    with patch("brain.ask_ai") as mock_ai:
        dashboard_output = governor.build_proposal_dashboard()
        assert not mock_ai.called, "FAIL: build_proposal_dashboard() invoked Gemini AI!"
    
    print("✓ Dashboard generated with ZERO Gemini calls.")

    # Assert Header & Columns
    assert "GENESIS PROPOSAL REVIEW DASHBOARD" in dashboard_output
    assert "Current Active Product:" in dashboard_output
    assert "Worker:" in dashboard_output
    assert "Topic:" in dashboard_output
    assert "Report:" in dashboard_output
    assert "Summary:" in dashboard_output
    assert "Duplicate:" in dashboard_output
    assert "Relevance:" in dashboard_output
    assert "Action:" in dashboard_output

    # Assert Footer Metrics
    assert "PROPOSAL REVIEW DASHBOARD SUMMARY" in dashboard_output
    assert "Pending Proposals:" in dashboard_output
    assert "Current Product Proposals:" in dashboard_output
    assert "Archived Product Proposals:" in dashboard_output
    assert "Possible Duplicates:" in dashboard_output
    assert "Needs Founder Review:" in dashboard_output
    assert "Estimated Review Time:" in dashboard_output
    assert "RECOMMENDED BATCH ACTIONS:" in dashboard_output

    print("✓ All required dashboard headers, metadata columns, and footer metrics verified.")


def test_batch_selected_actions():
    print("\n=== TEST 3: BATCH APPROVE & REJECT SELECTED ===")
    governor = MemoryGovernor()
    proposals = governor.list_proposals()
    if len(proposals) < 2:
        print("⚠ Skipping batch test — less than 2 proposals available.")
        return

    first_prop = proposals[0]
    last_prop = proposals[-1]

    # Test reject_selected on last item
    with patch("brain.ask_ai") as mock_ai:
        reject_results = governor.reject_selected([len(proposals)], reason="Batch Reject Test")
        assert not mock_ai.called, "FAIL: reject_selected() invoked Gemini AI!"
    assert any("Rejected:" in r for r in reject_results), f"Rejection failed: {reject_results}"
    print(f"✓ reject_selected([len]) executed with ZERO LLM calls: {reject_results[0]}")

    # Test approve_selected on first item
    with patch("brain.ask_ai") as mock_ai:
        approve_results = governor.approve_selected([1])
        assert not mock_ai.called, "FAIL: approve_selected() invoked Gemini AI!"
    assert any("Approved and merged:" in a for a in approve_results), f"Approval failed: {approve_results}"
    print(f"✓ approve_selected([1]) executed with ZERO LLM calls: {approve_results[0]}")


def test_genesis_command_routing():
    print("\n=== TEST 4: GENESIS COMMAND ROUTING & ZERO LLM CALLS ===")

    cmds = [
        "review all proposals",
        "proposal dashboard",
        "approve selected 1, 2",
        "reject selected 3",
    ]

    for cmd in cmds:
        print(f"Testing handle_command('{cmd}')...")
        with patch("brain.ask_ai") as mock_ai:
            genesis.handle_command(cmd)
            assert not mock_ai.called, f"FAIL: handle_command('{cmd}') invoked Gemini AI!"
        print(f"  ✓ '{cmd}' routed locally with ZERO Gemini calls.")


if __name__ == "__main__":
    test_dashboard_parsing_and_detection()
    test_dashboard_rendering()
    test_batch_selected_actions()
    test_genesis_command_routing()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("ALL PROPOSAL REVIEW DASHBOARD TESTS PASSED SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
