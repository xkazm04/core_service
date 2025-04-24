from fastapi import APIRouter,HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.models import Beat
from uuid import UUID
from pydantic import BaseModel
from services.beats import create_beat
from schemas.beat import BeatCreate

router = APIRouter(tags=["Beats"])

# Get beats by project_id
@router.get("/project/{project_id}")
def get_beats_by_project_id(project_id: UUID, db: Session = Depends(get_db)):
    beats = db.query(Beat).filter(Beat.project_id == project_id).all()
    if not beats:
        raise HTTPException(status_code=404, detail="No beats found")
    return beats

# Get beats by act_id
@router.get("/act/{act_id}")
def get_beats_by_act_id(act_id: str, db: Session = Depends(get_db)):
    beats = db.query(Beat).filter(Beat.act_id == act_id).all()
    if not beats:
        raise HTTPException(status_code=404, detail="No beats found")
    return beats

    
@router.post("/")
def create_beat_api(beat: BeatCreate, db: Session = Depends(get_db)):
    new_beat = create_beat(beat, db)
    if not new_beat:
        raise HTTPException(status_code=400, detail="Failed to create beat")
    return new_beat

# Edit name or description of a beat
class BeatEdit(BaseModel):
    name: str = None
    description: str = None
    
@router.put("/{beat_id}")
def update_beat(beat_id: str, beat: BeatEdit, db: Session = Depends(get_db)):
    db_beat = db.query(Beat).filter(Beat.id == beat_id).first()
    if not db_beat:
        raise HTTPException(status_code=404, detail="Beat not found")
    for key, value in beat.dict().items():
        setattr(db_beat, key, value)
    db.commit()
    db.refresh(db_beat)
    return db_beat

# Delete a beat
@router.delete("/{beat_id}")
def delete_beat(beat_id: str, db: Session = Depends(get_db)):
    db_beat = db.query(Beat).filter(Beat.id == beat_id).first()
    if not db_beat:
        raise HTTPException(status_code=404, detail="Beat not found")
    db.delete(db_beat)
    db.commit()
    return {"detail": "Beat deleted successfully"}

# Delete project beats
@router.delete("/project/{project_id}")
def delete_project_beats(project_id: str, db: Session = Depends(get_db)):
    beats = db.query(Beat).filter(Beat.project_id == project_id).all()
    if not beats:
        raise HTTPException(status_code=404, detail="No beats found for this project")
    for beat in beats:
        db.delete(beat)
    db.commit()
    return {"detail": "All beats for the project deleted successfully"}