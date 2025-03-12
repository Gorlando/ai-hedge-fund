"""
Helper functions for interacting with Large Language Models (LLMs).

This module provides utilities for making reliable API calls to different LLM providers,
handling response parsing, error recovery, and standardizing outputs into structured data.
"""

import json
from typing import TypeVar, Type, Optional, Any
from pydantic import BaseModel
from utils.progress import progress

# Define a generic type T that must be a Pydantic model
# This allows us to create strongly-typed functions that work with any Pydantic model
T = TypeVar('T', bound=BaseModel)

def call_llm(
    prompt: Any,
    model_name: str,
    model_provider: str,
    pydantic_model: Type[T],
    agent_name: Optional[str] = None,
    max_retries: int = 3,
    default_factory = None
) -> T:
    """
    Makes an LLM call with retry logic, handling both Deepseek and non-Deepseek models.
    
    This function is a central wrapper for all LLM calls in the system. It:
    1. Gets the appropriate LLM model based on name and provider
    2. Configures structured output formatting if supported
    3. Implements retry logic for resiliency against API errors
    4. Handles response parsing differently based on model capabilities
    5. Provides fallback mechanisms when all retries fail
    
    In financial terms, this is like having a standardized protocol for getting analyst
    opinions that works regardless of which research firm you're contacting, with
    built-in redundancy for when communication channels fail.
    
    Args:
        prompt: The prompt to send to the LLM (question/instruction)
        model_name: Name of the model to use (e.g., "gpt-4o", "claude-3-5-sonnet")
        model_provider: Provider of the model (e.g., "OpenAI", "Anthropic")
        pydantic_model: The Pydantic model class to structure the output
        agent_name: Optional name of the agent for progress updates in the UI
        max_retries: Maximum number of retries before falling back to defaults
        default_factory: Optional function to create custom default response on failure
        
    Returns:
        An instance of the specified Pydantic model containing the LLM's response
    """
    # Import here to avoid circular imports
    from llm.models import get_model, get_model_info
    
    # Get information about the model and initialize the LLM client
    model_info = get_model_info(model_name)
    llm = get_model(model_name, model_provider)
    
    # For non-Deepseek models, we can use structured output
    if not (model_info and model_info.is_deepseek()):
        llm = llm.with_structured_output(
            pydantic_model,
            method="json_mode",  # Use the model's native JSON mode for reliability
        )
    
    # Call the LLM with retries for error resilience
    for attempt in range(max_retries):
        try:
            # Call the LLM API
            result = llm.invoke(prompt)
            
            # For Deepseek, we need to extract and parse the JSON manually
            if model_info and model_info.is_deepseek():
                parsed_result = extract_json_from_deepseek_response(result.content)
                if parsed_result:
                    # Convert the parsed JSON to our Pydantic model
                    return pydantic_model(**parsed_result)
            else:
                # For non-Deepseek models, the result is already a Pydantic model
                return result
                
        except Exception as e:
            # Update progress UI if agent_name is provided
            if agent_name:
                progress.update_status(agent_name, None, f"Error - retry {attempt + 1}/{max_retries}")
            
            # If this was our last retry attempt, handle the failure
            if attempt == max_retries - 1:
                print(f"Error in LLM call after {max_retries} attempts: {e}")
                
                # Use custom default_factory if provided, otherwise use generic default
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)

    # This should never be reached due to the retry logic above
    return create_default_response(pydantic_model)

def create_default_response(model_class: Type[T]) -> T:
    """
    Creates a safe default response based on the model's fields.
    
    This function examines the Pydantic model's structure and creates appropriate
    default values for each field based on its type. This ensures that even when
    the LLM fails completely, the system can continue with sensible fallback values.
    
    In financial terms, this is similar to having placeholder assumptions in your
    financial models when certain data points aren't available.
    
    Args:
        model_class: The Pydantic model class to create defaults for
        
    Returns:
        An instance of the model class with safe default values
    """
    default_values = {}
    
    # Loop through each field in the model and create an appropriate default value
    for field_name, field in model_class.model_fields.items():
        # Handle different data types with appropriate defaults
        if field.annotation == str:
            default_values[field_name] = "Error in analysis, using default"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == dict:
            default_values[field_name] = {}  # Empty dictionary for dict fields
        else:
            # For other types (like Literal), try to use the first allowed value
            if hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None
    
    # Create and return the model instance with the default values
    return model_class(**default_values)

def extract_json_from_deepseek_response(content: str) -> Optional[dict]:
    """
    Extracts JSON from Deepseek's markdown-formatted response.
    
    Deepseek models typically return JSON embedded within code blocks in markdown.
    This function extracts that JSON and parses it.
    
    Args:
        content: The raw text response from a Deepseek model
        
    Returns:
        Parsed JSON as a dictionary, or None if extraction fails
    """
    try:
        # Look for the start of a JSON code block
        json_start = content.find("```json")
        if json_start != -1:
            # Extract everything after the ```json marker
            json_text = content[json_start + 7:]  # Skip past ```json
            
            # Find the end of the code block
            json_end = json_text.find("```")
            if json_end != -1:
                # Extract just the JSON text and remove whitespace
                json_text = json_text[:json_end].strip()
                
                # Parse the JSON text into a Python dictionary
                return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting JSON from Deepseek response: {e}")
    
    # Return None if extraction fails at any point
    return None