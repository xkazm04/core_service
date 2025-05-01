from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class ProjectAnalysisRequest(BaseModel):
    project_id: UUID

class ProjectFieldsStatus(BaseModel):
    genre: bool = False
    concept: bool = False
    overview: bool = False
    time_period: bool = False
    audience: bool = False
    setting: bool = False

class CharacterTraitStatus(BaseModel):
    character_id: UUID
    character_name: str
    traits_filled: int
    traits_needed: int = 5

class SceneStatus(BaseModel):
    scene_id: UUID
    scene_name: str
    act_name: Optional[str] = None
    has_description: bool = False

class BeatStatus(BaseModel):
    completed: int = 0
    total: int = 0

class ProjectAnalysisResponse(BaseModel):
    project_id: UUID
    project_fields: ProjectFieldsStatus
    characters: List[CharacterTraitStatus] = []
    scenes: List[SceneStatus] = []
    beats: BeatStatus