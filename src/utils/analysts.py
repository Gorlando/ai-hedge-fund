"""Constants and utilities related to analysts configuration."""

from agents.ben_graham import ben_graham_agent
from agents.bill_ackman import bill_ackman_agent
from agents.cathie_wood import cathie_wood_agent
from agents.charlie_munger import charlie_munger_agent
from agents.fundamentals import fundamentals_agent
from agents.sentiment import sentiment_agent
from agents.technicals import technical_analyst_agent
from agents.valuation import valuation_agent
from agents.warren_buffett import warren_buffett_agent

# Define analyst configuration - single source of truth
# This dictionary serves as the central configuration for all analysts in the system
# Each entry provides metadata and links to the actual agent implementation
ANALYST_CONFIG = {
    # Value investing pioneer who focuses on intrinsic value and margin of safety
    "ben_graham": {
        "display_name": "Ben Graham",         # Human-readable name shown in the UI
        "agent_func": ben_graham_agent,       # Function that implements the agent's logic
        "order": 0,                           # Display/execution order (lower = higher priority)
    },
    # Activist investor known for concentrated positions and corporate influence
    "bill_ackman": {
        "display_name": "Bill Ackman",
        "agent_func": bill_ackman_agent,
        "order": 1,
    },
    # Innovation-focused investor specializing in disruptive technology
    "cathie_wood": {
        "display_name": "Cathie Wood",
        "agent_func": cathie_wood_agent,
        "order": 2,
    },
    # Focuses on business quality, mental models, and long-term competitive advantages
    "charlie_munger": {
        "display_name": "Charlie Munger",
        "agent_func": charlie_munger_agent,
        "order": 3,
    },
    "warren_buffett": {
        "display_name": "Warren Buffett",
        "agent_func": warren_buffett_agent,
        "order": 5,
    },
    # Analyzes price patterns, trends, and market indicators rather than fundamentals
    "technical_analyst": {
        "display_name": "Technical Analyst",
        "agent_func": technical_analyst_agent,
        "order": 4,
    },
    # Focuses purely on financial statements, ratios, and fundamental business metrics
    "fundamentals_analyst": {
        "display_name": "Fundamentals Analyst",
        "agent_func": fundamentals_agent,
        "order": 7,
    },
    # Analyzes news, social media, and market sentiment indicators
    "sentiment_analyst": {
        "display_name": "Sentiment Analyst",
        "agent_func": sentiment_agent,
        "order": 8,
    },
    # Specializes in different valuation methodologies and fair value estimation
    "valuation_analyst": {
        "display_name": "Valuation Analyst",
        "agent_func": valuation_agent,
        "order": 9,
    },
}

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
# This creates a list of tuples in the format (display_name, key) sorted by the order field
# Used for maintaining a consistent display order in the UI or sequential processing
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]


def get_analyst_nodes():
    """
    Get the mapping of analyst keys to their (node_name, agent_func) tuples.
    
    This function transforms the analyst configuration into a format that can be
    used directly in a workflow or graph-based execution system, where each analyst
    is represented as a node with a specific processing function.
    
    Returns:
        dict: A dictionary mapping analyst keys (e.g., "ben_graham") to tuples containing:
              - node_name: The name to use for the node in a processing graph (e.g., "ben_graham_agent")
              - agent_func: The actual function that implements the analyst's logic
    
    Example usage in a workflow system:
        nodes = get_analyst_nodes()
        for key, (node_name, func) in nodes.items():
            graph.add_node(node_name, function=func)
    """
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}