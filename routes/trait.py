from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
from typing import List
from models.models import CharacterTrait
from uuid import uuid4, UUID

router = APIRouter()

class TraitItem(BaseModel):
    character_id: UUID
    type: str
    description: str

class TraitResponse(BaseModel):
    id: UUID
    character_id: UUID
    type: str
    description: str
    
    class Config:   
        from_attributes = True  # Updated from orm_mode = True

@router.post("/")
def create_character_trait(trait: TraitItem, db: Session = Depends(get_db)):
    # Check if trait already exists for this character and type
    existing_trait = db.query(CharacterTrait).filter(
        CharacterTrait.character_id == trait.character_id,
        CharacterTrait.type == trait.type
    ).first()
    
    if existing_trait:
        existing_trait.description = trait.description
    else:
        # Create new trait
        new_trait = CharacterTrait(
            id=str(uuid4()),
            character_id=trait.character_id,
            type=trait.type,
            description=trait.description
        )
        db.add(new_trait)
    
    db.commit()
    
    return {
        "message": "Trait created or updated successfully."
    }

@router.get("/character/{character_id}")
def get_character_traits(character_id: str, db: Session = Depends(get_db)):
    traits = db.query(CharacterTrait).filter(
        CharacterTrait.character_id == character_id
    ).all()
    
    if not traits:
        return {"message": "No traits found for the character.", "traits": []}
    
    return [TraitResponse.from_orm(trait) for trait in traits]

@router.delete("/{trait_id}")
def delete_character_trait(trait_id: str, db: Session = Depends(get_db)):
    trait = db.query(CharacterTrait).filter(
        CharacterTrait.id == trait_id
    ).first()
    
    if not trait:
        raise HTTPException(status_code=404, detail="Trait not found")
        
    db.delete(trait)
    db.commit()
    
    return {"message": "Trait deleted successfully."}
