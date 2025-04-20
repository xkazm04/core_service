from uuid import UUID
from pydantic import BaseModel 

class BeatCreate(BaseModel):
    name: str
    act_id: UUID
    default_flag: bool = False
    description: str = None
    type: str = 'act'
    order: int = 0