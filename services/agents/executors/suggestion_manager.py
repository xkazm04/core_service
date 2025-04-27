import logging
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from schemas.agent import Suggestion

logger = logging.getLogger(__name__)

# Import the suggestion data - adjust path if needed
from services.agents.executors.suggestions import suggestion_data

def get_suggestions_for_topic(topic: str, entity_id: Optional[UUID] = None, **context) -> List[Dict[str, Any]]:
    """
    Gets suggestions relevant to the given topic and context.
    
    Args:
        topic: The topic/request_type for which to get suggestions
        entity_id: The primary entity ID (character_id, story_id, etc.) if available
        **context: Additional context parameters that may affect suggestion relevance
    
    Returns:
        List of suggestions objects relevant to the current context
    """
    logger.info(f"Getting suggestions for topic '{topic}', entity_id={entity_id}")
    
    # Get all suggestions for the topic
    from services.agents.executors.suggestion_loader import load_suggestions_by_topic
    potential_suggestions = load_suggestions_by_topic(topic)
    
    # If no suggestions were loaded, fall back to hardcoded suggestions
    if not potential_suggestions:
        logger.warning(f"No suggestions loaded for topic '{topic}'. Falling back to hardcoded suggestions.")
        potential_suggestions = [s for s in suggestion_data if s.get("topic", "").lower() == topic.lower()]
    
    # Handle entity ID requirements based on topic
    if topic.lower() == "character" and entity_id is None:
        # Character topic requires a character_id - check if select_character suggestion exists
        select_character_exists = any(
            s.get("be_function") == "select_character" or s.get("fe_function") == "character_select" 
            for s in potential_suggestions
        )
        
        if not select_character_exists:
            # Add default select_character suggestion
            select_character_suggestion = get_default_select_suggestion("character")
            potential_suggestions.append(select_character_suggestion)
            logger.info("Added default select_character suggestion to potential suggestions")
    
    # Similar blocks for other entity types can be added here
    elif topic.lower() == "story" and entity_id is None:
        # Add story selection suggestion if needed
        select_story_exists = any(
            s.get("be_function") == "select_story" or s.get("fe_function") == "story_select" 
            for s in potential_suggestions
        )
        
        if not select_story_exists:
            # Add default select_story suggestion (when implemented)
            select_story_suggestion = get_default_select_suggestion("story")
            potential_suggestions.append(select_story_suggestion)
            logger.info("Added default select_story suggestion to potential suggestions")
    
    # Add more entity types as needed
    
    logger.info(f"Returning {len(potential_suggestions)} potential suggestions")
    return potential_suggestions

def get_suggestion_prompt(topic: str, potential_suggestions: List[Dict[str, Any]], entity_id: Optional[UUID] = None) -> str:
    """
    Generates the LLM prompt part for suggestions.
    
    Args:
        topic: The topic/request_type for suggestions
        potential_suggestions: List of potential suggestions to include in the prompt
        entity_id: The primary entity ID if available
    
    Returns:
        Formatted prompt string about suggestions
    """
    if potential_suggestions:
        suggestions_list_str = json.dumps(potential_suggestions, indent=2)
        return (
            f"\n\nConsider the following potential suggestions for the user (topic: {topic}). "
            f"Evaluate if any are relevant based on their 'initiator' condition and the current conversation context. "
            f"Include relevant ones in the 'suggestions' list in your JSON output. Only include suggestions if their initiator condition is met by the current context.\n"
            f"You MUST include multiple suggestions in the list if they are all relevant to the conversation.\n"
            f"If the conversation is about {topic} but no specific {topic} ID is set, ALWAYS include the 'select_{topic}' suggestion.\n\n"
            f"Potential Suggestions:\n{suggestions_list_str}"
        )
    else:
        # Create a minimal prompt with just the required selection suggestion if applicable
        entity_missing = (
            (topic.lower() == "character" and entity_id is None) or
            (topic.lower() == "story" and entity_id is None)
            # Add more entity types as needed
        )
        
        if entity_missing:
            select_suggestion = get_default_select_suggestion(topic)
            suggestions_list_str = json.dumps([select_suggestion], indent=2)
            return (
                f"\n\nYou MUST include the following suggestion in your response:\n"
                f"{suggestions_list_str}"
            )
        else:
            return "\n\nNo specific suggestions available for this topic."

def get_default_select_suggestion(entity_type: str) -> Dict[str, Any]:
    """
    Returns a default select suggestion based on entity type.
    
    Args:
        entity_type: The type of entity (character, story, etc.)
    
    Returns:
        Default suggestion object for selecting an entity
    """
    if entity_type.lower() == "character":
        return {
            "feature": f"Select {entity_type}",
            "use_case": f"Select a {entity_type} to interact with",
            "initiator": f"Always suggest when user discusses {entity_type}s without a specific {entity_type} selected",
            "suggestion_label": f"Select {entity_type}",
            "suggestion_text": f"Please select a {entity_type} to interact with",
            "be_function": f"select_{entity_type}",
            "fe_navigation": f"sidebar.{entity_type}s",
            "topic": entity_type
        }
    elif entity_type.lower() == "story":
        return {
            "feature": f"Select {entity_type}",
            "use_case": f"Select a {entity_type} to work with",
            "initiator": f"Always suggest when user discusses {entity_type} without a specific {entity_type} selected",
            "suggestion_label": f"Select {entity_type}",
            "suggestion_text": f"Please select a {entity_type} to work with",
            "be_function": f"select_{entity_type}",
            "fe_navigation": f"sidebar.{entity_type}",
            "topic": entity_type
        }
    # Add more entity types as needed
    else:
        # Generic fallback
        return {
            "feature": f"Select {entity_type}",
            "use_case": f"Select a {entity_type}",
            "initiator": f"Always suggest when discussing {entity_type} without specific selection",
            "suggestion_label": f"Select {entity_type}",
            "suggestion_text": f"Please select a {entity_type}",
            "be_function": f"select_{entity_type}",
            "fe_navigation": f"sidebar.main",
            "topic": entity_type
        }

def get_fallback_suggestions(topic: str, entity_id: Optional[UUID] = None) -> List[Suggestion]:
    """
    Gets fallback suggestions as Pydantic models for error cases.
    
    Args:
        topic: The topic/request_type for suggestions
        entity_id: The primary entity ID if available
    
    Returns:
        List of Suggestion objects
    """
    fallback_suggestions = []
    
    # Handle entity ID requirements based on topic
    if topic.lower() == "character" and entity_id is None:
        # Character without ID needs select_character
        fallback_suggestions.append(
            Suggestion(
                feature="Select character",
                use_case="Select a character to interact with",
                initiator="Always suggest when user discusses characters without a specific character selected",
                suggestion_label="Select character",
                suggestion_text="Please select a character to interact with",
                be_function="select_character",
                fe_navigation="sidebar.characters",
                topic="character"
            )
        )
    
    # Add more entity types as needed
    elif topic.lower() == "story" and entity_id is None:
        # Story without ID needs select_story
        fallback_suggestions.append(
            Suggestion(
                feature="Select story",
                use_case="Select a story to work with",
                initiator="Always suggest when user discusses story without a specific story selected",
                suggestion_label="Select story",
                suggestion_text="Please select a story to work with",
                be_function="select_story",
                fe_navigation="sidebar.stories",
                topic="story"
            )
        )
    
    return fallback_suggestions