from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Act, Beat
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

    
router = APIRouter(tags=["Acts"])

class CreateAct(BaseModel):
    project_id: UUID
    name: str
    order: int
    description: Optional[str] = None

class ActResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    order: int
    description: Optional[str] = None
    
    class Config:
        orm_mode = True

#1. Function to create an act
def create_act(db: Session, act_data: CreateAct):
    act = Act(**act_data.model_dump()) 
    db.add(act)
    db.commit()
    db.refresh(act)
    return act

#2. POST route to add a new act
@router.post("/", response_model=ActResponse)
def add_act(act_data: CreateAct, db: Session = Depends(get_db)):
    act = create_act(db, act_data)
    return act

#3. GET route to get all acts by project ID
@router.get("/project/{project_id}", response_model=List[ActResponse])
def get_acts_by_project(project_id: UUID, db: Session = Depends(get_db)):
    acts = db.query(Act).filter(Act.project_id == project_id).all()
    return acts if acts else []

##. GET route to get act by project ID and order number
@router.get("/project/{project_id}/order/{order}", response_model=ActResponse)
def get_act_by_project_and_order(project_id: UUID, order: int, db: Session = Depends(get_db)):
    act = db.query(Act).filter(Act.project_id == project_id, Act.order == order).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    return act
#4. PUT route to update description of an act
@router.put("/{act_id}", response_model=ActResponse)
def update_act_description(act_id: str, description: str, db: Session = Depends(get_db)):
    act = db.query(Act).filter(Act.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    act.description = description
    db.commit()
    db.refresh(act)
    return act

#5. DELETE route to delete an act by ID
@router.delete("/{act_id}", response_model=ActResponse)
def delete_act(act_id: str, db: Session = Depends(get_db)):
    act = db.query(Act).filter(Act.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    db.delete(act)
    db.commit()
    return act


# Create a proper Pydantic model for the Beat response
class BeatResponse(BaseModel):
    id: UUID
    act_id: UUID
    name: str
    order: int
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class GetBeatsResponse(BaseModel):
    act_name: str
    act_description: str
    beats: List[BeatResponse]
    
    class Config:
        orm_mode = True

#6. Get all beats by act ID
@router.get("/{act_id}/beats", response_model=List[BeatResponse])
def get_beats_by_act(act_id: str, db: Session = Depends(get_db)):
    beats = db.query(Beat).filter(Beat.act_id == act_id).all()
    act = db.query(Act).filter(Act.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    return beats if beats else []

class BeatRequestSchema(BaseModel):
    name: str
    order: int
    description: Optional[str] = None
    status: Optional[str] = None

#7. POST beat to act
@router.post("/{act_id}/beats", response_model=BeatResponse)
def add_beat_to_act(act_id: str, beat_data: BeatRequestSchema, db: Session = Depends(get_db)):
    beat = Beat(**beat_data.dict(), act_id=act_id)
    db.add(beat)
    db.commit()
    db.refresh(beat)
    return beat