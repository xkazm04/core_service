from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from uuid import UUID
from schemas.project import ProjectSchema
from schemas.beat import BeatCreate
from database import get_db
from models.models import Project, Character, Act, Faction, FactionRelationship
from services.beats import create_beat
from data.beatsDefault import default_beats
from data.factionsDefault import default_factions, default_faction_relationships

# Configure logging
logger = logging.getLogger(__name__)

def create_project(project_data: ProjectSchema, db: Session = Depends(get_db)):
    """
    Creates a new project with default associated data.
    Args:
        project_data: Project schema containing required project information
        db: Database session
    Returns:
        Project: The created project object
    Raises:
        HTTPException: If project creation fails
    """
    try:
        # Create project (mandatory)
        project = Project(
            name=project_data.name,
            user=project_data.user,
            type=project_data.type,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

    # Optional elements - continue even if these fail
    # Create narrator character
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
    
    # Create first act
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
    
    # Create default beats if act was created successfully
    if act:
        for beat_data in default_beats:
            try:
                beat = BeatCreate(
                    name=beat_data["name"],
                    act_id=act.id,
                    type=beat_data["type"],
                    description=beat_data["description"],
                    order=beat_data["order"],
                    default_flag=beat_data["default_flag"]
                )
                create_beat(beat, db)
                logger.info(f"Created beat '{beat_data['name']}' for Act 1")
            except Exception as e:
                logger.error(f"Failed to create beat '{beat_data['name']}': {str(e)}")
    
    # Create default factions
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
    
    # Create faction relationships using the actually created faction IDs
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