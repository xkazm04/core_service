import logging
from typing import Dict, Any
from uuid import uuid4

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from ..agent_state import AgentState
from ..llm_config import llm
from ...templates.graph_instructions import CONFIRMATION_REQUIRED_OPERATIONS
from services.agents.templates.fn_processor_config import PARAMETER_REFINEMENT_CONFIGS
from services.agents.executor import EXECUTOR_MAP

logger = logging.getLogger(__name__)

def _trigger_refinement(param_value: Any, user_message: str, conditions: Dict) -> bool:
    """Checks if refinement should be triggered based on conditions."""
    if "parameter_value_equals" in conditions:
        if param_value in conditions["parameter_value_equals"]:
            return True
    if "user_message_contains" in conditions and user_message:
        for keyword in conditions["user_message_contains"]:
            if keyword in user_message.lower():
                return True
    return False

def process_intent(state: AgentState) -> Dict[str, Any]:
    logger.info(f"--- Entering Intent Processor ---")
    operation_intent = state['operation_intent']
    operation_params = state.get('operation_params', {})
    messages = state['messages']
    last_human_message_content = ""
    if messages and isinstance(messages[-1], HumanMessage):
        last_human_message_content = messages[-1].content

    if not operation_intent or operation_intent not in EXECUTOR_MAP:
        logger.warning(f"Intent processor called with invalid or no operation_intent: {operation_intent}")
        return {"messages": [AIMessage(content="I'm not sure how to proceed with that request. Could you try rephrasing?")]}

    refined_params = dict(operation_params)

    # --- Generic LLM-Powered Parameter Refinement ---
    if operation_intent in PARAMETER_REFINEMENT_CONFIGS:
        for config in PARAMETER_REFINEMENT_CONFIGS[operation_intent]:
            param_name_to_refine = config["parameter_name"]
            current_param_value = refined_params.get(param_name_to_refine)

            if param_name_to_refine in refined_params and \
               _trigger_refinement(current_param_value, last_human_message_content, config["trigger_conditions"]):
                
                logger.info(f"Attempting LLM refinement for parameter '{param_name_to_refine}' in operation '{operation_intent}'. Current value: {current_param_value}")

                prompt_template_vars = {}
                # Populate template variables from operation_params or defaults
                for tmpl_var, source_key in config.get("context_vars_for_template", {}).items():
                    prompt_template_vars[tmpl_var] = refined_params.get(source_key, config.get("default_values_for_template", {}).get(tmpl_var))
                
                # Add current value of the parameter being refined explicitly
                # This ensures 'current_description' or similar is always available if mapped to the parameter itself
                if "current_description" in config.get("context_vars_for_template", {}) and \
                    config["context_vars_for_template"]["current_description"] == param_name_to_refine:
                    prompt_template_vars["current_description"] = current_param_value


                if config.get("user_message_context_var") and last_human_message_content:
                    prompt_template_vars[config["user_message_context_var"]] = last_human_message_content
                
                try:
                    refinement_prompt_text = config["prompt_template"].format(**prompt_template_vars)
                    refinement_prompt_messages = [
                        SystemMessage(content=refinement_prompt_text),
                        HumanMessage(content=f"Refine this: {current_param_value}") # Generic human message part
                    ]
                    
                    refined_response = llm.invoke(refinement_prompt_messages)
                    if refined_response.content:
                        logger.info(f"LLM refined '{param_name_to_refine}' to: {refined_response.content}")
                        refined_params[param_name_to_refine] = refined_response.content
                    else:
                        logger.warning(f"LLM refinement for '{param_name_to_refine}' returned empty content.")
                except KeyError as ke:
                    logger.error(f"Missing key for prompt template during refinement of '{param_name_to_refine}': {ke}. Vars: {prompt_template_vars}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error during LLM refinement for '{param_name_to_refine}': {e}", exc_info=True)
                    # Proceed with original parameter value if refinement fails

    if operation_intent in CONFIRMATION_REQUIRED_OPERATIONS:
        logger.info(f"Intent '{operation_intent}' with params {refined_params} requires confirmation.")
        current_op_details = {"operation": operation_intent, "params": refined_params}
        
        confirmation_question = f"Okay, I'm ready to perform the operation: '{operation_intent}' with the following details: {refined_params}. Shall I proceed?"
        if operation_intent == "scene_create": 
            confirmation_question = f"I can create a scene named '{refined_params.get('scene_name', 'Unnamed Scene')}' with the description: '{refined_params.get('scene_description', '[No description provided]')}' (Act: {refined_params.get('act_id', 'Default/First Act')}). Does that sound right?"
        else: # Generic confirmation question
            confirmation_question = f"Okay, I'm ready to perform the operation: '{operation_intent}' with the following details: {refined_params}. Shall I proceed?"


        logger.info(f"Asking for confirmation: {confirmation_question}")
        return {
            "messages": [AIMessage(content=confirmation_question)],
            "awaiting_confirmation": True,
            "pending_operation_details": current_op_details,
            "operation_intent": None, "operation_params": {}, "missing_params": [] # Clear intent as it's now pending
        }
    else:
        logger.info(f"Executing non-confirmation operation: {operation_intent} with params {refined_params}")
        tool_call_id = f"t_{str(uuid4())}"
        tool_call = {
            "name": "ExecutorFunctionArgs",
            "args": {"function_name": operation_intent, "params": refined_params},
            "id": tool_call_id
        }
        return {
            "messages": [AIMessage(content=f"Okay, I'll proceed with {operation_intent}.", tool_calls=[tool_call])],
            "operation_intent": None, "operation_params": {}, "missing_params": [], # Clear intent
            "awaiting_confirmation": False, "pending_operation_details": None
        }