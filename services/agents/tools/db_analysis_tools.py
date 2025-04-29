"""
Database analysis tools for identifying improvement opportunities
"""
import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import Character, CharacterTrait, Act

logger = logging.getLogger(__name__)

def db_gap_analysis_tool(db: Session, project_id: UUID, topic: str, character_id: Optional[UUID] = None) -> str:
    """
    Analyzes project components for gaps that should be improved.
    
    For characters: Checks if all essential trait types exist
    For story: Checks for acts with missing descriptions
    """
    logger.info(f"--- Running DB Gap Analysis Tool ---")
    logger.info(f"Project ID: {project_id}, Topic: {topic}, Character ID: {character_id}")
    
    result = f"Gap Analysis for {topic}:\n\n"
    
    if topic.lower() == 'character':
        if not character_id:
            return "Cannot analyze character gaps without a character_id. Please specify a character."
        
        # Get the character to confirm it exists
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            return f"Character with ID {character_id} not found."
        
        # Define the essential trait types that should be present
        essential_trait_types = ['knowledge', 'personality', 'humor', 'communication', 'background']
        
        # Query for existing trait types for this character
        existing_traits = db.query(CharacterTrait).filter(
            CharacterTrait.character_id == character_id
        ).all()
        
        # Create a set of existing trait types for easy lookup
        existing_trait_types = {trait.type.lower() for trait in existing_traits}
        
        # Find missing trait types
        missing_trait_types = [t for t in essential_trait_types if t.lower() not in existing_trait_types]
        
        if missing_trait_types:
            result += f"Character '{character.name}' is missing the following important traits:\n"
            for trait_type in missing_trait_types:
                result += f"- {trait_type.capitalize()} trait\n"
            
            result += "\nDeveloping these traits will help create a more well-rounded character."
        else:
            result += f"Character '{character.name}' has all essential trait types defined. Good job!\n"
            
        # Also provide info about existing traits
        if existing_traits:
            result += "\nExisting traits:\n"
            for trait in existing_traits:
                result += f"- {trait.type}: {trait.label or 'No label'} - {trait.description or 'No description'}\n"
    
    elif topic.lower() == 'story':
        # Get all acts for this project
        acts = db.query(Act).filter(Act.project_id == project_id).order_by(Act.order).all()
        
        if not acts:
            return "No acts found for this project. Consider creating an act structure for your story."
        
        # Find acts with missing descriptions
        incomplete_acts = [act for act in acts if not act.description]
        
        if incomplete_acts:
            result += "The following acts need descriptions:\n"
            for act in incomplete_acts:
                result += f"- Act {act.order}: {act.name}\n"
            
            result += "\nAdding descriptions to these acts will improve your story structure."
        else:
            result += "All acts in your project have descriptions. Great job on your story structure!\n"
        
        # Summary of existing acts
        result += f"\nYour project has {len(acts)} acts in total."
    
    else:
        result = f"Gap analysis for topic '{topic}' is not currently supported. " \
                 f"Supported topics are 'character' and 'story'."
    
    logger.info(f"Gap Analysis Result:\n{result}")
    return result