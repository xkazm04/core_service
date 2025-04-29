"""
Main chat agent implementation using langgraph
"""
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from services.agents.pre_processors.name_extraction import extract_character_name
from services.agents.chat.agent_state import AgentState
from services.agents.chat.graph_nodes import (
    call_model_for_tool_or_direct,
    tool_node_executor,
    generate_final_response
)
from services.agents.chat.graph_logic import should_continue_or_finalize

logger = logging.getLogger(__name__)

# --- Build the Langgraph Graph ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("extract_character_names", extract_character_name)
workflow.add_node("agent_tool_or_direct", call_model_for_tool_or_direct)
workflow.add_node("call_tool", tool_node_executor)
workflow.add_node("final_responder", generate_final_response)

# Define entry point - start with character name extraction
workflow.set_entry_point("extract_character_names") 

# Add edge from character extraction to agent
workflow.add_edge("extract_character_names", "agent_tool_or_direct")

# Add conditional edges
workflow.add_conditional_edges(
    "agent_tool_or_direct", # Source node
    should_continue_or_finalize, # Function to decide next step
    {
        "call_tool": "call_tool", # If tool call needed
        "finalize": "final_responder", # If no tool call, generate final response
        "continue_generation": "agent_tool_or_direct" # Should not be returned here, but handle defensively
    }
)

# Add edge from tool execution back to the agent to process results
workflow.add_edge("call_tool", "agent_tool_or_direct")

# The final_responder node is an end node in this path
workflow.add_edge("final_responder", END)

# --- Compile the Graph with Memory ---
memory = MemorySaver()
compiled_graph = workflow.compile(checkpointer=memory)

# --- Main Execution (Placeholder) ---
if __name__ == "__main__":
    print("Agent definition loaded. Run via FastAPI application.")