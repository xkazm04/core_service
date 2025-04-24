from models.models import Act, Project, Beat
from sqlalchemy.orm import Session
from database import get_db
from fastapi import Depends, HTTPException

# Input = project_id
# 1. Get Project.overview of given project 
# 2. Get all Acts of the project and retrieve Act.name and Act.description, sorted by Act.order
# 3. Get all Beats of the project and retrieve Beat.name and Beat.description, sorted by Beat.order
# 4. Compose all data into a prompt template - Prepare the template in separate file
# 5. Return the filled prompt template

def compose_story(project_id: str, db: Session = Depends(get_db)) -> str:
    """
    Compose a story based on the project ID.
    
    Args:
        project_id (str): The ID of the project to compose the story for.
        
    Returns:
        str: The composed story.
    """
    # Get project overview
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_overview = project.overview
    # Get acts and beats
    acts = db.query(Act).filter(Act.project_id == project_id).order_by(Act.order).all()
    beats = db.query(Beat).filter(Beat.project_id == project_id).order_by(Beat.order).all()
    
    # Import the template and compose it with variables
    template = get_story_prompt_template()
    
    # Format acts and beats into structured text
    formatted_acts = format_acts(acts)
    formatted_beats = format_beats(beats)
    
    # Fill the template with the project data
    composed_prompt = template.format(
        project_overview=project_overview,
        acts_section=formatted_acts,
        beats_section=formatted_beats
    )
    
    return composed_prompt


def get_story_prompt_template() -> str:
    """
    Returns the template for story composition.
    
    This template structures story project information for an LLM to help
    users develop book or game stories.
    
    Returns:
        str: The story prompt template with placeholders.
    """
    template = """
    # Story Development Assistant

    ## Story high-level description
    {project_overview}

    ### Acts
    {acts_section}

    ### Key Story Beats
    {beats_section}

    ---

    Based on the project overview, acts, and key story beats provided above, please help develop this story idea further.
    You can suggest:
    - Character development opportunities
    - Plot refinements
    - Thematic elements to explore
    - Potential conflicts and resolutions
    - World-building elements
    - Dialog snippets for key moments

    Feel free to ask clarifying questions if you need more information about any aspect of the story.
    """
    return template


def format_acts(acts):
    """
    Format the acts data into a structured text section.
    
    Args:
        acts (List): List of Act objects with name and description attributes.
        
    Returns:
        str: Formatted acts section.
    """
    if not acts:
        return "No acts defined yet."
    
    formatted_acts = ""
    for i, act in enumerate(acts):
        formatted_acts += f"#### Act {i+1}: {act.name}\n{act.description}\n\n"
    
    return formatted_acts.strip()


def format_beats(beats):
    """
    Format the beats data into a structured text section.
    
    Args:
        beats (List): List of Beat objects with name and description attributes.
        
    Returns:
        str: Formatted beats section.
    """
    if not beats:
        return "No story beats defined yet."
    
    formatted_beats = ""
    for i, beat in enumerate(beats):
        formatted_beats += f"#### Beat {i+1}: {beat.name}\n{beat.description}\n\n"
    
    return formatted_beats.strip()