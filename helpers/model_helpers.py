from typing import Optional, Tuple, Any
from enum import Enum
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import logging
import traceback
from langsmith.wrappers import wrap_openai

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelProvider(str, Enum):
    GPT = "gpt"
    GROQ = "groq"
    GEMINI = "gemini"
    NVIDIA = "nvidia"
    
GPT_MODELS = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
GROQ_MODELS = ["deepseek-r1-distill-qwen-32b", "llama3-70b-8192", "llama-3.3-70b-specdec"]
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-2.5-pro-exp-03-25", "models/gemini-2.0-flash-lite"]
NVIDIA_MODELS = ["deepseek-ai/deepseek-r1", "nvidia/llama-3.3-nemotron-super-49b-v1", "qwq-32b", "meta/llama-3.3-70b-instruct"]

# Provider configuration
PROVIDER_CONFIG = {
    ModelProvider.GPT: {"base_url": None, "key_env": "OPENAI_API_KEY", "default_model": "gpt-4o", "models": GPT_MODELS},
    ModelProvider.GROQ: {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY", "default_model": "llama3-70b-8192", "models": GROQ_MODELS},
    ModelProvider.NVIDIA: {"base_url": "https://integrate.api.nvidia.com/v1", "key_env": "NVIDIA_API_KEY", "default_model": "deepseek-ai/deepseek-r1", "models": NVIDIA_MODELS},
    ModelProvider.GEMINI: {"key_env": "GEMINI_API_KEY", "default_model": "gemini-2.0-flash", "models": GEMINI_MODELS},
}

project_root = Path(__file__).parents[2] 
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))
    logger.info(f"Loaded .env file from: {env_path}")
else:
    load_dotenv()
    logger.warning(f".env file not found at {env_path}, using default load_dotenv() behavior")

# Get API keys but don't initialize clients yet - we'll do this on-demand
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# LangSmith configuration
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "st")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_TRACING_ENABLED = os.getenv("LANGCHAIN_TRACING", "false").lower() == "true"

def setup_langsmith_env():
    """Set up LangSmith environment variables."""
    if LANGCHAIN_TRACING_ENABLED and LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = LANGCHAIN_ENDPOINT
        return True
    return False

def init_openai_compatible_client(api_key: str, base_url: Optional[str] = None) -> Tuple[Any, bool]:
    """Initialize an OpenAI-compatible client."""
    if not api_key:
        return None, False
    
    try:
        # Initialize client with appropriate base URL if needed
        client_params = {"api_key": api_key}
        if base_url:
            client_params["base_url"] = base_url
        
        client = OpenAI(**client_params)
        
        # Try to list models to verify the client works
        try:
            models = client.models.list()
            model_ids = [m.id for m in models.data[:3]] if hasattr(models, 'data') else []
            logger.info(f"Client initialized successfully with models: {model_ids}")
        except Exception as model_error:
            logger.error(f"Client created but failed to list models: {str(model_error)}")
        
        # Apply LangSmith wrapping if enabled
        if setup_langsmith_env():
            try:
                client = wrap_openai(client)
                logger.info("Successfully wrapped client with LangSmith")
            except Exception as e:
                logger.error(f"Failed to wrap client with LangSmith: {str(e)}")
        
        return client, True
    except Exception as e:
        logger.error(f"Failed to initialize client: {str(e)}")
        logger.debug(traceback.format_exc())
        return None, False

def initialize_client(provider: ModelProvider) -> Tuple[Any, bool]:
    """Initialize a client for the specified provider on demand."""
    try:
        if isinstance(provider, str):
            provider = ModelProvider(provider.lower())
    except ValueError:
        logger.warning(f"Invalid provider string: {provider}, defaulting to GPT")
        provider = ModelProvider.GPT
    
    # Handle OpenAI-compatible providers (GPT, GROQ, NVIDIA)
    if provider in [ModelProvider.GPT, ModelProvider.GROQ, ModelProvider.NVIDIA]:
        config = PROVIDER_CONFIG[provider]
        api_key = os.getenv(config["key_env"])
        base_url = config["base_url"]
        return init_openai_compatible_client(api_key, base_url)
    
    # Handle Gemini separately
    elif provider == ModelProvider.GEMINI:
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not found")
            return None, False
            
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("Gemini client initialized successfully")
            return client, True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            logger.debug(traceback.format_exc())
            return None, False
    
    return None, False

