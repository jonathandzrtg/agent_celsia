from typing import TypedDict, Annotated, List, Any
import operator
from langchain_core.messages import AIMessage, HumanMessage # Assuming these imports are needed for AgentState

class AgentState(TypedDict):
    # The list of messages passed between the agent and the tools
    messages: Annotated[List[Any], operator.add]
    # The 'next' field indicates where to route the control flow
    next: str
