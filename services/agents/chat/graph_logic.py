"""
Graph logic and edge conditions for the agent workflow
"""
import logging
from langchain_core.messages import AIMessage, ToolMessage

from .agent_state import AgentState

logger = logging.getLogger(__name__)

def should_continue_or_finalize(state: AgentState) -> str:
    """
    Determines the next step: call tool, continue generation, or finalize.
    """
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage):
        if last_message.tool_calls:
            # LLM wants to call a tool
            tool_call = last_message.tool_calls[0]
            tool_name = tool_call['name']
            logger.info(f"LLM requested tool call: '{tool_name}'")
            known_tool_schemas = {
                "CharacterLookupArgs",
                "StoryLookupArgs",
                "BeatLookupArgs",
                "SceneLookupArgs",
                "ProjectGapAnalysisArgs",
                "YouTubeSearchArgs"  
            }
            if tool_name in known_tool_schemas:
                logger.info(f"--- Decision: Call Tool ('{tool_name}') ---")
                return "call_tool"
            else:
                logger.warning(f"LLM requested unknown tool: '{tool_name}'. Finalizing.")
                return "finalize"
        else:
            # LLM generated a text response, potentially intermediate. Let's finalize.
            logger.info("--- Decision: Finalize Response ---")
            return "finalize"
    elif isinstance(last_message, ToolMessage):
        # Just got tool results, continue generation
        logger.info("--- Decision: Continue Generation (after tool) ---")
        return "continue_generation"
    else:
        # Should not happen in normal flow after entry point
        logger.warning("Unexpected message type at decision point. Finalizing.")
        return "finalize"