def select_model(provider: str, requested_model: Optional[str], creativity: Optional[float]) -> tuple:
    """
    Select the appropriate model and client based on provider and requested model.
    This function initializes the client on-demand.
    
    Returns:
        For GPT/GROQ/NVIDIA: (client, model, temperature)
        For GEMINI: (client, model, None)  # Always returns tuple of 3 items
    """
    temperature = min(max(creativity or 0.7, 0.0), 1.0)
    
    # Validate and standardize the provider input
    try:
        # Convert string to enum if needed
        if isinstance(provider, str):
            provider = ModelProvider(provider.lower())
    except ValueError:
        logger.warning(f"Invalid provider '{provider}', defaulting to GPT")
        provider = ModelProvider.GPT
    
    logger.info(f"Selecting model with provider: {provider}, requested_model: {requested_model}, creativity: {creativity}")
    
    # Try to initialize the requested provider first
    client, success = initialize_client(provider)
    
    if success:
        logger.info(f"Successfully initialized {provider} client")
        config = PROVIDER_CONFIG[provider]
        model_list = config["models"]
        default_model = config["default_model"]
        
        # Use requested model if it's in the list of valid models, otherwise use default
        model = requested_model if requested_model in model_list else default_model
        logger.info(f"Using {provider} model: {model}")
        
        # For Gemini, return None as the third value to indicate special handling is needed
        if provider == ModelProvider.GEMINI:
            return client, model, None
        else:
            return client, model, temperature
    else:
        logger.warning(f"Failed to initialize {provider} client")
    
    # If requested provider initialization failed, try others in order of preference for fallback
    fallback_providers = [p for p in ModelProvider if p != provider]
    
    for fallback_provider in fallback_providers:
        logger.warning(f"Trying fallback provider: {fallback_provider}")
        client, success = initialize_client(fallback_provider)
        
        if success:
            config = PROVIDER_CONFIG[fallback_provider]
            default_model = config["default_model"]
            logger.info(f"Falling back to {fallback_provider} with model {default_model}")
            
            # For Gemini, return None as the third value
            if fallback_provider == ModelProvider.GEMINI:
                return client, default_model, None
            else:
                return client, default_model, temperature
    
    # Emergency fallback - just raise an exception if we can't initialize any clients
    logger.error("No language model clients could be initialized")
    raise ValueError("No language model clients could be initialized. Please check your API keys.")

def determine_provider_and_model(model: Optional[str] = None) -> tuple:
    """
    Determine the appropriate provider, client, and model based on the requested model name.
    Initializes clients on-demand.
    """
    logger.info(f"Determining provider and model for requested model: {model}")
    
    # If model is specified, find which provider supports it
    if model:
        for provider in ModelProvider:
            if model in PROVIDER_CONFIG[provider]["models"]:
                client, success = initialize_client(provider)
                if success:
                    return client, model, provider
    
    # If no model specified or couldn't find a provider for the model,
    # try providers in order of preference
    for provider in [ModelProvider.GROQ, ModelProvider.GPT, ModelProvider.NVIDIA, ModelProvider.GEMINI]:
        client, success = initialize_client(provider)
        if success:
            default_model = PROVIDER_CONFIG[provider]["default_model"]
            return client, default_model, provider
    
    # If we get here, no clients could be initialized
    logger.error("No language model clients could be initialized")
    raise ValueError("No language model clients could be initialized. Please check your API keys.")