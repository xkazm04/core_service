# Agent state
The agent's state is managed by the `AgentState` TypedDict (defined in [`core_service.services.agents.chat.agent_state.AgentState`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\agent_state.py)), which includes messages, project/character/act IDs, operation intents, parameters, and flags for confirmation or database updates.
System prompts and certain operational configurations (like `CONFIRMATION_REQUIRED_OPERATIONS`) are managed in [`core_service.services.agents.chat.graph_instructions.py`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\graph_instructions.py).

# Workflow explained
The agent uses a LangGraph workflow defined in [`core_service.services.agents.chat_agent.compiled_graph`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat_agent.py). The workflow is composed of several specialized nodes.

## A. Question workflow - complete
User writes a request with enough information for the agent to act.

Request is delivered via REST API to [`core_service.routes.agent.chat_endpoint`](c:\Users\kazda\dac\StoryTeller\core_service\routes\agent.py) with parameters like:
- `user_id`
- `message` - User's text.
- `type` - Topic hint (e.g., 'character', 'story', 'general').
- `project_id`
- `character_id` (optional)
- `act_id` (optional)
- `chat_session_id`
- `be_function` (optional, for direct function execution from UI)
- `function_params` (optional, params for `be_function`)

1.  **Initial State & Graph Entry**:
    - [`chat_endpoint`](c:\Users\kazda\dac\StoryTeller\core_service\routes\agent.py) prepares an `initial_state`.
    - The LangGraph workflow starts at the `extract_operations` node.

2.  **Intent & Parameter Extraction (`extract_operations` node)**:
    - Calls [`core_service.services.agents.pre_processors.intent_detection.extract_operation_intent`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\pre_processors\intent_detection.py) to identify `operation_intent`, `operation_params`, `missing_params`, etc., updating `AgentState`.

3.  **Initial Routing (`route_initial_request` conditional logic in `chat_agent.py`)**:
    - Based on `AgentState` (e.g., `awaiting_confirmation`, `operation_intent`, `missing_params`), the workflow routes to one of the specialized handler nodes:
        - `handle_confirmation_node`: If `awaiting_confirmation` is true.
        - `collect_parameters_node`: If `operation_intent` is present but has `missing_params`.
        - `process_intent_node`: If `operation_intent` is present and `missing_params` is empty.
        - `call_general_llm_node`: Otherwise (e.g., general chat, no clear intent).

4.  **Specialized Handler Nodes (in `core_service/services/agents/chat/subgraph_nodes/`)**:
    *   **`handle_confirmation_node` ([`confirmation_handler.py`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\subgraph_nodes\confirmation_handler.py))**:
        - If the agent was awaiting confirmation for an operation.
        - Uses an LLM (with `CONFIRMATION_INTERPRETATION_PROMPT_TEMPLATE`) to interpret the user's response ("yes", "no", "modify").
        - If "yes": Prepares a tool call for `ExecutorFunctionArgs`.
        - If "no": Generates a cancellation message.
        - If "modify": Updates parameters (potentially using LLM for changes) and re-asks for confirmation.
        - Routes to `route_after_subgraph_processing`.
    *   **`collect_parameters_node` ([`parameter_collector.py`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\subgraph_nodes\parameter_collector.py))**:
        - If an intent was detected but requires more parameters.
        - Constructs an AIMessage asking the user for the `missing_params`.
        - Routes directly to `final_responder_node`.
    *   **`process_intent_node` ([`intent_processor.py`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\subgraph_nodes\intent_processor.py))**:
        - If an intent is present with all necessary parameters.
        - **Parameter Refinement**: For certain operations (e.g., `scene_create`), it may use an LLM (with `SCENE_DESCRIPTION_REFINEMENT_PROMPT_TEMPLATE`) to refine parameters like `scene_description`.
        - **Confirmation Check**: If `operation_intent` is in `CONFIRMATION_REQUIRED_OPERATIONS` (from `graph_instructions.py`), it generates an AIMessage asking for user confirmation and sets `awaiting_confirmation` to `True`.
        - **Direct Execution**: If not requiring confirmation, it prepares a direct tool call (e.g., `ExecutorFunctionArgs`).
        - Routes to `route_after_subgraph_processing`.
    *   **`call_general_llm_node` ([`general_llm_caller.py`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\subgraph_nodes\general_llm_caller.py))**:
        - Invoked if no specific intent path is active, or after a tool execution to process results.
        - Uses `llm_with_tools` with `GENERAL_LLM_SYSTEM_PROMPT` or `TOOL_ERROR_RECOVERY_SYSTEM_PROMPT`.
        - The LLM can either respond directly or decide to call a tool.
        - Routes to `route_after_subgraph_processing`.

