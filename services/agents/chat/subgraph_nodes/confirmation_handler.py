import logging
from typing import Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from ..agent_state import AgentState
from ..llm_config import llm
from ...templates.graph_instructions import CONFIRMATION_INTERPRETATION_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

class ConfirmationDecision(BaseModel):
    """Structured response for interpreting user's confirmation."""
    decision: str = Field(description="User's decision: 'yes', 'no', or 'modify'.")
    changes: Optional[Dict[str, Any]] = Field(None, description="If decision is 'modify', this contains the parameters to change or their new values.")
    reasoning: Optional[str] = Field(None, description="Brief reasoning for the decision or a message to relay if modification is complex.")

def handle_confirmation(state: AgentState) -> Dict[str, Any]:
    logger.info(f"--- Entering Confirmation Handler ---")
    pending_operation_details = state['pending_operation_details']
    messages = state['messages']
    last_human_message_content = ""
    if messages and isinstance(messages[-1], HumanMessage):
        last_human_message_content = messages[-1].content

    if not pending_operation_details:
        logger.error("Confirmation handler called without pending_operation_details.")
        return {"messages": [AIMessage(content="I seem to have lost track of what we were confirming. Could you please clarify?")]}

    logger.info(f"Awaiting confirmation for: {pending_operation_details}. User response: '{last_human_message_content}'")

    confirmation_llm = llm.with_structured_output(ConfirmationDecision)
    system_prompt_confirm_interpret = CONFIRMATION_INTERPRETATION_PROMPT_TEMPLATE.format(
        operation=pending_operation_details['operation'],
        params=pending_operation_details['params'],
        user_response=last_human_message_content
    )

    try:
        llm_confirm_response = confirmation_llm.invoke([
            SystemMessage(content=system_prompt_confirm_interpret),
            HumanMessage(content=last_human_message_content)
        ])
        decision = llm_confirm_response.decision
        changes = llm_confirm_response.changes
        reasoning = llm_confirm_response.reasoning
        logger.info(f"LLM confirmation decision: {decision}, changes: {changes}, reasoning: {reasoning}")

    except Exception as e:
        logger.error(f"Error interpreting confirmation with LLM: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="I had trouble understanding your response. Could you please clarify if you'd like to proceed, cancel, or change something?")],
            "awaiting_confirmation": True, # Remain in confirmation state
            "pending_operation_details": pending_operation_details,
        }

    if decision == "yes":
        logger.info(f"User confirmed via LLM. Proceeding with tool call for {pending_operation_details['operation']}")
        tool_call_id = f"t_{str(uuid4())}"
        tool_call = {
            "name": "ExecutorFunctionArgs",
            "args": {
                "function_name": pending_operation_details['operation'],
                "params": pending_operation_details['params']
            },
            "id": tool_call_id
        }
        return {
            "messages": [AIMessage(content=f"Alright, I will perform the action: {pending_operation_details['operation']}.", tool_calls=[tool_call])],
            "awaiting_confirmation": False,
            "pending_operation_details": None,
            "operation_intent": None, "operation_params": {}, "missing_params": [] # Clear intent
        }
    elif decision == "no":
        logger.info("User cancelled operation via LLM.")
        return {
            "messages": [AIMessage(content=reasoning or "Okay, I've cancelled the operation.")],
            "awaiting_confirmation": False, "pending_operation_details": None,
            "operation_intent": None, "operation_params": {}, "missing_params": []
        }
    elif decision == "modify":
        logger.info(f"User wants to modify operation via LLM. Changes: {changes}")
        if changes:
            updated_params = pending_operation_details['params'].copy()
            updated_params.update(changes)
            updated_op_details = {"operation": pending_operation_details['operation'], "params": updated_params}
            
            confirmation_question = f"Okay, I've updated the details for '{updated_op_details['operation']}'. New parameters are: {updated_op_details['params']}. Shall I proceed with these changes?"
            if updated_op_details['operation'] == "scene_create":
                confirmation_question = f"Understood. I've updated the scene details. New name: '{updated_params.get('scene_name', 'Unnamed Scene')}', new description: '{updated_params.get('scene_description', '[No description provided]')}' (Act: {updated_params.get('act_id', 'Default/First Act')}). Does this look correct now?"
            
            logger.info(f"Asking for re-confirmation with modified params: {confirmation_question}")
            return {
                "messages": [AIMessage(content=confirmation_question)],
                "awaiting_confirmation": True, # Remain in confirmation state
                "pending_operation_details": updated_op_details,
            }
        else:
            clarification_message = reasoning or f"I see you might want to change something regarding {pending_operation_details['operation']}. Could you please specify what you'd like to adjust?"
            logger.info("User wants to modify, but changes unclear. Asking for clarification.")
            return {
                "messages": [AIMessage(content=clarification_message)],
                "awaiting_confirmation": True, # Remain in confirmation state
                "pending_operation_details": pending_operation_details,
            }
    else:
        logger.warning(f"Unexpected decision from LLM: {decision}. Asking user to clarify.")
        return {
            "messages": [AIMessage(content=f"I'm a bit confused by the response regarding {pending_operation_details['operation']}. Could you please clarify if you want to proceed, cancel, or change details?")],
            "awaiting_confirmation": True, # Remain in confirmation state
            "pending_operation_details": pending_operation_details,
        }