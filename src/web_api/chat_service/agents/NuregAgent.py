from typing import Type

from .KnowledgeAgent import KnowledgeAgentBase
from functions import NuregPlugin
from models import NUREGSection32, ReportabilityContext
from state import StateBase
from prompts.AgentsPrompt import AgentsPrompt


class NuregAgent(KnowledgeAgentBase):
    """Agent for interacting with the Reportability Manual."""
    def __init__(self, state: StateBase[ReportabilityContext]) -> None:
        """Initializes the agent with a state object.

        Args:
            state (StateBase[ReportabilityContext]): The state for agent operations.
        """
        super().__init__(
            display_name="NUREG 1022 Knowledge Agent",
            trace_name="NuregKnowledgeAgent",
            state=state,
            plugin_defs=[(NuregPlugin(state.get_state()), "NuregPlugin")]
        )

    def get_knowledge_specific_instructions(self) -> str:
        return AgentsPrompt.NuregAgentPrompt

    def get_reviewed_doc_model(self) -> Type:
        """Returns the class type for reviewed documents."""
        return NUREGSection32
