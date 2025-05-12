"""
Core graph nodes for langgraph-based agent
"""
import logging
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage, BaseMessage # Added BaseMessage
from services.agents.chat.message_utils import ensure_tool_call_integrity
from .agent_state import AgentState
from .llm_config import  structured_llm 
from services.agents.executors.suggestion_manager import (
    get_suggestions_for_topic, 
    get_suggestion_prompt, 
    get_fallback_suggestions
)
from schemas.agent import ChatResponse
import logging
from .message_utils import truncate_problematic_history

logger = logging.getLogger(__name__)


def tool_node_executor(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Executes tools based on the last AI message."""
    logger.info("--- Executing Tool Node ---")
    last_message = state['messages'][-1]
    
    # Initialize be_function and db_updated flag
    be_function = None
    db_updated_by_tool = False # Local flag
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logger.error("Expected AI message with tool calls, but found none")
        return {"messages": [SystemMessage(content="Error: Tool executor called without tool calls in the last AI message.")]}
    # Get the configurable components (e.g., database session)
    db_session = config['configurable'].get('db_session')
    if not db_session:
        logger.error("DB Session not found in config for tool node execution!")
        tool_messages = []
        for tool_call in last_message.tool_calls: # Iterate even in error to provide a response for each
            tool_id = tool_call['id']
            tool_messages.append(ToolMessage(
                content="Error: Database connection not available for tool execution.", 
                tool_call_id=tool_id
            ))
        return {"messages": tool_messages}
    
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_id = tool_call['id']
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        logger.info(f"Processing tool call: {tool_name} (ID: {tool_id}) with args: {tool_args}")
        
        try:
            if tool_name == "ExecutorFunctionArgs":
                function_name = tool_args.get("function_name")
                params = tool_args.get("params", {})
                
                be_function = function_name # Capture the function name for the state
                
                logger.info(f"Agent-initiated execution of '{function_name}' with params: {params}")
                
                from services.agents.executor import execute_suggestion_function # Local import if preferred
                result = execute_suggestion_function(
                    function_name=function_name,
                    db=db_session,
                    project_id=state.get("project_id"),
                    character_id=state.get("character_id"),
                    act_id=state.get("act_id"), # Pass act_id if available in state
                    **params
                )
                result_msg = f"Executed function '{function_name}': {result}"
                # Determine if DB was updated based on function type or result (heuristic)
                # This might need more sophisticated logic based on function names
                if function_name and any(kw in function_name.lower() for kw in ["create", "update", "delete", "add", "remove"]):
                    db_updated_by_tool = True
                logger.info(f"Tool {function_name} executed, result: {result}, db_updated_by_tool: {db_updated_by_tool}")
                
                tool_messages.append(ToolMessage(content=result_msg, tool_call_id=tool_id))

            elif tool_name in ["CharacterLookupArgs", "StoryLookupArgs", "BeatLookupArgs", "SceneLookupArgs", "ProjectGapAnalysisArgs"]:
                from services.agents.tools.db_tool_executor import execute_db_tool
                # execute_db_tool expects a state-like dict and db_session
                # We need to ensure it returns a ToolMessage or content for one.
                # The previous implementation of execute_db_tool seemed to return a dict with 'messages'.
                # Let's adapt to ensure a single ToolMessage is created per call.
                
                # Construct a minimal state for the db_tool_executor if it needs specific fields
                # For now, assuming it can work with tool_args and project/character IDs
                tool_result_content = execute_db_tool(
                    tool_name=tool_name, # Pass tool_name and args
                    tool_args=tool_args,
                    project_id=state.get("project_id"),
                    character_id=state.get("character_id"),
                    act_id=state.get("act_id"),
                    db_session=db_session,
                    # Pass other necessary state parts if db_tool_executor requires them
                    # extracted_character_names=state.get("extracted_character_names", [])
                )
                # Ensure tool_result_content is a string
                if not isinstance(tool_result_content, str):
                    tool_result_content = str(tool_result_content)

                tool_messages.append(ToolMessage(content=tool_result_content, tool_call_id=tool_id))
            
            elif tool_name == "YouTubeSearchArgs": # Assuming this tool exists
                from services.agents.tools import execute_youtube_tool # Ensure this path is correct
                tool_result = execute_youtube_tool(tool_call['args'], state) # Pass args directly
                tool_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))
                
            else:
                error_msg = f"Unknown tool: {tool_name}"
                logger.error(error_msg)
                tool_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            tool_messages.append(ToolMessage(
                content=f"Error executing tool {tool_name}: {str(e)}",
                tool_call_id=tool_id
            ))
    
    # Ensure all tool calls got a response (LangGraph requirement)
    # This loop might be redundant if the above logic correctly appends for each tool_call.
    # However, it's a good safeguard.
    all_called_ids = {tc['id'] for tc in last_message.tool_calls}
    responded_ids = {tm.tool_call_id for tm in tool_messages}
    for tool_id in all_called_ids:
        if tool_id not in responded_ids:
            logger.warning(f"Tool call {tool_id} did not receive a response. Adding fallback.")
            tool_messages.append(ToolMessage(content="Error: Tool call did not produce a response.", tool_call_id=tool_id))

    logger.info(f"Returning {len(tool_messages)} tool messages.")
    
    update_dict = {"messages": tool_messages}
    if be_function: # If any ExecutorFunctionArgs was called
        update_dict["be_function"] = be_function
    if db_updated_by_tool: # If any tool likely updated the DB
        update_dict["db_updated"] = True
    
    # Reset confirmation flags after tool execution attempt, as the next step will be general LLM processing
    update_dict["awaiting_confirmation"] = False
    update_dict["pending_operation_details"] = None
    
    logger.debug(f"Tool node executor returning: {update_dict}")
    return update_dict
def generate_final_response(state: AgentState) -> Dict[str, Any]:
    """
    Calls the LLM bound with the ChatResponse schema to generate the final
    structured output including the text response and relevant suggestions.
    If awaiting_confirmation is true, the main response is taken from the last message.
    """
    logger.info("--- Generating Final Structured Response ---")
    
    clean_messages = ensure_tool_call_integrity(state['messages'])
    clean_messages = truncate_problematic_history(clean_messages)

    is_awaiting_confirmation = state.get('awaiting_confirmation', False)
    pending_op_details = state.get('pending_operation_details')
    response_content = ""
    llm_prompt_messages: list[BaseMessage] = [] # Ensure llm_prompt_messages is typed

    if is_awaiting_confirmation and clean_messages and isinstance(clean_messages[-1], AIMessage):
        # If awaiting confirmation, the last AI message IS the confirmation question.
        response_content = clean_messages[-1].content
        logger.info(f"Awaiting confirmation. Using last AI message as response: '{response_content}'")
        # For suggestions, we can still use the LLM, but the main response is fixed.
        # The prompt for suggestions should reflect that we are asking for confirmation.
        suggestion_context_prompt = (
            f"The user is currently being asked for confirmation: '{response_content}'. "
            f"Based on the operation being confirmed ({pending_op_details.get('operation') if pending_op_details else 'unknown operation'}) "
            "and the overall conversation history, provide relevant next step suggestions."
        )
        # We need to decide if we still use the full message history for suggestions
        # or just the confirmation context. For now, let's use a focused prompt.
        # The `get_suggestion_prompt` might need to be aware of this state.
        # For simplicity here, we'll just use the existing suggestion mechanism but acknowledge
        # the LLM's main text generation will be overridden.
        # The LLM call below will still happen for suggestions.
        # We will override its textual response part.

        # Construct a prompt for the LLM that focuses on suggestions given the confirmation context
        # This is a simplified approach; you might want a more tailored prompt for suggestions during confirmation.
        llm_prompt_messages = [
            SystemMessage(content=(
                "You are an assistant. The user is currently being asked for confirmation about an action. "
                "Your primary goal is to provide helpful next-step suggestions. "
                "The main response text is already determined. "
                "Focus on generating relevant suggestions based on the pending action and conversation. "
                f"The pending action is: {pending_op_details.get('operation') if pending_op_details else 'unknown'} with parameters {pending_op_details.get('params') if pending_op_details else 'unknown'}."
                "The user is being asked: " + response_content
            ))
        ]
        # Add some history for context for suggestions, but not necessarily all of it.
        # For now, let's pass the last few messages for suggestion context.
        llm_prompt_messages.extend(clean_messages[-3:]) # Example: last 3 messages for context

    else:
        # Normal response generation using LLM for text and suggestions
        logger.info("Not awaiting confirmation. Generating response with LLM.")
        # Add system instruction to detect execution opportunities
        # This part can remain similar, but ensure it doesn't conflict with confirmation logic
        # (which it won't if is_awaiting_confirmation is false)
        # ... (existing logic for general system prompt if needed) ...
        llm_prompt_messages = list(clean_messages) # Use all clean messages for general response

    # Get suggestions (this part can be common, but the context might differ)
    suggestions = get_suggestions_for_topic(
        project_id=state.get("project_id"),
        topic=state.get("request_type", "general"), # Use request_type from state
        entity_id=state.get("character_id") or state.get("act_id"), # Pass relevant ID
        current_operation_intent=pending_op_details.get("operation") if is_awaiting_confirmation and pending_op_details else state.get("operation_intent"),
        current_operation_params=pending_op_details.get("params") if is_awaiting_confirmation and pending_op_details else state.get("operation_params")
    )
    
    suggestion_prompt_text = None # Initialize suggestion_prompt_text
    if suggestions:
        suggestion_prompt_text = get_suggestion_prompt(topic=state.get("request_type", "general"), potential_suggestions=suggestions)
    if suggestion_prompt_text:
        # Append or insert suggestion prompt. Appending for now.
        llm_prompt_messages.append(SystemMessage(content=suggestion_prompt_text))

    # Call the structured LLM
    # The LLM will generate a 'response' field and a 'suggestions' field in its Pydantic model.
    # If is_awaiting_confirmation, we will override its 'response' field.
    try:
        logger.debug(f"Messages for structured LLM: {llm_prompt_messages}")
        structured_response_obj = structured_llm.invoke(llm_prompt_messages) # Pass the list of messages directly
        
        # If we are awaiting confirmation, override the LLM's generated text response
        # with the actual confirmation question.
        llm_generated_text = structured_response_obj.response
        if is_awaiting_confirmation:
            logger.info(f"Overriding LLM text response. Original LLM text: '{llm_generated_text}'. Using confirmation question: '{response_content}'")
            final_text_response = response_content # This is the confirmation question
        else:
            final_text_response = llm_generated_text

        suggestions_for_response = structured_response_obj.suggestions
        logger.info(f"Structured LLM Response: response='{final_text_response}' suggestions={suggestions_for_response}")

    except Exception as e:
        logger.error(f"Error calling structured LLM for final response: {e}", exc_info=True)
        final_text_response = "I encountered an issue while formulating my response. Please try again."
        suggestions_for_response = get_fallback_suggestions(state.get("request_type", "general"))


    # Construct the final ChatResponse object
    # `be_function` and `db_updated` should reflect the state *before* this final response generation,
    # especially if it's just a confirmation question.
    # When awaiting confirmation, these should typically be None/False.
    final_chat_response = ChatResponse(
        response=final_text_response,
        suggestions=suggestions_for_response,
        be_function=state.get("be_function") if not is_awaiting_confirmation else None, # Only set if not just confirming
        db_updated=state.get("db_updated", False) if not is_awaiting_confirmation else False # Only set if not just confirming
    )
    
    # Update state: Add the AI's final response message (text part only) to history
    # The full ChatResponse object is stored in 'final_response' key
    # The AIMessage here should contain what the user sees as the bot's reply.
    updated_messages = clean_messages + [AIMessage(content=final_text_response)]

    return {"messages": updated_messages, "final_response": final_chat_response}