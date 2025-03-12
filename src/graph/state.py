from typing_extensions import Annotated, Sequence, TypedDict

import operator
from langchain_core.messages import BaseMessage
import json


def merge_dicts(a: dict[str, any], b: dict[str, any]) -> dict[str, any]:
    """
    Merges two dictionaries together.
    
    This utility function combines two dictionaries, with values from the second
    dictionary (b) overriding any duplicate keys from the first dictionary (a).
    It's used for combining state information from different stages of analysis.
    
    Args:
        a: First dictionary (base values)
        b: Second dictionary (override values)
        
    Returns:
        Combined dictionary with all keys from both inputs
    """
    return {**a, **b}  # Python's dictionary unpacking syntax for merging


# Define agent state structure using TypedDict
class AgentState(TypedDict):
    """
    Type definition for agent state in the workflow.
    
    This structure defines how the state of the analyst agents is maintained
    and combined throughout the workflow. It uses Annotated types to specify
    how each field should be merged when states are combined:
    
    - messages: Conversation history is concatenated (using operator.add)
    - data: Analysis data dictionaries are merged (using merge_dicts)
    - metadata: Configuration metadata is merged (using merge_dicts)
    
    This is similar to how different analysts might contribute to a collaborative
    investment report, where their individual insights are combined into a
    comprehensive analysis.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]  # Messages are concatenated
    data: Annotated[dict[str, any], merge_dicts]              # Data dictionaries are merged
    metadata: Annotated[dict[str, any], merge_dicts]          # Metadata dictionaries are merged


def show_agent_reasoning(output, agent_name):
    """
    Displays the reasoning process of an analyst agent in a readable format.
    
    This function outputs the detailed reasoning behind an agent's analysis or
    recommendation, formatted for human readability. It's similar to viewing the
    detailed notes and calculations behind an analyst's investment thesis.
    
    Args:
        output: The reasoning output from the agent (can be dict, list, or string)
        agent_name: Name of the agent (e.g., "Warren Buffett" or "Technical Analyst")
    """
    # Print a header with the agent name centered
    print(f"\n{'=' * 10} {agent_name.center(28)} {'=' * 10}")

    def convert_to_serializable(obj):
        """
        Recursive helper function to convert complex objects to JSON-serializable format.
        
        This handles various data types that might be included in an agent's reasoning,
        such as Pandas DataFrames, custom objects, or nested structures.
        
        Args:
            obj: Object to convert to a JSON-serializable format
            
        Returns:
            JSON-serializable version of the input object
        """
        if hasattr(obj, "to_dict"):  # Handle Pandas Series/DataFrame
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):  # Handle custom objects
            return obj.__dict__
        elif isinstance(obj, (int, float, bool, str)):
            return obj  # Basic types don't need conversion
        elif isinstance(obj, (list, tuple)):
            return [convert_to_serializable(item) for item in obj]  # Convert each item in sequences
        elif isinstance(obj, dict):
            return {key: convert_to_serializable(value) for key, value in obj.items()}  # Convert dict values
        else:
            return str(obj)  # Fallback to string representation for unsupported types

    if isinstance(output, (dict, list)):
        # For dictionary or list output, convert to JSON-serializable format and pretty print
        serializable_output = convert_to_serializable(output)
        print(json.dumps(serializable_output, indent=2))
    else:
        try:
            # Try to parse the output as JSON (in case it's a JSON string)
            parsed_output = json.loads(output)
            print(json.dumps(parsed_output, indent=2))
        except json.JSONDecodeError:
            # If not valid JSON, just print the raw output
            print(output)

    # Print footer
    print("=" * 48)