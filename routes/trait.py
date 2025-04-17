from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
from typing import List
from models.models import CharacterTrait
from uuid import uuid4, UUID

router = APIRouter()

# Models for trait data
class TraitItem(BaseModel):
    type: List[str]
    label: List[str]
    description: List[str]
    
class CharacterTraitsRequest(BaseModel):
    character_id: UUID
    traits: List[TraitItem]

class TraitResponse(BaseModel):
    id: UUID
    character_id: UUID
    type: str
    label: str
    description: str
    
    class Config:   
        from_attributes = True  # Updated from orm_mode = True

@router.post("/")
def create_character_traits(character_traits: CharacterTraitsRequest, db: Session = Depends(get_db)):
    # First, delete existing traits for this character
    db.query(CharacterTrait).filter(
        CharacterTrait.character_id == character_traits.character_id
    ).delete()
    
    created_traits = []
    
    # Then create new traits
    for trait_group in character_traits.traits:
        for i in range(len(trait_group.label)):
            if i < len(trait_group.type) and i < len(trait_group.label) and i < len(trait_group.description):
                new_trait = CharacterTrait(
                    id=str(uuid4()),
                    character_id=character_traits.character_id,
                    type=trait_group.type[i],
                    label=trait_group.label[i],
                    description=trait_group.description[i]
                )
                db.add(new_trait)
                created_traits.append(new_trait)
    
    db.commit()
    
    # Refresh all created traits
    for trait in created_traits:
        db.refresh(trait)
        
    return {"message": "Traits created successfully.", "traits_count": len(created_traits)}

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
