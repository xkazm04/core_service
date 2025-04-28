from typing import TypedDict, Annotated, Sequence, List, Optional
from uuid import UUID
import logging
from pydantic import BaseModel, Field
from schemas.agent import Suggestion
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from services.agents.pre_processors.name_extraction import extract_character_name
from services.agents.tools.db_lookup import (
    CharacterLookupArgs,
    StoryLookupArgs,
    BeatLookupArgs
)
from services.agents.executors.suggestion_manager import (
    get_suggestions_for_topic, 
    get_suggestion_prompt, 
    get_fallback_suggestions
)

class ChatResponse(BaseModel):
    response: str
    suggestions: List[Suggestion] = Field(default_factory=list)

logger = logging.getLogger(__name__)

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    project_id: Optional[UUID]
    character_id: Optional[UUID]
    request_type: Optional[str] # Add request_type to state
    extracted_character_names: Optional[List[str]] # Add this new field
    final_response: Optional[ChatResponse]

# --- LLM and Tool Binding ---
llm = ChatOpenAI(model="gpt-4.1-mini")
# model notes:
# -- gpt-4o-mini = is not able to fit into reasonable time limits, responses are often inaaccurate VS price
# -- gpt-4.1-mini = fair price, very fast VS little bit less accurate - GOTO FOR TESTING - FUNCTIONAL REQUESTS (e.g. "create a entity in db")
# -- gpt-4o = precise and quick VS expensive price
llm_with_tools = llm.bind_tools(
    [CharacterLookupArgs, StoryLookupArgs, BeatLookupArgs],
    tool_choice="auto"
)
# Bind the ChatResponse schema to the LLM for the final output generation
structured_llm = llm.with_structured_output(ChatResponse)

# --- Graph Nodes ---

# Add this new function before the graph definition


def call_model_for_tool_or_direct(state: AgentState):
    """
    Invokes the LLM. If tools were just used, it processes results.
    Otherwise, it responds directly or calls tools.
    It does NOT generate the final structured response yet.
    """
    messages = state['messages']
    # Check if the last message is a ToolMessage, indicating we need to process tool results
    if isinstance(messages[-1], ToolMessage):
        logger.info("--- Calling LLM to process tool results ---")
        # Just use the regular LLM, might call more tools or generate intermediate response
        response = llm_with_tools.invoke(messages)
    else:
        logger.info("--- Calling LLM for initial response or tool call ---")
        # Use the LLM with tool binding
        response = llm_with_tools.invoke(messages)

    logger.info(f"LLM intermediate response/tool call: {response}")
    return {"messages": [response]}

