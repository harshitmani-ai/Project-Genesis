"""
skills/google_review_product/skill.py

Google Review Product Skill
Category: Product Evaluation

Pipeline: Research → Acquisition → Marketing → Finance

This skill runs the complete four-worker pipeline to evaluate a new product
opportunity end-to-end.  It is an architecture demonstration — it contains
no product-specific business logic.

Workers are executed exclusively through WorkerOrchestrator.
"""

from core.skill_manager import Skill, SkillResult


class GoogleReviewProductSkill(Skill):
    """
    Full product evaluation skill.

    Runs Research → Acquisition → Marketing → Finance through the
    WorkerOrchestrator and wraps the FinalCompanyReport in a SkillResult.
    """

    name = "google_review_product"
    version = "1.0.0"
    description = "Full product evaluation pipeline: Research → Acquisition → Marketing → Finance."
    category = "Product Evaluation"
    required_workers = ["research", "acquisition", "marketing", "finance"]
    required_tools = []

    def execute(self, goal, worker_registry, orchestrator, tool_manager=None):
        pipeline = ["research", "acquisition", "marketing", "finance"]

        # Validate required workers are present
        missing = [w for w in pipeline if w not in worker_registry]
        if missing:
            return SkillResult(
                skill_name=self.name,
                success=False,
                output=None,
                error=f"Missing required workers: {missing}",
                workers_used=[],
            )

        # Execute through the Worker Framework (orchestrator) — never bypass
        final_report = orchestrator.run(goal, pipeline)

        return SkillResult(
            skill_name=self.name,
            success=final_report.success_count > 0,
            output=final_report,
            error=None if final_report.success_count > 0 else "All workers failed",
            workers_used=list(final_report.workers_executed),
            metadata={
                "success_count": final_report.success_count,
                "failure_count": final_report.failure_count,
            },
        )
