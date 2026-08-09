"""
skills/business_evaluation/skill.py

Business Evaluation Skill
Category: Business Analysis

Pipeline: Research → Finance

This skill researches the market opportunity and then immediately models
the financial viability — without spending time on acquisition or marketing.
Useful for quick go/no-go decisions before committing further resources.

Workers are executed exclusively through WorkerOrchestrator.
"""

from core.skill_manager import Skill, SkillResult


class BusinessEvaluationSkill(Skill):
    """
    Business evaluation skill.

    Runs Research → Finance to determine whether a business idea is
    worth pursuing from both a market and financial perspective.
    """

    name = "business_evaluation"
    version = "1.0.0"
    description = "Evaluate a business idea's viability and financials: Research → Finance."
    category = "Business Analysis"
    required_workers = ["research", "finance"]
    required_tools = []

    def execute(self, goal, worker_registry, orchestrator, tool_manager=None):
        pipeline = ["research", "finance"]

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
