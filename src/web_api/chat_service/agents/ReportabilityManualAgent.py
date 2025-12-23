from typing import Type

from .KnowledgeAgent import KnowledgeAgentBase
from functions import ReportabilityManualPlugin
from models import ReportabilityContext, ReportabilityManual
from state import StateBase
from prompts.AgentsPrompt import AgentsPrompt


class ReportabilityManualAgent(KnowledgeAgentBase):
    """Agent for interacting with the Reportability Manual."""
    def __init__(self, state: StateBase[ReportabilityContext]) -> None:
        """Initializes the agent with a state object.

        Args:
            state (StateBase[ReportabilityContext]): The state for agent operations.
        """
        super().__init__(
            display_name="Reportability Manual Knowledge Agent",
            trace_name="ReportabilityManualKnowledgeAgent",
            state=state,
            plugin_defs=[(ReportabilityManualPlugin(state.get_state()), "ReportabilityManualPlugin")]
        )

    def get_knowledge_specific_instructions(self) -> str:
        return AgentsPrompt.ReportabilityManualAgentPrompt

    def get_reviewed_doc_model(self) -> Type:
        """Returns the class type for reviewed documents."""
        return ReportabilityManual
