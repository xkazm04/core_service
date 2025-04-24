import json
from pydantic import BaseModel
from templates.improvement_temps import transcription_temp
import re
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI
from helpers.model_helpers import select_model, ModelProvider
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#--------Analysis---------
class TextInput(BaseModel):
    text: str
    
async def extract_personality(prompt_input: TextInput):
    """API endpoint to extract personality traits from a given text transcription."""
    logger.info(f"Received personality extraction request with input: {prompt_input.text}")
    
    # Add "JSON" to the system message to satisfy OpenAI's requirement
    system_message = transcription_temp + "\nRespond with valid JSON format."
    
    try:
        # Get client and model using the new helper function
        # Default to GPT provider since this function needs JSON response format
        client, model, temperature = select_model(
            ModelProvider.GPT,  # Preferably use GPT for structured JSON output
            "gpt-4o",           # Specific model request
            0.3                 # Low creativity for consistent analysis
        )
        
        # Handle different client types based on the provider
        # The client returned from select_model could be OpenAI, Groq, or Gemini
        if isinstance(client, OpenAI):
            # OpenAI client approach
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Analyze this transcription and provide the results as JSON: {prompt_input.text}"}
                ],
                response_format={"type": "json_object"},  # Enforce JSON format
                temperature=temperature
            )
            response_text = response.choices[0].message.content.strip()
        else:
            # Generic approach for other providers (Groq, Gemini)
            # This may need to be adjusted based on the actual client API
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Analyze this transcription and provide the results as JSON: {prompt_input.text}"}
                    ],
                    temperature=temperature
                )
                response_text = response.choices[0].message.content.strip()
            except AttributeError:
                # Fallback if the client doesn't follow the OpenAI/Groq API pattern
                logger.warning("Using alternative API pattern for the current client")
                # For Gemini or other non-standard clients
                if hasattr(client, "generate_content"):
                    response = client.generate_content(
                        [system_message, f"Analyze this transcription and provide the results as JSON: {prompt_input.text}"]
                    )
                    response_text = response.text.strip()
                else:
                    raise ValueError(f"Unsupported client type: {type(client)}")
        
        logger.info(f"Raw response: {response_text[:100]}...")
        
        # Try to parse the JSON
        try:
            personality_data = json.loads(response_text)
            logger.info("Successfully parsed JSON directly")
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {str(e)}, trying to extract JSON")
            
            # Try to extract JSON using regex
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    personality_data = json.loads(json_match.group(0))
                    logger.info("Successfully extracted JSON with regex")
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Failed to parse extracted JSON data")
            else:
                # If no JSON found, create a structured response from the text
                logger.warning("No JSON structure found, creating template")
                personality_data = {
                    "Personality Traits": "Could not parse response format. Please try again.",
                    "Communication Style": "",
                    "Emotional Expression": "",
                    "Sense of Humor": "",
                    "Behavioral Tendencies": "",
                    "Possible Background and Motivations": response_text[:200] + "..."
                }
        
        # Ensure all required fields are present
        required_fields = [
            "Personality Traits", 
            "Communication Style", 
            "Emotional Expression", 
            "Sense of Humor", 
            "Behavioral Tendencies", 
            "Possible Background and Motivations"
        ]
        
        for field in required_fields:
            if field not in personality_data:
                personality_data[field] = ""
                
        logger.info("Personality extraction completed successfully.")
        return personality_data
        
    except Exception as e:
        logger.error(f"Error in extract_personality: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract personality: {str(e)}")