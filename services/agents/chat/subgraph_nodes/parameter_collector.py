import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage
from ..agent_state import AgentState

logger = logging.getLogger(__name__)

def collect_parameters(state: AgentState) -> Dict[str, Any]:
    logger.info(f"--- Entering Parameter Collector ---")
    operation_intent = state['operation_intent']
    missing_params = state['missing_params']

    if not operation_intent or not missing_params:
        logger.warning("Parameter collector called without operation_intent or missing_params.")
        # This case should ideally be handled by routing logic before calling this node
        return {"messages": [AIMessage(content="I'm not sure what information I need. Could you clarify your request?")]}

    missing_params_str = ", ".join(missing_params)
    question = f"To proceed with '{operation_intent}', I need some more information: {missing_params_str}. Could you please provide it?"
    logger.info(f"Asking user for missing parameters: {missing_params_str} for intent {operation_intent}")
    
    return {
        "messages": [AIMessage(content=question)],
        # Keep intent, params, missing_params in state for the next cycle
        "operation_intent": operation_intent,
        "operation_params": state.get('operation_params', {}),
        "missing_params": missing_params,
        "awaiting_confirmation": False, # Not awaiting confirmation for the overall operation yet
        "pending_operation_details": None
    }