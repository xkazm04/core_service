
## A. Question workflow - complete
1. **User interface**
User writes a request in chat window from React application in form of free text message without given structure. To achieve completion of user's task **we DO know enough information**
- Request is delivered via REST API
TBD structure of the request

TBD rewrite this part for full decomposure what is happening inside the code

1. The workflow starts with character name extraction via pre-processor `name_extraction.py`
2. Function pre-processing: parsing attributes from free text via pre-processors `intent_deteciton.py`
2. The agent processes messages in `call_model_for_tool_or_direct`
3. It uses tools via `tool_node_executor`
4. Operations are executed through `execute_suggestion_function`

The agent has prompts to detect execution opportunities through the `execution_detection_message` in `graph_nodes.py`.


---
## B. Question workflow - Incomplete
1. **User interface**
User writes a request in chat window from React application in form of free text message without given structure. To achieve completion of user's task **we DO NOT know enough information** and need to ask for further detail
- Request is delivered via REST API
TBD structure of the request

2. **Intent detection**
`extract_operation_intent`: Detects `operation_intent='character_create'`, `params={}`, `missing_params=['target_char_name']`. These are stored in `AgentState`.
3. **Executor map**
Workflow finds instructions based on the intent with `call_model_for_tool_or_direct` 
- Finds `operation_intent`.
- Sees `missing_params` is not empty.
- Constructs an AIMessage: "To proceed with `character_create`, I need some more information: `target_char_name`. Could you please provide it?"
- Returns this `message`. `operation_intent`, `operation_params`, and `missing_params` remain in the state.
4. **Tool decision - negative**
In this case there is no tool to call in `should_continue_or_finalize`, so it routes to finalize. The agent asks the user the question to specify name further
5. **User input #2**
User provides again information necessary and points above are retun in the same order, this time with extracter `target_char_name`
6. **Tool decision - positive**
- Finds a tool to execute database function for character POST. Success is then responded to the user
TBD - map response schema

---



## C. Suggestions 
