from colorama import Fore, Style  # Library for colored terminal output
from tabulate import tabulate  # Library for creating nice ASCII tables in the terminal
from .analysts import ANALYST_ORDER  # Import the analyst order configuration we saw earlier
import os


def sort_analyst_signals(signals):
    """
    Sort analyst signals in a consistent order based on the ANALYST_ORDER configuration.
    
    This ensures that analysts always appear in the same order in output tables,
    making it easier to compare results across different runs or stocks.
    
    Args:
        signals (list): List of analyst signal data rows to be sorted
        
    Returns:
        list: The sorted list of analyst signals
    """
    # Create a mapping of analyst display names to their position in the order list
    analyst_order = {display: idx for idx, (display, _) in enumerate(ANALYST_ORDER)}
    
    # Add Risk Management at the end if it's not already in the order
    analyst_order["Risk Management"] = len(ANALYST_ORDER)
    
    # Sort signals using the order mapping (uses 999 as a fallback for any unknown analysts)
    return sorted(signals, key=lambda x: analyst_order.get(x[0], 999))


def print_trading_output(result: dict) -> None:
    """
    Print formatted trading results with colored tables for multiple tickers.
    
    This function creates a visually appealing console output with:
    1. A section for each ticker showing analyst signals and confidence
    2. The final trading decision (BUY/SELL/HOLD) with quantity and confidence
    3. A reasoning summary for each decision
    4. A portfolio summary showing all decisions across tickers
    
    Args:
        result (dict): Dictionary containing decisions and analyst signals for multiple tickers
    """
    # Extract the decisions from the result dictionary
    decisions = result.get("decisions")
    if not decisions:
        # If no decisions are available, print an error and exit
        print(f"{Fore.RED}No trading decisions available{Style.RESET_ALL}")
        return

    # Process each ticker one by one
    for ticker, decision in decisions.items():
        # Print ticker header with formatting
        print(f"\n{Fore.WHITE}{Style.BRIGHT}Analysis for {Fore.CYAN}{ticker}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 50}{Style.RESET_ALL}")

        # Prepare analyst signals table for this ticker
        table_data = []
        for agent, signals in result.get("analyst_signals", {}).items():
            # Skip if this ticker isn't in this agent's signals
            if ticker not in signals:
                continue

            # Extract the signal data for this ticker and agent
            signal = signals[ticker]
            
            # Format the agent name for display (e.g. "ben_graham_agent" -> "Ben Graham")
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            
            # Get the signal type (BULLISH, BEARISH, NEUTRAL) and convert to uppercase
            signal_type = signal.get("signal", "").upper()

            # Choose color based on signal type
            signal_color = {
                "BULLISH": Fore.GREEN,  # Green for bullish
                "BEARISH": Fore.RED,    # Red for bearish
                "NEUTRAL": Fore.YELLOW, # Yellow for neutral
            }.get(signal_type, Fore.WHITE)  # Default to white if unknown

            # Add a row to the table with appropriate coloring
            table_data.append(
                [
                    f"{Fore.CYAN}{agent_name}{Style.RESET_ALL}",  # Analyst name in cyan
                    f"{signal_color}{signal_type}{Style.RESET_ALL}",  # Signal with color based on type
                    f"{Fore.YELLOW}{signal.get('confidence')}%{Style.RESET_ALL}",  # Confidence percentage in yellow
                ]
            )

        # Sort the signals according to the predefined order
        table_data = sort_analyst_signals(table_data)

        # Print analyst signals table with formatting
        print(f"\n{Fore.WHITE}{Style.BRIGHT}ANALYST SIGNALS:{Style.RESET_ALL} [{Fore.CYAN}{ticker}{Style.RESET_ALL}]")
        print(
            tabulate(
                table_data,
                headers=[f"{Fore.WHITE}Analyst", "Signal", "Confidence"],
                tablefmt="grid",  # Use grid format for better visual separation
                colalign=("left", "center", "right"),  # Align columns for better readability
            )
        )

        # Print Trading Decision Table
        action = decision.get("action", "").upper()
        
        # Choose color based on action type
        action_color = {
            "BUY": Fore.GREEN,    # Green for buy
            "SELL": Fore.RED,     # Red for sell
            "HOLD": Fore.YELLOW,  # Yellow for hold
        }.get(action, Fore.WHITE)  # Default to white if unknown

        # Format the decision data with appropriate coloring
        decision_data = [
            ["Action", f"{action_color}{action}{Style.RESET_ALL}"],
            ["Quantity", f"{action_color}{decision.get('quantity')}{Style.RESET_ALL}"],
            [
                "Confidence",
                f"{Fore.YELLOW}{decision.get('confidence'):.1f}%{Style.RESET_ALL}",  # Format confidence to 1 decimal place
            ],
        ]

        # Print trading decision table with formatting
        print(f"\n{Fore.WHITE}{Style.BRIGHT}TRADING DECISION:{Style.RESET_ALL} [{Fore.CYAN}{ticker}{Style.RESET_ALL}]")
        print(tabulate(decision_data, tablefmt="grid", colalign=("left", "right")))

        # Print Reasoning section
        print(f"\n{Fore.WHITE}{Style.BRIGHT}Reasoning:{Style.RESET_ALL} {Fore.CYAN}{decision.get('reasoning')}{Style.RESET_ALL}")

    # Print Portfolio Summary section (shows all tickers together)
    print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")
    portfolio_data = []
    
    # Process each ticker's decision for the summary table
    for ticker, decision in decisions.items():
        action = decision.get("action", "").upper()
        
        # Choose color based on action type (includes SHORT and COVER in addition to BUY/SELL/HOLD)
        action_color = {
            "BUY": Fore.GREEN,
            "SELL": Fore.RED,
            "HOLD": Fore.YELLOW,
            "COVER": Fore.GREEN,  # Cover short position (buying) = green
            "SHORT": Fore.RED,    # Short selling = red
        }.get(action, Fore.WHITE)
        
        # Add a row to the portfolio summary table
        portfolio_data.append(
            [
                f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",  # Ticker symbol in cyan
                f"{action_color}{action}{Style.RESET_ALL}",  # Action with appropriate color
                f"{action_color}{decision.get('quantity')}{Style.RESET_ALL}",  # Quantity with same color as action
                f"{Fore.YELLOW}{decision.get('confidence'):.1f}%{Style.RESET_ALL}",  # Confidence with 1 decimal place
            ]
        )

    # Print the portfolio summary table
    print(
        tabulate(
            portfolio_data,
            headers=[f"{Fore.WHITE}Ticker", "Action", "Quantity", "Confidence"],
            tablefmt="grid",
            colalign=("left", "center", "right", "right"),  # Align columns for better readability
        )
    )


