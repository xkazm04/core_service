"""
Core graph nodes for langgraph-based agent
"""
import logging
from typing import Dict, Any
from langgraph.graph import END
from services.agents.chat.message_utils import truncate_problematic_history
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
from services.agents.executor import EXECUTOR_MAP
from uuid import uuid4
from services.agents.chat.message_utils import ensure_tool_call_integrity

logger = logging.getLogger(__name__)

def call_model_for_tool_or_direct(state: AgentState) -> Dict[str, Any]:
    operation_intent = state.get('operation_intent')
    operation_params = state.get('operation_params', {})
    missing_params = state.get('missing_params', []) # Get missing_params from state

    if operation_intent and operation_intent in EXECUTOR_MAP:
        if missing_params:
            # Parameters are missing, ask the user for them.
            # You can make this question more sophisticated later.
            # For now, just list the first one or all.
            # Example: Use the get_parameter_prompts from previous suggestion
            # For simplicity here:
            missing_params_str = ", ".join(missing_params)
            question = f"To proceed with '{operation_intent}', I need some more information: {missing_params_str}. Could you please provide it?"
            
            logger.info(f"Asking user for missing parameters: {missing_params_str}")
            ai_message = AIMessage(content=question)
            
            # Return the question. Importantly, keep operation_intent and current params in state.
            # missing_params can be kept as is, or you might refine how it's updated based on the question asked.
            return {
                "messages": [ai_message],
                "operation_intent": operation_intent, # Keep current intent
                "operation_params": operation_params, # Keep collected params
                "missing_params": missing_params    # Keep list of missing params
            }
        else:
            # All parameters are present, proceed with tool call
            logger.info(f"All params present. Using pre-detected operation: {operation_intent} with params: {operation_params}")
            tool_call = {
                "name": "ExecutorFunctionArgs",
                "args": {
                    "function_name": operation_intent,
                    "params": operation_params
                },
                "id": f"at-{str(uuid4())}" # Changed prefix from "auto-" to "at-"
            }
            ai_message = AIMessage(
                content="I'll help you with that operation.", # Or a more dynamic confirmation
                tool_calls=[tool_call]
            )
            # Clear the intent now that it's being actioned
            return {
                "messages": [ai_message],
                "operation_intent": None,
                "operation_params": {},
                "missing_params": []
            }
    
    # Ensure message integrity before processing (original logic)
    messages = ensure_tool_call_integrity(state['messages'])
    messages = truncate_problematic_history(messages) 
    
    # Check if there were recent errors in tool execution
    recent_errors = []
    for msg in messages[-3:]:  # Check last 3 messages
        if isinstance(msg, ToolMessage) and "error" in msg.content.lower():
            recent_errors.append(msg.content)
    
    # Check if the last message is a ToolMessage, indicating we need to process tool results
    if isinstance(messages[-1], ToolMessage):
        logger.info("--- Calling LLM to process tool results ---")
        
        # If this tool message contains an error, add recovery guidance
        if "error" in messages[-1].content.lower():
            recovery_message = SystemMessage(content="""
            The previous operation resulted in an error. Please:
            1. Acknowledge the error in your response
            2. Explain what might have gone wrong in simple terms
            3. Suggest an alternative approach or ask for more information
            4. Do NOT attempt the exact same operation again without changes
            """)
            messages.append(recovery_message)
            
        response = llm_with_tools.invoke(messages)
    else:
        logger.info("--- Calling LLM for initial response or tool call (no pre-detected intent path) ---")
        # Add system instruction to detect execution opportunities
        execution_detection_message = SystemMessage(content="""
        While responding to the user, consider if their request implies a need to modify data in the system.
        If their message suggests creating, updating, or managing characters, factions, story elements, etc.,
        use the appropriate tool to perform that operation.
        
        Available operations include:
        - CharacterLookupArgs: To look up character information
        - StoryLookupArgs: To look up story information
        - BeatLookupArgs: To look up beat information
        - ProjectGapAnalysisArgs: To analyze project gaps
        - ExecutorFunctionArgs: To execute database changes like creating or renaming characters
        
        If you determine a database operation is needed based on user intent, call the appropriate tool.
        """)
        
        augmented_messages = messages + [execution_detection_message]
        response = llm_with_tools.invoke(augmented_messages)

    logger.info(f"LLM intermediate response/tool call: {response}")
    return {"messages": [response]}

