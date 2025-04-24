from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class CharacterBase(BaseModel):
    id: Optional[str] = None
    name: str
    type: str
    
class CharacterCreate(CharacterBase):
    """Schema for creating a character"""
    pass
    
class CharacterResponse(CharacterBase):
    id: UUID
    project_id: UUID
    
    class Config:
        orm_mode = True