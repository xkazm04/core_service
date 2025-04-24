from agno.memory.v2 import UserMemory, Memory
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# TBD not sure about use cases for the app 

# Initialize the memory
def initialize_memory():
    memory = Memory()
    create_memory(memory)
    return memory

# Create a new memor
def create_memory(memory):
    memory.add_user_memory(
        memory=UserMemory(memory="The user's name is John Doe", topics=["name"]),
    )

    for user_id, user_memories in memory.memories.items():
        logger.info(f"User: {user_id}")
        for um in user_memories.values():
            logger.info(um.memory)

# Create a new memory   
def add_memories(memory):
    person_id = "jane_doe@example.com"
    logger.info(f"User: {person_id}")
    memory_id_1 = memory.add_user_memory(
        memory=UserMemory(memory="The user's name is Jane Doe", topics=["name"]),
        user_id=person_id,
    )
    memory_id_2 = memory.add_user_memory(
        memory=UserMemory(memory="She likes to play tennis", topics=["hobbies"]),
        user_id=person_id,
    )

    memories = memory.get_user_memories(user_id=person_id)
    for m in memories:
        logger.info(m.memory)
    logger.info("")

# Delete a memory
def delete_memory(memory, person_id):
    memory.delete_user_memory(user_id=person_id, memory_id=person_id)
    logger.info("Memory deleted")
    logger.info("")
    memories = memory.get_user_memories(user_id=person_id)
    for m in memories:
        logger.info(m.memory)
    logger.info("")
    
# Replace a memory
def replace_memory(memory, person_id):
    memory.replace_user_memory(
        user_id=person_id,
        memory_id=person_id,
        new_memory=UserMemory(memory="The user's name is Jane Smith", topics=["name"]),
    )
    logger.info("Memory replaced")
    
# Get all memories for a user
def get_memories(memory, person_id):
    memories = memory.get_user_memories(user_id=person_id)
    for m in memories:
        logger.info(m.memory)
    
    # Convert memories to a list of dictionaries
    memories_json = [{"memory": m.memory, "topics": m.topics} for m in memories]
    return memories_json

# Searching through the memories
def search_memories(memory, person_id):
    memories = memory.search_user_memories(
        user_id=person_id,
        query="What does the user like to do on weekends?",
        retrieval_method="agentic",
    )
    for i, m in enumerate(memories):
        logger.info(f"{i}: {m.memory}")
