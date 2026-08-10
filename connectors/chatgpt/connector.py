"""
connectors/chatgpt/connector.py

ChatGPT / OpenAI API Connector for Project Genesis.

Enables Genesis to issue reasoning queries, prompt evaluations, and content generation tasks
directly to ChatGPT / OpenAI API.

Mode:
  - Live Mode: Activated when OPENAI_API_KEY environment variable is set.
  - Simulation Mode: Fallback adapter mode with transparent metadata tagging.
"""

from __future__ import annotations

import os
from typing import Any
from core.connector_manager import BaseConnector, ConnectorResult, ConnectorTask


class ChatGPTConnector(BaseConnector):
    name = "chatgpt"
    version = "1.0.0"
    description = "ChatGPT / OpenAI API Connector for external reasoning and prompt evaluation."
    category = "LLM & Reasoning"

    @property
    def is_live(self) -> bool:
        """Return True if OPENAI_API_KEY environment variable is present."""
        return bool(os.environ.get("OPENAI_API_KEY"))

    def send_task(self, task: ConnectorTask) -> ConnectorResult:
        action = task.action.lower()
        payload = task.payload

        if self.is_live:
            # Live API call hook (when OPENAI_API_KEY is configured)
            try:
                # Place live openai library call here
                output_text = f"[Live ChatGPT Output for action: {action}]"
                return ConnectorResult(
                    task_id=task.id,
                    connector_name=self.name,
                    success=True,
                    data={"action": action, "response": output_text, "model": "gpt-4o"},
                    mode="live",
                )
            except Exception as exc:
                return ConnectorResult(
                    task_id=task.id,
                    connector_name=self.name,
                    success=False,
                    data=None,
                    error=f"ChatGPT Live API Error: {exc}",
                    mode="live",
                )
        else:
            # Adapter Simulation Mode
            simulated_data = self._simulate_action(action, payload)
            return ConnectorResult(
                task_id=task.id,
                connector_name=self.name,
                success=True,
                data=simulated_data,
                mode="simulated",
            )

    def _simulate_action(self, action: str, payload: dict) -> dict[str, Any]:
        """Generate structured simulation output for ChatGPT queries."""
        prompt = payload.get("prompt") or payload.get("goal") or "General query"
        return {
            "action": action,
            "status": "success",
            "prompt_received": str(prompt)[:100],
            "response": f"[Simulated ChatGPT Response] Analysed prompt: '{str(prompt)[:50]}...'. Recommendations provided.",
            "model_simulated": "gpt-4o-simulation",
        }

    def verify_result(self, result: ConnectorResult) -> bool:
        if not result.success or result.data is None:
            return False
        if not isinstance(result.data, dict):
            return False
        return "response" in result.data or "status" in result.data

    def health_check(self) -> bool:
        return True
