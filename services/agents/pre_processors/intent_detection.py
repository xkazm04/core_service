"""
Intent detection system for parsing user messages into structured operations
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
from uuid import UUID
from services.agents.chat.agent_state import AgentState
from services.agents.pre_processors.name_extraction import extract_character_name

logger = logging.getLogger(__name__)

def detect_operation_intent(
    message: str, 
    project_id: UUID,
    act_id: Optional[UUID] = None,
    character_id: Optional[UUID] = None,
    request_type: str = "general"
) -> Tuple[Optional[str], Dict[str, Any], List[str]]: # Ensure return type includes List[str] for missing_info
    """
    Analyzes the user message to detect operation intent and extract parameters.
    Returns tuple of (detected_function, extracted_params)
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    
    # Define the template based on request type
    system_template = f"""You are an expert in parsing user requests related to {request_type}. 
    Analyze the user's message and determine:
    1. If they're requesting a specific database operation
    2. What parameters they're providing for that operation
    
    Supported operations for {request_type} context:
    """
    
    # Add operation descriptions based on request type
    if request_type == "character":
        system_template += """
        - character_create: Creates a new character (extract: target_char_name for the character's name, type if available - if not, use default value 'major')
        - character_rename: Renames a character (extract: existing character reference, new name as target_char_name)
        - trait_add: Adds a trait to a character (extract: trait type, trait description)
        - relationship_add: Creates a relationship (extract: both character references, relationship type, description)
        """
    elif request_type == "story":
        system_template += """
        - act_create: Creates a new act (extract: act name, description)
        - act_edit: Edits an existing act (extract: act reference, new description)
        - beat_create: Creates a new beat (extract: beat name, description)
        - beat_edit: Edits a beat (extract: beat reference, new description)
        - scene_create: Creates a new scene (extract: scene name, description, act order/number). If description not provided, create engaging scene description based on the message context. If not act provided, use Act 1.
        """
    elif request_type == "faction":
        system_template += """
        - faction_create: Creates a new faction (extract: faction name, description)
        - faction_rename: Renames a faction (extract: faction reference, new name)
        """
    
    system_template += """
    Return your analysis as a JSON object with these fields:
    - operation: The detected operation name, or null if no operation is detected
    - confidence: Number between 0-1 indicating confidence in detection
    - parameters: Object containing extracted parameters needed for the operation
    - missing_info: Array of parameters needed but not found in the user message
    """
    
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
        missing_info = result.get("missing_info", []) # Ensure this is a list

        if operation is None or confidence < 0.7:
            return None, {}, []
        
        return operation, parameters, missing_info
    except Exception as e:
        logger.error(f"Error in intent detection: {e}")
        return None, {}, []
    
def extract_operation_intent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the user's message to detect operation intent and parameters.
    Updates state with operation_intent and operation_params when detected.
    """
    # Extract character names first (keeping existing functionality)
    updated_state = extract_character_name(state)
    
    # Get the last human message
    messages = updated_state['messages']
    human_messages = [msg for msg in messages if hasattr(msg, 'type') and msg.type == 'human']
    
    if not human_messages:
        logger.warning("No human messages found in state")
        return updated_state
    
    # Get the last human message content
    last_human_msg = human_messages[-1].content
    
    # Detect intent using our new function
    project_id = updated_state.get('project_id')
    character_id = updated_state.get('character_id')
    act_id = updated_state.get('act_id')
    request_type = updated_state.get('request_type', 'general')
    
    operation, params, missing = detect_operation_intent( # Capture missing_params
        last_human_msg, 
        project_id, 
        character_id,
        act_id,
        request_type
    )
    
    if operation:
        logger.info(f"Detected operation intent: {operation} with params: {params}, missing: {missing}")
        updated_state['operation_intent'] = operation
        updated_state['operation_params'] = params
        updated_state['missing_params'] = missing # Store missing_params in state
    else:
        # If no operation, clear any lingering intent state
        updated_state['operation_intent'] = None
        updated_state['operation_params'] = {}
        updated_state['missing_params'] = []
        
    return updated_state