def tool_node_executor(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Executes tools based on the last AI message."""
    logger.info("--- Executing Tool Node ---")
    last_message = state['messages'][-1]
    
    # Initialize be_function and db_updated flag
    be_function = None
    db_updated = False
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logger.error("Expected AI message with tool calls, but found none")
        return {"messages": [SystemMessage(content="Error: No tool calls found in the last message.")]}
    
    # Get the configurable components (e.g., database session)
    db_session = config['configurable'].get('db_session')
    if not db_session:
        logger.error("DB Session not found in config for tool node execution!")
        # Make sure to respond to ALL tool calls, even in error cases
        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_id = tool_call['id']
            tool_messages.append(ToolMessage(
                content="Error: Database connection not available.", 
                tool_call_id=tool_id
            ))
        return {"messages": tool_messages}
    
    # Process each tool call
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_id = tool_call['id']
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        logger.info(f"Processing tool call: {tool_name} (ID: {tool_id})")
        
        try:
            # Handle the ExecutorFunctionArgs tool
            if tool_name == "ExecutorFunctionArgs":
                # Extract function name and params from tool args
                function_name = tool_args.get("function_name")
                params = tool_args.get("params", {})
                
                # Store the function name in state
                be_function = function_name
                
                # Log execution attempt
                logger.info(f"Agent-initiated execution of '{function_name}' with params: {params}")
                
                # Execute the function using the existing executor
                try:
                    from services.agents.executor import execute_suggestion_function
                    result = execute_suggestion_function(
                        function_name=function_name,
                        db=db_session,
                        project_id=state.get("project_id"),
                        character_id=state.get("character_id"),
                        **params
                    )
                    result_msg = f"Executed function '{function_name}': {result}"
                    # Set flag to indicate DB was updated
                    db_updated = True
                    logger.info(f"db_updated: {db_updated}")
                except Exception as e:
                    logger.error(f"Error executing function {function_name}: {e}", exc_info=True)
                    result_msg = f"Error executing function {function_name}: {str(e)}"
                
                tool_messages.append(ToolMessage(
                    content=result_msg,
                    tool_call_id=tool_id
                ))
            # Handle other tools as before...
            elif tool_name in ["CharacterLookupArgs", "StoryLookupArgs", "BeatLookupArgs", "SceneLookupArgs", "ProjectGapAnalysisArgs"]:
                # Handle database tools
                from services.agents.tools.db_tool_executor import execute_db_tool
                single_tool_state = {
                    "messages": [last_message], 
                    "project_id": state.get("project_id"),
                    "character_id": state.get("character_id"),
                    "extracted_character_names": state.get("extracted_character_names", [])
                }
                tool_result = execute_db_tool(single_tool_state, db_session)
                
                # Make sure we're adding exactly one ToolMessage per tool_call_id
                if "messages" in tool_result and tool_result["messages"]:
                    # Check if we got a ToolMessage with the right ID
                    for message in tool_result["messages"]:
                        if isinstance(message, ToolMessage) and message.tool_call_id == tool_id:
                            tool_messages.append(message)
                            break
                    else:
                        # If no matching ToolMessage was found, create one
                        content = str(tool_result.get("messages", ["No result"])[0].content 
                                      if hasattr(tool_result.get("messages", [""])[0], "content") 
                                      else "Tool execution complete but no content returned")
                        tool_messages.append(ToolMessage(
                            content=content,
                            tool_call_id=tool_id
                        ))
                else:
                    # Fallback if no messages were returned
                    tool_messages.append(ToolMessage(
                        content="Tool execution completed but returned no messages.",
                        tool_call_id=tool_id
                    ))
            
            elif tool_name == "YouTubeSearchArgs":
                from services.agents.tools import execute_youtube_tool
                tool_result = execute_youtube_tool(tool_call, state)
                tool_messages.append(ToolMessage(content=tool_result, tool_call_id=tool_id))
                
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
    
    # Ensure we have at least one response for each tool call
    tool_call_ids = [tc['id'] for tc in last_message.tool_calls]
    response_ids = [tm.tool_call_id for tm in tool_messages if hasattr(tm, 'tool_call_id')]
    
    # Check for any missing responses
    for tool_id in tool_call_ids:
        if tool_id not in response_ids:
            logger.warning(f"No tool response for call ID {tool_id}, adding fallback response")
            tool_messages.append(ToolMessage(
                content="No specific handler processed this tool call",
                tool_call_id=tool_id
            ))
    
    logger.info(f"Returning {len(tool_messages)} tool messages for {len(tool_call_ids)} tool calls")
    
    # Return messages, be_function if found, and db_updated flag
    result = {"messages": tool_messages}
    if be_function:
        result["be_function"] = be_function
    result["db_updated"] = db_updated
    
    return result

def generate_final_response(state: AgentState) -> Dict[str, Any]:
    """
    Calls the LLM bound with the ChatResponse schema to generate the final
    structured output including the text response and relevant suggestions.
    """
    logger.info("--- Generating Final Structured Response ---")
    
    # Use our utility to ensure all tool calls have responses
    clean_messages = ensure_tool_call_integrity(state['messages'])
    
    request_type = state.get('request_type', 'general')
    character_id = state.get('character_id')
    be_function = state.get('be_function')  # Get the executed function name
    db_updated = state.get('db_updated', False)  # Get the DB update status
    
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
    prompt_messages = clean_messages + [
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
        
        # Add executed function and db_updated status to the response if available
        if be_function:
            structured_response.be_function = be_function
        structured_response.db_updated = db_updated
        
        # Return the structured response
        return {"final_response": structured_response}
        
    except Exception as e:
        logger.error(f"Error generating final response: {e}", exc_info=True)
        response = ChatResponse(
            response=f"Error generating response: {str(e)}", 
            suggestions=[],
            db_updated=db_updated
        )
        if be_function:
            response.be_function = be_function
        return {"final_response": response}