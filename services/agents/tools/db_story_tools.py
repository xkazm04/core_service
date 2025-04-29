"""
Database lookup tools for story-related operations
"""
import logging
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import Project, Act, Beat, Scene

logger = logging.getLogger(__name__)

def db_story_lookup_tool(db: Session, project_id: UUID) -> str:
    """
    Retrieves the project overview and act descriptions for a given project.
    """
    logger.info(f"--- Running DB Story Lookup ---")
    logger.info(f"Project ID: {project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        logger.warning(f"Project with ID {project_id} not found for story lookup.")
        return f"Project with ID {project_id} not found."

    acts = db.query(Act).filter(Act.project_id == project_id).order_by(Act.order).all()

    # Format the result for the LLM
    result = f"Story Context for Project '{project.name}' (ID: {project_id}):\n"
    result += f"## Overview:\n{project.overview or 'No overview provided.'}\n"

    if acts:
        result += "\n## Acts:\n"
        for act in acts:
            result += f"- Act {act.order} ({act.name or 'Unnamed Act'}): {act.description or 'No description.'}\n"
    else:
        result += "\n## Acts:\nNo acts defined for this project yet.\n"

    logger.info(f"Story Lookup Result:\n{result}")
    return result

def db_beat_lookup_tool(db: Session, project_id: UUID) -> str:
    """
    Retrieves the story beats (objectives) and their completion status for a given project.
    """
    logger.info(f"--- Running DB Beat Lookup ---")
    logger.info(f"Project ID: {project_id}")

    beats = db.query(Beat).filter(Beat.project_id == project_id).order_by(Beat.order).all()
    if not beats:
        logger.warning(f"Beats with project ID {project_id} not found for beat lookup.")
        return f"No story beats (objectives) found for project ID {project_id}."

    # Format the result for the LLM
    result = f"Story Beats/Objectives for Project ID {project_id}:\n"
    for beat in beats:
        status = "Completed" if beat.completed else "Not Completed"
        result += f"- {beat.name or 'Unnamed Beat'}: {beat.description or 'No description.'} [{status}]\n"

    logger.info(f"Beat Lookup Result:\n{result}")
    return result

def db_scene_lookup_tool(db: Session, scene_id: UUID) -> str:
    """
    Retrieves the scene details for a given scene ID.
    """
    logger.info(f"--- Running DB Scene Lookup ---")
    logger.info(f"Scene ID: {scene_id}")

    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        logger.warning(f"Scene with ID {scene_id} not found for scene lookup.")
        return f"Scene with ID {scene_id} not found."

    # Format the result for the LLM
    result = f"Scene Details for Scene ID {scene_id}:\n"
    result += f"- Name: {scene.name or 'Unnamed Scene'}\n"
    result += f"- Description: {scene.description or 'No description provided.'}\n"

    logger.info(f"Scene Lookup Result:\n{result}")
    return result