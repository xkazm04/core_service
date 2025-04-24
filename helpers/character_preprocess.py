from sqlalchemy.orm import Session
from models.models import Prompt

def get_character_traits(db: Session, character_id: str):
    """
    Fetches character traits from the database and formats them for the prompt.
    
    Args:
        db: Database session
        character_id: UUID of the character
        
    Returns:
        Formatted string containing character traits
    """
    trait_types = ["communication", "emotion", "humor", "behavior", "background"]
    
    prompts = db.query(Prompt).filter(
        Prompt.char_id == character_id,
        Prompt.type.in_(trait_types)
    ).all()
    
    if not prompts:
        return "No traits found for this character."
    
    # Group prompts by type
    traits_by_type = {}
    for prompt in prompts:
        if prompt.type not in traits_by_type:
            traits_by_type[prompt.type] = []
        traits_by_type[prompt.type].append(prompt.text)
    
    # Format into sections
    formatted_traits = []
    for trait_type in trait_types:
        if trait_type in traits_by_type and traits_by_type[trait_type]:
            type_label = trait_type.capitalize()
            traits_text = "; ".join(traits_by_type[trait_type])
            formatted_traits.append(f"{type_label}: {traits_text}")
    
    return "\n\n".join(formatted_traits)

def format_charline_temp(config):
    """
    Formats the charline_temp with the appropriate sections based on configuration.
    
    Args:
        config: Dictionary with Boolean flags for each section
            - include_traits: Whether to include the character profile section
            - include_context: Whether to include the dialog context section
            - include_history: Whether to include the dialog history section
            - context_description: Description of the dialog context (only used if include_context is True)
            - character_traits: Character traits to include in the profile (only used if include_traits is True)
    
    Returns:
        Formatted template string
    """
    from templates.dialog_temp import traits_section, context_section, history_section, charline_temp_base
    
    # Prepare each section based on configuration
    traits_section_text = ""
    if config.get("include_traits", False):
        traits_section_text = traits_section.format(
            character_profile=config.get("character_traits", "No character profile available.")
        )
    
    context_section_text = ""
    if config.get("include_context", False):
        context_section_text = context_section.format(
            dialog_context=config.get("context_description", "")
        )
    
    history_section_text = ""
    if config.get("include_history", False):
        history_section_text = history_section.format(
            dialog_history=config.get("dialog_history", "")
        )
    
    # Format the base template with the prepared sections
    template_sections = {
        "traits_section": traits_section_text,
        "context_section": context_section_text,
        "history_section": history_section_text,
        "intended_line": config.get("intended_line", "")  # Add the intended_line parameter
    }
    
    return charline_temp_base.format(**template_sections)

