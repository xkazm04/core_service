"""
Database lookup tools for character-related operations
"""
from typing import Optional
from uuid import UUID
import logging
from sqlalchemy.orm import Session, joinedload
from models.models import Character

logger = logging.getLogger(__name__)

def db_character_lookup_tool(
    db: Session,
    project_id: UUID,
    character_id: Optional[UUID] = None,
    character_name: Optional[str] = None
) -> str:
    """
    Retrieves details for a specific character within a project,
    identified by ID or name. Fetches character info and traits.
    """
    logger.info(f"--- Running DB Character Lookup ---")
    logger.info(f"Project ID: {project_id}, Character ID: {character_id}, Character Name: {character_name}")

    query = db.query(Character).options(joinedload(Character.trait)) # Eager load traits

    if character_id:
        character = query.filter(
            Character.project_id == project_id,
            Character.id == character_id
        ).first()
    elif character_name:
        # Use exact match first for potentially better performance/accuracy if names are unique
        character = query.filter(
            Character.project_id == project_id,
            Character.name == character_name # Case-sensitive exact match
        ).first()
        # Fallback to case-insensitive search if exact match fails
        if not character:
            logger.info(f"Exact match for '{character_name}' failed, trying case-insensitive search.")
            character = query.filter(
                Character.project_id == project_id,
                Character.name.ilike(f"%{character_name}%") # Case-insensitive search
            ).first()

        if character:
            logger.info(f"Found character by name: {character.name} (ID: {character.id})")
        else:
             logger.warning(f"Character '{character_name}' not found by name in project {project_id}.")
    else:
        logger.error("Character lookup tool called without character_id or character_name.")
        return "Error: Character lookup requires either character_id or character_name."

    if not character:
        return f"Character not found for Project {project_id} with given ID/Name."

    # Format the result for the LLM
    result = f"Character Details for '{character.name}' (ID: {character.id}):\n"
    result += f"- Type: {character.type or 'N/A'}\n"
    result += f"- Description: {character.description or 'N/A'}\n"
    result += f"- Voice: {character.voice or 'N/A'}\n"
    
    # Safely access faction name if relationship exists and is loaded/accessible
    try:
        if character.faction:
             result += f"- Faction: {character.faction.name}\n"
    except Exception as e:
        logger.warning(f"Could not access faction name for character {character.id}: {e}")
        result += f"- Faction: Error accessing faction info\n"

    if character.trait:
        result += "- Traits:\n"
        for trait in character.trait:
            result += f"  - {trait.type} ({trait.label or 'General'}): {trait.description}\n"
    else:
        result += "- Traits: None defined.\n"

    logger.info(f"Character Lookup Result:\n{result}")
    return result