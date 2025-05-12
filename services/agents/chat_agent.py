"""
Main chat agent implementation using langgraph
"""
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from services.agents.pre_processors.intent_detection import extract_operation_intent
from services.agents.chat.agent_state import AgentState
from services.agents.chat.graph_nodes import (
    tool_node_executor, # Keep
    generate_final_response # Keep
)
# Import new subgraph nodes
from services.agents.chat.subgraph_nodes.confirmation_handler import handle_confirmation
from services.agents.chat.subgraph_nodes.parameter_collector import collect_parameters
from services.agents.chat.subgraph_nodes.intent_processor import process_intent
from services.agents.chat.subgraph_nodes.general_llm_caller import call_general_llm
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

memory = MemorySaver()
workflow = StateGraph(AgentState)

# --- Add Nodes ---
workflow.add_node("extract_operations", extract_operation_intent)
workflow.add_node("handle_confirmation_node", handle_confirmation)
workflow.add_node("collect_parameters_node", collect_parameters)
workflow.add_node("process_intent_node", process_intent)
workflow.add_node("call_general_llm_node", call_general_llm)
workflow.add_node("call_tool_node", tool_node_executor) # Renamed for clarity if needed, but "call_tool" is fine
workflow.add_node("final_responder_node", generate_final_response)

# --- Define Entry Point ---
workflow.set_entry_point("extract_operations")

# --- Define Routing Logic ---

def route_initial_request(state: AgentState):
    logger.debug(f"Routing initial request. Awaiting_confirmation: {state.get('awaiting_confirmation')}, Intent: {state.get('operation_intent')}, Missing_params: {state.get('missing_params')}")
    if state.get('awaiting_confirmation') and state.get('pending_operation_details'):
        return "handle_confirmation_node"
    if state.get('operation_intent'):
        if state.get('missing_params'):
            return "collect_parameters_node"
        else: # Intent present, no missing params
            return "process_intent_node"
    return "call_general_llm_node" # Default if no intent or confirmation

def route_after_subgraph_processing(state: AgentState):
    """
    Routes after confirmation_handler, intent_processor, or general_llm_caller.
    Decides if a tool call is next, or if we should finalize the response.
    """
    messages = state['messages']
    last_message = messages[-1] if messages else None
    logger.debug(f"Routing after subgraph. Last message: {type(last_message)}")

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        logger.debug("Routing to call_tool_node.")
        return "call_tool_node"
    else:
        # This includes cases where:
        # - confirmation_handler asked for clarification or cancelled (AIMessage, no tool_calls)
        # - intent_processor asked for confirmation (AIMessage, no tool_calls)
        # - general_llm_caller produced a direct textual response (AIMessage, no tool_calls)
        logger.debug("Routing to final_responder_node.")
        return "final_responder_node"

# --- Add Edges ---
workflow.add_conditional_edges(
    "extract_operations",
    route_initial_request,
    {
        "handle_confirmation_node": "handle_confirmation_node",
        "collect_parameters_node": "collect_parameters_node",
        "process_intent_node": "process_intent_node",
        "call_general_llm_node": "call_general_llm_node"
    }
)

# Parameter collector always asks a question, so it goes to final_responder
workflow.add_edge("collect_parameters_node", "final_responder_node")

# After confirmation handling, intent processing, or general LLM call, decide to call tool or finalize
workflow.add_conditional_edges(
    "handle_confirmation_node",
    route_after_subgraph_processing,
    {"call_tool_node": "call_tool_node", "final_responder_node": "final_responder_node"}
)
workflow.add_conditional_edges(
    "process_intent_node",
    route_after_subgraph_processing,
    {"call_tool_node": "call_tool_node", "final_responder_node": "final_responder_node"}
)
workflow.add_conditional_edges(
    "call_general_llm_node",
    route_after_subgraph_processing,
    {"call_tool_node": "call_tool_node", "final_responder_node": "final_responder_node"}
)

# After tool execution, results are processed by the general LLM caller
workflow.add_edge("call_tool_node", "call_general_llm_node")

# Final responder is an end node
workflow.add_edge("final_responder_node", END)

# --- Compile the Graph ---
compiled_graph = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    print("Agent definition loaded with new subgraph structure. Run via FastAPI application.")