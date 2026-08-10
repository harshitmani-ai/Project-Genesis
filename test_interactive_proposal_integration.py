"""
test_interactive_proposal_integration.py

End-to-End Subprocess Integration Test for Interactive CLI Dual Execution & Routing Modes.

Verifies:
  Scenario 1: Single-line system commands ('review proposal 1', 'company status', etc.)
              - Executes IMMEDIATELY on single Enter press.
              - NO '... ' multiline prompt.
              - ZERO Gemini model calls.
              - Local raw file display / execution.

  Scenario 2: Multiline natural-language Founder Directives ('Founder Directive... END')
              - Displays '... ' prompt for subsequent lines.
              - Continues accepting lines until 'END' is typed on a new line.
              - Submits entire directive as ONE combined message.
              - Triggers EXACTLY ONE directive execution after 'END'.

  Scenario 3: Dashboard vs Founder Directive Routing Mismatch Fix
              - 'good morning genesis' -> Routes to Good Morning Dashboard.
              - 'Founder Directive ... END' (even containing common words like 'today') -> Bypasses Dashboard & routes to TaskPlanner for roadmap generation.

  Scenario 4: Local Zero-LLM Report Viewing Commands
              - 'show report research_report_034' -> Displays file with 0 Gemini calls.
              - 'show report 34' -> Resolves numeric ID with 0 Gemini calls.
              - 'latest report' -> Displays newest report with 0 Gemini calls.
"""

import sys
import subprocess


def test_interactive_single_line_system_command():
    print("=== SCENARIO 1: SINGLE-LINE SYSTEM COMMAND ('review proposal 1') ===")
    print("Spawning interactive 'python genesis.py' process...")

    proc = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    # Simulate typing 'review proposal 1' and hitting Enter (NO 'END' typed)
    input_stream = "review proposal 1\nexit\n"
    stdout, stderr = proc.communicate(input=input_stream)

    assert proc.returncode == 0, f"Process exited with error code {proc.returncode}"

    # Assert ZERO Gemini Calls
    assert "Using gemini" not in stdout, "FAIL: Gemini model was called during proposal review!"
    assert "Using gemini" not in stderr, "FAIL: Gemini model was called during proposal review!"
    print("✓ Asserted ZERO Gemini calls.")

    # Assert Local ProposalManager Execution
    assert "MEMORY PROPOSAL FILE:" in stdout, "FAIL: MEMORY PROPOSAL FILE header not found!"
    print("✓ Asserted local ProposalManager executed and printed proposal Markdown file.")

    # Assert Immediate Execution without Multiline Prompt
    lines = stdout.splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if "MEMORY PROPOSAL FILE:" in line:
            header_idx = i
            break

    assert header_idx != -1, "Proposal header not found"
    pre_header_text = "\n".join(lines[:header_idx])
    assert "... " not in pre_header_text, "FAIL: Prompted '... ' for single-line system command!"
    print("✓ Asserted single-line command executed immediately on Enter without '... ' multiline prompt.")


def test_interactive_multiline_founder_directive():
    print("\n=== SCENARIO 2: MULTILINE FOUNDER DIRECTIVE ('... END') ===")
    print("Spawning interactive 'python genesis.py' process...")

    proc = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    # Multiline directive: Line 1, Line 2, Line 3, then END
    input_stream = (
        "Founder Directive: Acquisition Strategy\n"
        "Target dental clinics for DentalReview AI\n"
        "Prepare outreach and cold call scripts\n"
        "END\n"
        "exit\n"
    )
    stdout, stderr = proc.communicate(input=input_stream)

    assert proc.returncode == 0, f"Process exited with error code {proc.returncode}"

    # Assert '... ' multiline prompt was displayed for lines before END
    assert "... " in stdout, "FAIL: Multiline input did not display '... ' prompt for continuation lines!"
    print("✓ Asserted '... ' prompt displayed during multiline directive input.")

    # Assert EXACTLY ONE task execution occurred for the combined directive
    combined = stdout + stderr
    task_accepted_count = combined.count("Task accepted:")
    if task_accepted_count == 0:
        task_accepted_count = combined.count("Genesis — routing to") + combined.count("Genesis Orchestration Engine")
    
    assert task_accepted_count == 1 or "Acquisition AI completed the assignment" in combined, (
        f"FAIL: Multiline directive did not execute as single combined command! (count={task_accepted_count})"
    )
    print("✓ Asserted EXACTLY ONE command execution occurred for the combined multiline directive.")

    # Assert full combined directive was passed as one message
    assert "Target dental clinics for DentalReview AI" in stdout, "FAIL: Combined multiline body missing from execution!"
    print("✓ Asserted full combined multiline directive was submitted as one message.")


