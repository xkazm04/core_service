from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class PromptCreate(BaseModel):
    text: str
    type: Optional[str] = None
    subtype: Optional[str] = None
    char_id: Optional[UUID] = None
    scene_id: Optional[UUID] = None
    project_id: UUID

class PromptUpdate(BaseModel):
    text: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None

class PromptResponse(BaseModel):
    id: UUID
    text: str
    type: Optional[str]
    subtype: Optional[str]
    char_id: Optional[UUID]
    scene_id: Optional[UUID]
    project_id: UUID

    class Config:
        orm_mode = True