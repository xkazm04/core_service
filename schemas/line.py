from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

class DialogLineCreate(BaseModel):
    scene_id: UUID
    character_id: Optional[UUID] = None
    text: str
    tone: Optional[str] = "Normal"
    x: int
    y: int
    is_final: bool
    predecessor_id: Optional[UUID] = None
    successors: List[UUID] = []

class DialogLineUpdate(BaseModel):
    text: Optional[str] = None
    tone: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    is_final: Optional[bool] = None
    predecessor_id: Optional[UUID] = None
    successors: List[UUID] = []

class LineCreate(BaseModel):
    character_id: Optional[UUID] = None
    scene_id: UUID
    text: str
    tone: Optional[str] = "Normal"