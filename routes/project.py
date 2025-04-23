from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.project import ProjectSchema, ProjectEvaluateRequestSchema, ProjectUpdateSchema
from database import get_db
from models.models import Project, Character
from services.project import update_project_by_id
from services.project_builder import create_project

router = APIRouter(tags=["Projects"])

@router.post("/")
def create_project_api(project_data: ProjectSchema, db: Session = Depends(get_db)):
    project = create_project(project_data, db)
    if not project:
        raise HTTPException(status_code=400, detail="Project creation failed")
    return {"message": "Project created successfully", "project_id": str(project.id)}


@router.get("/")
def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects if projects else []


@router.delete("/{project_id}")
def delete_project_by_id_endpoint(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


@router.get("/user/{user_id}")
def get_projects_by_user_id(user_id: str, db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.user == user_id).all()
    return projects if projects else []


@router.get("/{project_id}")
def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}")
def update_project(project_id: str, project_data: ProjectUpdateSchema, db: Session = Depends(get_db)):
    result = update_project_by_id(project_id, project_data, db)
    return result


@router.post("/evaluate")
def evaliate_project(project_data: ProjectEvaluateRequestSchema, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Evaluation 
    #1. How many characters are in the project
    characters = db.query(Character).filter(Character.project_id == project_data.project_id).all()
    num_characters = len(characters)
    #2. How many characters have assigned voices
    assigned_characters = len([c for c in characters if c.voice is not None])
    
    return {"message": "Project evaluation started"}