5.  **Secondary Routing (`route_after_subgraph_processing` conditional logic in `chat_agent.py`)**:
    - After `handle_confirmation_node`, `process_intent_node`, or `call_general_llm_node`.
    - If the last AIMessage from these nodes contains tool calls: Routes to `call_tool_node`.
    - Else (no tool calls, direct AI response, or question for user): Routes to `final_responder_node`.

6.  **Tool Execution (`call_tool_node` using `tool_node_executor` from [`graph_nodes.py`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\graph_nodes.py))**:
    - Iterates through `tool_calls` from the AIMessage.
    - Executes functions via `ExecutorFunctionArgs` (calling `execute_suggestion_function`) or other specific tools (e.g., `CharacterLookupArgs` via `execute_db_tool`).
    - Appends `ToolMessage`(s) with results to `AgentState.messages`.
    - Routes to `call_general_llm_node` to process tool results.

7.  **Final Response Generation (`final_responder_node` using `generate_final_response` from [`graph_nodes.py`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\graph_nodes.py))**:
    - Generates a structured `ChatResponse` (text response + suggestions) using `structured_llm`.
    - Includes `be_function` and `db_updated` status.
    - Routes to `END`.

---
## B. Question workflow - Incomplete
User writes a request, but not enough information is provided.

1.  **User interface & Initial State**: Same as A.1.
2.  **Intent detection (`extract_operations` node)**: Detects `operation_intent` and non-empty `missing_params`.
3.  **Initial Routing (`route_initial_request`)**: Routes to `collect_parameters_node`.
4.  **Parameter Collection (`collect_parameters_node`)**:
    - Constructs an AIMessage asking for the `missing_params`.
    - Routes to `final_responder_node`.
5.  **Deliver Question (`final_responder_node`)**: Crafts and delivers the question for missing parameters.
6.  **User input #2**: User provides the missing information.
7.  **Second Cycle - Intent & Parameter Extraction (`extract_operations` node)**: Processes new message. `missing_params` should now be empty for the original intent.
8.  **Second Cycle - Initial Routing (`route_initial_request`)**: Routes to `process_intent_node`.
9.  **Second Cycle - Intent Processing (`process_intent_node`)**:
    - Handles the intent, potentially asking for confirmation (if required by `CONFIRMATION_REQUIRED_OPERATIONS`) or preparing a tool call.
    - Routes to `route_after_subgraph_processing`.
10. **Subsequent Flow**: Continues as per "A. Question workflow - complete" from step A.5 or A.6, leading to tool execution or final response.

---
## C. Suggestions-driven workflow (User clicks a suggestion in UI)
This flow is typically initiated when the frontend sends a `ChatRequest` with `be_function` and `function_params` already populated.

1.  **User Interface & Initial State**:
    - `initial_state` is prepared with `operation_intent = request.be_function`, `operation_params = request.function_params`, and `missing_params` empty.
2.  **Intent & Parameter Extraction (`extract_operations` node)**:
    - This node runs. `extract_operation_intent` should ideally preserve pre-filled `operation_intent` and `operation_params` if `be_function` was provided directly.
3.  **Initial Routing (`route_initial_request`)**:
    - Since `operation_intent` is present and `missing_params` is empty, it routes to `process_intent_node`.
4.  **Intent Processing (`process_intent_node`)**:
    - The pre-set `operation_intent` (from `be_function`) and `operation_params` are used.
    - If `operation_intent` is in `CONFIRMATION_REQUIRED_OPERATIONS`:
        - Asks for user confirmation. Routes to `final_responder_node` (via `route_after_subgraph_processing`).
        - User confirms. Next cycle, `route_initial_request` routes to `handle_confirmation_node`.
        - `handle_confirmation_node` processes "yes" and prepares tool call. Routes to `call_tool_node` (via `route_after_subgraph_processing`).
    - Else (not requiring confirmation):
        - Directly prepares a tool call for `ExecutorFunctionArgs`. Routes to `call_tool_node` (via `route_after_subgraph_processing`).
5.  **Tool Execution (`call_tool_node`)**:
    - Executes the function. Sets `be_function` and `db_updated` in `AgentState`.
    - Routes to `call_general_llm_node`.
6.  **Process Tool Result (`call_general_llm_node`)**:
    - Processes the `ToolMessage`. Typically leads to a direct response.
    - Routes to `final_responder_node` (via `route_after_subgraph_processing`).
7.  **Final Response Generation (`final_responder` node)**:
    - [`generate_final_response`](c:\Users\kazda\dac\StoryTeller\core_service\services\agents\chat\graph_nodes.py) creates the structured `ChatResponse`.
    - The `response.be_function` field is populated with the name of the function that was executed.
    - The `response.db_updated` field reflects whether the database was modified.
    - New suggestions are generated for the next interaction.
    - Routes to `END`.