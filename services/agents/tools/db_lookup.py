from typing import List, Optional
from uuid import UUID
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
# Make sure Beat model is imported and has relevant fields (e.g., name, description, completed)
from models.models import Character, Project, Act, Beat
import logging

logger = logging.getLogger(__name__)

# --- Tool Argument Schemas ---

class CharacterLookupArgs(LangchainBaseModel):
    """Arguments for looking up character details."""
    character_name: Optional[str] = Field(None, description="The name of the character to look up. Use if character_id is not known.")
    character_id: Optional[UUID] = Field(None, description="The specific UUID of the character.")

class StoryLookupArgs(LangchainBaseModel):
    """Arguments for looking up story overview and acts."""
    pass

# --- NEW: Beat Lookup Schema ---
class BeatLookupArgs(LangchainBaseModel):
    """Arguments for looking up story beats (objectives)."""
    pass

# --- Tool Implementations ---

def db_character_lookup_tool(
    db: Session,
    project_id: UUID,
    character_id: Optional[UUID] = None,
    character_name: Optional[str] = None
) -> str:
    """
    Retrieves details for a specific character within a project,
    identified by ID or name. Fetches character info and traits.
    """
    logger.info(f"--- Running DB Character Lookup ---")
    logger.info(f"Project ID: {project_id}, Character ID: {character_id}, Character Name: {character_name}")

    query = db.query(Character).options(joinedload(Character.trait)) # Eager load traits

    if character_id:
        character = query.filter(
            Character.project_id == project_id,
            Character.id == character_id
        ).first()
    elif character_name:
        # Use exact match first for potentially better performance/accuracy if names are unique
        character = query.filter(
            Character.project_id == project_id,
            Character.name == character_name # Case-sensitive exact match
        ).first()
        # Fallback to case-insensitive search if exact match fails
        if not character:
            logger.info(f"Exact match for '{character_name}' failed, trying case-insensitive search.")
            character = query.filter(
                Character.project_id == project_id,
                Character.name.ilike(f"%{character_name}%") # Case-insensitive search
            ).first()

        if character:
            logger.info(f"Found character by name: {character.name} (ID: {character.id})")
        else:
             logger.warning(f"Character '{character_name}' not found by name in project {project_id}.")
    else:
        logger.error("Character lookup tool called without character_id or character_name.")
        return "Error: Character lookup requires either character_id or character_name."

    if not character:
        return f"Character not found for Project {project_id} with given ID/Name."

    # Format the result for the LLM
    result = f"Character Details for '{character.name}' (ID: {character.id}):\n"
    result += f"- Type: {character.type or 'N/A'}\n"
    result += f"- Description: {character.description or 'N/A'}\n"
    result += f"- Voice: {character.voice or 'N/A'}\n"
    # Safely access faction name if relationship exists and is loaded/accessible
    try:
        if character.faction:
             result += f"- Faction: {character.faction.name}\n"
    except Exception as e:
        logger.warning(f"Could not access faction name for character {character.id}: {e}")
        result += f"- Faction: Error accessing faction info\n"


    if character.trait:
        result += "- Traits:\n"
        for trait in character.trait:
            result += f"  - {trait.type} ({trait.label or 'General'}): {trait.description}\n"
    else:
        result += "- Traits: None defined.\n"

    logger.info(f"Character Lookup Result:\n{result}")
    return result

