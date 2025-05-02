from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Paragraph
from typing import List
from uuid import UUID
from schemas.paragraph import ParagraphResponse, CreateParagraph, EditParagraph
from services.story import create_paragraph

# Written story paragraphs on the project level

router = APIRouter(tags=["Paragraphs"])

# ------ Paragraph API ------------
#1. Get project paragraphs by project ID
@router.get("/project/{project_id}", response_model=List[ParagraphResponse])
def get_paragraphs_by_project(project_id: UUID, db: Session = Depends(get_db)):
    paragraphs = db.query(Paragraph).filter(Paragraph.project_id == project_id).all()
    if not paragraphs:
        return []
    paragraphs.sort(key=lambda x: x.order)
    return paragraphs if paragraphs else []

#2. Create a new paragraph
@router.post("/")
def add_paragraph(paragraph_data: CreateParagraph, db: Session = Depends(get_db)):
    create_paragraph(db, paragraph_data)
    return {"message": "Paragraph created successfully"}


#3. Delete a paragraph 
@router.delete("/{paragraph_id}")
def delete_paragraph(paragraph_id: str, db: Session = Depends(get_db)):
    paragraph = db.query(Paragraph).filter(Paragraph.id == paragraph_id).first()
    if not paragraph:
        raise HTTPException(status_code=404, detail="Paragraph not found")
    db.delete(paragraph)
    db.commit()
    return {"message": "Paragraph deleted successfully"}

#4. Edit a paragraph by ID
@router.put("/")
def update_paragraph(paragraph_edit: EditParagraph, db: Session = Depends(get_db)):
    paragraph = db.query(Paragraph).filter(Paragraph.id == paragraph_edit.id).first()
    if not paragraph:
        raise HTTPException(status_code=404, detail="Paragraph not found")
    for key, value in paragraph_edit.model_dump(exclude_unset=True).items():
        setattr(paragraph, key, value)
    db.commit()
    db.refresh(paragraph)
    return {"message": "Paragraph updated successfully"}