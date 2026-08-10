"""
test_local_proposal_manager.py

Automated Test Suite for Local ProposalManager & Non-AI Proposal Command Routing.
"""

import sys
import shutil
from pathlib import Path
from unittest.mock import patch

from core.memory_governor import MemoryGovernor, ProposalManager, DEFAULT_PROPOSAL_MANAGER
import genesis

def test_proposal_manager():
    print("=== TEST 1: PROPOSALMANAGER IMPORT & ALIAS ===")
    assert ProposalManager is MemoryGovernor
    assert isinstance(DEFAULT_PROPOSAL_MANAGER, MemoryGovernor)
    print("✓ ProposalManager alias verified.")

    print("\n=== TEST 2: PROPOSAL IDENTIFIER RESOLUTION ===")
    proposals_dir = Path("company_memory") / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test proposals if needed
    test_p1 = proposals_dir / "proposal_test_901.md"
    test_p2 = proposals_dir / "proposal_test_902.md"
    test_p1.write_text("# Proposal 901\nTest content 901\n", encoding="utf-8")
    test_p2.write_text("# Proposal 902\nTest content 902\n", encoding="utf-8")

    pm = ProposalManager()
    path1, err1 = pm.resolve_proposal(1)
    assert err1 is None
    assert path1 is not None
    print(f"✓ Resolved index 1 to {path1.name}")

    path2, err2 = pm.resolve_proposal("proposal_test_902.md")
    assert err2 is None
    assert path2 is not None
    assert path2.name == "proposal_test_902.md"
    print(f"✓ Resolved filename 'proposal_test_902.md' to {path2.name}")

    _, err_inv = pm.resolve_proposal(999)
    assert err_inv is not None
    print(f"✓ Out of bounds error handled: {err_inv}")

    print("\n=== TEST 3: ZERO-LLM LOCAL PROPOSAL REVIEW ===")
    review_output = pm.review_proposal("proposal_test_901.md")
    assert "MEMORY PROPOSAL FILE" in review_output
    assert "Test content 901" in review_output
    print("✓ Proposal review output rendered locally without LLM.")

    print("\n=== TEST 4: COMMAND ROUTING HELPERS IN GENESIS.PY ===")
    assert genesis.should_review_single_proposal("review proposal 1")
    assert genesis.should_review_single_proposal("show proposal 2")
    assert genesis.should_review_single_proposal("view proposal proposal_test_901.md")
    
    assert genesis.should_approve_single_proposal("approve proposal 1")
    assert genesis.should_approve_single_proposal("merge proposal 2")

    assert genesis.should_reject_single_proposal("reject proposal 1")
    assert genesis.should_reject_single_proposal("deny proposal 2")

    assert genesis.should_reject_all_proposals("reject all proposals")
    assert genesis.is_proposal_command("review proposal 1")
    print("✓ All proposal command routing helpers verified.")

    print("\n=== TEST 5: ZERO LLM CALLS ON HANDLE_COMMAND ===")
    with patch("brain.ask_ai") as mock_ask_ai:
        genesis.handle_command("review proposal 1")
        mock_ask_ai.assert_not_called()
        print("✓ genesis.handle_command('review proposal 1') made ZERO LLM calls.")

    # Cleanup temporary test proposals
    if test_p1.exists():
        test_p1.unlink()
    if test_p2.exists():
        test_p2.unlink()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("ALL LOCAL PROPOSAL MANAGER TESTS PASSED SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == "__main__":
    test_proposal_manager()
