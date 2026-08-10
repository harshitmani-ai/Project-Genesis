# Changelog

All notable changes to Project Genesis will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-10

### Major Release — Genesis V1 Complete Autonomous AI Company Platform

#### Added
- **Phase 1-4: Core Architecture & Worker Framework**
  - Modular AI Workers (`ResearchWorker`, `AcquisitionWorker`, `MarketingWorker`, `FinanceWorker`).
  - Standardized JSON/Markdown report output schemas with empirical verifiers.
  - Multi-worker Orchestration Pipeline (`Orchestrator`) for end-to-end business execution.
- **Phase 5-8: Memory & Governance Engine**
  - `MemoryGovernor` (`ProposalManager`) — sole authority for committing memory proposals to `company_memory.md`.
  - Immutable audit trail (`company_memory/audit_log.md`) with duplicate prevention.
  - Zero-LLM local proposal resolution (`review proposal <n>`, `approve proposal <n>`, `reject proposal <n>`).
- **Phase 9: Intelligent Task Planner**
  - Natural language task decomposition and multi-worker pipeline planning.
- **Phase 10: Tool Manager & Safe File Access**
  - Tool Registry (`ToolManager`) with built-in tools (`file_reader`, `file_writer`, `directory_lister`, `web_search`, `report_exporter`).
  - Path safety enforcement preventing out-of-root writes and source code modification.
- **Phase 11: Skill Registry & Extensibility**
  - `SkillManager` and auto-discovered skills (`business_evaluation`, `customer_validation`, `google_review_product`).
- **Phase 12: Task Queue & Dependency Engine**
  - Asynchronous task queue (`TaskQueue`) with priority clamping, dependency resolution, auto-incrementing task IDs, and persistence.
- **Phase 13: Executive Company Dashboard**
  - Daily brief (`company status`) and weekly executive summary metrics.
- **Phase 14: Autonomous Auto-Pilot Engine**
  - `AutoPilotEngine` (`run_autopilot_mode`) — autonomous queue execution, dependency progression, memory updates, and max-step limit enforcement.
- **Project Genesis V2: Connector Framework & Proposals Dashboard**
  - `ConnectorManager` supporting modular external connectors (`antigravity`, `chatgpt`) with automatic retries and persistence.
  - **Proposal Review Dashboard (`review all proposals`):** 100% local, zero-LLM proposal matrix, dynamic active product relevance scoring, duplicate detection, archived product categorization, and batch actions (`approve selected`, `reject selected`).
  - Single-line CLI immediate execution mode in `genesis.py` preventing multiline input stalling.

#### Fixed
- Fixed Research Worker verification schema mismatch during Task Queue execution.
- Fixed single-line interactive CLI routing to guarantee 0 Gemini API calls on local proposal commands.

#### Tested & Verified
- Complete 9-suite regression test suite passing 100% with zero regressions.
- End-to-end interactive subprocess terminal integration tests passing 100%.
