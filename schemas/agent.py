from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json

class Suggestion(BaseModel):
    feature: str
    use_case: str
    initiator: str
    message: str
    fe_function: Optional[str] = None
    be_function: Optional[str] = None
    fe_navigation: Optional[str] = None
    topic: str
    doublecheck: Optional[bool] = None
    
    class Config:
        extra = "forbid"  # This tells Pydantic to reject extra fields

class ChatResponse(BaseModel):
    response: str
    suggestions: List[Suggestion] = Field(default_factory=list)
    be_function: Optional[str] = None
    db_updated: bool
