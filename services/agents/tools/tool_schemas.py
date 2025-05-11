"""
Schema definitions for database tool arguments
"""
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum
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

class ExecutorFunctionType(str, Enum):
    CHARACTER_CREATE = "character_create"
    CHARACTER_RENAME = "character_rename"
    ADD_TRAIT_BEHAVIOR = "trait_add"
    RELATIONSHIP_ADD = "relationship_add"
    FACTION_CREATE = "faction_create"
    FACTION_RENAME = "faction_rename"
    ACT_CREATE = "act_create"
    ACT_EDIT = "act_edit"
    BEAT_CREATE = "beat_create"
    BEAT_EDIT = "beat_edit"
    SCENE_CREATE = "scene_create"

class ExecutorFunctionArgs(LangchainBaseModel):
    """Execute a specific database operation based on user intent."""
    function_name: str = Field(..., 
                 description="The specific function to execute (e.g., character_create, character_rename)")
    params: Dict[str, Any] = Field(default_factory=dict,
                 description="Parameters to pass to the function")

    def run(self, project_id: UUID, character_id: Optional[UUID] = None, db=None):
        """Execute the requested function."""
        from services.agents.executor import execute_suggestion_function
        
        if not db:
            return "Error: Database session not available."
        
        try:
            result = execute_suggestion_function(
                function_name=self.function_name,
                db=db,
                project_id=project_id,
                character_id=character_id,
                **self.params
            )
            return f"Function execution result: {result}"
        except Exception as e:
            return f"Error executing function: {str(e)}"