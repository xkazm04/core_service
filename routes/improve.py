import logging
from fastapi import APIRouter, HTTPException, Depends
from services.llm.text_analysis import extract_personality
from templates.improvement_temps import char_temp, scene_temp, avatar_temp
from sqlalchemy.orm import Session
from database import get_db
from schemas.improve import PromptInput, ImproveUniversalInput, DialogInput, DialogLine, DialogResponse, PromptInputBasic, PromptInputBasicResponse, ExtractInput, ExtractOutput, LineInput, PersonalityTraits
from services.llm.basic_response import generate_response, get_system_prompt, get_user_prompt, generate_dialog
from helpers.model_helpers import select_model


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Improve routes module initialized")

router = APIRouter(tags=["Improve"])

    
@router.post("/dialog", response_model=PromptInputBasicResponse)
async def improve_dialog(dialog_input: PromptInputBasic):
    """API endpoint to generate improved dialog based on user input."""
    # Add diagnostic logs
    print(f"Direct print - Received dialog re   uest: {dialog_input}")
    logger.info(f"Received dialog request: {dialog_input.model_dump_json(exclude_none=True)}")
    
    # Get appropriate prompts
    system_prompt = get_system_prompt(dialog_input.tone, dialog_input.setting)
    user_prompt = get_user_prompt(dialog_input.text, dialog_input.character_count)
    logger.debug(f"System prompt: {system_prompt[:100]}...")
    
    # Select model and client
    client, model, temperature = select_model(
        dialog_input.model_provider, 
        dialog_input.model_name,
        dialog_input.creativity
    )
    
    # Generate dialog
    logger.info(f"Generating dialog using {model} with temperature {temperature}")
    dialog = generate_dialog(client, model, system_prompt, user_prompt, temperature)
    
    logger.info("Dialog generation completed successfully")
    return {"improved_dialog": dialog, "model_used": model}
    
# Improve character background and story
@router.post("/character")
async def improve_character(prompt_input: PromptInput):
    """API endpoint to improve descriptions."""
    logger.info(f"Received improvement request with input: {prompt_input.text}")
    if prompt_input.type == "character":
        system_message = (char_temp)
    else:
        system_message = (scene_temp)
    
    # Ensure model_provider is properly handled as ModelProvider enum
    try:
        from helpers.model_helpers import ModelProvider
        model_provider = ModelProvider(prompt_input.model_provider.lower()) if prompt_input.model_provider else ModelProvider.GPT
        logger.info(f"Using model provider: {model_provider}")
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid model provider '{prompt_input.model_provider}', defaulting to GPT: {str(e)}")
        model_provider = ModelProvider.GPT
    
    # Select model and client with improved error handling
    client, model, temperature = select_model(
        model_provider,
        prompt_input.model_name,
        prompt_input.creativity
    )
    
    improved_prompt = generate_response(system_message, prompt_input.text, model, temperature)
    
    logger.info(f"Improvement completed successfully using model {model}.")
    return {"improved_prompt": improved_prompt, "model_used": model}


@router.post("/dialog-advanced", response_model=DialogResponse)
async def improve_dialog(dialog_input: DialogInput):
    """API endpoint to generate a structured dialog between multiple characters in a given scenery."""
    logger.info(f"Received dialog improvement request with {len(dialog_input.characters)} characters.")

    character_descriptions = "\n".join(
        [f"- {char.character_name}: {char.character_prompt}" for char in dialog_input.characters]
    )
    user_input = (
        f"Scenery description: {dialog_input.scenery_prompt}\n\n"
        f"Characters:\n{character_descriptions}\n\n"
        "Generate a natural and engaging conversation between these characters, ensuring the dialog is immersive, "
        "believable, and fits the given scenery. Structure the response as numbered dialog lines."
    )

    system_message = (
        "You are an expert storyteller and screenwriter. Your task is to create a dynamic, engaging, and character-driven "
        "dialog between multiple characters. Ensure each character's personality is reflected in their speech patterns, "
        "word choices, and interaction style. Keep the dialog natural, immersive, and meaningful within the given scene."
    )

    # Select model and client
    client, model, temperature = select_model(
        dialog_input.model_provider,
        dialog_input.model_name,
        dialog_input.creativity
    )
    
    raw_response = generate_response(system_message, user_input, model, temperature)

    dialog_lines = []
    lines = raw_response.split("\n")
    for index, line in enumerate(lines, start=1):
        if ":" in line:
            parts = line.split(":", 1)
            character_name = parts[0].strip()
            dialog_text = parts[1].strip()
            dialog_lines.append(DialogLine(order=index, character_name=character_name, dialog_line=dialog_text))

    logger.info(f"Dialog generation completed successfully using model {model}.")
    return {"dialog": dialog_lines, "model_used": model}


@router.post("/avatar", response_model=ExtractOutput)
async def improve_avatar(prompt_input: ExtractInput):
    """API endpoint to improve an avatar image of a game character"""
    logger.info(f"Received avatar improvement request with input: {prompt_input.text}")
    system_message = avatar_temp
    
    # Select model and client - fix the unpacking to match the return values
    client, model, temperature = select_model(
        prompt_input.model_provider,
        prompt_input.model_name,
        prompt_input.creativity
    )
    improved_prompt = generate_response(system_message, prompt_input.text, model, temperature)
    
    logger.info(f"Avatar improvement completed successfully using model {model}.")
    return {"improved_dialog": improved_prompt, "model_used": model}


@router.post("/uni", response_model=ExtractOutput)
async def improve_universal(prompt_input: ImproveUniversalInput):
    logger.info(f"Received universal improvement request with input: {prompt_input.instructions}")
    
    # Select model and client - fix the unpacking to match the return values
    client, model, temperature = select_model(
        prompt_input.model_provider,
        prompt_input.model_name,
        0.7  # Fixed creativity for this endpoint
    )
    
    improved_prompt = generate_response(prompt_input.instructions, prompt_input.type, model, temperature)
    
    logger.info(f"Universal improvement completed successfully using model {model}.")
    return {"improved_dialog": improved_prompt, "model_used": model}

