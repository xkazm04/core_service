import logging
from typing import Optional
from fastapi import HTTPException
from helpers.model_helpers import ModelProvider, determine_provider_and_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_response(system_message: str, user_input: str, model: Optional[str] = None, temperature: float = 0.7):
    """
    Helper function to call LLM API and return the generated response.
    
    Args:
        system_message: The system prompt to guide the model
        user_input: The user's input
        model: Optional model name to use (default: None, which will use Groq llama3-70b-8192)
        temperature: Creativity parameter (default: 0.7)
    
    Returns:
        The generated text response
    """
    try:
        client, model, provider = determine_provider_and_model(model)
        logger.info(f"Using {provider.value} client with model {model}")
        
        # Generate response based on provider
        if provider == ModelProvider.GEMINI:
            if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                response = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_message,
                        },
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ],
                    model=model,
                )
                # Extract the text based on the response structure
                if hasattr(response, "text"):
                    return response.text.strip()
                elif hasattr(response, "candidates"):
                    return response.candidates[0].content.parts[0].text.strip()
                else:
                    return str(response)
            else:
                raise ValueError(f"Unsupported Gemini client type: {type(client)}")
        else:
            # Groq and GPT use the same chat completions API structure
            response = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_message,
                        },
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ],
                    model=model,
                    temperature=temperature,
                    max_tokens=1500,
                )
            return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"API error with model {model}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response from API using {model}.")
    
def get_system_prompt(tone: Optional[str], setting: Optional[str]) -> str:
    """Generate a detailed system prompt based on optional parameters."""
    base_prompt = (
        "You are an expert creative writer specializing in crafting authentic, engaging dialog. "
        "Your expertise is in developing character voices that are distinct, memorable, and true to their personalities. "
    )
    
    if tone:
        base_prompt += f"The dialog should maintain a {tone} tone throughout. "
    
    if setting:
        base_prompt += f"The dialog takes place in {setting}. Subtly incorporate environmental details that ground the conversation in this setting. "
    
    base_prompt += (
        "Focus on creating dialog that:\n"
        "1. Shows rather than tells character emotions and intentions\n"
        "2. Incorporates natural speech patterns, including interruptions, verbal tics, and unique expressions\n"
        "3. Advances subtle character development through word choice and interaction\n"
        "4. Balances exposition and subtext to create depth\n"
        "5. Uses realistic pacing with appropriate pauses and reactions\n"
        "6. Avoids clichés and predictable exchanges\n"
    )
    
    return base_prompt

def get_user_prompt(input_text: str, character_count: int) -> str:
    """Generate a detailed user prompt based on input parameters."""
    prompt = f"Starting idea: {input_text}\n\n"
    
    prompt += (
        f"Create an engaging dialog between {character_count} characters based on this idea. "
        "Each character should have a distinct voice that reflects their personality, background, and current emotional state. "
        "Format the dialog as character name followed by their line, with clear attribution of who is speaking.\n\n"
        "In your response:\n"
        "- Include subtle nonverbal cues and actions in italics where appropriate\n"
        "- Develop natural speech rhythms with varied sentence lengths\n"
        "- Use dialog to reveal character traits and relationships indirectly\n"
        "- Incorporate appropriate jargon, dialect, or speech patterns that fit each character\n"
    )
    
    return prompt

def generate_dialog(client, model: str, system_message: str, user_message: str, temperature: float) -> str:
    """Generate dialog using the specified model and client."""
    try:
        response = client.responses.create(
            model=model,
            instructions=system_message,
            input=user_message,
            temperature=temperature,
            max_tokens=1500
        )

        return response.output_text
    except Exception as e:
        logger.error(f"API error with {model}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dialog using {model}.")