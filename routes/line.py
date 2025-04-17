from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
from models.models import Line, dialog_transitions
from uuid import UUID
from pydantic import BaseModel
from schemas.line import DialogLineCreate, DialogLineUpdate, LineCreate 

router = APIRouter(tags=["Line"])


# Create a new line
@router.post("/", response_model=dict)
def create_line_endpoint(line_data: LineCreate, db: Session = Depends(get_db)):
    # Fetch all lines in the scene to determine order
    lines = db.query(Line).filter(Line.scene_id == line_data.scene_id).all()
    order = len(lines) + 1

    # Create new line
    line = Line(
        character_id=line_data.character_id,
        scene_id=line_data.scene_id,
        text=line_data.text,
        tone=line_data.tone,
        order=order
    )

    db.add(line)
    db.commit()
    db.refresh(line)

    return {"message": "Line created successfully", "line_id": str(line.id)}

# Create a new dialog node
@router.post("/node", response_model=DialogLineCreate)
def create_dialog_line(dialog_data: DialogLineCreate, db: Session = Depends(get_db)):
    lines = db.query(Line).filter(Line.scene_id == dialog_data.scene_id).all()
    order = len(lines) + 1
    new_line = Line(
        scene_id=dialog_data.scene_id,
        character_id=dialog_data.character_id,
        text=dialog_data.text,
        tone=dialog_data.tone,
        x=dialog_data.x,
        y=dialog_data.y,
        is_final=dialog_data.is_final,
        predecessor_id=dialog_data.predecessor_id,
        order=order
    )
    db.add(new_line)
    db.commit()
    db.refresh(new_line)

    # Add successors
    for successor_id in dialog_data.successors:
        db.execute(
            dialog_transitions.insert().values(source_id=new_line.id, target_id=successor_id)
        )

    db.commit()
    return new_line

# Update a dialog line
@router.put("/node/{line_id}")
def update_dialog_line(line_id: UUID, update_data: DialogLineUpdate, db: Session = Depends(get_db)):
    line = db.query(Line).filter(Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Dialog line not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(line, key, value)

    # Update transitions
    if update_data.successors:
        db.execute(dialog_transitions.delete().where(dialog_transitions.c.source_id == line_id))
        for successor_id in update_data.successors:
            db.execute(dialog_transitions.insert().values(source_id=line_id, target_id=successor_id))

    db.commit()
    return {"message": "Dialog line updated"}

# Edit a line's tone
class LineToneUpdate(BaseModel):
    tone: str
@router.put("/{line_id}/tone")
def edit_line_tone_endpoint(line_id: str, tone_data: LineToneUpdate, db: Session = Depends(get_db)):
    line = db.query(Line).filter(Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found.")
    line.tone = tone_data.tone
    db.commit()
    return {"message": "Line tone updated successfully."}

# Edit a line's character_id
class LineCharacterUpdate(BaseModel):
    character_id: UUID
@router.put("/{line_id}/character")
def edit_line_character_endpoint(line_id: str, character_data: LineCharacterUpdate, db: Session = Depends(get_db)):
    line = db.query(Line).filter(Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found.")
    line.character_id = character_data.character_id
    db.commit()
    return {"message": "Line character updated successfully."}

# Edit a line's text
class LineTextUpdate(BaseModel):
    text: str
@router.put("/{line_id}/text")
async def edit_line_text_endpoint(
    line_id: str, 
    text_data: LineTextUpdate = Body(...), 
    db: Session = Depends(get_db)
):
    line = db.query(Line).filter(Line.id == line_id).first()
    
    if not line:
        raise HTTPException(status_code=404, detail="Line not found.")

    line.text = text_data.text  
    db.commit()
    db.refresh(line) 
    
    return {"message": "Line text updated successfully", "updated_text": line.text}

# Delete a line by id
@router.delete("/{line_id}")
def delete_line_endpoint(line_id: str, db: Session = Depends(get_db)):
    line = db.query(Line).filter(Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found.")
    db.delete(line)
    db.commit()
    return {"message": "Line deleted successfully."}

# Get all lines by scene_id
@router.get("/scene/{scene_id}")
def get_lines_by_scene_id_endpoint(scene_id: str, db: Session = Depends(get_db)):
    lines = db.query(Line).filter(Line.scene_id == scene_id).all()
    return lines if lines else []

# Get all lines by character_id
@router.get("/character/{character_id}")
def get_lines_by_character_id_endpoint(character_id: str, db: Session = Depends(get_db)):
    lines = db.query(Line).filter(Line.character_id == character_id).all()
    return lines if lines else []
