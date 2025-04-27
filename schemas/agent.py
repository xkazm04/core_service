from pydantic import BaseModel 
from typing import Optional, List
from pydantic import Field

class Suggestion(BaseModel):
    feature: str
    use_case: str
    initiator: str
    suggestion_label: str
    suggestion_text: str
    be_function: Optional[str] = None
    fe_navigation: Optional[str] = None
    topic: str

class ChatResponse(BaseModel):
    response: str
    suggestions: List[Suggestion] = Field(default_factory=list)
