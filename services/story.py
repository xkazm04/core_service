from schemas.act import CreateAct
from sqlalchemy.orm import Session
from models.models import Act
import datetime 

def create_act(db: Session, act_data: CreateAct):
    act = Act(**act_data.model_dump()) 
    max_order = db.query(Act).filter(Act.project_id == act_data.project_id).count()
    act.order = max_order + 1 if max_order else 1
    act.created_at = datetime.utcnow()
    db.add(act)
    db.commit()
    db.refresh(act)
    return act