from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from models.models import Beat
from schemas.beat import BeatCreate

def create_beat(beat: BeatCreate, db: Session = Depends(get_db)):
    new_beat = Beat(**beat.dict())
    db.add(new_beat)
    db.commit()
    db.refresh(new_beat)
    return new_beat