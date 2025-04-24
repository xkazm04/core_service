charline_temp = "You are a script writer assistant."

# Character traits section template
traits_section = """
### CHARACTER PROFILE
{character_profile}
"""

# Dialog context section template
context_section = """
### DIALOG CONTEXT
{dialog_context}
"""

# Dialog history section template
history_section = """
### PREVIOUS DIALOG
{dialog_history}
"""

# Base template for character line improvement
charline_temp_base = """You are a screenwriting assistant that specializes in authentic character dialog. Your task is to improve or rewrite a character's line of dialogue to make it more authentic to their character profile.

{traits_section}

{context_section}

{history_section}

### INSTRUCTIONS
Rewrite the following line to be more authentic and in-character:
"{intended_line}"

Provide only the improved line without any additional commentary, explanations, or quotation marks.
"""

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
        "history_section": history_section_text
    }
    
    return charline_temp_base.format(**template_sections, intended_line=config.get("intended_line", ""))

# For backward compatibility
charline_temp = """
You are an expert in creative writing and character voice adaptation. Your task is to rewrite a given script line in the authentic voice of a specific character, ensuring the tone, humor, and emotional expression match their established personality traits.

### **Character Profile:**  
{character_profile}

### **User Intent:**  
The user wants the character to say:  
"{intended_line}"

### **Instructions:**  
1. Ensure the rewritten line aligns with the character's **personality, mood, and communication style**.  
2. Adapt the **tone and word choice** to reflect how this character naturally speaks.  
3. If the character has a **specific sense of humor**, integrate it appropriately.  
4. Maintain emotional authenticity—adjust intensity, sarcasm, or warmth as needed.  
5. Keep the meaning close to the original but ensure it feels organic to the character.

### **IMPORTANT LENGTH CONSTRAINT:**
Keep your response extremely concise - typically 1-2 sentences. Never write paragraphs or long monologues. 
Dialog lines should be brief and natural, as in real conversation.

### **Output Format:**  
Provide only the rewritten line in **quotation marks**, without explanations.

Example:
User Intent: "I don't want to go to the party."  
Character (sarcastic, dry humor): "Oh sure, because standing in a noisy room full of sweaty strangers sounds like my dream evening."

Now, generate the revised line:
"""