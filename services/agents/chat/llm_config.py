"""
LLM configuration and initialization for agent
"""
import logging
from langchain_openai import ChatOpenAI
from services.agents.tools.tool_schemas import (
    CharacterLookupArgs,
    StoryLookupArgs,
    BeatLookupArgs,
    SceneLookupArgs,
    ProjectGapAnalysisArgs,
    # YouTubeSearchArgs,
    ExecutorFunctionArgs  # Add the new tool
)
from schemas.agent import ChatResponse

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o")
# model notes:
# -- gpt-4o-mini = is not able to fit into reasonable time limits, responses are often inaccurate VS price
# -- gpt-4.1-mini = fair price, very fast VS little bit less accurate - GOTO FOR TESTING - FUNCTIONAL REQUESTS
# -- gpt-4o = precise and quick VS expensive price

# Bind tools to LLM
llm_with_tools = llm.bind_tools(
    [
        CharacterLookupArgs,
        StoryLookupArgs,
        BeatLookupArgs,
        SceneLookupArgs,
        ProjectGapAnalysisArgs,
        # YouTubeSearchArgs,
        ExecutorFunctionArgs  # Add the new tool
    ],
    tool_choice="auto"
)


# Bind structured output for final response generation
structured_llm = llm.with_structured_output(
    ChatResponse
)