from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Scene, Line
from pydantic import BaseModel
from typing import List, Optional
from schemas.scene import SceneBase, SceneCreate, SceneUpdate, SceneResponse, SceneReorder
router = APIRouter(tags=["Scenes"])

# Pydantic Models for Response

@router.post("/", response_model=SceneResponse)
def create_scene(scene_data: SceneCreate, db: Session = Depends(get_db)):
    scene = Scene(**scene_data.dict())
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return {"message": "Scene created successfully", "scene": scene}


@router.put("/{scene_id}", response_model=SceneResponse)
def update_scene_name(scene_id: str, scene_update: SceneUpdate, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    scene.name = scene_update.name

    db.commit()
    db.refresh(scene)
    return {"message": "Scene updated successfully", "scene": scene}


@router.post("/reorder", response_model=SceneResponse)
def reorder_scene(scene_data: SceneReorder, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_data.scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    current_order = scene.order  # Old position
    project_id = scene.project_id
    act = scene.act

    if current_order == scene_data.new_order:
        return {"message": "No reordering needed", "scene": scene}

    # Fetch all scenes within the same project and act, ordered by current order
    scenes = (
        db.query(Scene)
        .filter(Scene.act == act, Scene.project_id == project_id)
        .order_by(Scene.order)
        .all()
    )

    # Reordering Logic: Shift affected scenes
    if current_order < scene_data.new_order:  # Moving scene **down**
        for s in scenes:
            if current_order < s.order <= scene_data.new_order:
                s.order -= 1  # Shift up
    else:  # Moving scene **up**
        for s in scenes:
            if scene_data.new_order <= s.order < current_order:
                s.order += 1  # Shift down

    # Update dragged scene to its new order
    scene.order = scene_data.new_order

    db.commit()
    return {"message": "Scene reordered successfully", "scene": scene}



@router.get("/", response_model=List[SceneBase])
def get_all_scenes(db: Session = Depends(get_db)):
    scenes = db.query(Scene).all()
    return scenes if scenes else []


@router.get("/{scene_id}", response_model=SceneBase)
def get_scene_by_id(scene_id: str, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene

# Get scenes by project ID
@router.get("/project/{project_id}", response_model=List[SceneBase])
def get_scenes_by_project_id(project_id: str, db: Session = Depends(get_db)):
    scenes = db.query(Scene).filter(Scene.project_id == project_id).all()
    return scenes if scenes else []

# Get scenes by project ID and act
@router.get("/project/{project_id}/act/{act}", response_model=List[SceneBase])
def get_scenes_by_project_id_and_act(project_id: str, act: str, db: Session = Depends(get_db)):
    scenes = db.query(Scene).filter(Scene.project_id == project_id, Scene.act_id == act).all()
    # if not scenes, return 200 OK with empty list
    if not scenes:
        return []
    return scenes if scenes else []

# Response model contains a list of errors or success message
class SceneValidationResponse(BaseModel):
    message: str
    errors: Optional[List[str]] = None

# Validate scenes for given act - Each scene has assigned an Image and Dialog line
@router.post("/{project_id}/act/{act}/validate", response_model=SceneValidationResponse)
def validate_scenes(project_id: str, act: int, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(Scene).filter(Scene.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=400, detail="Invalid project_id")
    
    # Get all scenes for the project and act
    scenes = db.query(Scene).filter(Scene.project_id == project_id, Scene.act == act).all()
    
    # If no scenes found for this act, return 400
    if not scenes:
        raise HTTPException(status_code=400, detail="Invalid act or no scenes found for this act")
    
    errors = []
    
    # Check if each scene has assigned Line
    for scene in scenes:
        lines = db.query(Line).filter(Line.scene_id == scene.id).all()
        if not lines:
            errors.append(f"Scene {scene.order} (name: {scene.name}) is missing a dialog line")
    
    # Check if each scene has assigned Image
    for scene in scenes:
        if not scene.assigned_image_url:
            errors.append(f"Scene {scene.order} (name: {scene.name}) is missing an assigned image")
    
    if errors:
        return {"message": "STATUS_ERR", "errors": errors}
    else:
        return {"message": "STATUS_OK"}

@router.delete("/{scene_id}", response_model=SceneResponse)
def delete_scene(scene_id: str, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    db.delete(scene)
    db.commit()

    # Reorder remaining scenes
    remaining_scenes = db.query(Scene).filter(Scene.act == scene.act, Scene.project_id == scene.project_id).order_by(Scene.order).all()
    for index, s in enumerate(remaining_scenes):
        s.order = index + 1

    db.commit()
    return {"message": "Scene deleted successfully"}
