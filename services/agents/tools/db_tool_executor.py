"""
Database tool executor - handles dispatching and session management
"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from langchain_core.messages import AIMessage, ToolMessage

from .tool_schemas import (
    CharacterLookupArgs, 
    StoryLookupArgs, 
    BeatLookupArgs, 
    ProjectGapAnalysisArgs,
    SceneLookupArgs
)
from .db_character_tools import db_character_lookup_tool
from .db_story_tools import db_story_lookup_tool, db_beat_lookup_tool, db_scene_lookup_tool
from .db_analysis_tools import db_gap_analysis_tool

logger = logging.getLogger(__name__)

def execute_db_tool(state: Dict[str, Any], db: Session) -> Dict[str, Any]:
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
        elif tool_name == BeatLookupArgs.__name__:
            tool_result_content = db_beat_lookup_tool(
                db=db,
                project_id=project_id
            )
        elif tool_name == ProjectGapAnalysisArgs.__name__:
            parsed_args = ProjectGapAnalysisArgs.parse_obj(tool_args)
            tool_result_content = db_gap_analysis_tool(
                db=db,
                project_id=project_id,
                topic=parsed_args.topic,
                character_id=parsed_args.character_id or state.get('character_id')
            )
        elif tool_name == SceneLookupArgs.__name__:
            parsed_args = SceneLookupArgs.parse_obj(tool_args)
            tool_result_content = db_scene_lookup_tool(
                db=db,
                project_id=project_id,
                scene_id=parsed_args.scene_id
            )
        else:
            logger.error(f"Unknown tool schema name received: '{tool_name}'")
            tool_result_content = f"Error: Unknown tool '{tool_name}' called."

    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        tool_result_content = f"Error executing tool {tool_name}: {str(e)}"

    logger.info(f"Tool '{tool_name}' result content length: {len(tool_result_content)}") 
    return {"messages": [ToolMessage(content=tool_result_content, tool_call_id=tool_call_id)]}