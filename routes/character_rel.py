from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Character, CharacterRelationshipEvent
import logging
from schemas.character import RelCreate, RelEdit
router = APIRouter(tags=["Character-Relationships"])
logging.basicConfig(level=logging.INFO)

# 0. Get all relationships by character_id
@router.get("/character/{character_id}")
def get_relationships_by_character_id(
    character_id: str,
    db: Session = Depends(get_db),
):
    try:
        relationships = db.query(CharacterRelationshipEvent).filter(
            (CharacterRelationshipEvent.character_a_id == character_id) |
            (CharacterRelationshipEvent.character_b_id == character_id)
        ).all()
        
        if not relationships:
            raise HTTPException(status_code=404, detail="No relationships found for this character.")
        
        return relationships
    except Exception as e:
        logging.error(f"Error fetching relationships for character {character_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching relationships: {str(e)}")
    
# 1. Create a new relationship
@router.post("/")
def create_relationship_endpoint(
    relationship_data: RelCreate,
    db: Session = Depends(get_db),
):
    try:
        character_a = db.query(Character).filter(Character.id == relationship_data.character_a_id).first()
        character_b = db.query(Character).filter(Character.id == relationship_data.character_b_id).first()
        if not character_a or not character_b:
            raise HTTPException(status_code=404, detail="One or both characters not found.")
        relationship = CharacterRelationshipEvent(
            character_a_id=relationship_data.character_a_id,
            character_b_id=relationship_data.character_b_id,
            event_date=relationship_data.event_date,
            act_id=relationship_data.act_id,
            relationship_type=relationship_data.relationship_type,
            description=relationship_data.description
        )
        db.add(relationship)  
        db.commit()
        db.refresh(relationship)
        return {"message": "Relationship created successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating relationship: {str(e)}")

# 2. Delete a relationship
@router.delete("/{relationship_id}")
def delete_relationship_endpoint(
    relationship_id: str,
    db: Session = Depends(get_db),
):
    try:
        relationship = db.query(CharacterRelationshipEvent).filter(CharacterRelationshipEvent.id == relationship_id).first()
        if not relationship:
            raise HTTPException(status_code=404, detail="Relationship not found.")
        
        db.delete(relationship)
        db.commit()
        return {"message": "Relationship deleted successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting relationship: {str(e)}")

# 3. Edit relationship 
@router.put("/{relationship_id}")
def edit_relationship_endpoint(
    relationship_id: str,
    relationship_data: RelEdit,
    db: Session = Depends(get_db),
):
    try:
        relationship = db.query(CharacterRelationshipEvent).filter(CharacterRelationshipEvent.id == relationship_id).first()
        if not relationship:
            raise HTTPException(status_code=404, detail="Relationship not found.")
        
        for field, value in relationship_data.dict(exclude_unset=True).items():
            if hasattr(relationship, field):
                setattr(relationship, field, value)
            else:
                logging.warning(f"Attempted to update unknown field: {field}")
        
        db.commit()
        return {"message": "Relationship updated successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating relationship {relationship_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating relationship: {str(e)}")
