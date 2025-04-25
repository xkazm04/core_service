from pydantic import BaseModel, validator
from typing import List, Optional
from enum import Enum
from pydantic.fields import Field

class ModelProvider(str, Enum):
    GPT = "gpt"
    GROQ = "groq"
    GEMINI = "gemini"
    

class Character(BaseModel):
    character_name: str
    character_prompt: str

class PromptInput(BaseModel):
    text: str
    type: str
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    creativity: float = Field(0.7, description="Creativity level (0.0-1.0)", ge=0.0, le=1.0)
    model_provider: ModelProvider = Field(ModelProvider.GPT, description="AI model provider to use")


class DialogInput(BaseModel):
    characters: List[Character]
    scenery_prompt: str
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    creativity: float = Field(0.7, description="Creativity level (0.0-1.0)", ge=0.0, le=1.0)
    model_provider: ModelProvider = Field(ModelProvider.GPT, description="AI model provider to use")

class DialogLine(BaseModel):
    order: int
    character_name: str
    dialog_line: str

class DialogResponse(BaseModel):
    dialog: List[DialogLine]
    model_used: Optional[str] = None
    
class PromptInputBasic(BaseModel):
    text: str = Field(..., description="The initial idea or context for the dialog")
    character_count: int = Field(2, description="Number of characters in the dialog")
    tone: Optional[str] = Field(None, description="Tone of the dialog (e.g., humorous, dramatic, tense)")
    setting: Optional[str] = Field(None, description="Setting where the dialog takes place")
    model_provider: ModelProvider = Field(ModelProvider.GPT, description="AI model provider to use")
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    creativity: float = Field(0.7, description="Creativity level (0.0-1.0)", ge=0.0, le=1.0)
    
class PromptInputBasicResponse(BaseModel):
    improved_dialog: str
    model_used: str

class ExtractInput(BaseModel):
    text: str
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    creativity: float = Field(0.7, description="Creativity level (0.0-1.0)", ge=0.0, le=1.0)
    model_provider: ModelProvider = Field(ModelProvider.GPT, description="AI model provider to use")
    
class LineInput(BaseModel):
    text: str
    traits: bool = False
    context: bool = False
    history: bool = False
    context_description: Optional[str] = None
    character_id: Optional[str] = None
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    creativity: float = Field(0.7, description="Creativity level (0.0-1.0)", ge=0.0, le=1.0)
    model_provider: ModelProvider = Field(ModelProvider.GPT, description="AI model provider to use")
    
    @validator('context_description')
    def validate_context_description(cls, v, values):
        if values.get('context', False) and not v:
            raise ValueError("context_description is required when context is True")
        return v
        
    @validator('character_id')
    def validate_character_id(cls, v, values):
        if values.get('traits', False) and not v:
            raise ValueError("character_id is required when traits is True")
        return v
    
class ExtractOutput(BaseModel):
    improved_dialog: str
    model_used: Optional[str] = None

class ExtractInput(BaseModel):
    text: str
    
class LineInput(BaseModel):
    text: str
    traits: bool = False
    context: bool = False
    history: bool = False
    context_description: Optional[str] = None
    character_id: Optional[str] = None
    model_provider: ModelProvider = Field(ModelProvider.GPT, description="AI model provider to use")
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    
    @validator('context_description')
    def validate_context_description(cls, v, values):
        if values.get('context', False) and not v:
            raise ValueError("context_description is required when context is True")
        return v
        
    @validator('character_id')
    def validate_character_id(cls, v, values):
        if values.get('traits', False) and not v:
            raise ValueError("character_id is required when traits is True")
        return v
    
class ExtractOutput(BaseModel):
    improved_dialog: str

class PersonalityTraits(BaseModel):
    """Model for personality traits extracted from transcription"""
    personality_traits: str = Field(..., alias="Personality Traits")
    communication_style: str = Field(..., alias="Communication Style")
    emotional_expression: str = Field(..., alias="Emotional Expression")
    sense_of_humor: str = Field(..., alias="Sense of Humor")
    behavioral_tendencies: str = Field(..., alias="Behavioral Tendencies")
    possible_background_and_motivations: str = Field(..., alias="Possible Background and Motivations")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        
        
class ImproveUniversalInput(BaseModel):
    instructions: str
    type: str
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    model_provider: ModelProvider = Field(ModelProvider.GPT, description="AI model provider to use")