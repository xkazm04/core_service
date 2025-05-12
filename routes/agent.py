from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database import get_db
from schemas.agent import ChatResponse
from services.agents.chat_agent import AgentState, workflow, memory
from services.agents.tools import CharacterLookupArgs, StoryLookupArgs, BeatLookupArgs
from services.agents.executor import execute_suggestion_function

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

import logging

logger = logging.getLogger(__name__)

# --- Suggestion and Response Models ---

# --- Request Model ---
class ChatRequest(BaseModel):
    user_id: Optional[str]
    message: str
    type: str
    project_id: UUID
    act_id: Optional[UUID] = None
    character_id: Optional[UUID] = None
    chat_session_id: Optional[str] = Field(None, description="Unique ID for the chat session to maintain conversation memory")
    be_function: Optional[str] = Field(None, description="The 'be_function' name if the request comes from clicking a suggestion.")
    function_params: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Parameters to pass to the be_function if specified"
    )

router = APIRouter(tags=["Agent Chat"])

# --- Compile Graph ---
compiled_graph = workflow.compile(checkpointer=memory)

# --- API Endpoint ---
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Receives user message or suggestion click, executes backend function if applicable,
    and returns agent response with suggestions.
    """
    
    user_input = request.message # This will be suggestion_text if suggestion was clicked
    user_id = "test_user" if not request.user_id else request.user_id
    act_id = request.act_id # Get act_id from request
    project_id = request.project_id
    character_id = request.character_id
    request_type = request.type.lower()
    selected_be_function = request.be_function 
    
    chat_session_id = f"{user_id}:{request.chat_session_id}" if request.chat_session_id else f"{user_id}:default"

    logger.info(f"Received request from user {user_id} for project {project_id} with type {request_type}.")
    logger.info(f"Using chat session ID: {chat_session_id}")
    if selected_be_function:
        logger.info(f"Request originated from suggestion click: executing '{selected_be_function}'")


    execution_result_message = None
    if selected_be_function:
        try:
            # Pass function parameters directly from the request
            result_message = execute_suggestion_function(
                function_name=selected_be_function,
                db=db,
                act_id=act_id,
                project_id=request.project_id,
                character_id=request.character_id,
                **request.function_params  # Use provided parameters
            )
            execution_result_message = result_message
        except Exception as e:
            logger.error(f"Error executing suggestion function: {e}", exc_info=True)
            execution_result_message = f"Error executing action: {str(e)}"

    # --- Prepare Agent Input ---
    agent_input_message = user_input
    if execution_result_message:
        agent_input_message = f"[Action Result: {execution_result_message}]\n\nUser message: {user_input}"
        logger.info("Prepended execution result to agent input.")

    config = {
        "configurable": {
            "thread_id": chat_session_id, 
            "db_session": db 
        }
    }

    # --- Initial State Setup ---
    # Use the potentially modified agent_input_message
    initial_messages = [HumanMessage(content=agent_input_message)]
    
    # Add system messages based on request_type (same as before)
    system_message_content = ""
    if request_type == 'character':
        system_message_content = """
        You are a helpful assistant for character development.
        
        If the user's message suggests creating, editing, or managing characters:
        1. Use the ExecutorFunctionArgs tool with the appropriate function_name
        2. Construct the params object with the necessary parameters
        
        Available functions:
        - character_create: Creates a new character (params: target_char_name)
        - character_rename: Renames a character (params: target_char_name)
        - trait_add: Adds a trait to a character (params: trait_description, trait_type)
        - relationship_add: Creates a relationship (params: secondary_character_id, relationship_type, relationship_description)
        """
    elif request_type == 'story':
        system_message_content = """
        You are a helpful assistant for story development.
        
        If the user's message suggests creating, editing, or managing story elements:
        1. Use the ExecutorFunctionArgs tool with the appropriate function_name
        2. Construct the params object with the necessary parameters
        
        Available functions:
        - act_create: Creates a new act (params: act_name, act_description)
        - act_edit: Edits an act (params: act_id, act_description)
        - beat_create: Creates a new beat (params: beat_name, beat_description)
        - beat_edit: Edits a beat (params: beat_id, beat_description)
        """
    elif request_type == 'analysis':
         system_message_content = (
             f"The user wants an analysis of the story progress for project {project_id}. "
             f"To answer effectively, you should first gather context using the {StoryLookupArgs.__name__} tool "
             f"for the overall story structure (overview, acts) AND the {BeatLookupArgs.__name__} tool "
             f"for the specific objectives (beats) and their completion status. "
             f"Synthesize the information from both tools to provide the analysis."
         )
    else: # General
         system_message_content = (
             f"You are a helpful assistant discussing project {project_id}. You can look up character details ({CharacterLookupArgs.__name__}), "
             f"story overview/acts ({StoryLookupArgs.__name__}), or story beats/objectives ({BeatLookupArgs.__name__}) if needed."
         )

    initial_messages.insert(0, SystemMessage(content=system_message_content))

    initial_state = AgentState(
        messages=initial_messages,
        project_id=project_id,
        character_id=character_id,
        act_id=act_id, # Pass act_id to initial state
        request_type=request_type,
        extracted_character_names=None, # Initialize if not set earlier
        be_function=None, # Initialize
        operation_intent=None, # Initialize
        operation_params={}, # Initialize
        missing_params=[], # Initialize
        final_response=None, # Initialize
        # Initialize new state fields
        pending_operation_details=None,
        awaiting_confirmation=False,
        db_updated=False 
    )
    logger.info(f"Initial State (after potential execution): {initial_state}")
    final_state_values = None
    try:
        logger.info("Starting graph stream...")
        async for event in compiled_graph.astream(initial_state, config=config, stream_mode="values"):
            logger.debug(f"Graph Event State: {event}")
            final_state_values = event
        logger.info("Graph stream finished.")
    except Exception as e:
        logger.error(f"Error during graph execution for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent processing error: {e}")

    # --- Extract Structured Response ---
    if final_state_values and final_state_values.get("final_response"):
        final_response_obj = final_state_values["final_response"]
        
        # Import the expected class to ensure we're using the right one
        from schemas.agent import ChatResponse as ExpectedChatResponse
        
        if isinstance(final_response_obj, ExpectedChatResponse):
             logger.info(f"Final structured response (db_updated: {final_response_obj.db_updated}): {final_response_obj}")
             return final_response_obj
        else:
             logger.warning(f"Final state 'final_response' was not the expected ChatResponse type: {type(final_response_obj)}")
             # Try to convert it to the right type
             try:
                 if hasattr(final_response_obj, 'response') and hasattr(final_response_obj, 'suggestions'):
                     response = final_response_obj.response
                     suggestions = final_response_obj.suggestions
                     logger.info(f"Converting from {type(final_response_obj)} to ExpectedChatResponse")
                     return ExpectedChatResponse(response=response, suggestions=suggestions)
                 elif isinstance(final_response_obj, dict):
                     logger.info(f"Converting dict to ExpectedChatResponse")
                     return ExpectedChatResponse(
                         response=final_response_obj.get("response", "Error: Could not parse response."),
                         suggestions=final_response_obj.get("suggestions", [])
                     )
                 else:
                     logger.error(f"Could not convert {type(final_response_obj)} to ExpectedChatResponse")
                     return ExpectedChatResponse(response="Error: Could not generate structured response.", suggestions=[])
             except Exception as e:
                 logger.error(f"Error converting to ExpectedChatResponse: {e}")
                 return ExpectedChatResponse(response="Error: Could not generate structured response.", suggestions=[])
    elif final_state_values and "messages" in final_state_values:
        # Try to extract the last AI message as a fallback
        db_updated_status = final_state_values.get("db_updated", False)
        try:
            messages = final_state_values["messages"]
            last_ai_msg = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
            if last_ai_msg:
                logger.info(f"Using last AI message as fallback response. db_updated: {db_updated_status}")
                # Ensure suggestions are handled, e.g., get_fallback_suggestions
                from services.agents.executors.suggestion_manager import get_fallback_suggestions
                fallback_suggestions = get_fallback_suggestions(final_state_values.get('request_type', 'general'))
                return ChatResponse(response=last_ai_msg.content, suggestions=fallback_suggestions, db_updated=db_updated_status)
        except Exception as e:
            logger.error(f"Error in fallback response generation: {e}")
            # Fall through to generic error

    logger.warning("No final_response or suitable fallback messages found in final agent state.")
    # Ensure db_updated is included even in this generic error response
    db_updated_status_at_end = final_state_values.get("db_updated", False) if final_state_values else False
    from services.agents.executors.suggestion_manager import get_fallback_suggestions
    final_fallback_suggestions = get_fallback_suggestions(request.type.lower() if request else 'general')
    return ChatResponse(
        response="Sorry, I encountered an issue and couldn't complete your request.", 
        suggestions=final_fallback_suggestions, 
        db_updated=db_updated_status_at_end
    )

# @router.post("/reset_chat")
# async def reset_chat(
#     user_id: str = Query(..., description="User ID"),
#     chat_session_id: Optional[str] = Query(None, description="Optional specific chat session ID"),
#     project_id: Optional[UUID] = Query(None, description="Optional project ID to include in initial state")
# ):
#     """
#     Reset the conversation memory for a specific chat session.
#     Use this when the conversation gets stuck in an error loop.
#     """
#     session_key = f"{user_id}:{chat_session_id}" if chat_session_id else f"{user_id}:default"
    
#     try:
#         # Clear the memory for this session
#         memory.clear(session_key)
        
#         logger.info(f"Chat memory reset for session {session_key}")
        
#         # Return success response
#         return {
#             "status": "success", 
#             "message": f"Chat memory reset for session {session_key}"
#         }
#     except Exception as e:
#         logger.error(f"Failed to reset chat memory: {str(e)}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Failed to reset chat memory: {str(e)}"
#         )