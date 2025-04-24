from pydantic import BaseModel
from typing import Optional
class ProjectSchema(BaseModel):
    name: str
    user: str 
    type: str = None
    overview: Optional[str] = None
    genre: Optional[str] = None
    
    
class ProjectEvaluateRequestSchema(BaseModel):
    project_id: str
    act_id: str
    
class ProjectEvaluateResponseSchema(BaseModel):
    num_characters: int
    assigned_characters: int
    
class ProjectUpdateSchema(BaseModel):
    name: str = None
    type: str = None
    genre: str = None
    theme: str = None
    concept: str = None
    overview: str = None