def db_story_lookup_tool(db: Session, project_id: UUID) -> str:
    """
    Retrieves the project overview and act descriptions for a given project.
    """
    logger.info(f"--- Running DB Story Lookup ---")
    logger.info(f"Project ID: {project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        logger.warning(f"Project with ID {project_id} not found for story lookup.")
        return f"Project with ID {project_id} not found."

    acts = db.query(Act).filter(Act.project_id == project_id).order_by(Act.order).all()

    # Format the result for the LLM
    result = f"Story Context for Project '{project.name}' (ID: {project_id}):\n"
    result += f"## Overview:\n{project.overview or 'No overview provided.'}\n" # Add project overview if available in model

    if acts:
        result += "\n## Acts:\n"
        for act in acts:
            result += f"- Act {act.order} ({act.name or 'Unnamed Act'}): {act.description or 'No description.'}\n"
    else:
        result += "\n## Acts:\nNo acts defined for this project yet.\n"

    logger.info(f"Story Lookup Result:\n{result}")
    return result

# --- MODIFIED: db_beat_lookup_tool ---
def db_beat_lookup_tool(db: Session, project_id: UUID) -> str:
    """
    Retrieves the story beats (objectives) and their completion status for a given project.
    """
    logger.info(f"--- Running DB Beat Lookup ---")
    logger.info(f"Project ID: {project_id}")

    # Assuming Beat model has 'name', 'description', 'completed' fields
    # Add ordering if relevant, e.g., by an 'order' field
    beats = db.query(Beat).filter(Beat.project_id == project_id).order_by(Beat.order).all() # Example ordering
    if not beats:
        logger.warning(f"Beats with project ID {project_id} not found for beat lookup.")
        return f"No story beats (objectives) found for project ID {project_id}."

    # Format the result for the LLM
    result = f"Story Beats/Objectives for Project ID {project_id}:\n"
    for beat in beats:
        status = "Completed" if beat.completed else "Not Completed"
        result += f"- {beat.name or 'Unnamed Beat'}: {beat.description or 'No description.'} [{status}]\n"

    logger.info(f"Beat Lookup Result:\n{result}")
    return result

# --- Tool Executor (Handles dispatching and DB session) ---

# Update the execute_db_tool function to use extracted names
def execute_db_tool(state: dict, db: Session) -> dict:
    """
    Parses the latest AI tool call, gets required context (like project_id),
    and executes the corresponding database lookup function based on SCHEMA NAME.
    Includes support for extracted character names.
    """
    messages = state['messages']
    last_message = messages[-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logger.error("execute_db_tool called without AIMessage or tool_calls in last message.")
        return {"messages": [ToolMessage(content="Error: Expected tool call not found.", tool_call_id="error_no_tool_call")]}

    # Assuming one tool call per turn for simplicity
    tool_call = last_message.tool_calls[0]
    tool_name = tool_call['name'] # SCHEMA NAME
    tool_args = tool_call['args']
    tool_call_id = tool_call['id']

    logger.info(f"Executing tool: '{tool_name}' with args: {tool_args}")

    project_id = state.get('project_id')
    if not project_id:
         logger.error("project_id missing in state during tool execution.")
         return {"messages": [ToolMessage(content="Error: project_id missing in state.", tool_call_id=tool_call_id)]}

    tool_result_content = ""

    try:
        if tool_name == CharacterLookupArgs.__name__:
            parsed_args = CharacterLookupArgs.parse_obj(tool_args)
            character_id = parsed_args.character_id or state.get('character_id')
            character_name = parsed_args.character_name
            
            # If character_name is None but we have extracted names, use the first one
            if not character_name and not character_id and "extracted_character_names" in state:
                extracted_names = state["extracted_character_names"]
                if extracted_names:
                    character_name = extracted_names[0]
                    logger.info(f"Using extracted character name: {character_name}")
            
            tool_result_content = db_character_lookup_tool(
                db=db,
                project_id=project_id,
                character_id=character_id,
                character_name=character_name
            )
        elif tool_name == StoryLookupArgs.__name__:
            tool_result_content = db_story_lookup_tool(
                db=db,
                project_id=project_id
            )
        # --- NEW: Handle Beat Lookup ---
        elif tool_name == BeatLookupArgs.__name__:
            tool_result_content = db_beat_lookup_tool(
                db=db,
                project_id=project_id
            )
        # --- End New ---
        else:
            logger.error(f"Unknown tool schema name received: '{tool_name}'")
            tool_result_content = f"Error: Unknown tool '{tool_name}' called."

    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        tool_result_content = f"Error executing tool {tool_name}: {str(e)}"

    logger.info(f"Tool '{tool_name}' result content length: {len(tool_result_content)}") # Log length instead of full content potentially
    return {"messages": [ToolMessage(content=tool_result_content, tool_call_id=tool_call_id)]}
