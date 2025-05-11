"""
Agent state and data models
"""
from typing import TypedDict, Annotated, Sequence, List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from schemas.agent import Suggestion

class ChatResponse(BaseModel):
    """Structured response from the chat agent."""
    response: str
    suggestions: List[Suggestion] = Field(default_factory=list)
    be_function: Optional[str] = None  # Replace executed_functions with be_function

class AgentState(TypedDict):
    """State maintained throughout the agent's execution."""
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    project_id: Optional[UUID]
    character_id: Optional[UUID]
    request_type: Optional[str]
    extracted_character_names: Optional[List[str]]
    be_function: Optional[str] = None
    operation_intent: Optional[str] = None  
    operation_params: Optional[Dict[str, Any]] = {} 
    missing_params: Optional[List[str]] = [] 
    final_response: Optional[ChatResponse]