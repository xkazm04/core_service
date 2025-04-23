from pydantic import BaseModel
from typing import List, Optional
from models.models import Project, Faction
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from uuid import UUID

router = APIRouter(tags=["Factions"])

class FactionBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    color: Optional[str] = None
    project_id: UUID

class FactionCreate(FactionBase):
    pass

class FactionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    image_url: Optional[str] = None
  

class FactionResponse(FactionBase):
    id: UUID
    
    class Config:
        orm_mode = True

# 1. Get all factions for given project
@router.get("/projects/{project_id}", response_model=List[FactionResponse])
def get_factions(project_id: UUID, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    factions = db.query(Faction).filter(Faction.project_id == project_id).all()
    return factions if factions else []

# 2. Create a new faction
@router.post("/", response_model=FactionResponse)
def create_faction(faction_data: FactionCreate, db: Session = Depends(get_db)):
    faction = Faction(**faction_data.dict())
    db.add(faction)
    db.commit()
    db.refresh(faction)
    return faction

# 3. Delete a faction
@router.delete("/{faction_id}", response_model=FactionResponse)
def delete_faction(faction_id: UUID, db: Session = Depends(get_db)):
    faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    db.delete(faction)
    db.commit()
    return faction

# 4. Update a faction
@router.put("/{faction_id}", response_model=FactionResponse)
def update_faction(faction_id: UUID, faction_data: FactionUpdate, db: Session = Depends(get_db)):
    faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    for key, value in faction_data.dict(exclude_unset=True).items():
        setattr(faction, key, value)
    db.commit()
    db.refresh(faction)
    return faction

class MigrateFactionsRequest(BaseModel):
    source_project_id: UUID
    target_project_id: UUID
# 5. Migrate factions from one project to another
@router.post("/migrate/", response_model=List[FactionResponse])
def migrate_factions(r: MigrateFactionsRequest, db: Session = Depends(get_db)):
    source_project = db.query(Project).filter(Project.id == r.source_project_id).first()
    target_project = db.query(Project).filter(Project.id == r.target_project_id).first()
    if not source_project or not target_project:
        raise HTTPException(status_code=404, detail="Source or target project not found")
    
    factions = db.query(Faction).filter(Faction.project_id == r.source_project_id).all()
    for faction in factions:
        faction.project_id = r.target_project_id
        db.add(faction)
    db.commit()
    return factions if factions else []
