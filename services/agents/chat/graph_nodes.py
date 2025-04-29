"""
Core graph nodes for langgraph-based agent
"""
import logging
from typing import Dict, Any
from langgraph.graph import END
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from schemas.agent import ChatResponse
from .agent_state import AgentState
from .llm_config import llm_with_tools, structured_llm 
from services.agents.executors.suggestion_manager import (
    get_suggestions_for_topic, 
    get_suggestion_prompt, 
    get_fallback_suggestions
)

logger = logging.getLogger(__name__)

def call_model_for_tool_or_direct(state: AgentState) -> Dict[str, Any]:
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

def tool_node_executor(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Executes tools based on the last AI message."""
    logger.info("--- Executing Tool Node ---")
    last_message = state['messages'][-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logger.error("Expected AI message with tool calls, but found none")
        return {"messages": [SystemMessage(content="Error: No tool calls found in the last message.")]}
    
    # Get the configurable components (e.g., database session)
    db_session = config['configurable'].get('db_session')
    if not db_session:
        logger.error("DB Session not found in config for tool node execution!")
        tool_call_id = last_message.tool_calls[0]['id'] if last_message.tool_calls else "error_no_tool_call_id"
        return {"messages": [ToolMessage(content="Error: Database connection not available.", tool_call_id=tool_call_id)]}
    
    # Process each tool call
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_id = tool_call['id']
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        logger.info(f"Processing tool call: {tool_name} (ID: {tool_id})")
        
        try:
            # Dispatch to the appropriate tool handler
            if tool_name in ["CharacterLookupArgs", "StoryLookupArgs", "BeatLookupArgs", "ProjectGapAnalysisArgs"]:
                # Handle database tools
                from services.agents.tools import execute_db_tool
                # We'll execute just this tool and get the result
                single_tool_state = {
                    "messages": [last_message], 
                    "project_id": state.get("project_id"),
                    "character_id": state.get("character_id"),
                    "extracted_character_names": state.get("extracted_character_names", [])
                }
                tool_result = execute_db_tool(single_tool_state, db_session)
                tool_messages.extend(tool_result["messages"])
            
            elif tool_name == "YouTubeSearchArgs":
                from services.agents.tools import execute_youtube_tool
                tool_result = execute_youtube_tool(tool_call, state)
                tool_messages.extend([ToolMessage(content=tool_result, tool_call_id=tool_id)])
            
            else:
                error_msg = f"Unknown tool: {tool_name}"
                logger.error(error_msg)
                tool_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            tool_messages.append(ToolMessage(
                content=f"Error executing tool: {str(e)}",
                tool_call_id=tool_id
            ))
    
    logger.info(f"Returning {len(tool_messages)} tool messages")
    return {"messages": tool_messages}

def generate_final_response(state: AgentState) -> Dict[str, Any]:
    """
    Calls the LLM bound with the ChatResponse schema to generate the final
    structured output including the text response and relevant suggestions.
    """
    logger.info("--- Generating Final Structured Response ---")
    messages = state['messages']
    request_type = state.get('request_type', 'general')
    character_id = state.get('character_id')
    
    # Get context-appropriate suggestions using the suggestion manager
    potential_suggestions = get_suggestions_for_topic(
        topic=request_type,
        entity_id=character_id,
    )
    
    # Generate the suggestion prompt part
    suggestions_prompt_part = get_suggestion_prompt(
        topic=request_type,
        potential_suggestions=potential_suggestions,
        entity_id=character_id
    )

    # Construct a prompt for the structured LLM
    prompt_messages = messages + [
        SystemMessage(
            content=(
                f"Based on the entire conversation history and the context provided (including any tool results), "
                f"generate a helpful and informative text response. "
                f"{suggestions_prompt_part}\n"
                f"Format your entire output as a JSON object matching the 'ChatResponse' schema, "
                f"containing a 'response' string and a 'suggestions' list (which may be empty)."
            )
        )
    ]

    # Invoke the LLM configured for structured output
    try:
        structured_response = structured_llm.invoke(prompt_messages)
        logger.info(f"Structured LLM Response: {structured_response}")
        
        # Return the structured response
        return {"final_response": structured_response}
        
    except Exception as e:
        logger.error(f"Error invoking structured LLM: {e}", exc_info=True)
        fallback_resp = ChatResponse(
            response=f"Sorry, an error occurred while generating the response: {e}",
            suggestions=get_fallback_suggestions(request_type, character_id)
        )
        return {"final_response": fallback_resp}