def print_backtest_results(table_rows: list) -> None:
    """
    Print the backtest results in a nicely formatted table.
    
    This function clears the screen and displays:
    1. A portfolio summary with current value, cash balance, and performance metrics
    2. A detailed table showing each trade and position over time
    
    Args:
        table_rows (list): List of formatted rows containing backtest results
    """
    # Clear the screen for a clean display
    os.system("cls" if os.name == "nt" else "clear")

    # Split rows into ticker rows and summary rows
    ticker_rows = []
    summary_rows = []

    # Separate regular ticker rows from portfolio summary rows
    for row in table_rows:
        if isinstance(row[1], str) and "PORTFOLIO SUMMARY" in row[1]:
            summary_rows.append(row)
        else:
            ticker_rows.append(row)

    # Display latest portfolio summary information if available
    if summary_rows:
        latest_summary = summary_rows[-1]  # Get the most recent summary
        print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")

        # Extract values and remove commas before converting to float
        # The string parsing here extracts numeric values from formatted output strings
        cash_str = latest_summary[7].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        position_str = latest_summary[6].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        total_str = latest_summary[8].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")

        # Print summary metrics with formatting
        print(f"Cash Balance: {Fore.CYAN}${float(cash_str):,.2f}{Style.RESET_ALL}")
        print(f"Total Position Value: {Fore.YELLOW}${float(position_str):,.2f}{Style.RESET_ALL}")
        print(f"Total Value: {Fore.WHITE}${float(total_str):,.2f}{Style.RESET_ALL}")
        print(f"Return: {latest_summary[9]}")
        
        # Display performance metrics if available
        if latest_summary[10]:  # Sharpe ratio - risk-adjusted return measure
            print(f"Sharpe Ratio: {latest_summary[10]}")
        if latest_summary[11]:  # Sortino ratio - downside risk-adjusted return
            print(f"Sortino Ratio: {latest_summary[11]}")
        if latest_summary[12]:  # Max drawdown - largest peak-to-trough drop
            print(f"Max Drawdown: {latest_summary[12]}")

    # Add vertical spacing for better readability
    print("\n" * 2)

    # Print the table with just ticker rows (detailed trade history)
    print(
        tabulate(
            ticker_rows,
            headers=[
                "Date",             # Date of the trade
                "Ticker",           # Stock symbol
                "Action",           # BUY/SELL/HOLD/SHORT/COVER
                "Quantity",         # Number of shares
                "Price",            # Price per share
                "Shares",           # Total shares owned after trade
                "Position Value",   # Total position value
                "Bullish",          # Count of bullish analysts
                "Bearish",          # Count of bearish analysts 
                "Neutral",          # Count of neutral analysts
            ],
            tablefmt="grid",
            colalign=(
                "left",   # Date
                "left",   # Ticker
                "center", # Action
                "right",  # Quantity
                "right",  # Price
                "right",  # Shares
                "right",  # Position Value
                "right",  # Bullish
                "right",  # Bearish
                "right",  # Neutral
            ),
        )
    )

    # Add vertical spacing at the end
    print("\n" * 4)


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    shares_owned: float,
    position_value: float,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
    is_summary: bool = False,
    total_value: float = None,
    return_pct: float = None,
    cash_balance: float = None,
    total_position_value: float = None,
    sharpe_ratio: float = None,
    sortino_ratio: float = None,
    max_drawdown: float = None,
) -> list[any]:
    """
    Format a row for the backtest results table with appropriate coloring.
    
    This function handles two types of rows:
    1. Regular ticker rows showing individual trades
    2. Summary rows showing portfolio performance metrics
    
    Args:
        date (str): Date of the trade/summary
        ticker (str): Stock symbol
        action (str): BUY/SELL/HOLD/SHORT/COVER
        quantity (float): Number of shares traded
        price (float): Price per share
        shares_owned (float): Total shares owned after trade
        position_value (float): Value of position after trade
        bullish_count (int): Number of analysts with bullish signals
        bearish_count (int): Number of analysts with bearish signals
        neutral_count (int): Number of analysts with neutral signals
        is_summary (bool): Whether this is a summary row
        total_value (float): Total portfolio value (for summary rows)
        return_pct (float): Total return percentage (for summary rows)
        cash_balance (float): Available cash (for summary rows)
        total_position_value (float): Total value of all positions (for summary rows)
        sharpe_ratio (float): Sharpe ratio performance metric
        sortino_ratio (float): Sortino ratio performance metric
        max_drawdown (float): Maximum drawdown percentage
        
    Returns:
        list: Formatted row with appropriate colors for display
    """
    # Choose color based on action type
    action_color = {
        "BUY": Fore.GREEN,    # Green for buy actions
        "COVER": Fore.GREEN,  # Green for covering short positions
        "SELL": Fore.RED,     # Red for sell actions
        "SHORT": Fore.RED,    # Red for short selling
        "HOLD": Fore.YELLOW,  # Yellow for hold actions
    }.get(action.upper(), Fore.WHITE)  # Default to white if unknown

    if is_summary:
        # Format for summary rows (portfolio performance)
        return_color = Fore.GREEN if return_pct >= 0 else Fore.RED  # Green for positive returns, red for negative
        
        return [
            date,
            f"{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY{Style.RESET_ALL}",
            "",  # Action (empty for summary)
            "",  # Quantity (empty for summary)
            "",  # Price (empty for summary)
            "",  # Shares (empty for summary)
            f"{Fore.YELLOW}${total_position_value:,.2f}{Style.RESET_ALL}",  # Total Position Value with 2 decimal places
            f"{Fore.CYAN}${cash_balance:,.2f}{Style.RESET_ALL}",  # Cash Balance with 2 decimal places
            f"{Fore.WHITE}${total_value:,.2f}{Style.RESET_ALL}",  # Total Value with 2 decimal places
            f"{return_color}{return_pct:+.2f}%{Style.RESET_ALL}",  # Return with sign and 2 decimal places
            f"{Fore.YELLOW}{sharpe_ratio:.2f}{Style.RESET_ALL}" if sharpe_ratio is not None else "",  # Sharpe Ratio
            f"{Fore.YELLOW}{sortino_ratio:.2f}{Style.RESET_ALL}" if sortino_ratio is not None else "",  # Sortino Ratio
            f"{Fore.RED}{max_drawdown:.2f}%{Style.RESET_ALL}" if max_drawdown is not None else "",  # Max Drawdown
        ]
    else:
        # Format for regular ticker rows (individual trades)
        return [
            date,
            f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",  # Ticker in cyan
            f"{action_color}{action.upper()}{Style.RESET_ALL}",  # Action with appropriate color
            f"{action_color}{quantity:,.0f}{Style.RESET_ALL}",  # Quantity with same color as action, no decimals
            f"{Fore.WHITE}{price:,.2f}{Style.RESET_ALL}",  # Price with 2 decimal places
            f"{Fore.WHITE}{shares_owned:,.0f}{Style.RESET_ALL}",  # Shares owned with no decimals
            f"{Fore.YELLOW}{position_value:,.2f}{Style.RESET_ALL}",  # Position value with 2 decimal places
            f"{Fore.GREEN}{bullish_count}{Style.RESET_ALL}",  # Bullish count in green
            f"{Fore.RED}{bearish_count}{Style.RESET_ALL}",  # Bearish count in red
            f"{Fore.BLUE}{neutral_count}{Style.RESET_ALL}",  # Neutral count in blue
        ]