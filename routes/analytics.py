from fastapi import APIRouter,HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from uuid import UUID
from schemas.analytics import ProjectAnalysisResponse
from services.project_analysis import analyze_project_status

router = APIRouter(tags=["Anal"])

@router.get("/project/{project_id}", response_model=ProjectAnalysisResponse)
async def get_project_analysis(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Analyze the current state of a project and return a summary of its completion status.
    
    Returns a detailed breakdown of:
    - Which project fields are filled
    - Character traits completion status
    - Scene descriptions completion status
    - Beat completion statistics
    """
    try:
        analysis_result = analyze_project_status(db, project_id)
        return analysis_result
    except ValueError as e:
        # Handle case where project is not found
        if f"Project with ID {project_id}" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
