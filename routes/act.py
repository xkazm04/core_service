from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Act, Beat
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from schemas.act import CreateAct, EditAct
from services.story import create_act
    
router = APIRouter(tags=["Acts"])

class ActResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    order: int
    description: Optional[str] = None
    
    class Config:
        orm_mode = True

#1. GET act by ID
@router.get("/{act_id}", response_model=ActResponse)
def get_act_by_id(act_id: str, db: Session = Depends(get_db)):
    act = db.query(Act).filter(Act.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    return act


#2. POST route to add a new act
@router.post("/", response_model=ActResponse)
def add_act(act_data: CreateAct, db: Session = Depends(get_db)):
    act = create_act(db, act_data)
    return act

#3. GET route to get all acts by project ID, order by order number
@router.get("/project/{project_id}", response_model=List[ActResponse])
def get_acts_by_project(project_id: UUID, db: Session = Depends(get_db)):
    acts = db.query(Act).filter(Act.project_id == project_id).all()
    if not acts:
        raise HTTPException(status_code=404, detail="No acts found for this project")
    acts.sort(key=lambda x: x.order)
    return acts if acts else []


#4. PUT route to edit any field of an act by ID
@router.put("/{act_id}", response_model=ActResponse)
def update_act_description(act_edit: EditAct, db: Session = Depends(get_db)):
    # Get the act by ID
    act = db.query(Act).filter(Act.id == act_edit.id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    # Edit changes from request object, if the change contains order, recalculate all orders of project acts
    if act_edit.order:
        acts = db.query(Act).filter(Act.project_id == act.project_id).all()
        for a in acts:
            if a.order >= act_edit.order:
                a.order += 1
        act.order = act_edit.order
    # Update the act with the new values
    for key, value in act_edit.model_dump(exclude_unset=True).items():
        setattr(act, key, value)
    db.commit()
    db.refresh(act)
    return {"act": act, "message": "Act updated successfully"}

#5. DELETE route to delete an act by ID
@router.delete("/{act_id}", response_model=ActResponse)
def delete_act(act_id: str, db: Session = Depends(get_db)):
    act = db.query(Act).filter(Act.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    db.delete(act)
    db.commit()
    return act