# 🚀 Master Migration Plan: Project Genesis Worker Framework

**Author:** Lead Software Engineer  
**Target Architecture:** Modular Hub-and-Spoke AI Worker Framework (`BaseWorker`)  
**Status:** Planning Phase — **No Production Code Written**  

---

## 1. Current Architecture

### Overview
Project Genesis currently operates as a collection of loosely coupled Python scripts that execute via CLI loops or standalone scripts. Intelligence is powered by `brain.py` (Gemini SDK wrapper), while memory is loaded into prompts via `memory.py`.

### Component Responsibility Matrix

| Component | Current Responsibility | Alignment with Worker Framework |
| :--- | :--- | :--- |
| `genesis.py` | Main CLI loop, keyword matching, intent routing. | **High Alignment** — Serves as the initial prototype of the Central Orchestrator. |
| `brain.py` | LLM Client wrapper, fallback models, exponential backoff retries. | **High Alignment** — Serves as the core LLM Gateway middleware. |
| `memory.py` | Loads `constitution.md` & `company_memory.md` strings for prompt injection. | **Medium Alignment** — Needs wrapping in a formal memory interface with staging support. |
| `company_manager.py` | CLI viewer for static memory files in `company_memory/`. | **Medium Alignment** — Remains a standalone memory management viewer. |
| `research_worker.py` | Generates product hypotheses, saves markdown reports, appends to `company_memory.md`. | **High Alignment** — Already follows the standard `Generate -> Save -> Update Memory` flow. |
| `product_evaluator.py` | Evaluates research hypotheses against 6 scoring factors (100pt max). | **High Alignment** — Prototype of `ProductEvaluatorWorker`. |
| `market_intelligence.py` | Collects objective market evidence without making business decisions. | **High Alignment** — Prototype of `MarketIntelligenceWorker`. |
| `assistant_ai.py` | Code self-editing assistant with syntax validation and rollback. | **High Alignment** — Prototype of `DeveloperWorker`. |
| `file_editor.py` | Atomic file updates with timestamped backups in `backups/`. | **Infrastructure** — Shared core utility for file editing safety. |

---

## 2. Target Architecture

The target architecture enforces a strict **Hub-and-Spoke model** where all worker modules subclass `BaseWorker` and communicate solely through **Genesis**:

```
                       ┌────────────────────────┐
                       │    Harshit (Founder)   │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │  Genesis Orchestrator  │ (Central Router)
                       └───────────┬────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Worker Framework │      │ Worker Framework │      │ Worker Framework │
│  ResearchWorker  │      │ AcquisitionWorker│      │  MarketingWorker │
└──────────────────┘      └──────────────────┘      └──────────────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │ Core Memory Staging Area  │
                     │ (company_memory/proposals)│
                     └───────────────────────────┘
```

---

## 3. Safest Implementation Order (Phased Roadmap)

To guarantee zero downtime and preserve system stability, migration is broken into **4 distinct, risk-isolated phases**.

```
┌─────────────────────────┐
│ PHASE 1: CORE INFRA     │ Create core/ package (BaseWorker, Logger, MemoryInterface)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ PHASE 2: WORKER ADAPT   │ Migrate ResearchWorker to BaseWorker (Side-by-side)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ PHASE 3: ORCHESTRATOR   │ Update genesis.py to route via Worker Framework
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ PHASE 4: REMAINING      │ Migrate Product Evaluator, Market Intel & Assistant AI
└─────────────────────────┘
```

---

### Phase 1: Core Framework Infrastructure Setup

* **Objective:** Introduce the `core/` package without touching existing executable entry points.
* **New Files:**
  * `core/__init__.py`
  * `core/worker_identity.py`
  * `core/worker_report.py`
  * `core/memory_interface.py`
  * `core/logger.py`
  * `core/base_worker.py`
* **Affected Files:** None.
* **Unchanged Files:** All existing project files (`genesis.py`, `research_worker.py`, `brain.py`, etc.).
* **Risk Level:** 🟢 **LOW** (Zero impact on existing codebase).
* **Rollback Strategy:** Delete the `core/` directory.

---

### Phase 2: Research Worker Migration (Side-by-Side Validation)

* **Objective:** Refactor `research_worker.py` to subclass `BaseWorker` while maintaining backwards compatibility for existing direct script calls.
* **New Files:** `workers/__init__.py`, `workers/research_worker.py` (New subclassed version).
* **Affected Files:** `research_worker.py` (Acts as a backward-compatible proxy forwarding requests to `workers/research_worker.py`).
* **Unchanged Files:** `genesis.py`, `brain.py`, `company_manager.py`.
* **Risk Level:** 🟡 **MEDIUM** (Modifies research execution path).
* **Rollback Strategy:** Revert `research_worker.py` from git backup.

---

### Phase 3: Genesis Orchestrator Integration

* **Objective:** Update `genesis.py` to dispatch tasks to workers via the new `BaseWorker` interface.
* **New Files:** None.
* **Affected Files:** `genesis.py`.
* **Unchanged Files:** `core/*`, `workers/*`, `brain.py`.
* **Risk Level:** 🟡 **MEDIUM** (Modifies CLI routing logic).
* **Rollback Strategy:** Restore `genesis.py` from timestamped backup created in `backups/`.

---

### Phase 4: Remaining Workers & Cleanup

* **Objective:** Migrate `product_evaluator.py`, `market_intelligence.py`, and `assistant_ai.py` to the `workers/` directory.
* **New Files:**
  * `workers/product_evaluator_worker.py`
  * `workers/market_intelligence_worker.py`
  * `workers/assistant_worker.py`
