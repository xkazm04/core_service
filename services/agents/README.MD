1. The workflow starts with character name extraction via pre-processor `name_extraction.py`
2. Function pre-processing: parsing attributes from free text via pre-processors `intent_deteciton.py`
2. The agent processes messages in `call_model_for_tool_or_direct`
3. It uses tools via `tool_node_executor`
4. Operations are executed through `execute_suggestion_function`

The agent has prompts to detect execution opportunities through the `execution_detection_message` in `graph_nodes.py`.


---

## Missing intents
User writes "create a chracter" in chat window
1. `extract_operation_intent`: Detects `operation_intent='character_create'`, `params={}`, `missing_params=['target_char_name']`. These are stored in AgentState.

2. extract_operation_intent: Detects operation_intent='character_create', params={}, missing_params=['target_char_name']. These are stored in AgentState.
3. call_model_for_tool_or_direct:
Finds operation_intent.
Sees missing_params is not empty.
Constructs an AIMessage: "To proceed with 'character_create', I need some more information: target_char_name. Could you please provide it?"
Returns this message. operation_intent, operation_params, and missing_params remain in the state.
4. should_continue_or_finalize: The AIMessage has no tool calls, so it routes to finalize. The agent asks the user the question.
5. User Responds: "Call him Sith."
6. extract_operation_intent (Next Turn):
It gets the new message "Call him Sith."
Ideally, detect_operation_intent should now be prompted with the context that an operation (character_create) is ongoing and some parameters (target_char_name) are being sought. It should then extract {'target_char_name': 'Sith'}.
extract_operation_intent updates AgentState: operation_intent='character_create', operation_params={'target_char_name': 'Sith'}, missing_params=[].
7. call_model_for_tool_or_direct (Next Turn):
Finds operation_intent.
Sees missing_params is now empty.
Creates the tool call for character_create with {'target_char_name': 'Sith'}.
Returns the AIMessage with the tool call and clears operation_intent, operation_params, missing_params from the state.
8. should_continue_or_finalize: Routes to call_tool.
9. tool_node_executor: Executes character_create successfully with the name "Sith".
Further Enhancement (Contextual Intent Detection):

---
For step 6 to work robustly, detect_operation_intent should be aware of the ongoing operation. You can pass the current operation_intent, collected_params, and missing_params from the state into detect_operation_intent. Then, its system prompt can be adjusted:

If an operation is ongoing, the prompt should instruct the LLM to focus on extracting the still missing parameters from the new user message, in the context of the already known operation and collected parameters.
If no operation is ongoing, it uses the general intent detection prompt.
This makes the LLM's task more targeted during conversational parameter collection.

