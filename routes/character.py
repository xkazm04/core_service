from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Character
import logging
from pydantic import BaseModel
from services.sse import broadcast_event
router = APIRouter(tags=["Characters"])
logging.basicConfig(level=logging.INFO)

class AssignVoiceRequest(BaseModel):
    voice_id: str
class RenameRequest(BaseModel):
    new_name: str
    
# 1. Create a new character
@router.post("/")
def create_character_endpoint(
    character_data: dict,
    db: Session = Depends(get_db),
):
    try:
        character = Character(
            name=character_data.get("name"),
            project_id=character_data.get("project_id"),
            type=character_data.get("type"),
            faction_id=character_data.get("faction_id"),
        )
        # Validate duplicate character names inside the same project
        existing_character = db.query(Character).filter(
            Character.project_id == character.project_id,
            Character.name == character.name
        ).first()
        if existing_character:
            raise HTTPException(status_code=400, detail="Character name already exists in this project.")
        db.add(character)  
        db.commit()
        db.refresh(character)
        return {"message": "Character created successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating character: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating character: {str(e)}")

# 2. Edit a character - used for metadata like image urls, factions
@router.put("/{character_id}")
def edit_character_endpoint(character_id: str, character_data: dict, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found.")
    
    for field, value in character_data.items():
        if hasattr(character, field):
            setattr(character, field, value)
        else:
            logging.warning(f"Attempted to update unknown field: {field}")
    
    try:
        db.commit()
        logging.info(f"Character {character_id} updated successfully.")
        return {"message": "Character updated successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating character {character_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

# 3. Get all characters by project_id
@router.get("/project/{project_id}")
def get_characters_by_project_id_endpoint(project_id: str, db: Session = Depends(get_db)):
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    broadcast_event("characters_updated", {"project_id": project_id})
    return characters if characters else []

# 4. Delete a character by id
@router.delete("/{character_id}")
def delete_character_endpoint(character_id: str, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found.")
    db.delete(character)
    db.commit()
    return {"message": "Character deleted successfully."}

# 5. Assign a voice to a character
@router.put("/{character_id}/voice")
def assign_voice_to_character_endpoint(character_id: str, request: AssignVoiceRequest, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        logging.warning(f"Character with ID {character_id} not found.")
        raise HTTPException(status_code=404, detail="Character not found.")
    
    character.voice = request.voice_id

    try:
        db.commit()
        logging.info(f"Assigned voice {request.voice_id} to character {character_id}.")
        return {"message": "Voice assigned to character successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error assigning voice to character {character_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    
# 6. Rename a character
@router.put("/{character_id}/rename")
def rename_character_endpoint(character_id: str, request: RenameRequest, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        logging.warning(f"Character with ID {character_id} not found.")
        raise HTTPException(status_code=404, detail="Character not found.")
    
    character.name = request.new_name

    try:
        db.commit()
        logging.info(f"Renamed character {character_id} to {request.new_name}.")
        return {"message": "Character renamed successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error renaming character {character_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")   
    
# 7. Get character by id
@router.get("/{character_id}")
def get_character_by_id_endpoint(character_id: str, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    return character if character else {}

# 8. Add avatar_url to a character
class AddAvatarRequest(BaseModel):
    avatar_url: str
    
@router.put("/{character_id}/avatar")
def add_avatar_to_character_endpoint(character_id: str, request: AddAvatarRequest, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        logging.warning(f"Character with ID {character_id} not found.")
        raise HTTPException(status_code=404, detail="Character not found.")
    character.avatar_url = request.avatar_url
    try:
        db.commit()
        logging.info(f"Added avatar URL to character {character_id}.")
        return {"message": "Avatar added to character successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error adding avatar to character {character_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    
# Get characters by faction_id
@router.get("/faction/{faction_id}")
def get_characters_by_faction_id_endpoint(faction_id: str, db: Session = Depends(get_db)):
    characters = db.query(Character).filter(Character.faction_id == faction_id).all()
    return characters if characters else []