from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Scene, SceneParams
from pydantic import BaseModel
from typing import List, Optional
from schemas.scene import BasicResponse, SceneParamPost, SceneParamResponse
router = APIRouter(tags=["Scenes-params"])

# Basic CRUD operations for scene parameters
## Create scene parameter
@router.post('/', response_model=BasicResponse)
def create_scene_params(scene_params: SceneParamPost, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_params.scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene_param = SceneParams(**scene_params.dict())
    db.add(scene_param)
    db.commit()
    db.refresh(scene_param)
    return {"message": "Scene parameter created successfully", "scene": scene_param}

## Get scene parameters by scene ID
@router.get('/scene/{scene_id}', response_model=List[SceneParamResponse])
def get_scene_params(scene_id: str, db: Session = Depends(get_db)):
    scene_params = db.query(SceneParams).filter(SceneParams.scene_id == scene_id).all()
    return scene_params if scene_params else []

## Delete scene parameter by ID
@router.delete('/params/{param_id}', response_model=BasicResponse)
def delete_scene_param(param_id: str, db: Session = Depends(get_db)):
    scene_param = db.query(SceneParams).filter(SceneParams.id == param_id).first()
    if not scene_param:
        raise HTTPException(status_code=404, detail="Scene parameter not found")

    db.delete(scene_param)
    db.commit()
    return {"message": "Scene parameter deleted successfully"}

## Update scene parameter by ID
class SceneParamUpdate(BaseModel):
    param_name: Optional[str] = None
    param_value: Optional[str] = None
    
@router.put('/params/{param_id}', response_model=BasicResponse)
def update_scene_param(param_id: str, scene_param_update: SceneParamUpdate, db: Session = Depends(get_db)):
    scene_param = db.query(SceneParams).filter(SceneParams.id == param_id).first()
    if not scene_param:
        raise HTTPException(status_code=404, detail="Scene parameter not found")

    # Update only provided fields
    for key, value in scene_param_update.dict(exclude_unset=True).items():
        if value is not None:
            setattr(scene_param, key, value)

    db.commit()
    db.refresh(scene_param)
    return {"message": "Scene parameter updated successfully", "scene": scene_param}