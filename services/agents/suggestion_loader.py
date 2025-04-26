import json
import os
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Define the base path relative to this file or use absolute paths
# Adjust this path as necessary
SUGGESTIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_suggestions_by_topic(topic: str) -> List[Dict[str, Any]]:
    """Loads suggestion definitions from a JSON/TS file based on topic."""
    # Assuming files are named like 'suggestions_{topic}.json'
    # Handle potential .ts extension if needed (might require a TS parser or saving as JSON)
    file_path_json = os.path.join(SUGGESTIONS_DIR, f"suggestions_{topic}.json")
    file_path_ts = os.path.join(SUGGESTIONS_DIR, f"suggestions_{topic}.ts") # Check for .ts too

    file_path = None
    if os.path.exists(file_path_json):
        file_path = file_path_json
    elif os.path.exists(file_path_ts):
        # Basic handling for TS-like JSON array structure
        file_path = file_path_ts
    else:
        logger.warning(f"Suggestion file not found for topic '{topic}' in {SUGGESTIONS_DIR}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Handle potential comments if reading .ts file directly
            # A simple approach: read lines, filter comments, join, parse
            content = "".join(line for line in f if not line.strip().startswith('//'))
            suggestions = json.loads(content)
            if isinstance(suggestions, list):
                # Basic validation: check if items are dicts
                if all(isinstance(item, dict) for item in suggestions):
                    logger.info(f"Loaded {len(suggestions)} suggestions for topic '{topic}' from {file_path}")
                    return suggestions
                else:
                    logger.error(f"Invalid format in suggestion file {file_path}: expected list of objects.")
                    return []
            else:
                 logger.error(f"Invalid format in suggestion file {file_path}: expected a JSON list.")
                 return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading suggestions from {file_path}: {e}")
        return []

# Example usage (optional, for testing)
if __name__ == '__main__':
    # Create dummy data file if it doesn't exist
    dummy_topic = "character"
    dummy_file_path = os.path.join(SUGGESTIONS_DIR, f"suggestions_{dummy_topic}.json")
    if not os.path.exists(dummy_file_path):
         os.makedirs(SUGGESTIONS_DIR, exist_ok=True)
         dummy_data = [
             {
                 "feature": "Character Trait",
                 "use_case": "Add missing behavior trait",
                 "initiator": "Character does not have CharacterTrait with type='behavior'",
                 "suggestion_label": "Add Behavior Trait",
                 "suggestion_text": "Let's define the character's typical behavior.",
                 "be_function": "add_trait_behavior",
                 "fe_navigation": "center.actors.traits",
                 "topic": "character"
             },
             {
                 "feature": "Character Trait",
                 "use_case": "Add missing knowledge trait",
                 "initiator": "Character does not have CharacterTrait with type='knowledge'",
                 "suggestion_label": "Add Knowledge Trait",
                 "suggestion_text": "What specific knowledge does this character possess?",
                 "be_function": "add_trait_knowledge",
                 "fe_navigation": "center.actors.traits",
                 "topic": "character"
             }
         ]
         try:
             with open(dummy_file_path, 'w', encoding='utf-8') as f:
                 json.dump(dummy_data, f, indent=2)
             print(f"Created dummy suggestion file: {dummy_file_path}")
         except Exception as e:
             print(f"Error creating dummy file: {e}")


    loaded = load_suggestions_by_topic(dummy_topic)
    print(f"Loaded suggestions for '{dummy_topic}': {loaded}")