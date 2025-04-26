import logging
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import Character, CharacterTrait # Import necessary models

logger = logging.getLogger(__name__)

# --- Suggestion Execution Functions ---

def add_trait_behavior(db: Session, project_id: UUID, character_id: UUID, **kwargs) -> str:
    """Adds a placeholder 'behavior' trait to a character."""
    logger.info(f"Executing 'add_trait_behavior' for character {character_id} in project {project_id}")
    if not character_id:
        return "Error: Cannot add trait without a character ID."

    character = db.query(Character).filter(Character.id == character_id, Character.project_id == project_id).first()
    if not character:
        return f"Error: Character with ID {character_id} not found in project {project_id}."

    # Check if a behavior trait already exists (optional, depends on desired logic)
    existing_trait = db.query(CharacterTrait).filter(
        CharacterTrait.character_id == character_id,
        CharacterTrait.type == 'behavior'
    ).first()

    if existing_trait:
        logger.warning(f"Character {character_id} already has a 'behavior' trait.")
        return f"Character '{character.name}' already has a behavior trait." # Or update it?

    try:
        # Create a new placeholder trait
        new_trait = CharacterTrait(
            character_id=character_id,
            type='behavior',
            label='Default Behavior', # Placeholder label
            description='[Please describe the typical behavior]' # Placeholder description
        )
        db.add(new_trait)
        db.commit()
        logger.info(f"Successfully added 'behavior' trait to character {character_id}.")
        return f"Added a placeholder 'behavior' trait for character '{character.name}'. You can now edit its details."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add 'behavior' trait for character {character_id}: {e}", exc_info=True)
        return f"Error: Failed to add behavior trait due to a database issue."

def add_trait_knowledge(db: Session, project_id: UUID, character_id: UUID, **kwargs) -> str:
    """Adds a placeholder 'knowledge' trait to a character."""
    logger.info(f"Executing 'add_trait_knowledge' for character {character_id} in project {project_id}")
    if not character_id:
        return "Error: Cannot add trait without a character ID."

    character = db.query(Character).filter(Character.id == character_id, Character.project_id == project_id).first()
    if not character:
        return f"Error: Character with ID {character_id} not found in project {project_id}."

    # Check if a knowledge trait already exists (optional)
    existing_trait = db.query(CharacterTrait).filter(
        CharacterTrait.character_id == character_id,
        CharacterTrait.type == 'knowledge'
    ).first()

    if existing_trait:
        logger.warning(f"Character {character_id} already has a 'knowledge' trait.")
        return f"Character '{character.name}' already has a knowledge trait."

    try:
        new_trait = CharacterTrait(
            character_id=character_id,
            type='knowledge',
            label='General Knowledge', # Placeholder
            description='[Please describe the character\'s knowledge]' # Placeholder
        )
        db.add(new_trait)
        db.commit()
        logger.info(f"Successfully added 'knowledge' trait to character {character_id}.")
        return f"Added a placeholder 'knowledge' trait for character '{character.name}'. You can now edit its details."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add 'knowledge' trait for character {character_id}: {e}", exc_info=True)
        return f"Error: Failed to add knowledge trait due to a database issue."

# --- Add more functions as needed ---
# def create_character(...)
# def update_story_overview(...)

# --- Executor Dispatcher ---

# Map function names (from suggestions) to actual functions
EXECUTOR_MAP = {
    "add_trait_behavior": add_trait_behavior,
    "add_trait_knowledge": add_trait_knowledge,
    # Add other mappings here
    # "create_character": create_character,
}

def execute_suggestion_function(
    function_name: str,
    db: Session,
    project_id: UUID,
    character_id: Optional[UUID] = None,
    # Add other potential context arguments needed by functions
    **kwargs
) -> str:
    """Looks up and executes the backend function corresponding to the suggestion."""
    if function_name in EXECUTOR_MAP:
        func = EXECUTOR_MAP[function_name]
        logger.info(f"Dispatching execution to function: {function_name}")
        try:
            # Pass necessary arguments. Ensure functions accept them or use **kwargs.
            result_message = func(
                db=db,
                project_id=project_id,
                character_id=character_id,
                # Pass any other relevant context if needed
                **kwargs
            )
            return result_message
        except Exception as e:
            logger.error(f"Error during execution of suggestion function '{function_name}': {e}", exc_info=True)
            return f"An unexpected error occurred while trying to execute '{function_name}'."
    else:
        logger.warning(f"No backend function found matching suggestion function name: '{function_name}'")
        return f"Error: Backend function '{function_name}' is not implemented."