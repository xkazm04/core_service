from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict
import datetime

class SceneBase(BaseModel):
    id: UUID
    act: Optional[UUID] = None
    name: str
    order: int
    project_id: UUID
    assigned_image_url: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True  # Ensures SQLAlchemy models can be converted to Pydantic

class SceneCreate(BaseModel):
    act_id: UUID
    name: str
    order: int
    project_id: UUID

class SceneUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None

class SceneResponse(BaseModel):
    message: str
    scene: Optional[SceneBase] = None
    
class SceneReorder(BaseModel):
    scene_id: str
    new_order: int    

class NarrationRequest(BaseModel):
    text: str
    emotion: Optional[str] = None
    style: Optional[str] = None
    
class NarrationResponse(BaseModel):
    original_text: str
    narrated_text: str
    examples: Optional[List[Dict]] = None
    include_examples: Optional[bool] = False
    
# -------- SCENNE PARAMETERS ---------
class SceneParamPost(BaseModel):
    scene_id: UUID
    param_name: str
    param_value: str

class SceneParamResponse(BaseModel):
    id: UUID
    scene_id: UUID
    param_name: str
    param_value: str
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    
    class Config:
        orm_mode = True 
    
class BasicResponse(BaseModel):
    message: str
    scene: Optional[SceneBase] = None