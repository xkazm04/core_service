from pydantic import BaseModel
from typing import List, Optional
from models.models import Project, FactionRelationship, Faction
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from uuid import UUID

router = APIRouter(tags=["Faction-Relationships"])


class FactionRelCreate(BaseModel):
    faction_a: UUID
    faction_b: UUID
    relationship_type: str  
    event: Optional[str] = None  
    event_act: Optional[UUID] = None  
    
# Create a new faction relationship
@router.post("/", response_model=FactionRelCreate)
def create_faction_relationship(faction_rel_data: FactionRelCreate, db: Session = Depends(get_db)):
    faction_a = db.query(Faction).filter(Faction.id == faction_rel_data.faction_a).first()
    faction_b = db.query(Faction).filter(Faction.id == faction_rel_data.faction_b).first()
    
    if not faction_a or not faction_b:
        raise HTTPException(status_code=404, detail="One or both factions not found")
    
    faction_relationship = FactionRelationship(**faction_rel_data.dict())
    db.add(faction_relationship)
    db.commit()
    db.refresh(faction_relationship)
    return faction_relationship
# Delete a faction relationship
@router.delete("/{faction_rel_id}", response_model=FactionRelCreate)
def delete_faction_relationship(faction_rel_id: UUID, db: Session = Depends(get_db)):
    faction_relationship = db.query(FactionRelationship).filter(FactionRelationship.id == faction_rel_id).first()
    if not faction_relationship:
        raise HTTPException(status_code=404, detail="Faction relationship not found")
    db.delete(faction_relationship)
    db.commit()
    return faction_relationship

# Get all relationships for a given faction
@router.get("/faction/{faction_id}", response_model=List[FactionRelCreate])
def get_faction_relationships(faction_id: UUID, db: Session = Depends(get_db)):
    faction_relationships = db.query(FactionRelationship).filter(
        (FactionRelationship.faction_a == faction_id) | (FactionRelationship.faction_b == faction_id)
    ).all()
    if not faction_relationships:
        raise HTTPException(status_code=404, detail="No relationships found for this faction")
    return faction_relationships

# Edit a faction relationship
@router.put("/{faction_rel_id}", response_model=FactionRelCreate)
def edit_faction_relationship(faction_rel_id: UUID, faction_rel_data: FactionRelCreate, db: Session = Depends(get_db)):
    faction_relationship = db.query(FactionRelationship).filter(FactionRelationship.id == faction_rel_id).first()
    if not faction_relationship:
        raise HTTPException(status_code=404, detail="Faction relationship not found")
    
    for field, value in faction_rel_data.dict().items():
        if hasattr(faction_relationship, field):
            setattr(faction_relationship, field, value)
    
    db.commit()
    db.refresh(faction_relationship)
    return faction_relationship