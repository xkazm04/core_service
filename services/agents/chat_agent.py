import os
import json
from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from uuid import UUID, uuid4
import logging

from fastapi import FastAPI, Depends
from pydantic import BaseModel # Keep this for internal models if needed
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import StateSnapshot
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel # Use for LLM schema binding
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

# Import tool schemas and executor
from services.agents.db_lookup import (
    execute_db_tool,
    CharacterLookupArgs,
    StoryLookupArgs,
    BeatLookupArgs
)
from database import get_db
# Import suggestion loader and response models (adjust path if needed)
from services.suggestion_loader import load_suggestions_by_topic
from routes.agent import Suggestion, ChatResponse # Import from agent route file

logger = logging.getLogger(__name__)

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    project_id: Optional[UUID]
    character_id: Optional[UUID]
    request_type: Optional[str] # Add request_type to state
    # Store the final structured response
    final_response: Optional[ChatResponse]

# --- LLM and Tool Binding ---
# Use a model that supports JSON mode well (like newer GPT-4o/GPT-4 Turbo)
llm = ChatOpenAI(model="gpt-4o") # Or gpt-4-turbo
llm_with_tools = llm.bind_tools(
    [CharacterLookupArgs, StoryLookupArgs, BeatLookupArgs],
    tool_choice="auto"
)
# --- NEW: LLM for Structured JSON Output ---
# Bind the ChatResponse schema to the LLM for the final output generation
structured_llm = llm.with_structured_output(ChatResponse)

# --- Graph Nodes ---

def call_model_for_tool_or_direct(state: AgentState):
    """
    Invokes the LLM. If tools were just used, it processes results.
    Otherwise, it responds directly or calls tools.
    It does NOT generate the final structured response yet.
    """
    messages = state['messages']
    # Check if the last message is a ToolMessage, indicating we need to process tool results
    if isinstance(messages[-1], ToolMessage):
        logger.info("--- Calling LLM to process tool results ---")
        # Just use the regular LLM, might call more tools or generate intermediate response
        response = llm_with_tools.invoke(messages)
    else:
        logger.info("--- Calling LLM for initial response or tool call ---")
        # Use the LLM with tool binding
        response = llm_with_tools.invoke(messages)

    logger.info(f"LLM intermediate response/tool call: {response}")
    return {"messages": [response]}

def tool_node_executor(state: AgentState, config: RunnableConfig):
    """Executes DB tools based on the last AI message."""
    # ... (tool_node_executor remains the same) ...
    logger.info("--- Executing Tool Node ---")
    db_session = config['configurable'].get('db_session')
    if not db_session:
        logger.error("DB Session not found in config for tool node execution!")
        last_message = state['messages'][-1]
        tool_call_id = last_message.tool_calls[0]['id'] if isinstance(last_message, AIMessage) and last_message.tool_calls else "error_no_tool_call_id"
        return {"messages": [ToolMessage(content="Error: Database connection not available.", tool_call_id=tool_call_id)]}
    tool_result = execute_db_tool(state, db_session)
    logger.info(f"Tool Execution Result: {tool_result}")
    return tool_result


# --- NEW: Node to Generate Final Structured Response ---
def generate_final_response(state: AgentState):
    """
    Calls the LLM bound with the ChatResponse schema to generate the final
    structured output including the text response and relevant suggestions.
    """
    logger.info("--- Generating Final Structured Response ---")
    messages = state['messages']
    request_type = state.get('request_type', 'general') # Get topic from state

    # Load potential suggestions for the current topic
    potential_suggestions = load_suggestions_by_topic(request_type)
    suggestions_prompt_part = ""
    if potential_suggestions:
        suggestions_list_str = json.dumps(potential_suggestions, indent=2)
        suggestions_prompt_part = (
            f"\n\nConsider the following potential suggestions for the user (topic: {request_type}). "
            f"Evaluate if any are relevant based on their 'initiator' condition and the current conversation context. "
            f"Include relevant ones in the 'suggestions' list in your JSON output. Only include suggestions if their initiator condition is met by the current context.\n"
            f"Potential Suggestions:\n{suggestions_list_str}"
        )
    else:
        suggestions_prompt_part = "\n\nNo specific suggestions available for this topic."

    # Construct a prompt for the structured LLM
    prompt_messages = messages + [
        SystemMessage(
            content=(
                f"Based on the entire conversation history and the context provided (including any tool results), generate a helpful and informative text response. "
                f"{suggestions_prompt_part}\n"
                f"Format your entire output as a JSON object matching the 'ChatResponse' schema, containing a 'response' string and a 'suggestions' list (which may be empty)."
            )
        )
    ]

    # Invoke the LLM configured for structured output
    try:
        structured_response = structured_llm.invoke(prompt_messages)
        logger.info(f"Structured LLM Response: {structured_response}")
        # Validate if it matches the Pydantic model (structured_llm should handle this)
        if isinstance(structured_response, ChatResponse):
             return {"final_response": structured_response}
        else:
             logger.error(f"Structured LLM output did not match ChatResponse schema: {structured_response}")
             # Fallback response
             fallback_resp = ChatResponse(response="Sorry, I encountered an issue generating the final response format.", suggestions=[])
             return {"final_response": fallback_resp}
    except Exception as e:
        logger.error(f"Error invoking structured LLM: {e}", exc_info=True)
        fallback_resp = ChatResponse(response=f"Sorry, an error occurred while generating the response: {e}", suggestions=[])
        return {"final_response": fallback_resp}


# --- Graph Logic (Edges) ---
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
                CharacterLookupArgs.__name__,
                StoryLookupArgs.__name__,
                BeatLookupArgs.__name__
            }
            if tool_name in known_tool_schemas:
                logger.info(f"--- Decision: Call Tool ('{tool_name}') ---")
                return "call_tool"
            else:
                logger.warning(f"LLM requested unknown tool: '{tool_name}'. Finalizing.")
                return "finalize" # Unknown tool, go to final response generation
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


# --- Build the Langgraph Graph ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent_tool_or_direct", call_model_for_tool_or_direct)
workflow.add_node("call_tool", tool_node_executor)
workflow.add_node("final_responder", generate_final_response) # New final node

# Define entry point
workflow.set_entry_point("agent_tool_or_direct")

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
# compiled_graph defined in agent.py

# --- Main Execution (Placeholder) ---
if __name__ == "__main__":
    print("Agent definition loaded. Run via FastAPI application (e.g., agent.py).")