* **Affected Files:** Wrapper scripts in root directory.
* **Unchanged Files:** Core framework (`core/*`).
* **Risk Level:** 🟢 **LOW** (Isolated worker-by-worker conversion).
* **Rollback Strategy:** Revert individual worker files.

---

## 4. `BaseWorker` Implementation Plan

To introduce `BaseWorker` without breaking existing workflows:

1. **Non-Breaking Addition:** `BaseWorker` is created inside `core/base_worker.py`. Existing scripts do not import it until they are explicitly ready to migrate.
2. **Template Method Pattern:** The main entry point `run_lifecycle(task)` executes the standard 5-step flow:
   $$\text{Goal} \rightarrow \text{Plan} \rightarrow \text{Execute} \rightarrow \text{Verify} \rightarrow \text{Learn}$$
3. **Backwards Compatible Data Structures:** The output `WorkerReport` exposes helper methods to extract raw text outputs matching existing worker return signatures.

---

## 5. Research Worker Migration Strategy

When migrating `research_worker.py`:
1. **Preserve Prompts & Formatting:** The exact prompt text, hypothesis scoring factors (1-10), Markdown output format, and notice disclaimers will remain 100% identical.
2. **Class Encapsulation:**
   * `create_plan()`: Builds the structured hypothesis strategy.
   * `execute()`: Invokes LLM reasoning via `brain.py`.
   * `verify()`: Confirms output contains expected sections (`Product name`, `Customer problem`, `Main risk`).
   * `learn()`: Generates memory update proposals.
3. **Legacy Entry Point Preserved:** `research_worker.py` in the root folder will expose the legacy `run_research_assignment(audience)` function, delegating under the hood to `workers.research_worker.ResearchWorker().run_lifecycle(...)`.

---

## 6. Genesis Orchestrator Changes

`genesis.py` will undergo minimal, clean modifications:

1. **Worker Registry:** Introduces a worker lookup dictionary:
   ```python
   WORKER_REGISTRY = {
       "research": ResearchWorker(),
       "evaluation": ProductEvaluatorWorker(),
       "market": MarketIntelligenceWorker(),
   }
   ```
2. **Natural Command Dispatcher:** When `should_run_research(command)` triggers, `genesis.py` passes the request to `WORKER_REGISTRY["research"].run_lifecycle(TaskRequest(...))`.
3. **Standardized Status Output:** Replaces custom status print statements with unified `WorkerReport` status output.

---

## 7. Company Memory Integration & Governance

Memory functionality will continue working seamlessly during and after migration:

1. **Read Path (Unchanged):** Workers use `CompanyMemoryInterface.read_context()` which calls `memory.load_company_context()` to load `constitution.md` and `company_memory.md`.
2. **Write Path (Staging Area):** Workers submit proposed additions via `CompanyMemoryInterface.propose_update()`. Proposals are saved as `.md` files in `company_memory/proposals/`.
3. **Commit Mechanism:** `Genesis` logs candidate memory proposals and appends them to `company_memory.md` upon verification.

---

## 8. Validation Plan

### Phase 1 Validation (Core Framework)
- **Test:** Run `python -m py_compile core/*.py`.
- **Expected Result:** Zero syntax or import errors.
- **Success Criteria:** `core` package imports successfully in isolation.

### Phase 2 Validation (Research Worker Migration)
- **Test 1:** Execute `python -c "from workers.research_worker import ResearchWorker; w = ResearchWorker(); print(w.identity.name)"`.
- **Test 2:** Execute legacy entry point `run_research_assignment("small business")`.
- **Expected Result:** Generates valid research report in `research_reports/` and returns identical `(result, report_path)` tuple.
- **Success Criteria:** Zero regression in research report quality or output format.

### Phase 3 Validation (Genesis Orchestrator)
- **Test 1:** Run multi-line command `research HR tools for small business\nEND` through `genesis.py`.
- **Test 2:** Run command `exit` to ensure session closes cleanly.
- **Expected Result:** Genesis routes task through `BaseWorker` lifecycle, prints status, and exits cleanly.
- **Success Criteria:** Multi-line CLI input, routing, and error reporting function perfectly.

---

## 9. Rollback Plan

If any phase fails:

1. **File Editor Backups:** Every modified file is automatically backed up to `backups/<filename>_<timestamp>.backup`.
2. **Step-by-Step Recovery:**
   * **To Roll Back Phase 3:** Copy latest `genesis.py.backup` over `genesis.py`.
   * **To Roll Back Phase 2:** Copy latest `research_worker.py.backup` over `research_worker.py` and delete `workers/`.
   * **To Roll Back Phase 1:** Delete `core/` folder.
3. **Data Protection:** Existing `company_memory.md`, `constitution.md`, and generated reports in `research_reports/` are never deleted or modified during rollbacks.

---

## 10. Final Readiness Review

### Is Project Genesis Ready for Migration?
**YES.** The current codebase is modular, clean, and fully verified. The explicit separation of `research_worker.py` from `company_manager.py` achieved in previous iterations makes it 100% ready for Phase 1.

### What Remaining Architectural Risks Exist?
1. **API Rate Limiting:** High multi-step worker tasks could hit Gemini rate limits if retries are not configured properly in `brain.py`.
2. **Memory Proposal Bloat:** Unfiltered memory proposals in `company_memory/proposals/` could accumulate if not periodically committed or pruned by Genesis.

### What Should Be Completed Before Writing Production Code?
1. Founder approval of this `migration_plan.md`.
2. Creation of unit test stubs for `BaseWorker` lifecycle verification.

---

## Deliverables Summary

- [x] Complete migration roadmap (Phases 1–4)
- [x] File-by-file migration plan (Section 3)
- [x] Risk assessment (Low/Medium/High per phase)
- [x] Validation checklist (Section 8)
- [x] Rollback checklist (Section 9)
