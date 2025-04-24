from fastapi import APIRouter, HTTPException
import logging
from services.llm.basic_response import generate_response
from services.name_randomizer import generate_scifi_names
from pydantic import BaseModel
from templates.character.randomize import randomizedNameTemplate
from enum import Enum
from typing import Optional
router = APIRouter(tags=["Characters-LLM"])
logging.basicConfig(level=logging.INFO)


class SciFiType(str, Enum):
    star_wars = "Star Wars"
    cyberpunk = "Cyberpunk"


class Gender(str, Enum):
    male = "Male"
    female = "Female"


# Randomize character name request model with extended parameters
class CharacterNameRequest(BaseModel):
    user_input: str
    type_name: Optional[SciFiType] = SciFiType.star_wars
    gender: Optional[Gender] = Gender.male
    count: Optional[int] = 1


@router.post("/randomize")
def randomize_character_name(request: CharacterNameRequest):
    try:
        # First attempt: Use the generate_scifi_names function
        names = generate_scifi_names(
            type_name=request.type_name,
            gender=request.gender,
            count=request.count
        )
        
        # Check if names were successfully generated
        if names:
            return {
                "message": "Character name generated successfully.",
                "names": names,
                "source": "name_api"
            }
        
        # Fallback to LLM if API call failed
        logging.warning("API name generation failed, falling back to LLM")
        user_input = f"{request.user_input} (Type: {request.type_name}, Gender: {request.gender})"
        
        response = generate_response(
            system_message=randomizedNameTemplate, 
            user_input=user_input,
            temperature=0.1,
            model="meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        
        if response:
            return {
                "message": "Character name generated successfully.",
                "names": response,
                "source": "llm"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate new name.")
    
    except Exception as e:
        logging.error(f"Error generating new name for character: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")