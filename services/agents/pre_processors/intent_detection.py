"""
Intent detection system for parsing user messages into structured operations
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
from services.agents.chat.agent_state import AgentState
from services.agents.pre_processors.name_extraction import extract_character_name
from ..templates.intent_instructions import operations_list_all, operations_list_char, operations_list_story

logger = logging.getLogger(__name__)

def detect_operation_intent(
    message: str, 
    request_type: str = "general"
) -> Tuple[Optional[str], Dict[str, Any], List[str], Optional[str]]: # Added Optional[str] for detected_topic
    """
    Analyzes the user message to detect operation intent and extract parameters.
    Returns tuple of (detected_function, extracted_params, missing_info, detected_topic)
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    system_template_intro = ""
    operations_list_str = ""
    json_output_fields_str = """
    - operation: The detected operation name, or null if no operation is detected
    - confidence: Number between 0-1 indicating confidence in detection
    - parameters: Object containing extracted parameters needed for the operation
    - missing_info: Array of parameters needed but not found in the user message
"""

    if request_type == "general":
        system_template_intro = """You are an expert in parsing user requests for a story-telling assistant.
Analyze the user's message and determine:
1. If they're requesting a specific database operation.
2. What parameters they're providing for that operation.
3. Categorize the request into a general topic: 'character', 'story', 'faction', or 'other' if it doesn't fit.

Supported operations across all topics:
"""
        operations_list_str = operations_list_all
        json_output_fields_str += "- detected_topic: The categorized topic ('character', 'story', 'faction', 'other', or null if not applicable).\n"
    else: # Specific request types (character, story, faction)
        system_template_intro = f"""You are an expert in parsing user requests related to {request_type}. 
Analyze the user's message and determine:
1. If they're requesting a specific database operation
2. What parameters they're providing for that operation

Supported operations for {request_type} context:
"""
        if request_type == "character":
            operations_list_str = operations_list_char
        elif request_type == "story":
            operations_list_str = operations_list_story
        elif request_type == "faction":
            operations_list_str = """- faction_create: Creates a new faction (extract: faction name, description)
- faction_rename: Renames a faction (extract: faction reference, new name)
"""
    
    system_template = system_template_intro + operations_list_str + "\nReturn your analysis as a JSON object with these fields:\n" + json_output_fields_str
    
    human_template = "{input}"
    
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", human_template),
    ])
    
    model = ChatOpenAI(model="gpt-4o") 
    parser = JsonOutputParser()
    
    chain = chat_prompt | model | parser
    
    try:
        result = chain.invoke({"input": message})
        logger.info(f"Intent detection result: {result}")
        
        operation = result.get("operation")
        confidence = result.get("confidence", 0)
        parameters = result.get("parameters", {})
        missing_info = result.get("missing_info", []) 
        detected_topic = result.get("detected_topic") if request_type == "general" else None

        if operation is None or confidence < 0.7: # Adjust confidence as needed
            return None, {}, [], detected_topic # Return detected_topic even if no op
        
        return operation, parameters, missing_info, detected_topic
    except Exception as e:
        logger.error(f"Error in intent detection: {e}")
        return None, {}, [], None
    
def extract_operation_intent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the user's message to detect operation intent and parameters.
    Updates state with operation_intent, operation_params, and potentially request_type.
    Then, if the topic is character-related, extracts character names.
    """
    # Make a mutable copy of the state to avoid modifying the input directly if it's a TypedDict
    # or to ensure we are working with a standard dictionary.
    if isinstance(state, dict):
        updated_state = state.copy() 
    else:
        # If AgentState is a class instance or other non-dict type that needs specific conversion
        logger.warning(f"Initial state type is {type(state)}, attempting conversion if necessary.")
        updated_state = dict(state) # Fallback, ensure this matches AgentState structure

    messages = updated_state.get('messages', []) # Use .get for safety
    human_messages = [msg for msg in messages if hasattr(msg, 'type') and msg.type == 'human']

    if not human_messages:
        logger.warning("No human messages found in state for intent detection.")
        return updated_state

    last_human_msg = human_messages[-1].content
    current_request_type = updated_state.get('request_type', 'general')

    # 1. Detect operation and topic first
    operation, params, missing, detected_topic = detect_operation_intent(
        last_human_msg,
        request_type=current_request_type
    )

    if operation:
        logger.info(f"Detected operation intent: {operation} with params: {params}, missing: {missing}")
        updated_state['operation_intent'] = operation
        updated_state['operation_params'] = params
        updated_state['missing_params'] = missing
    else:
        updated_state['operation_intent'] = None
        updated_state['operation_params'] = {}
        updated_state['missing_params'] = []

    # 2. Update request_type in state if it was 'general' and a specific topic was detected
    if current_request_type == "general" and detected_topic and detected_topic in ["character", "story", "faction", "other"]:
        logger.info(f"General request's topic detected as '{detected_topic}'. Updating request_type in state.")
        updated_state['request_type'] = detected_topic
        # Update current_request_type variable as well for the next step
        current_request_type = detected_topic 
    
    # 3. Conditionally extract character name if the topic is now 'character'
    #    and no character_id is already set (as name extraction is usually for identifying a new character context)
    if current_request_type == "character" and not updated_state.get('character_id'):
        logger.info(f"Topic is '{current_request_type}', attempting character name extraction.")
        # Pass the current state (which includes messages and updated request_type)
        # extract_character_name should return the modified state
        updated_state_after_name_extraction = extract_character_name(updated_state)
        # Ensure all keys from extract_character_name are merged back if it returns a modified copy
        if isinstance(updated_state_after_name_extraction, dict):
            updated_state.update(updated_state_after_name_extraction)
        else:
            logger.error("extract_character_name did not return a dictionary.")
    elif current_request_type == "character" and updated_state.get('character_id'):
        logger.info(f"Topic is '{current_request_type}' but character_id is already set. Skipping name extraction.")


    return updated_state