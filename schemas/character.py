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
        
    
class RelCreate(BaseModel):
    """Schema for creating a relationship"""
    character_a_id: UUID
    character_b_id: UUID
    event_date: Optional[str] = None
    act_id: Optional[UUID] = None
    relationship_type: Optional[str] = None
    description: str
    
class RelEdit(BaseModel):
    """Schema for editing a relationship"""
    rel_id: UUID
    event_date: Optional[str] = None
    act_id: Optional[UUID] = None
    relationship_type: Optional[str] = None
    description: Optional[str] = None