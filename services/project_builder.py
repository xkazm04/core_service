from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import List, Optional
from schemas.project import ProjectSchema
from schemas.beat import BeatCreate
from schemas.character import CharacterCreate
from database import get_db
from models.models import Project, Character, Act, Faction, FactionRelationship
from services.beats import create_beat
from data.beatsDefault import default_beats
from data.factionsDefault import default_factions, default_faction_relationships

# Configure logging
logger = logging.getLogger(__name__)

def create_project(
    project_data: ProjectSchema, 
    db: Session = Depends(get_db),
    custom_characters: Optional[List[CharacterCreate]] = None,
    custom_beats: Optional[List[BeatCreate]] = None  # Changed from List[str] to List[BeatCreate]
):
    """
    Creates a new project with default associated data and optional custom elements.
    Args:
        project_data: Project schema containing required project information
        db: Database session
        custom_characters: Optional list of custom characters to create
        custom_beats: Optional list of custom beat names to create
    Returns:
        Project: The created project object
    Raises:
        HTTPException: If project creation fails
    """
    try:
    # 1. Create project (mandatory)
        project = Project(
            name=project_data.name,
            user=project_data.user,
            type=project_data.type,
            overview=project_data.overview,
            genre=project_data.genre,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

    # Optional elements - continue even if these fail
    # 2. Create narrator character
    try:
        character = Character(
            name="Narrator",
            project_id=project.id,
            type="Narrator",
        )
        db.add(character)
        db.commit()
        db.refresh(character)
        logger.info(f"Created narrator character for project {project.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create narrator character: {str(e)}")
        
    # 3. Create characters from user input if provided
    if custom_characters:
        for char_data in custom_characters:
            # Skip characters with empty names
            if not char_data.name or char_data.name.strip() == "":
                logger.info(f"Skipping character with empty name for project {project.id}")
                continue
                
            try:
                character = Character(
                    name=char_data.name,
                    type=char_data.type,
                    project_id=project.id
                )
                db.add(character)
                db.commit()
                db.refresh(character)
                logger.info(f"Created custom character '{char_data.name}' for project {project.id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to create custom character '{char_data.name}': {str(e)}")
    
    # 4. Create first act
    act = None
    try:
        act = Act(
            project_id=project.id,
            name="Act 1",
            order=1,
            description="First act of the story"
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        logger.info(f"Created Act 1 for project {project.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create Act 1: {str(e)}")
    
    # 5. Create default beats if act was created successfully
    if act:
        for beat_data in default_beats:
            try:
                beat = BeatCreate(
                    name=beat_data["name"],
                    project_id=project.id,
                    type=beat_data["type"],
                    description=beat_data["description"],
                    order=beat_data["order"],
                    default_flag=beat_data["default_flag"]
                )
                create_beat(beat, db)
                logger.info(f"Created beat '{beat_data['name']}' for Act 1")
            except Exception as e:
                logger.error(f"Failed to create beat '{beat_data['name']}': {str(e)}")
                
    # 6. Create beats from user input if provided
    if act and custom_beats:
        # Start with the order after default beats
        start_order = len(default_beats) + 1
        
        for i, beat_data in enumerate(custom_beats):
            # Skip beats with empty names
            if not beat_data.name or beat_data.name.strip() == "":
                logger.info(f"Skipping beat with empty name for project {project.id}")
                continue
                
            try:
                beat = BeatCreate(
                    project_id=project.id,
                    name=beat_data.name,
                    type='act', 
                    order=start_order + i,
                    default_flag=False
                )
                create_beat(beat, db)
                logger.info(f"Created custom beat '{beat_data.name}' for Act 1")
            except Exception as e:
                logger.error(f"Failed to create custom beat '{beat_data.name}': {str(e)}")
    
    # 7. Create default factions
    faction_map = {}  # To map faction names to IDs for relationship creation
    for faction_data in default_factions:
        try:
            faction = Faction(
                name=faction_data["name"],
                description=faction_data["description"],
                project_id=project.id,
                image_url=faction_data["image_url"],
                color=faction_data["color"]
            )
            db.add(faction)
            db.commit()
            db.refresh(faction)
            faction_map[faction_data["name"]] = faction.id
            logger.info(f"Created faction '{faction_data['name']}' for project {project.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create faction '{faction_data['name']}': {str(e)}")
    
    # 8. Create faction relationships using the actually created faction IDs
    if act and len(faction_map) >= 2:
        try:
            for relationship_data in default_faction_relationships:
                # Get the faction names from the relationship data
                faction_a_name = None
                faction_b_name = None
                
                # Find faction names by looking up the IDs in default_factions
                for faction in default_factions:
                    if relationship_data.get("faction_a_id") == faction.get("id", str(default_factions.index(faction) + 1)):
                        faction_a_name = faction["name"]
                    if relationship_data.get("faction_b_id") == faction.get("id", str(default_factions.index(faction) + 1)):
                        faction_b_name = faction["name"]
                
                # If faction names weren't found or factions weren't created, skip this relationship
                if not faction_a_name or not faction_b_name or \
                   faction_a_name not in faction_map or faction_b_name not in faction_map:
                    logger.warning(f"Skipping relationship - missing faction reference")
                    continue
                
                relationship = FactionRelationship(
                    faction_a_id=faction_map[faction_a_name],
                    faction_b_id=faction_map[faction_b_name],
                    relationship_type=relationship_data["relationship_type"],
                    event=relationship_data["event"],
                    event_act_id=act.id
                )
                db.add(relationship)
                db.commit()
                db.refresh(relationship)
                logger.info(f"Created relationship between '{faction_a_name}' and '{faction_b_name}'")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create faction relationship: {str(e)}")
    
    return project