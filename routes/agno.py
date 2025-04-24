from fastapi import APIRouter,HTTPException, Depends
from services.llm.story_response import generate_response
router = APIRouter(tags=["Agno"])


import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Principles
# Working with user memory to keep chat reasonable
# Get SQL data into the memory or vector database
# Implement guardrails to limit topics chatting about

@router.get("/")
def test_agent():
    response = generate_response() 
    # Return memories as JSON
    return response.content


