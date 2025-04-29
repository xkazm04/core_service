"""
Schema definitions for database tool arguments
"""
from typing import Optional
from uuid import UUID
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel, Field

class CharacterLookupArgs(LangchainBaseModel):
    """Arguments for looking up character details."""
    character_name: Optional[str] = Field(None, description="The name of the character to look up. Use if character_id is not known.")
    character_id: Optional[UUID] = Field(None, description="The specific UUID of the character.")

class StoryLookupArgs(LangchainBaseModel):
    """Arguments for looking up story overview and acts."""
    pass

class BeatLookupArgs(LangchainBaseModel):
    """Arguments for looking up story beats (objectives)."""
    pass

class ProjectGapAnalysisArgs(LangchainBaseModel):
    """Arguments for analyzing gaps in project components."""
    topic: str = Field(..., description="The area to analyze for gaps ('character', 'story', etc.)")
    character_id: Optional[UUID] = Field(None, description="Character ID if analyzing character-specific gaps")
    
class SceneLookupArgs(LangchainBaseModel):
    """Arguments for looking up scene details."""
    scene_id: UUID = Field(..., description="The ID of the scene to look up.")