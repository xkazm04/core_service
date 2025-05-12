"""
Configurations for feature-specific logic within the agent, 
such as LLM-powered parameter refinement for specific operations.
"""

SCENE_DESCRIPTION_REFINEMENT_PROMPT_TEMPLATE = """
You are a creative assistant helping to write a scene description.
The user wants to create a scene named '{scene_name}' for Act '{act_id}'.
Their current idea for the description is: '{current_description}'.
The user's original request or context was: '{user_request_context}'

Please refine and elaborate on the scene description to make it more engaging, vivid, and suitable for the scene context in a maximum of 50 words.
Respond with only the new, improved scene description text. Keep it short yet descriptive.
"""


PARAMETER_REFINEMENT_CONFIGS = {
    "scene_create": [
        {
            "parameter_name": "scene_description",
            "prompt_template": SCENE_DESCRIPTION_REFINEMENT_PROMPT_TEMPLATE,
            "context_vars_for_template": {
                "scene_name": "scene_name",       # Looks for 'scene_name' in operation_params
                "act_id": "act_id",             # Looks for 'act_id' in operation_params
                "current_description": "scene_description" # The current value of the parameter being refined
            },
            "default_values_for_template": { # Default values if context_vars are not found
                "scene_name": "Unnamed Scene",
                "act_id": "First Act"
            },
            "user_message_context_var": "user_request_context", # Template variable for last_human_message_content
            "trigger_conditions": {
                "parameter_value_equals": ["[Please describe the scene]"],
                "user_message_contains": [
                    "improve this description",
                    "make it more",
                    "elaborate on",
                    "refine description"
                ]
            }
        }
        # Add other parameter refinements for "scene_create" here if needed
    ]
    # Add other operation_intents and their refinement configs here
    # e.g., "character_create": [ { ...config for character bio refinement... } ]
}