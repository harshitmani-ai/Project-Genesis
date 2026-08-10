# Project Genesis (v1.0.0)

**An Autonomous AI Company Engine Built on Google Gemini**

Project Genesis is an autonomous AI company engine designed to think, learn, plan, execute, and evaluate business opportunities independently under human supervision.

---

## 🌟 Genesis V1 Platform Overview

Genesis operates as a self-contained AI organization featuring:

- **Autonomous Auto-Pilot Engine (`core/autopilot.py`):** Runs multi-step product pipelines autonomously, resolves task dependencies, writes verified reports, and updates company memory without manual intervention.
- **Worker Framework (`workers/`):** Specialized AI workers for `research`, `acquisition`, `marketing`, and `finance`.
- **Memory Governance (`core/memory_governor.py`):** Proposal-based memory architecture where workers stage proposals and `ProposalManager` safely merges approved knowledge into `company_memory.md` with audit logging.
- **Proposal Review Dashboard:** 100% local, zero-LLM proposal management dashboard (`review all proposals`) with dynamic product relevance detection, duplicate detection, archived product classification, and batch execution (`approve selected`, `reject selected`).
- **Task Queue & Planner (`core/task_queue.py`, `core/task_planner.py`):** Priority task queue with dependency resolution and natural language goal decomposition.
- **Skill & Tool Registries (`core/skill_manager.py`, `core/tool_manager.py`):** Extensible skill discovery and secure file/system tools.
- **Executive Dashboard (`core/company_dashboard.py`):** Daily briefs, weekly metrics, and company health monitoring (`company status`).
- **Connector Framework (`core/connector_manager.py`):** Modular connector architecture for external agent and LLM integration (`antigravity`, `chatgpt`).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key configured via environment variable `GEMINI_API_KEY` (or Google Antigravity environment)

### Launching Genesis Interactive CLI
```bash
python genesis.py
```

---

## 💻 Essential Commands

| Command | Description |
| :--- | :--- |
| `good morning genesis` / `company status` | Display executive company health dashboard |
| `autopilot` | Launch autonomous Auto-Pilot pipeline execution mode |
| `review all proposals` / `proposal dashboard` | Launch local zero-LLM Proposal Review Dashboard |
| `approve selected 1,2,4,5` | Batch approve and merge specific proposals into memory |
| `reject selected 3,6` | Batch reject specific proposals |
| `review proposal <n>` | Read raw proposal Markdown file locally |
| `build <goal>` | Decompose a high-level goal into an automated task plan |
| `show tasks` / `next task` | View or execute the next task in the queue |
| `show skills` / `show tools` | View registered skills and system tools |
| `show connectors` | View external connectors and status |
| `exit` | Safely close the Genesis CLI session |

---

## 🧪 Testing & Verification

Run the full regression test suite covering all 14 phases and V2 extensions:

```bash
python test_interactive_proposal_integration.py
python test_proposal_review_dashboard.py
python test_local_proposal_manager.py
python test_phase10_tool_manager.py
python test_phase11_skill_manager.py
python test_phase12_task_queue.py
python test_phase13_dashboard.py
python test_phase14_autopilot.py
python test_v2_connector_framework.py
```

---

## 📄 License & System Status

Genesis V1.0.0 is officially released and operating in **Maintenance Mode**.
All core architectural phases (Phases 1–14 + V2 extensions) are complete, fully tested, and verified.