import logging
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional
from services.agents.executors.character_executors import add_trait_behavior, character_create, character_rename, relationship_add
from services.agents.executors.faction_executors import faction_create, faction_rename
from services.agents.executors.story_executors import act_create, act_edit, beat_create, beat_edit

logger = logging.getLogger(__name__)

EXECUTOR_MAP = {
    # Character executors
    "character_create": character_create,
    "character_rename": character_rename,
    "relationship_add": relationship_add,
    "trait_add": add_trait_behavior,
    # Faction executors
    "faction_create": faction_create,
    "faction_rename": faction_rename,
    # Story executors
    "act_create": act_create,
    "act_edit": act_edit,
    "beat_create": beat_create,
    "beat_edit": beat_edit,
}

def execute_suggestion_function(
    function_name: str,
    db: Session,
    project_id: UUID,
    character_id: Optional[UUID] = None,
    **kwargs
) -> str:
    """Looks up and executes the backend function corresponding to the suggestion."""
    logger.info(f"Executing function '{function_name}' with params: {kwargs}")
    
    if function_name in EXECUTOR_MAP:
        func = EXECUTOR_MAP[function_name]
        logger.info(f"Dispatching execution to function: {function_name}")
        
        try:
            # Pass necessary arguments. Ensure functions accept them or use **kwargs.
            result_message = func(
                db=db,
                project_id=project_id,
                character_id=character_id,
                **kwargs
            )
            return result_message
        except Exception as e:
            logger.error(f"Error during execution of suggestion function '{function_name}': {e}", exc_info=True)
            return f"An unexpected error occurred while trying to execute '{function_name}'."
    else:
        logger.warning(f"No backend function found matching suggestion function name: '{function_name}'")
        return f"Error: Backend function '{function_name}' is not implemented."