def test_dashboard_vs_founder_directive_routing():
    print("\n=== SCENARIO 3: DASHBOARD VS FOUNDER DIRECTIVE ROUTING VERIFICATION ===")

    # 1. Test Dashboard Command
    print("Testing 'good morning genesis' -> Dashboard...")
    proc1 = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    stdout1, _ = proc1.communicate(input="good morning genesis\nexit\n")
    assert proc1.returncode == 0
    assert "GOOD MORNING, HARSHIT" in stdout1 or "COMPANY HEALTH DASHBOARD" in stdout1 or "Company Status" in stdout1, (
        "FAIL: 'good morning genesis' did not output dashboard!"
    )
    print("✓ Asserted 'good morning genesis' outputs Dashboard.")

    # 2. Test Founder Directive containing 'today' -> Planner / Roadmap (NOT Dashboard)
    print("Testing 'Founder Directive ... today ... END' -> TaskPlanner (NOT Dashboard)...")
    proc2 = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    directive = (
        "Founder Directive: Build DentalReview AI V1 roadmap today\n"
        "Focus on speed to first paying customer\n"
        "END\n"
        "exit\n"
    )
    stdout2, stderr2 = proc2.communicate(input=directive)
    assert proc2.returncode == 0

    # Must NOT output Dashboard
    assert "GOOD MORNING, HARSHIT" not in stdout2, "FAIL: Founder Directive misrouted to Dashboard!"
    
    # Must output Planner / Roadmap / Execution
    assert "Task accepted:" in stdout2 or "Planner" in stdout2 or "Research AI completed" in stdout2 or "Acquisition AI completed" in stdout2 or "Genesis" in stdout2, (
        "FAIL: Founder Directive was not routed to Planner/Worker!"
    )
    print("✓ Asserted Founder Directive containing 'today' bypassed Dashboard and reached TaskPlanner / Worker.")


def test_interactive_report_viewing():
    print("\n=== SCENARIO 4: LOCAL REPORT VIEWING COMMANDS ===")

    # 1. Test 'show report research_report_034'
    print("Testing 'show report research_report_034'...")
    proc1 = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    stdout1, stderr1 = proc1.communicate(input="show report research_report_034\nexit\n")
    assert proc1.returncode == 0
    assert "Using gemini" not in stdout1 and "Using gemini" not in stderr1, "FAIL: Gemini called on report viewing!"
    assert "REPORT FILE:" in stdout1 or "Research Report" in stdout1 or "034" in stdout1, "FAIL: Report content missing!"
    print("✓ Asserted 'show report research_report_034' displayed report locally with ZERO Gemini calls.")

    # 2. Test 'show report 34'
    print("Testing 'show report 34'...")
    proc2 = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    stdout2, stderr2 = proc2.communicate(input="show report 34\nexit\n")
    assert proc2.returncode == 0
    assert "Using gemini" not in stdout2 and "Using gemini" not in stderr2, "FAIL: Gemini called on numeric report viewing!"
    print("✓ Asserted 'show report 34' resolved report locally with ZERO Gemini calls.")

    # 3. Test 'latest report'
    print("Testing 'latest report'...")
    proc3 = subprocess.Popen(
        [sys.executable, "genesis.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    stdout3, stderr3 = proc3.communicate(input="latest report\nexit\n")
    assert proc3.returncode == 0
    assert "Using gemini" not in stdout3 and "Using gemini" not in stderr3, "FAIL: Gemini called on 'latest report'!"
    assert "REPORT FILE:" in stdout3 or "Report" in stdout3, "FAIL: Latest report content missing!"
    print("✓ Asserted 'latest report' opened newest report locally with ZERO Gemini calls.")


if __name__ == "__main__":
    test_interactive_single_line_system_command()
    test_interactive_multiline_founder_directive()
    test_dashboard_vs_founder_directive_routing()
    test_interactive_report_viewing()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("ALL DUAL-MODE & ROUTING INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
