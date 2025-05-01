from fastapi import APIRouter
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID
from models.models import Project, Beat, Act, Scene, Character, CharacterTrait


# Create the router
router = APIRouter(
    prefix="/projects",
    tags=["project-analysis"]
)

# Pydantic models for request and response

def analyze_project_status(db: Session, project_id: UUID) -> Dict[str, Any]:
    """
    Analyze the current state of a project and return a summary of its completion status.
    
    Args:
        db (Session): SQLAlchemy database session
        project_id (UUID): The UUID of the project to analyze
        
    Returns:
        Dict[str, Any]: A dictionary containing the analysis results with the following structure:
        {
            "project_id": UUID,
            "project_fields": {
                "genre": bool,
                "concept": bool,
                "overview": bool,
                "time_period": bool,
                "audience": bool,
                "setting": bool
            },
            "characters": [
                {
                    "character_id": UUID,
                    "character_name": str,
                    "traits_filled": int,
                    "traits_needed": int
                },
                ...
            ],
            "scenes": [
                {
                    "scene_id": UUID,
                    "scene_name": str,
                    "act_name": Optional[str],
                    "has_description": bool
                },
                ...
            ],
            "beats": {
                "completed": int,
                "total": int
            }
        }
    """
    result = {
        "project_id": project_id,
        "project_fields": {},
        "characters": [],
        "scenes": [],
        "beats": {}
    }
    
    # 1. Check if Project fields are filled
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project with ID {project_id} not found")
    
    fields_to_check = ["genre", "concept", "overview", "time_period", "audience", "setting"]
    for field in fields_to_check:
        field_value = getattr(project, field)
        result["project_fields"][field] = bool(field_value and field_value.strip())
    
    # 2. Check if each Character has at least 5 traits
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    for character in characters:
        traits_count = db.query(CharacterTrait).filter(CharacterTrait.character_id == character.id).count()
        result["characters"].append({
            "character_id": character.id,
            "character_name": character.name,
            "traits_filled": traits_count,
            "traits_needed": 5
        })
    
    # 3. Check if each Scene has a description, and pair with Act
    scenes = db.query(Scene).filter(Scene.project_id == project_id).all()
    acts = {act.id: act.name for act in db.query(Act).filter(Act.project_id == project_id).all()}
    
    for scene in scenes:
        act_name = acts.get(scene.act_id) if scene.act_id else None
        result["scenes"].append({
            "scene_id": scene.id,
            "scene_name": scene.name,
            "act_name": act_name,
            "has_description": bool(scene.description and scene.description.strip())
        })
    
    # 4. Calculate Beat completion statistics
    beats = db.query(Beat).filter(Beat.project_id == project_id).all()
    completed_beats = sum(1 for beat in beats if beat.completed)
    total_beats = len(beats)
    
    result["beats"] = {
        "completed": completed_beats,
        "total": total_beats
    }
    
    return result

