from rich.console import Console  # Advanced terminal output with formatting/colors
from rich.live import Live  # For creating live-updating displays in the terminal
from rich.table import Table  # For creating formatted tables in the terminal
from rich.style import Style  # For styling text with colors, bold, etc.
from rich.text import Text  # For creating text with multiple styles
from typing import Dict, Optional  # Type hints for better code documentation
from datetime import datetime  # Not used in this file but imported for potential timestamp features

# Initialize a Rich console for advanced terminal output
console = Console()


class AgentProgress:
    """
    Manages progress tracking for multiple agents in a live-updating display.
    
    This class creates a dynamic status dashboard in the terminal that shows
    the current state of all analyst agents in the system. It's similar to
    how you might track multiple workstreams in a restructuring project.
    """

    def __init__(self):
        """
        Initialize the progress tracker.
        
        Sets up the internal data structures and UI components needed for tracking.
        """
        # Dictionary to store the status of each agent
        # Format: {agent_name: {"status": "current_status", "ticker": "symbol"}}
        self.agent_status: Dict[str, Dict[str, str]] = {}
        
        # Create a simple table for the status display (no header, no box)
        self.table = Table(show_header=False, box=None, padding=(0, 1))
        
        # Create a live display that updates automatically
        # refresh_per_second=4 means it updates 4 times per second
        self.live = Live(self.table, console=console, refresh_per_second=4)
        
        # Track whether the live display has been started
        self.started = False

    def start(self):
        """
        Start the progress display.
        
        This activates the live-updating terminal display.
        """
        if not self.started:
            self.live.start()
            self.started = True

    def stop(self):
        """
        Stop the progress display.
        
        This deactivates the live-updating terminal display.
        """
        if self.started:
            self.live.stop()
            self.started = False

    def update_status(self, agent_name: str, ticker: Optional[str] = None, status: str = ""):
        """
        Update the status of an agent.
        
        This is the main method used to report progress. It's called whenever an agent's
        status changes, such as starting analysis, completing work, or encountering errors.
        
        Args:
            agent_name: Name of the agent to update (e.g., "ben_graham_agent")
            ticker: Stock symbol the agent is analyzing (optional)
            status: Current status text (e.g., "Analyzing financials", "Done", "Error")
        """
        # Create entry for this agent if it doesn't exist yet
        if agent_name not in self.agent_status:
            self.agent_status[agent_name] = {"status": "", "ticker": None}

        # Update the ticker if provided
        if ticker:
            self.agent_status[agent_name]["ticker"] = ticker
            
        # Update the status if provided
        if status:
            self.agent_status[agent_name]["status"] = status

        # Refresh the visual display with the updated information
        self._refresh_display()

    def _refresh_display(self):
        """
        Refresh the progress display.
        
        This private method rebuilds the status table with the latest information.
        It's called automatically whenever an agent's status is updated.
        """
        # Clear the existing table columns
        self.table.columns.clear()
        
        # Add a single column with fixed width
        self.table.add_column(width=100)

        # Define a sort function to organize agents in a specific order
        # This ensures Risk Management and Portfolio Management appear at the bottom
        def sort_key(item):
            agent_name = item[0]
            if "risk_management" in agent_name:
                return (2, agent_name)  # Second priority group
            elif "portfolio_management" in agent_name:
                return (3, agent_name)  # Third priority group
            else:
                return (1, agent_name)  # First priority group (regular analysts)

        # Process each agent's status in the sorted order
        for agent_name, info in sorted(self.agent_status.items(), key=sort_key):
            status = info["status"]
            ticker = info["ticker"]

            # Create the status text with appropriate styling based on status
            if status.lower() == "done":
                # Green checkmark for completed tasks
                style = Style(color="green", bold=True)
                symbol = "✓"
            elif status.lower() == "error":
                # Red X for errors
                style = Style(color="red", bold=True)
                symbol = "✗"
            else:
                # Yellow ellipsis for in-progress tasks
                style = Style(color="yellow")
                symbol = "⋯"

            # Format the agent name for display (e.g., "ben_graham_agent" -> "Ben Graham")
            agent_display = agent_name.replace("_agent", "").replace("_", " ").title()
            
            # Create a text object to hold the formatted status line
            status_text = Text()
            
            # Add the status symbol with appropriate color
            status_text.append(f"{symbol} ", style=style)
            
            # Add the agent name in bold
            status_text.append(f"{agent_display:<20}", style=Style(bold=True))

            # Add the ticker symbol in cyan if available
            if ticker:
                status_text.append(f"[{ticker}] ", style=Style(color="cyan"))
                
            # Add the status text with the appropriate style
            status_text.append(status, style=style)

            # Add the formatted status line to the table
            self.table.add_row(status_text)


# Create a global instance of the progress tracker that can be imported and used
# throughout the application
progress = AgentProgress()