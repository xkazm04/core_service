from pydantic import BaseModel 
from typing import Optional
from uuid import UUID

class ParagraphResponse(BaseModel):
    id: UUID
    act_id: Optional[UUID] = None
    project_id: UUID
    title: str
    description: Optional[str] = None
    reviewed: bool = False
    order: Optional[int] = None

    class Config:
        orm_mode = True
        
class CreateParagraph(BaseModel):
    project_id: UUID
    title: str
    description: Optional[str] = None
    
class EditParagraph(BaseModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    
