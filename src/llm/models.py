import os
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from enum import Enum
from pydantic import BaseModel
from typing import Tuple


class ModelProvider(str, Enum):
    """Enum for supported LLM providers"""
    OPENAI = "OpenAI"
    GROQ = "Groq"
    ANTHROPIC = "Anthropic"


class LLMModel(BaseModel):
    """
    This creates a template for storing information about each AI model.
    Similar to how you might create a structured Excel template with specific columns.
    """
    display_name: str       # The human-readable name shown in the UI (e.g., "[anthropic] claude-3.5-haiku")
    model_name: str         # The technical name used when connecting to the API (e.g., "claude-3-5-haiku-latest")
    provider: ModelProvider  # Which company provides this model (OpenAI, Anthropic, or Groq)
    
    def to_choice_tuple(self) -> Tuple[str, str, str]:
        """
        Converts the model info into a format that works with dropdown menus.
        Returns a package of three values: display name, model name, and provider name.
        
        This is like preparing data in Excel to be imported into another system that needs a specific format.
        """
        return (self.display_name, self.model_name, self.provider.value)
    
    def is_deepseek(self) -> bool:
        """
        Checks if this model is from the DeepSeek family.
        Returns True if the model name starts with "deepseek", otherwise False.
        
        This is like having a formula in Excel that checks if a cell starts with certain text.
        """
        return self.model_name.startswith("deepseek")
    
    def is_gemini(self) -> bool:
        """Check if the model is a Gemini model"""
        return self.model_name.startswith("gemini")


# Define the list of all available AI models
# This is similar to creating a reference table in Excel with all available options
AVAILABLE_MODELS = [
    # Anthropic models (Claude family)
    LLMModel(
        display_name="[anthropic] claude-3.5-haiku",  # What shows in the dropdown
        model_name="claude-3-5-haiku-latest",        # Technical name used for API
        provider=ModelProvider.ANTHROPIC              # Which company makes it
    ),
    LLMModel(
        display_name="[anthropic] claude-3.5-sonnet",
        model_name="claude-3-5-sonnet-latest",
        provider=ModelProvider.ANTHROPIC
    ),
    LLMModel(
        display_name="[anthropic] claude-3.7-sonnet",
        model_name="claude-3-7-sonnet-latest",
        provider=ModelProvider.ANTHROPIC
    ),
    
    # Groq-hosted models
    LLMModel(
        display_name="[deepseek] deepseek-r1",
        model_name="deepseek-reasoner",
        provider=ModelProvider.DEEPSEEK
    ),
    LLMModel(
        display_name="[deepseek] deepseek-v3",
        model_name="deepseek-chat",
        provider=ModelProvider.DEEPSEEK
    ),
    LLMModel(
        display_name="[gemini] gemini-2.0-flash",
        model_name="gemini-2.0-flash",
        provider=ModelProvider.GEMINI
    ),
    LLMModel(
        display_name="[gemini] gemini-2.0-pro",
        model_name="gemini-2.0-pro-exp-02-05",
        provider=ModelProvider.GEMINI
    ),
    LLMModel(
        display_name="[groq] llama-3.3 70b",
        model_name="llama-3.3-70b-versatile",
        provider=ModelProvider.GROQ
    ),
    LLMModel(
        display_name="[openai] gpt-4o",
        model_name="gpt-4o",
        provider=ModelProvider.OPENAI
    ),
    LLMModel(
        display_name="[openai] o1",
        model_name="o1",
        provider=ModelProvider.OPENAI
    ),
    LLMModel(
        display_name="[openai] o3-mini",
        model_name="o3-mini",
        provider=ModelProvider.OPENAI
    ),
]

# Convert all models to the format needed for the UI dropdown menu
# This is like transforming data in Excel using a formula applied to each row
LLM_ORDER = [model.to_choice_tuple() for model in AVAILABLE_MODELS]


def get_model_info(model_name: str) -> LLMModel | None:
    """
    Finds and returns information about a specific model by its technical name.
    
    This is like using VLOOKUP in Excel - you provide a model name and it finds
    the matching row in your model database.
    
    Returns None if no matching model is found.
    """
    return next((model for model in AVAILABLE_MODELS if model.model_name == model_name), None)


def get_model(model_name: str, model_provider: ModelProvider):
    """
    Creates a connection to the requested AI model.
    
    This is like establishing a connection to an external database or API:
    1. It checks which provider you want to use
    2. It verifies you have the right API key (like checking if you have login credentials)
    3. It sets up the connection with the specific model you requested
    
    If the API key is missing, it shows an error explaining what went wrong.
    """
    if model_provider == ModelProvider.GROQ:
        # Get the Groq API key from your environment variables
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Print error to console
            print(f"API Key Error: Please make sure GROQ_API_KEY is set in your .env file.")
            raise ValueError("Groq API key not found. Please make sure GROQ_API_KEY is set in your .env file.")
        # Return a connection to the Groq model
        return ChatGroq(model=model_name, api_key=api_key)
    
    elif model_provider == ModelProvider.OPENAI:
        # Get and validate OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Print error to console
            print(f"API Key Error: Please make sure OPENAI_API_KEY is set in your .env file.")
            raise ValueError("OpenAI API key not found. Please make sure OPENAI_API_KEY is set in your .env file.")
        # Return a connection to the OpenAI model
        return ChatOpenAI(model=model_name, api_key=api_key)
    
    elif model_provider == ModelProvider.ANTHROPIC:
        # Get and validate Anthropic API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print(f"API Key Error: Please make sure ANTHROPIC_API_KEY is set in your .env file.")
            raise ValueError("Anthropic API key not found. Please make sure ANTHROPIC_API_KEY is set in your .env file.")
        # Return a connection to the Anthropic model
        return ChatAnthropic(model=model_name, api_key=api_key)
    elif model_provider == ModelProvider.DEEPSEEK:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print(f"API Key Error: Please make sure DEEPSEEK_API_KEY is set in your .env file.")
            raise ValueError("DeepSeek API key not found.  Please make sure DEEPSEEK_API_KEY is set in your .env file.")
        return ChatDeepSeek(model=model_name, api_key=api_key)
    elif model_provider == ModelProvider.GEMINI:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print(f"API Key Error: Please make sure GOOGLE_API_KEY is set in your .env file.")
            raise ValueError("Google API key not found.  Please make sure GOOGLE_API_KEY is set in your .env file.")
        return ChatGoogleGenerativeAI(model=model_name, api_key=api_key)