def tool_node_executor(state: AgentState, config: RunnableConfig):
    """Executes DB tools based on the last AI message."""
    logger.info("--- Executing Tool Node ---")
    db_session = config['configurable'].get('db_session')
    if not db_session:
        logger.error("DB Session not found in config for tool node execution!")
        last_message = state['messages'][-1]
        tool_call_id = last_message.tool_calls[0]['id'] if isinstance(last_message, AIMessage) and last_message.tool_calls else "error_no_tool_call_id"
        return {"messages": [ToolMessage(content="Error: Database connection not available.", tool_call_id=tool_call_id)]}
    
    # Get the last message
    last_message = state['messages'][-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logger.error("Expected AI message with tool calls, but found none")
        return {"messages": [SystemMessage(content="Error: No tool calls found in the last message.")]}
    
    # Handle each tool call
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_id = tool_call['id']
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        logger.info(f"Processing tool call: {tool_name} (ID: {tool_id})")
        
        try:
            result_content = ""
            
            # Check if tool is CharacterLookupArgs and handle extracted names
            if tool_name == CharacterLookupArgs.__name__:
                from services.agents.tools.db_lookup import db_character_lookup_tool
                
                parsed_args = CharacterLookupArgs.parse_obj(tool_args)
                character_id = parsed_args.character_id or state.get('character_id')
                character_name = parsed_args.character_name
                
                # If no character_id or name provided, check extracted_character_names
                if not character_id and not character_name and 'extracted_character_names' in state:
                    extracted_names = state.get('extracted_character_names', [])
                    if extracted_names:
                        character_name = extracted_names[0]
                        logger.info(f"Using extracted character name: {character_name}")
                
                result_content = db_character_lookup_tool(
                    db=db_session,
                    project_id=state['project_id'],
                    character_id=character_id,
                    character_name=character_name
                )
            elif tool_name == StoryLookupArgs.__name__:
                from services.agents.tools.db_lookup import db_story_lookup_tool
                result_content = db_story_lookup_tool(
                    db=db_session,
                    project_id=state['project_id']
                )
            elif tool_name == BeatLookupArgs.__name__:
                from services.agents.tools.db_lookup import db_beat_lookup_tool
                result_content = db_beat_lookup_tool(
                    db=db_session,
                    project_id=state['project_id']
                )
            else:
                result_content = f"Error: Unknown tool '{tool_name}'"
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            result_content = f"Error executing tool: {str(e)}"
        
        # Create a tool message with the result
        tool_messages.append(ToolMessage(
            content=result_content,
            tool_call_id=tool_id
        ))
    
    logger.info(f"Returning {len(tool_messages)} tool messages")
    return {"messages": tool_messages}


def generate_final_response(state: AgentState):
    """
    Calls the LLM bound with the ChatResponse schema to generate the final
    structured output including the text response and relevant suggestions.
    """
    logger.info("--- Generating Final Structured Response ---")
    messages = state['messages']
    request_type = state.get('request_type', 'general')
    character_id = state.get('character_id')
    
    # Get context-appropriate suggestions using the suggestion manager
    potential_suggestions = get_suggestions_for_topic(
        topic=request_type,
        entity_id=character_id,
        # Can add additional context parameters here
    )
    
    # Generate the suggestion prompt part
    suggestions_prompt_part = get_suggestion_prompt(
        topic=request_type,
        potential_suggestions=potential_suggestions,
        entity_id=character_id
    )

    # Construct a prompt for the structured LLM
    prompt_messages = messages + [
        SystemMessage(
            content=(
                f"Based on the entire conversation history and the context provided (including any tool results), generate a helpful and informative text response. "
                f"{suggestions_prompt_part}\n"
                f"Format your entire output as a JSON object matching the 'ChatResponse' schema, containing a 'response' string and a 'suggestions' list (which may be empty)."
            )
        )
    ]

    # Invoke the LLM configured for structured output
    try:
        structured_response = structured_llm.invoke(prompt_messages)
        logger.info(f"Structured LLM Response: {structured_response}")
        
        # Validate if it matches the Pydantic model (structured_llm should handle this)
        if isinstance(structured_response, ChatResponse):
             return {"final_response": structured_response}
        else:
             logger.error(f"Structured LLM output did not match ChatResponse schema: {structured_response}")
             # Fallback response
             fallback_resp = ChatResponse(
                 response="Sorry, I encountered an issue generating the final response format.",
                 suggestions=get_fallback_suggestions(request_type, character_id)
             )
             return {"final_response": fallback_resp}
    except Exception as e:
        logger.error(f"Error invoking structured LLM: {e}", exc_info=True)
        fallback_resp = ChatResponse(
            response=f"Sorry, an error occurred while generating the response: {e}",
            suggestions=get_fallback_suggestions(request_type, character_id)
        )
        return {"final_response": fallback_resp}


# --- Graph Logic (Edges) ---
def should_continue_or_finalize(state: AgentState) -> str:
    """
    Determines the next step: call tool, continue generation, or finalize.
    """
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage):
        if last_message.tool_calls:
            # LLM wants to call a tool
            tool_call = last_message.tool_calls[0]
            tool_name = tool_call['name']
            logger.info(f"LLM requested tool call: '{tool_name}'")
            known_tool_schemas = {
                CharacterLookupArgs.__name__,
                StoryLookupArgs.__name__,
                BeatLookupArgs.__name__
            }
            if tool_name in known_tool_schemas:
                logger.info(f"--- Decision: Call Tool ('{tool_name}') ---")
                return "call_tool"
            else:
                logger.warning(f"LLM requested unknown tool: '{tool_name}'. Finalizing.")
                return "finalize" # Unknown tool, go to final response generation
        else:
            # LLM generated a text response, potentially intermediate. Let's finalize.
            logger.info("--- Decision: Finalize Response ---")
            return "finalize"
    elif isinstance(last_message, ToolMessage):
        # Just got tool results, continue generation
        logger.info("--- Decision: Continue Generation (after tool) ---")
        return "continue_generation"
    else:
        # Should not happen in normal flow after entry point
        logger.warning("Unexpected message type at decision point. Finalizing.")
        return "finalize"


# --- Build the Langgraph Graph ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("extract_character_names", extract_character_name)
workflow.add_node("agent_tool_or_direct", call_model_for_tool_or_direct)
workflow.add_node("call_tool", tool_node_executor)
workflow.add_node("final_responder", generate_final_response) # New final node

# Define entry point - start with character name extraction
workflow.set_entry_point("extract_character_names") 

# Add edge from character extraction to agent
workflow.add_edge("extract_character_names", "agent_tool_or_direct")

# Add conditional edges
workflow.add_conditional_edges(
    "agent_tool_or_direct", # Source node
    should_continue_or_finalize, # Function to decide next step
    {
        "call_tool": "call_tool", # If tool call needed
        "finalize": "final_responder", # If no tool call, generate final response
        "continue_generation": "agent_tool_or_direct" # Should not be returned here, but handle defensively
    }
)

# Add edge from tool execution back to the agent to process results
workflow.add_edge("call_tool", "agent_tool_or_direct")

# The final_responder node is an end node in this path
workflow.add_edge("final_responder", END)


# --- Compile the Graph with Memory ---
memory = MemorySaver()
# compiled_graph defined in agent.py

# --- Main Execution (Placeholder) ---
if __name__ == "__main__":
    print("Agent definition loaded. Run via FastAPI application (e.g., agent.py).")
