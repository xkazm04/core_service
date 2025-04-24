from uuid import UUID
from pydantic import BaseModel 
from typing import Optional

class BeatCreate(BaseModel):
    id: Optional[str] = None
    name: str
    act_id: Optional[UUID] = None
    default_flag: bool = False
    description: str = None
    type: str = 'act'
    order: int = 0
    project_id: Optional[UUID] = None