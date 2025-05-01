"""
Database analysis tools for identifying improvement opportunities
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import Character, CharacterTrait, Act
from services.project_analysis import analyze_project_status

logger = logging.getLogger(__name__)

def db_gap_analysis_tool(db: Session, project_id: UUID, topic: str, character_id: Optional[UUID] = None) -> str:
    """
    Analyzes project components for gaps that should be improved.
    
    For characters: Checks if all essential trait types exist
    For story: Checks for acts with missing descriptions
    """
    logger.info(f"--- Running DB Gap Analysis Tool ---")
    logger.info(f"Project ID: {project_id}, Topic: {topic}, Character ID: {character_id}")
    
    # Use analyze_project_status to get comprehensive project data
    try:
        project_data = analyze_project_status(db, project_id)
    except ValueError as e:
        logger.error(f"Error retrieving project data: {str(e)}")
        return f"Error: {str(e)}"
    
    result = f"Gap Analysis for {topic}:\n\n"
    
    if topic.lower() == 'character':
        return analyze_character_gaps(db, project_data, character_id, result)
    elif topic.lower() == 'story':
        return analyze_story_gaps(db, project_data, project_id, result)
    elif topic.lower() == 'project':
        return analyze_project_gaps(project_data, result)
    else:
        result = f"Gap analysis for topic '{topic}' is not currently supported. " \
                 f"Supported topics are 'character', 'story', and 'project'."
    
    logger.info(f"Gap Analysis Result:\n{result}")
    return result

def analyze_character_gaps(db: Session, project_data: Dict[str, Any], character_id: Optional[UUID], result: str) -> str:
    """Analyze gaps in character development"""
    if not character_id:
        # If no specific character requested, analyze all characters
        if not project_data["characters"]:
            return result + "No characters found in this project."
        
        incomplete_characters = []
        for char in project_data["characters"]:
            if char["traits_filled"] < char["traits_needed"]:
                incomplete_characters.append(char)
        
        if incomplete_characters:
            result += f"The following characters need more trait development:\n"
            for char in incomplete_characters:
                missing = char["traits_needed"] - char["traits_filled"]
                result += f"- {char['character_name']}: has {char['traits_filled']} traits, needs {missing} more\n"
            result += "\nDeveloping these characters will create a more engaging story."
        else:
            result += "All characters have the recommended minimum number of traits. Great job!\n"
            
        return result
    else:
        # Specific character analysis with trait types
        # First check if character exists in the project
        character_exists = False
        for char in project_data["characters"]:
            if str(char["character_id"]) == str(character_id):
                character_exists = True
                break
        
        if not character_exists:
            return f"Character with ID {character_id} not found in this project."
        
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
                
        return result

def analyze_story_gaps(db: Session, project_data: Dict[str, Any], project_id: UUID, result: str) -> str:
    """Analyze gaps in story structure and scenes"""
    # Check scenes first
    if not project_data["scenes"]:
        result += "No scenes found in this project. Consider creating scenes to develop your story.\n"
    else:
        scenes_without_description = [scene for scene in project_data["scenes"] if not scene["has_description"]]
        scenes_without_act = [scene for scene in project_data["scenes"] if not scene["act_name"]]
        
        if scenes_without_description:
            result += "The following scenes need descriptions:\n"
            for scene in scenes_without_description:
                result += f"- {scene['scene_name']}\n"
            result += "\nAdding descriptions to these scenes will improve your story clarity.\n"
        
        if scenes_without_act:
            result += "\nThe following scenes are not assigned to any act:\n"
            for scene in scenes_without_act:
                result += f"- {scene['scene_name']}\n"
            result += "\nAssigning scenes to acts helps organize your story structure.\n"
    
    # Check acts
    acts = db.query(Act).filter(Act.project_id == project_id).order_by(Act.order).all()
    
    if not acts:
        result += "No acts found for this project. Consider creating an act structure for your story."
    else:
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
    
    return result

def analyze_project_gaps(project_data: Dict[str, Any], result: str) -> str:
    """Analyze overall project completion status"""
    # Check project fields
    missing_fields = [field for field, is_filled in project_data["project_fields"].items() if not is_filled]
    
    if missing_fields:
        result += "Your project is missing the following important details:\n"
        for field in missing_fields:
            result += f"- {field.replace('_', ' ').capitalize()}\n"
        result += "\nFilling these fields will help define your project's direction.\n"
    else:
        result += "All core project fields are filled. Great job setting up your project!\n"
    
    # Check character development
    total_chars = len(project_data["characters"])
    complete_chars = sum(1 for char in project_data["characters"] 
                        if char["traits_filled"] >= char["traits_needed"])
    
    result += f"\nCharacter Development: {complete_chars}/{total_chars} characters fully developed"
    
    if total_chars > 0:
        completion_percentage = (complete_chars / total_chars) * 100
        result += f" ({completion_percentage:.1f}%)\n"
    else:
        result += "\nNo characters found in this project. Consider adding characters to your story.\n"
    
    # Check beat completion
    beats = project_data["beats"]
    if beats["total"] > 0:
        beat_percentage = (beats["completed"] / beats["total"]) * 100
        result += f"\nStory Beats: {beats['completed']}/{beats['total']} completed ({beat_percentage:.1f}%)"
        
        if beat_percentage < 50:
            result += "\nYour story beats need more work to complete the narrative structure."
        elif beat_percentage < 80:
            result += "\nYou're making good progress on your story beats."
        else:
            result += "\nYour story beats are well developed!"
    else:
        result += "\nNo story beats found in this project. Consider adding beats to structure your story."
    
    return result