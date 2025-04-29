import logging
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import Faction
import logging
logger = logging.getLogger(__name__)

# *kwargs: Optional parameters for character creation
# - faction_id: ID of the faction to be added (default: None)
# - faction_name: Name of the faction (default: 'Unnamed Faction')
# - faction_description: Description of the faction (default: '[Please describe the faction]')
    
def faction_create(db: Session, project_id: UUID, **kwargs) -> str:
    """
    Adds a faction to the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - **kwargs: Additional parameters for faction creation
        - faction_name: Name of the faction (default: 'Unnamed Faction')
        - faction_description: Description of the faction (default: '[Please describe the faction]')
    """
    logger.info(f"Executing 'faction_create' for project {project_id}")

    # Create a new faction with provided parameters or defaults
    try:
        name = kwargs.get('faction_name', 'Unnamed Faction')
        description = kwargs.get('faction_description', '[Please describe the faction]')

        new_faction = Faction(
            project_id=project_id,
            name=name,
            description=description,
        )
        db.add(new_faction)
        db.commit()
        logger.info(f"Successfully added new faction '{name}' to project {project_id}.")
        return f"Added new faction '{name}' to the project."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add new faction to project {project_id}: {e}", exc_info=True)
        return f"Error: Failed to add new faction due to a database issue."
    
def faction_rename(db: Session, project_id: UUID, **kwargs) -> str:
    """
    Renames a faction in the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - **kwargs: Additional parameters for renaming
        - faction_id: ID of the faction to be renamed (default: None)
        - faction_name: New name for the faction (default: 'Unnamed Faction')
    """
    faction_id = kwargs.get('faction_id')
    logger.info(f"Executing 'faction_rename' for faction {faction_id} in project {project_id}")
    if not faction_id:
        return "Error: Cannot rename faction without a faction ID."

    # Check if the faction exists in the project
    faction = db.query(Faction).filter(
        Faction.id == faction_id,
        Faction.project_id == project_id
    ).first()

    if not faction:
        return f"Error: Faction with ID {faction_id} not found in project {project_id}."

    # Rename the faction with provided parameters or defaults
    try:
        new_name = kwargs.get('faction_name', 'Unnamed Faction')
        faction.name = new_name
        db.commit()
        logger.info(f"Successfully renamed faction to '{new_name}' in project {project_id}.")
        return f"Renamed faction to '{new_name}'."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to rename faction {faction_id}: {e}", exc_info=True)
        return f"Error: Failed to rename faction due to a database issue."  