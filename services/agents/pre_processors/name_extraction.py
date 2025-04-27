from langchain_core.messages import HumanMessage
import logging
import re

logger = logging.getLogger(__name__)
def extract_character_name(state):
    """
    Analyzes the user's message to extract potential character names.
    Updates state with extracted character names and character_id when possible.
    """
    
    logger.info("--- Extracting Character Names ---")
    
    # Find the last human message
    messages = state['messages']
    human_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    
    if not human_messages:
        logger.warning("No human messages found in state")
        return state
    
    # Only process if we're in character context and don't have a character_id
    request_type = state.get('request_type', '')
    character_id = state.get('character_id')
    
    if request_type.lower() != 'character' or character_id is not None:
        logger.info(f"Skipping character extraction: type={request_type}, character_id={character_id}")
        return state
    
    last_human_msg = human_messages[-1].content
    logger.info(f"Extracting character name from: {last_human_msg[:100]}...")
    
    # Pattern matching for common character name request formats
    patterns = [
        r"(?:character|person|npc)(?:\s+named|\s+called)?\s+([A-Z][a-z]+)",  # "character named Malak"
        r"(?:about|on|regarding)\s+([A-Z][a-z]+)",  # "about Malak"
        r"(?:what|who|tell me about)\s+(?:is|about)?\s+([A-Z][a-z]+)",  # "what is Malak"
        r"([A-Z][a-z]+)(?:'s|\s+is|\s+was|\s+has)",  # "Malak's" or "Malak is"
    ]
    
    extracted_names = []
    for pattern in patterns:
        matches = re.findall(pattern, last_human_msg)
        extracted_names.extend(matches)
    
    # Remove duplicates while preserving order
    unique_names = []
    for name in extracted_names:
        if name not in unique_names:
            unique_names.append(name)
    
    if unique_names:
        logger.info(f"Extracted potential character names: {unique_names}")
        # Update state with extracted names
        updated_state = state.copy()
        updated_state["extracted_character_names"] = unique_names
        return updated_state
    
    logger.info("No character names extracted from message")
    return state