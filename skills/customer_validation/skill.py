"""
skills/customer_validation/skill.py

Customer Validation Skill
Category: Customer Discovery

Pipeline: Research → Acquisition

This skill identifies the target market and immediately builds the lead
database and outreach strategy.  It validates whether real customers exist
for a product idea before deeper investment.

Workers are executed exclusively through WorkerOrchestrator.
"""

from core.skill_manager import Skill, SkillResult


class CustomerValidationSkill(Skill):
    """
    Customer validation skill.

    Runs Research → Acquisition to identify whether a viable customer
    segment exists for the stated product idea.
    """

    name = "customer_validation"
    version = "1.0.0"
    description = "Validate a product idea with target customers: Research → Acquisition."
    category = "Customer Discovery"
    required_workers = ["research", "acquisition"]
    required_tools = []

    def execute(self, goal, worker_registry, orchestrator, tool_manager=None):
        pipeline = ["research", "acquisition"]

        missing = [w for w in pipeline if w not in worker_registry]
        if missing:
            return SkillResult(
                skill_name=self.name,
                success=False,
                output=None,
                error=f"Missing required workers: {missing}",
                workers_used=[],
            )

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
