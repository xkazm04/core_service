"""
Utility functions for handling messages and ensuring tool call integrity
"""
import logging
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, SystemMessage

logger = logging.getLogger(__name__)

def ensure_tool_call_integrity(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Ensures all tool calls in the message list have corresponding responses.
    If a tool call doesn't have a response, a dummy response is added.
    """
    if not messages:
        return messages
    
    # Track which tool calls need responses
    pending_tool_calls: Dict[str, Dict[str, Any]] = {}
    new_messages: List[BaseMessage] = []
    
    # First pass - identify tool calls and mark those that are responded to
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            # Record all tool calls from this message
            for tool_call in msg.tool_calls:
                tc_id = tool_call.get('id')
                if tc_id:
                    pending_tool_calls[tc_id] = tool_call
            
            new_messages.append(msg)
        elif isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            # This is a tool response, mark the corresponding call as handled
            tc_id = msg.tool_call_id
            if tc_id in pending_tool_calls:
                del pending_tool_calls[tc_id]
            
            new_messages.append(msg)
        else:
            # Not a tool call or response, pass through
            new_messages.append(msg)
    
    # If there are any pending tool calls, add dummy responses
    if pending_tool_calls:
        logger.warning(f"Adding {len(pending_tool_calls)} missing tool responses for: {list(pending_tool_calls.keys())}")
        for tc_id, tool_call in pending_tool_calls.items():
            tool_name = tool_call.get('name', 'unknown_tool')
            new_messages.append(ToolMessage(
                content=f"No response was provided for {tool_name} call",
                tool_call_id=tc_id
            ))
    
    return new_messages

def truncate_problematic_history(messages: List[BaseMessage], max_retries: int = 3) -> List[BaseMessage]:
    """
    Detect repeated errors or failures in conversation history and truncate if needed.
    This helps the agent recover from getting stuck in error loops.
    """
    if len(messages) < 4:  # Need at least a few messages to detect patterns
        return messages
        
    recent_errors = []
    recent_functions = [] # Stores function names from most recent to oldest
    error_pattern_detected = False
    
    # Scan up to the last 10 messages (5 pairs of AI/Tool or Human/AI)
    # to collect recent function calls and errors.
    # We iterate from the end of the messages list.
    for i in range(min(10, len(messages))):
        msg_idx = len(messages) - 1 - i
        msg = messages[msg_idx]
        
        if isinstance(msg, ToolMessage) and ("error" in msg.content.lower() or "failed" in msg.content.lower()):
            recent_errors.append(msg.content) # Order doesn't strictly matter for counting errors
            
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == "ExecutorFunctionArgs":
                    function_name = tool_call.get('args', {}).get('function_name')
                    if function_name:
                        # Insert at the beginning to keep recent_functions ordered from most recent to oldest
                        recent_functions.insert(0, function_name) 
    
    # Condition 1: Same function called multiple times recently AND the latest attempt resulted in an error.
    if len(recent_functions) >= 2 and recent_functions[0] == recent_functions[1]:
        # Check if the most recent ToolMessage (corresponding to recent_functions[0]) indicates an error.
        # We need to find the AIMessage that made the call recent_functions[0] and check its subsequent ToolMessage.
        last_function_call_ai_message_idx = -1
        # Find the AIMessage that made the most recent recorded function call (recent_functions[0])
        for i_search in range(len(messages) - 1, -1, -1):
            search_msg = messages[i_search]
            if isinstance(search_msg, AIMessage) and search_msg.tool_calls:
                # Check if this AIMessage made the call recent_functions[0]
                is_target_call = False
                for tc in search_msg.tool_calls:
                    if tc.get('name') == "ExecutorFunctionArgs" and \
                       tc.get('args', {}).get('function_name') == recent_functions[0]:
                        is_target_call = True
                        break
                if is_target_call:
                    # Check if this is indeed the *most recent* such call among the messages scanned
                    # by comparing its position with where recent_functions[0] would have been sourced from.
                    # This is a bit complex; simpler is to assume recent_functions[0] corresponds to the latest such AI message.
                    # For robustness, we'd need to track indices, but let's try a common case.
                    # We assume recent_functions[0] is from one of the last few AIMessages.
                    last_function_call_ai_message_idx = i_search
                    break # Found the most recent AIMessage that called recent_functions[0]

        if last_function_call_ai_message_idx != -1 and last_function_call_ai_message_idx + 1 < len(messages):
            next_msg_after_ai = messages[last_function_call_ai_message_idx + 1]
            # Ensure this next_msg is a ToolMessage responding to the AI message's tool call
            if isinstance(next_msg_after_ai, ToolMessage) and \
               hasattr(messages[last_function_call_ai_message_idx], 'tool_calls') and \
               messages[last_function_call_ai_message_idx].tool_calls and \
               next_msg_after_ai.tool_call_id == messages[last_function_call_ai_message_idx].tool_calls[0].get('id') and \
               ("error" in next_msg_after_ai.content.lower() or "failed" in next_msg_after_ai.content.lower()):
                error_pattern_detected = True
                logger.warning(f"Repetitive function call '{recent_functions[0]}' with a recent error detected. Triggering truncation.")
        
    # Condition 2: Multiple errors in succession (based on the count of error messages found)
    if len(recent_errors) >= max_retries:
        error_pattern_detected = True
        logger.warning(f"Multiple ({len(recent_errors)}) recent errors detected, triggering truncation.")
    
    if error_pattern_detected:
        logger.warning("Detected error loop pattern - truncating conversation history for recovery.")
        
        # Truncation logic: keep at least the system message and the first user message, or more if possible.
        # A simple strategy: remove the last few exchanges.
        # Let's try removing the last `max_retries` pairs of messages (AI + Tool or Human + AI).
        # This needs to be done carefully to not create new inconsistencies.
        # A safer simple truncation is to go back to a point before the suspected loop.
        # For now, let's use the existing truncation point logic if it was working for actual errors.
        # The key is that error_pattern_detected is now more accurate.

        # Keep at least the first 2 messages (e.g., System, Human)
        # Reduce history by roughly the number of retries (pairs of messages)
        num_messages_to_remove = max_retries * 2 
        truncation_point = len(messages) - num_messages_to_remove
        
        # Ensure we keep at least 2 messages, and not negative index
        truncation_point = max(2, truncation_point) 
        
        # Ensure truncation_point does not exceed current length
        truncation_point = min(truncation_point, len(messages))

        if truncation_point < len(messages):
            logger.info(f"Truncating messages from {len(messages)} to {truncation_point}")
            truncated_messages = messages[:truncation_point]
            # After truncation, ensure the last message isn't an AIMessage with an unfulfilled tool_call
            if truncated_messages and isinstance(truncated_messages[-1], AIMessage) and truncated_messages[-1].tool_calls:
                 # If so, it's safer to remove that last AIMessage as well, or try to add a dummy tool response.
                 # For simplicity, let's remove it if it's the new last message.
                 logger.warning("Last message after truncation is an AIMessage with tool_calls. Removing it to prevent API error.")
                 truncated_messages = truncated_messages[:-1]
                 if not truncated_messages and messages: # If removing it made it empty, keep original first message
                     truncated_messages = [messages[0]]


            # Ensure we always return at least one message if the original list wasn't empty
            if not truncated_messages and messages:
                return [messages[0]] # Fallback to just the first message
            elif not truncated_messages and not messages:
                return []

            return truncated_messages
        else:
            # No truncation needed based on this calculation
            return messages
            
    return messages