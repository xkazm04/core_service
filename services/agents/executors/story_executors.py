import logging
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import Act, Scene, Beat
import logging
logger = logging.getLogger(__name__)

# *kwargs: Optional parameters for character creation
# - act_id: ID of the act (for relationship creation)
# - act_name: Name of the act (default: 'Unnamed Act')
# - act_description: Description of the act (default: '[Please describe the act]')
# - beat_id: ID of the beat (for relationship creation)
# - beat_name: Name of the beat (default: 'Unnamed Beat')
# - beat_description: Description of the beat (default: '[Please describe the beat]')

def act_create(db: Session, project_id: UUID, **kwargs) -> str:
    """
    Adds an act to the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - **kwargs: Additional parameters for act creation
        - act_name: Name of the act (default: 'Unnamed Act')
        - act_description: Description of the act (default: '[Please describe the act]')
    """
    logger.info(f"Executing 'act_create' for project {project_id}")

    # Create a new act with provided parameters or defaults
    try:
        name = kwargs.get('act_name', 'Unnamed Act')
        description = kwargs.get('act_description', '[Please describe the act]')

        new_act = Act(
            project_id=project_id,
            name=name,
            description=description,
        )
        db.add(new_act)
        db.commit()
        logger.info(f"Successfully added new act '{name}' to project {project_id}.")
        return f"Added new act '{name}' to the project."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add new act to project {project_id}: {e}", exc_info=True)
        return f"Error: Failed to add new act due to a database issue."
    
def act_edit(db: Session, project_id: UUID, **kwargs) -> str:
    """
    Edits an act in the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - **kwargs: Additional parameters for act editing
        - act_id: ID of the act to edit
        - act_description: New description for the act (default: '[Please describe the act]')
    """
    logger.info(f"Executing 'act_edit' for project {project_id}")

    # Check if the act exists in the project
    act_id = kwargs.get('act_id')
    if not act_id:
        return "Error: Cannot edit act without an act ID."

    # Check if the act exists in the project
    act = db.query(Act).filter(
        Act.id == act_id,
        Act.project_id == project_id
    ).first()

    if not act:
        return f"Error: Act with ID {act_id} not found in project {project_id}."

    # Edit the act with provided parameters or defaults
    try:
        new_description = kwargs.get('act_description')
        act.description = new_description
        db.commit()
        logger.info(f"Successfully edited act '{act.name}' in project {project_id}.")
        return f"Edited act '{act.name}'."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to edit act {act_id}: {e}", exc_info=True)
        return f"Error: Failed to edit act due to a database issue."
    
def beat_create(db: Session, project_id: UUID, **kwargs) -> str:
    """
    Adds a beat to the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - **kwargs: Additional parameters for beat creation
        - beat_name: Name of the beat (default: 'Unnamed Beat')
        - beat_description: Description of the beat (default: '[Please describe the beat]')
    """
    logger.info(f"Executing 'beat_create' for project {project_id}")

    # Create a new beat with provided parameters or defaults
    try:
        name = kwargs.get('beat_name', 'Unnamed Beat')
        description = kwargs.get('beat_description', '[Please describe the beat]')

        new_beat = Beat(
            project_id=project_id,
            name=name,
            description=description,
        )
        db.add(new_beat)
        db.commit()
        logger.info(f"Successfully added new beat '{name}' to project {project_id}.")
        return f"Added new beat '{name}' to the project."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add new beat to project {project_id}: {e}", exc_info=True)
        return f"Error: Failed to add new beat due to a database issue."
    
def beat_edit(db: Session, project_id: UUID, **kwargs) -> str:
    """
    Edits a beat in the project.
    
    Parameters:
    - db: Database session
    - project_id: UUID of the project
    - **kwargs: Additional parameters for beat editing
        - beat_id: ID of the beat to edit
        - beat_description: New description for the beat (default: '[Please describe the beat]')
    """
    logger.info(f"Executing 'beat_edit' for project {project_id}")

    # Check if the beat exists in the project
    beat_id = kwargs.get('beat_id')
    if not beat_id:
        return "Error: Cannot edit beat without a beat ID."

    # Check if the beat exists in the project
    beat = db.query(Beat).filter(
        Beat.id == beat_id,
        Beat.project_id == project_id
    ).first()

    if not beat:
        return f"Error: Beat with ID {beat_id} not found in project {project_id}."

    # Edit the beat with provided parameters or defaults
    try:
        new_description = kwargs.get('beat_description')
        beat.description = new_description
        db.commit()
        logger.info(f"Successfully edited beat '{beat.name}' in project {project_id}.")
        return f"Edited beat '{beat.name}'."
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to edit beat {beat_id}: {e}", exc_info=True)
        return f"Error: Failed to edit beat due to a database issue."
