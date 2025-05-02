from schemas.act import CreateAct
from sqlalchemy.orm import Session
from models.models import Act, Scene, Paragraph

def create_act(db: Session, act_data: CreateAct):
    act = Act(**act_data.model_dump()) 
    max_order = db.query(Act).filter(Act.project_id == act_data.project_id).count()
    act.order = max_order + 1 if max_order else 1
    # Create a new scene for the act
    scene = Scene(name="Scene 1", act_id=act.id, order=1, project_id=act.project_id)
    db.add(scene)
    db.add(act)
    db.commit()
    db.refresh(act)
    return act

def create_paragraph(db: Session, paragraph_data: CreateAct):
    paragraph = Paragraph(**paragraph_data.model_dump())
    max_order = db.query(Paragraph).filter(Paragraph.project_id == paragraph_data.project_id).count()
    paragraph.order = max_order + 1 if max_order else 1
    db.add(paragraph)
    db.commit()
    db.refresh(paragraph)
    return paragraph