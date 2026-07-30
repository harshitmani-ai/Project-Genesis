"""
workers/__init__.py

The workers/ package contains fully-migrated Project Genesis workers
that subclass BaseWorker and participate in the hub-and-spoke lifecycle.

Phase 2 adds:
  workers.research_worker  →  ResearchWorker

Future phases will add:
  workers.product_evaluator_worker
  workers.market_intelligence_worker
  workers.assistant_worker
"""

from workers.research_worker import ResearchWorker

__all__ = ["ResearchWorker"]
