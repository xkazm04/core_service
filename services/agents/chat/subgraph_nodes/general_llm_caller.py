import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from ..agent_state import AgentState
from ..llm_config import llm_with_tools
from ...templates.graph_instructions import  GENERAL_LLM_SYSTEM_PROMPT, TOOL_ERROR_RECOVERY_SYSTEM_PROMPT

from ..message_utils import truncate_problematic_history, ensure_tool_call_integrity


logger = logging.getLogger(__name__)

def call_general_llm(state: AgentState) -> Dict[str, Any]:
    logger.info("--- Entering General LLM Caller ---")
    
    current_messages = ensure_tool_call_integrity(state['messages'])
    current_messages = truncate_problematic_history(current_messages)

    # This node is called when no specific intent is active,
    # or after a tool call to process results.
    
    if current_messages and isinstance(current_messages[-1], ToolMessage):
        logger.info("--- Calling LLM to process tool results ---")
        # If this tool message contains an error, add recovery guidance
        if "error" in current_messages[-1].content.lower(): # Simple check
            recovery_message = SystemMessage(content=TOOL_ERROR_RECOVERY_SYSTEM_PROMPT)
            # Insert before the last ToolMessage for context, or append
            # For simplicity, appending here. Better logic might insert it before the tool message.
            current_messages.append(recovery_message)
            
        response = llm_with_tools.invoke(current_messages)
    else:
        logger.info("--- Calling LLM for general response or new tool call ---")
        # Add system instruction to detect execution opportunities
        # Check if system prompt already exists to avoid duplication if re-entering
        has_general_system_prompt = any(
            isinstance(msg, SystemMessage) and msg.content == GENERAL_LLM_SYSTEM_PROMPT
            for msg in current_messages
        )
        
        augmented_messages = list(current_messages) # Make a mutable copy
        if not has_general_system_prompt:
             # Insert general system prompt before the last human message if possible, or at the end
            inserted = False
            if augmented_messages and isinstance(augmented_messages[-1], HumanMessage):
                augmented_messages.insert(-1, SystemMessage(content=GENERAL_LLM_SYSTEM_PROMPT))
                inserted = True
            if not inserted: # If no human message or empty, just append
                augmented_messages.append(SystemMessage(content=GENERAL_LLM_SYSTEM_PROMPT))

        response = llm_with_tools.invoke(augmented_messages)

    logger.info(f"General LLM response/tool call: {response}")
    return {
        "messages": [response],
        "operation_intent": None, "operation_params": {}, "missing_params": [], # Reset intent state
        "awaiting_confirmation": False, "pending_operation_details": None # Reset confirmation state
    }