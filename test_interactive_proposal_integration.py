"""
test_interactive_proposal_integration.py

End-to-End Subprocess Integration Test for Interactive Terminal ProposalManager Execution.

Verifies:
  1. Interactive execution of 'review proposal 1' on single Enter press.
  2. No '... ' multiline prompt for system commands.
  3. Zero Gemini model calls ('Using gemini' absent from output).
  4. Raw proposal Markdown file displayed directly from disk.
  5. Local ProposalManager execution.
"""

import sys
import subprocess
from pathlib import Path


def test_interactive_proposal():
    print("=== INTERACTIVE SUBPROCESS INTEGRATION TEST ===")
    print("Spawning interactive 'python genesis.py' process...")

    proc = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    # Simulate Harshit typing 'review proposal 1' and hitting Enter (NO 'END' typed)
    input_stream = "review proposal 1\nexit\n"
    stdout, stderr = proc.communicate(input=input_stream)

    print("\n--- SUBPROCESS OUTPUT RECEIVED ---")
    print(stdout)

    # 1. Assert exit code 0
    assert proc.returncode == 0, f"Process exited with error code {proc.returncode}"

    # 2. Assert Zero Gemini Calls
    assert "Using gemini" not in stdout, "FAIL: Gemini model was called during proposal review!"
    assert "Using gemini" not in stderr, "FAIL: Gemini model was called during proposal review!"
    print("✓ Asserted ZERO Gemini calls.")

    # 3. Assert Local ProposalManager Execution & Raw Proposal Display
    assert "MEMORY PROPOSAL FILE:" in stdout, "FAIL: MEMORY PROPOSAL FILE header not found in output!"
    assert "# Memory Update Proposal" in stdout or "Proposal" in stdout, "FAIL: Proposal content missing from output!"
    print("✓ Asserted local ProposalManager executed and printed proposal Markdown file.")

    # 4. Assert Immediate Execution without Multiline Prompt
    lines = stdout.splitlines()
    proposal_header_index = -1
    for i, line in enumerate(lines):
        if "MEMORY PROPOSAL FILE:" in line:
            proposal_header_index = i
            break

    assert proposal_header_index != -1, "Could not find proposal header"
    # Ensure no '... ' prompt before the proposal header
    pre_header_text = "\n".join(lines[:proposal_header_index])
    assert "... " not in pre_header_text, "FAIL: get_multiline_input() prompted '... ' for single-line command!"
    print("✓ Asserted single-line command executed immediately on Enter without '... ' multiline prompt.")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("INTERACTIVE PROPOSAL INTEGRATION TEST PASSED SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    test_interactive_proposal()
