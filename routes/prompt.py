from uuid import UUID
from typing import List
from schemas.prompt import PromptCreate, PromptUpdate, PromptResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.models import Prompt
from database import get_db

router = APIRouter(tags=["Prompts"])

# Create a new prompt
@router.post("/", response_model=PromptResponse)
def create_prompt(prompt_data: PromptCreate, db: Session = Depends(get_db)):
    prompt = Prompt(**prompt_data.dict())
    # Check if prompt for given type already exists, if yes, delete the original one
    if prompt.char_id:
        existing_prompt = db.query(Prompt).filter(Prompt.char_id == prompt.char_id, Prompt.type == prompt.type).first()
        if existing_prompt:
            db.delete(existing_prompt)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt  

# Delete a prompt by ID
@router.delete("/{prompt_id}", response_model=dict)
def delete_prompt(prompt_id: UUID, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.delete(prompt)
    db.commit()
    return {"message": "Prompt deleted successfully"}

# Update a prompt text
@router.put("/{prompt_id}", response_model=PromptResponse)
def update_prompt(prompt_id: UUID, prompt_update: PromptUpdate, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Update fields if provided
    if prompt_update.text:
        prompt.text = prompt_update.text
    if prompt_update.type is not None:
        prompt.type = prompt_update.type
    if prompt_update.subtype is not None:
        prompt.subtype = prompt_update.subtype

    db.commit()
    db.refresh(prompt)
    return prompt  

# Get all prompts by scene_id
@router.get("/scene/{scene_id}", response_model=List[PromptResponse])
def get_prompts_by_scene(scene_id: UUID, db: Session = Depends(get_db)):
    prompts = db.query(Prompt).filter(Prompt.scene_id == scene_id).all()
    return prompts if prompts else []

# Get all prompts by char_id
@router.get("/character/{char_id}", response_model=List[PromptResponse])
def get_prompts_by_character(char_id: UUID, db: Session = Depends(get_db)):
    prompts = db.query(Prompt).filter(Prompt.char_id == char_id).all()
    return prompts if prompts else []

# Get character prompts with type = Personality
@router.get("/character/{char_id}/personality", response_model=PromptResponse)
def get_personality_prompts(char_id: UUID, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.char_id == char_id, Prompt.type == "Personality").first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Personality prompt not found")
    return prompt
