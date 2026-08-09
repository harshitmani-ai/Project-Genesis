"""
test_phase10_tool_manager.py

Comprehensive Phase 10 Verification Test Suite for the Tool Integration Layer.

Tests:
  1.  Imports verification
  2.  ToolResult structure
  3.  Tool registration (valid and invalid)
  4.  Duplicate registration prevention
  5.  File Reader tool — success
  6.  File Reader tool — missing file error handling
  7.  File Writer tool — success (safe path)
  8.  File Writer tool — blocked: outside project root
  9.  File Writer tool — blocked: .py source file
  10. Directory Lister tool — success
  11. Web Search tool — placeholder result
  12. Report Exporter tool — markdown export
  13. ToolManager execution log — entries and summary
  14. Unknown tool name — graceful ToolResult failure
  15. DEFAULT_TOOL_MANAGER has all 5 built-in tools
  16. TOOL_MANAGER instance in genesis.py
  17. show_tools / should_show_tools routing helpers
  18. Backward compatibility — all prior keyword routes intact
  19. Custom tool registration by a worker
  20. Syntax compilation — all project files
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# ── 1. IMPORTS TEST ─────────────────────────────────────────────────────────
print("=== TEST 1: IMPORTS VERIFICATION ===")
try:
    from core.tool_manager import (
        Tool,
        ToolResult,
        ToolManager,
        FileReaderTool,
        FileWriterTool,
        DirectoryListerTool,
        WebSearchTool,
        ReportExporterTool,
        DEFAULT_TOOL_MANAGER,
    )
    from core import (
        Tool as ToolFromCore,
        ToolResult as TRFromCore,
        ToolManager as TMFromCore,
        DEFAULT_TOOL_MANAGER as DTMFromCore,
    )
    from genesis import (
        TOOL_MANAGER,
        show_tools,
        should_show_tools,
    )
    print("✓ All imports passed.")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# ── 2. TOOLRESULT STRUCTURE ──────────────────────────────────────────────────
print("\n=== TEST 2: TOOLRESULT STRUCTURE ===")
tr_ok = ToolResult(
    tool_name="test_tool",
    success=True,
    output="hello",
    execution_time_ms=12.5,
)
assert tr_ok.tool_name == "test_tool"
assert tr_ok.success is True
assert tr_ok.output == "hello"
assert tr_ok.error is None
assert tr_ok.execution_time_ms == 12.5
assert "✓" in str(tr_ok)

tr_fail = ToolResult(
    tool_name="broken_tool",
    success=False,
    output=None,
    error="Something went wrong",
    execution_time_ms=3.0,
)
assert tr_fail.success is False
assert "✗" in str(tr_fail)
assert "Something went wrong" in str(tr_fail)
print("✓ ToolResult fields, __str__ (✓/✗), and defaults verified.")

# ── 3. TOOL REGISTRATION ─────────────────────────────────────────────────────
print("\n=== TEST 3: TOOL REGISTRATION (VALID & INVALID) ===")
class SampleTool(Tool):
    name = "sample_tool"
    description = "A sample test tool."
    def execute(self, **kwargs): return "sample output"

tm = ToolManager()
tm.register(SampleTool())
assert "sample_tool" in tm.list_tools()
print("✓ Valid tool registered successfully.")

# Invalid: non-Tool object
try:
    tm.register("not a tool")
    assert False, "Should have raised TypeError"
except TypeError as e:
    print(f"✓ Non-Tool object rejected with TypeError: {e}")

# ── 4. DUPLICATE REGISTRATION PREVENTION ────────────────────────────────────
print("\n=== TEST 4: DUPLICATE REGISTRATION PREVENTION ===")
try:
    tm.register(SampleTool())  # second registration with same name
    assert False, "Should have raised ValueError"
except ValueError as e:
    print(f"✓ Duplicate tool name rejected with ValueError: {e}")

# Deregister and re-register (should succeed)
tm.deregister("sample_tool")
tm.register(SampleTool())
assert "sample_tool" in tm.list_tools()
print("✓ Deregister + re-register works correctly.")

# ── 5. FILE READER — SUCCESS ─────────────────────────────────────────────────
print("\n=== TEST 5: FILE READER TOOL — SUCCESS ===")
reader_tm = ToolManager()
reader_tm.register(FileReaderTool())

result = reader_tm.execute("file_reader", path="company_memory.md")
assert result.success is True, f"FileReader failed: {result.error}"
assert isinstance(result.output, str)
assert len(result.output) > 0
assert result.execution_time_ms >= 0
print(f"✓ FileReaderTool read company_memory.md ({len(result.output)} chars, {result.execution_time_ms}ms).")

# ── 6. FILE READER — MISSING FILE ERROR HANDLING ────────────────────────────
print("\n=== TEST 6: FILE READER TOOL — MISSING FILE (GRACEFUL FAILURE) ===")
result_missing = reader_tm.execute("file_reader", path="does_not_exist_xyz.md")
assert result_missing.success is False
assert result_missing.error is not None
assert "FileNotFoundError" in result_missing.error or "not found" in result_missing.error.lower()
print(f"✓ Missing file handled gracefully. Error: {result_missing.error[:60]}…")

# ── 7. FILE WRITER — SUCCESS (SAFE PATH) ────────────────────────────────────
print("\n=== TEST 7: FILE WRITER TOOL — SUCCESS (SAFE PATH) ===")
writer_tm = ToolManager()
writer_tm.register(FileWriterTool())

safe_path = Path("test_outputs") / "phase10_write_test.md"
result_write = writer_tm.execute(
    "file_writer",
    path=str(safe_path),
    content="# Phase 10 Write Test\n\nThis file was created by the Tool Integration Layer test suite.\n",
)
assert result_write.success is True, f"FileWriter failed: {result_write.error}"
assert safe_path.exists(), "File was not created"
content = safe_path.read_text(encoding="utf-8")
assert "Phase 10 Write Test" in content
print(f"✓ FileWriterTool wrote {len(content)} chars to {safe_path}")

# Cleanup
safe_path.unlink()
safe_path.parent.rmdir()

# ── 8. FILE WRITER — BLOCKED: OUTSIDE PROJECT ROOT ──────────────────────────
print("\n=== TEST 8: FILE WRITER TOOL — BLOCKED (OUTSIDE PROJECT ROOT) ===")
result_blocked = writer_tm.execute(
    "file_writer",
    path="C:\\Windows\\System32\\genesis_hack.txt",
    content="should never write",
)
assert result_blocked.success is False, "Out-of-root write should have been blocked"
assert result_blocked.error is not None
assert "PermissionError" in result_blocked.error or "outside" in result_blocked.error.lower()
print(f"✓ Out-of-root write blocked. Error: {result_blocked.error[:80]}…")

# ── 9. FILE WRITER — BLOCKED: PYTHON SOURCE FILE ────────────────────────────
print("\n=== TEST 9: FILE WRITER TOOL — BLOCKED (.py SOURCE FILE) ===")
result_py_blocked = writer_tm.execute(
    "file_writer",
    path="genesis.py",
    content="# malicious overwrite",
)
assert result_py_blocked.success is False, ".py write should have been blocked"
assert result_py_blocked.error is not None
assert "PermissionError" in result_py_blocked.error or ".py" in result_py_blocked.error.lower()
print(f"✓ Python source file write blocked. Error: {result_py_blocked.error[:80]}…")

# ── 10. DIRECTORY LISTER TOOL ────────────────────────────────────────────────
print("\n=== TEST 10: DIRECTORY LISTER TOOL ===")
dir_tm = ToolManager()
dir_tm.register(DirectoryListerTool())

result_dir = dir_tm.execute("directory_lister", path=".", pattern="*.py")
assert result_dir.success is True, f"DirectoryLister failed: {result_dir.error}"
assert isinstance(result_dir.output, list)
assert len(result_dir.output) > 0
assert any("genesis.py" in entry for entry in result_dir.output)
print(f"✓ DirectoryListerTool listed {len(result_dir.output)} .py files in project root.")

# Error case: missing directory
result_dir_missing = dir_tm.execute("directory_lister", path="/nonexistent/path/xyz")
assert result_dir_missing.success is False
print(f"✓ Missing directory handled gracefully: {result_dir_missing.error[:60]}…")

# ── 11. WEB SEARCH TOOL (PLACEHOLDER) ───────────────────────────────────────
print("\n=== TEST 11: WEB SEARCH TOOL — PLACEHOLDER ===")
ws_tm = ToolManager()
ws_tm.register(WebSearchTool())

result_search = ws_tm.execute("web_search", query="best AI SaaS products 2026")
assert result_search.success is True, f"WebSearch should succeed as placeholder: {result_search.error}"
assert isinstance(result_search.output, dict)
assert result_search.output.get("status") == "placeholder"
assert "query" in result_search.output
assert result_search.output["query"] == "best AI SaaS products 2026"
assert result_search.output["results"] == []
print(f"✓ WebSearchTool returns placeholder result. Query preserved: '{result_search.output['query']}'")

# ── 12. REPORT EXPORTER TOOL ─────────────────────────────────────────────────
print("\n=== TEST 12: REPORT EXPORTER TOOL ===")
re_tm = ToolManager()
re_tm.register(ReportExporterTool())

test_report_folder = Path("test_outputs")
result_export = re_tm.execute(
    "report_exporter",
    content="# Test Export Report\n\nGenerated by Phase 10 test suite.",
    folder=str(test_report_folder),
    filename="phase10_export_test.md",
)
assert result_export.success is True, f"ReportExporter failed: {result_export.error}"
exported_file = test_report_folder / "phase10_export_test.md"
assert exported_file.exists(), "Exported file not found"
exported_content = exported_file.read_text(encoding="utf-8")
assert "Test Export Report" in exported_content
print(f"✓ ReportExporterTool exported {len(exported_content)} chars to {exported_file}")

# Cleanup
exported_file.unlink()
test_report_folder.rmdir()

# ── 13. EXECUTION LOG ────────────────────────────────────────────────────────
print("\n=== TEST 13: EXECUTION LOG — ENTRIES & SUMMARY ===")
log_tm = ToolManager()
log_tm.register(FileReaderTool())
log_tm.register(DirectoryListerTool())

# Execute a few tools
log_tm.execute("file_reader", path="company_memory.md")
log_tm.execute("file_reader", path="does_not_exist.md")  # failure
log_tm.execute("directory_lister", path=".", pattern="*.md")

log = log_tm.get_log()
assert len(log) == 3, f"Expected 3 log entries, got {len(log)}"
assert log[0].success is True
assert log[1].success is False
assert log[2].success is True

# All entries have timing data
for entry in log:
    assert entry.execution_time_ms >= 0, "Execution time must be non-negative"
    assert entry.tool_name in ("file_reader", "directory_lister")

# log_summary() should return meaningful text
summary = log_tm.log_summary()
assert "Tool Execution Log" in summary
assert "file_reader" in summary
print(f"✓ Execution log has {len(log)} entries. All have timing. log_summary() verified.")

# ── 14. UNKNOWN TOOL NAME — GRACEFUL FAILURE ────────────────────────────────
print("\n=== TEST 14: UNKNOWN TOOL NAME — GRACEFUL FAILURE ===")
unknown_result = DEFAULT_TOOL_MANAGER.execute("nonexistent_tool", arg="value")
assert unknown_result.success is False
assert "not registered" in unknown_result.error.lower()
assert unknown_result.output is None
print(f"✓ Unknown tool returns ToolResult(success=False). Error: {unknown_result.error[:60]}…")

# ── 15. DEFAULT_TOOL_MANAGER HAS ALL 5 TOOLS ────────────────────────────────
print("\n=== TEST 15: DEFAULT_TOOL_MANAGER — ALL 5 BUILT-IN TOOLS ===")
registered = DEFAULT_TOOL_MANAGER.list_tools()
expected_tools = {"file_reader", "file_writer", "directory_lister", "web_search", "report_exporter"}
assert expected_tools.issubset(set(registered)), \
    f"Missing tools. Expected: {expected_tools}. Got: {registered}"
summary_text = DEFAULT_TOOL_MANAGER.tool_summary()
assert "Registered Tools (5 total)" in summary_text
print(f"✓ DEFAULT_TOOL_MANAGER has all 5 built-in tools: {sorted(registered)}")

# ── 16. TOOL_MANAGER INSTANCE IN GENESIS.PY ─────────────────────────────────
print("\n=== TEST 16: TOOL_MANAGER INSTANCE IN GENESIS.PY ===")
assert isinstance(TOOL_MANAGER, ToolManager), "TOOL_MANAGER is not a ToolManager instance"
# Must share the same DEFAULT_TOOL_MANAGER
assert TOOL_MANAGER is DEFAULT_TOOL_MANAGER, \
    "TOOL_MANAGER in genesis.py should be the same object as DEFAULT_TOOL_MANAGER"
print("✓ TOOL_MANAGER instance verified in genesis.py (same as DEFAULT_TOOL_MANAGER).")

# ── 17. SHOW_TOOLS / SHOULD_SHOW_TOOLS ROUTING ──────────────────────────────
print("\n=== TEST 17: SHOW_TOOLS / SHOULD_SHOW_TOOLS ROUTING ===")
assert should_show_tools("show tools")
assert should_show_tools("list tools")
assert should_show_tools("available tools")
assert should_show_tools("what tools do we have?")
assert should_show_tools("show tool registry")
assert not should_show_tools("show memory")
assert not should_show_tools("research the market")

tools_output = show_tools()
assert "Registered Tools" in tools_output
assert "file_reader" in tools_output
assert "file_writer" in tools_output
print("✓ should_show_tools routing verified. show_tools() returns complete registry listing.")

# ── 18. BACKWARD COMPATIBILITY ───────────────────────────────────────────────
print("\n=== TEST 18: BACKWARD COMPATIBILITY — ALL KEYWORD ROUTES ===")
from genesis import (
    should_show_memory, should_show_reports,
    should_show_proposals, should_approve_proposals,
    should_run_research, should_run_acquisition,
    should_run_marketing, should_run_finance,
    should_run_orchestration, should_show_tools,
)
assert should_show_memory("show company memory")
assert should_show_reports("show reports")
assert should_show_proposals("show proposals")
assert should_approve_proposals("approve all proposals")
assert should_run_research("research market for SaaS tools")
assert should_run_acquisition("find leads for B2B agencies")
assert should_run_marketing("marketing strategy for product")
assert should_run_finance("financial analysis for SaaS")
assert should_run_orchestration("run all workers for goal")
assert should_show_tools("show tools")
print("✓ All 10 existing + 1 new keyword routing helpers verified — zero regressions.")

# ── 19. CUSTOM TOOL REGISTRATION BY WORKER ──────────────────────────────────
print("\n=== TEST 19: CUSTOM TOOL REGISTRATION BY WORKER ===")
class PdfExporterTool(Tool):
    """Example of a worker registering its own domain-specific tool."""
    name = "pdf_exporter"
    description = "Export a report to PDF format (placeholder)."
    def execute(self, **kwargs):
        return {"status": "placeholder", "format": "pdf"}

# Workers should be able to create their own ToolManager or register with DEFAULT
custom_tm = ToolManager()
custom_tm.register(PdfExporterTool())
assert "pdf_exporter" in custom_tm.list_tools()

result_custom = custom_tm.execute("pdf_exporter", content="test content")
assert result_custom.success is True
assert result_custom.output["format"] == "pdf"
print("✓ Custom tool registration by worker pattern verified.")

# ── 20. SYNTAX COMPILATION ───────────────────────────────────────────────────
print("\n=== TEST 20: SYNTAX COMPILATION — ALL PROJECT FILES ===")
import subprocess
all_files = [
    "genesis.py",
    "core/__init__.py",
    "core/tool_manager.py",
    "core/task_planner.py",
    "core/memory_governor.py",
    "core/memory_interface.py",
    "core/orchestrator.py",
    "core/base_worker.py",
    "core/logger.py",
    "core/worker_identity.py",
    "core/worker_report.py",
    "workers/research_worker.py",
    "workers/acquisition_worker.py",
    "workers/marketing_worker.py",
    "workers/finance_worker.py",
    "workers/__init__.py",
    "research_worker.py",
    "acquisition_worker.py",
    "marketing_worker.py",
    "finance_worker.py",
    "test_phase10_tool_manager.py",
]
proc = subprocess.run(
    [sys.executable, "-m", "py_compile"] + all_files,
    capture_output=True, text=True,
)
if proc.returncode != 0:
    print(f"✗ Syntax errors:\n{proc.stderr}")
    sys.exit(1)
print(f"✓ Syntax clean — {len(all_files)} files, 0 errors.")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("ALL PHASE 10 VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
