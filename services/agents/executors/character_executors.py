import logging
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import Character, CharacterTrait, CharacterRelationshipEvent
import logging
logger = logging.getLogger(__name__)

# *kwargs: Optional parameters for character creation
# - target_char_name: Name of the character (default: 'Unnamed Character')
# - target_char_type: Type of the character (default: 'Unknown')
# - trait_type: Type of the trait (behavior, humor, speech, knowledge, communication)
# - trait_description: Description of the trait (default: '[Please describe the typical behavior]')
# - secondary_character_id: ID of the secondary character (for relationship creation)
# - relationship_type: Type of relationship (default: 'friend')
# - relationship_description: Description of the relationship (default: '[Please describe the relationship]')

def character_create(db: Session, project_id: UUID, **kwargs) -> str:
    """
    Adds a character to the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - **kwargs: Additional parameters for character creation
        - target_char_name: Name of the character
    """
    logger.info(f"Executing 'character_create' for project {project_id}")

    # Create a new character with provided parameters or defaults
    try:
        name = kwargs.get('target_char_name')

        new_character = Character(
            project_id=project_id,
            name=name,
            type='major',
        )
        # Validate existing character names in the project
        existing_character = db.query(Character).filter(
            Character.project_id == project_id,
            Character.name == name
        ).first()
        if existing_character:
            logger.warning(f"Character name '{name}' already exists in project {project_id}.")
            return f"Error: Character name '{name}' already exists in this project."
        db.add(new_character)
        db.commit()
        logger.info(f"Successfully added new character '{name}' to project {project_id}.")
        return f"Added new character '{name}' to the project."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add new character to project {project_id}: {e}", exc_info=True)
        return f"Error: Failed to add new character due to a database issue."
    
def character_rename(db: Session, project_id: UUID, character_id: UUID, **kwargs) -> str:
    """
    Renames a character in the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - character_id: UUID of the character
    - **kwargs: Additional parameters for renaming
        - target_char_name: New name for the character (default: 'Unnamed Character')
    """
    logger.info(f"Executing 'character_rename' for character {character_id} in project {project_id}")
    if not character_id:
        return "Error: Cannot rename character without a character ID."

    # Check if the character exists in the project
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.project_id == project_id
    ).first()

    if not character:
        return f"Error: Character with ID {character_id} not found in project {project_id}."

    # Rename the character with provided parameters or defaults
    try:
        new_name = kwargs.get('target_char_name', 'Unnamed Character')
        character.name = new_name
        db.commit()
        logger.info(f"Successfully renamed character to '{new_name}' in project {project_id}.")
        return f"Renamed character to '{new_name}'."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to rename character {character_id}: {e}", exc_info=True)
        return f"Error: Failed to rename character due to a database issue."

def add_trait_behavior(db: Session, project_id: UUID, character_id: UUID, **kwargs) -> str:
    """
    Adds a behavior trait to a character.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - character_id: UUID of the character
    - **kwargs: Additional parameters
        - trait_type: Optional custom label for the trait (default: 'Default Behavior')
        - trait_description: Optional custom description (default: '[Please describe the typical behavior]')
    """
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
        # If trait exists and update parameters provided, update the trait
        if 'trait_type' in kwargs or 'trait_description' in kwargs:
            try:
                if 'trait_type' in kwargs:
                    existing_trait.type = kwargs['trait_type']
                if 'trait_description' in kwargs:
                    existing_trait.description = kwargs['trait_description']
                db.commit()
                logger.info(f"Updated existing 'behavior' trait for character {character_id}.")
                return f"Updated behavior trait for character '{character.name}'."
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to update 'behavior' trait: {e}", exc_info=True)
                return f"Error: Failed to update behavior trait due to a database issue."
        else:
            logger.warning(f"Character {character_id} already has a 'behavior' trait.")
            return f"Character '{character.name}' already has a behavior trait." 

    try:
        # Get label and description from kwargs or use defaults
        trait_description = kwargs.get('trait_description', '[Please describe the typical behavior]')
        trait_type = kwargs.get('trait_type', 'behavior')
        
        # Create a new trait with provided parameters
        new_trait = CharacterTrait(
            character_id=character_id,
            type=trait_type,
            description=trait_description
        )
        db.add(new_trait)
        db.commit()
        logger.info(f"Successfully added 'behavior' trait to character {character_id}.")
        return f"Added a '{trait_type}' behavior trait for character '{character.name}'."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add 'behavior' trait for character {character_id}: {e}", exc_info=True)
        return f"Error: Failed to add behavior trait due to a database issue."
    
def relationship_add(db: Session, project_id: UUID, character_id: UUID, **kwargs) -> str:
    """
    Adds a relationship between two characters.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - character_id: UUID of the primary character
    - **kwargs: Additional parameters
        - secondary_character_id: ID of the secondary character (required)
        - relationship_type: Type of relationship (default: 'friend')
        - relationship_description: Description of the relationship (default: '[Please describe the relationship]')
    """
    logger.info(f"Executing 'relationship_add' for character {character_id} in project {project_id}")
    if not character_id:
        return "Error: Cannot add relationship without a character ID."

    # Check if the primary character exists in the project
    primary_character = db.query(Character).filter(
        Character.id == character_id,
        Character.project_id == project_id
    ).first()

    if not primary_character:
        return f"Error: Primary character with ID {character_id} not found in project {project_id}."

    # Get secondary character ID from kwargs
    secondary_character_id = kwargs.get('secondary_character_id')
    if not secondary_character_id:
        return "Error: Cannot add relationship without a secondary character ID."

    # Check if the secondary character exists in the project
    secondary_character = db.query(Character).filter(
        Character.id == secondary_character_id,
        Character.project_id == project_id
    ).first()

    if not secondary_character:
        return f"Error: Secondary character with ID {secondary_character_id} not found in project {project_id}."
    
    try:
        # Get relationship type and description from kwargs or use defaults
        relationship_type = kwargs.get('relationship_type', 'friend')
        relationship_description = kwargs.get('relationship_description', '[Please describe the relationship]')
        
        # Create a new relationship event with provided parameters
        new_relationship = CharacterRelationshipEvent(
            character_id=character_id,
            related_character_id=secondary_character_id,
            type=relationship_type,
            description=relationship_description
        )
        db.add(new_relationship)
        db.commit()
        logger.info(f"Successfully added relationship between {primary_character.name} and {secondary_character.name}.")
        return f"Added a '{relationship_type}' relationship between '{primary_character.name}' and '{secondary_character.name}'."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add relationship between {primary_character.name} and {secondary_character.name}: {e}", exc_info=True)
        return f"Error: Failed to add relationship due to a database issue."