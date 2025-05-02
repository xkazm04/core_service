from pydantic import BaseModel 
from typing import Optional
from uuid import UUID

class CreateAct(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    
class EditAct(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    
class ActResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    order: int
    description: Optional[str] = None
    
    class Config:
        orm_mode = True