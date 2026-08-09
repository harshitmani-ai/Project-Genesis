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
from workers.acquisition_worker import AcquisitionWorker
from workers.marketing_worker import MarketingWorker
from workers.finance_worker import FinanceWorker

__all__ = ["ResearchWorker", "AcquisitionWorker", "MarketingWorker", "FinanceWorker"]
