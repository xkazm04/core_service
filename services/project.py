
from schemas.project import  ProjectUpdateSchema
from sqlalchemy.orm import Session
from database import get_db
from models.models import Project
from fastapi import Depends, HTTPException

def update_project_by_id(project_id: str, project_data: ProjectUpdateSchema, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update the project fields
    if project_data.name:
        project.name = project_data.name
    if project_data.type:
        project.type = project_data.type
    if project_data.genre:
        project.genre = project_data.genre
    if project_data.theme:
        project.theme = project_data.theme
    if project_data.concept:
        project.concept = project_data.concept
    if project_data.overview:
        project.overview = project_data.overview
    
    db.commit()
    db.refresh(project)
    
    return {"message": "Project updated successfully"}