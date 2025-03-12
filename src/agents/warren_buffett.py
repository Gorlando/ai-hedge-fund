# Import necessary modules and components
from graph.state import AgentState, show_agent_reasoning  # For managing agent state and displaying reasoning
from langchain_core.prompts import ChatPromptTemplate     # For creating chat prompts
from langchain_core.messages import HumanMessage          # For creating human-readable messages
from pydantic import BaseModel                            # For data validation and settings management
import json                                               # For working with JSON data
from typing_extensions import Literal                     # For defining literal types
from tools.api import get_financial_metrics, get_market_cap, search_line_items  # Data fetching tools
from utils.llm import call_llm                            # For calling large language models
from utils.progress import progress                       # For tracking progress

# Define the structure of our output signal using Pydantic
class WarrenBuffettSignal(BaseModel):
    """Defines the structure of the investment signal output"""
    signal: Literal["bullish", "bearish", "neutral"]  # Possible values for the signal
    confidence: float                                  # Confidence level (0-100)
    reasoning: str                                     # Explanation for the decision

def warren_buffett_agent(state: AgentState):
    """Main agent function that analyzes stocks using Warren Buffett's principles"""
    # Get necessary data from the shared state
    data = state["data"]
    end_date = data["end_date"]    # The end date for our analysis
    tickers = data["tickers"]      # List of stock symbols to analyze (e.g., ['AAPL', 'GOOG'])

    # Prepare storage for our analysis results
    analysis_data = {}    # Stores raw analysis data
    buffett_analysis = {} # Stores final formatted analysis

    # Analyze each stock ticker one by one
    for ticker in tickers:
        # Update progress tracker
        progress.update_status("warren_buffett_agent", ticker, "Fetching financial metrics")
        
        # Step 1: Get financial metrics (e.g., ROE, debt ratios)
        metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=5)

        # Step 2: Get detailed financial line items from balance sheet/income statement
        progress.update_status("warren_buffett_agent", ticker, "Gathering financial line items")
        financial_line_items = search_line_items(
            ticker,
            ["capital_expenditure", "depreciation_and_amortization", "net_income",
             "outstanding_shares", "total_assets", "total_liabilities"],
            end_date,
            period="ttm",
            limit=5,
        )

        # Step 3: Get current company value (market capitalization)
        progress.update_status("warren_buffett_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)

        # Step 4: Analyze fundamental financial health
        progress.update_status("warren_buffett_agent", ticker, "Analyzing fundamentals")
        fundamental_analysis = analyze_fundamentals(metrics)

        # Step 5: Check consistency of earnings over time
        progress.update_status("warren_buffett_agent", ticker, "Analyzing consistency")
        consistency_analysis = analyze_consistency(financial_line_items)

        # Step 6: Calculate intrinsic value (true worth of company)
        progress.update_status("warren_buffett_agent", ticker, "Calculating intrinsic value")
        intrinsic_value_analysis = calculate_intrinsic_value(financial_line_items)

        # Calculate total score based on fundamental and consistency analysis
        total_score = fundamental_analysis["score"] + consistency_analysis["score"]
        max_possible_score = 10  # Initial maximum score possible

        # Calculate margin of safety (difference between intrinsic value and market price)
        margin_of_safety = None
        intrinsic_value = intrinsic_value_analysis["intrinsic_value"]
        if intrinsic_value and market_cap:
            margin_of_safety = (intrinsic_value - market_cap) / market_cap

            # Add bonus points for good margin of safety (>30%)
            if margin_of_safety > 0.3:
                total_score += 2
                max_possible_score += 2

        # Determine investment signal based on score thresholds
        if total_score >= 0.7 * max_possible_score:
            signal = "bullish"    # Good investment
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"    # Bad investment
        else:
            signal = "neutral"    # Neutral position

        # Store all analysis data for this stock
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "fundamental_analysis": fundamental_analysis,
            "consistency_analysis": consistency_analysis,
            "intrinsic_value_analysis": intrinsic_value_analysis,
            "market_cap": market_cap,
            "margin_of_safety": margin_of_safety,
        }

        # Generate final output using LLM with Buffett's principles
        progress.update_status("warren_buffett_agent", ticker, "Generating Buffett analysis")
        buffett_output = generate_buffett_output(
            ticker=ticker,
            analysis_data=analysis_data,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )

        # Store formatted results for this stock
        buffett_analysis[ticker] = {
            "signal": buffett_output.signal,
            "confidence": buffett_output.confidence,
            "reasoning": buffett_output.reasoning,
        }

        progress.update_status("warren_buffett_agent", ticker, "Done")

    # Create human-readable message with analysis results
    message = HumanMessage(content=json.dumps(buffett_analysis), name="warren_buffett_agent")

    # Show detailed reasoning if requested in settings
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(buffett_analysis, "Warren Buffett Agent")

    # Save results to the shared state
    state["data"]["analyst_signals"]["warren_buffett_agent"] = buffett_analysis

    return {"messages": [message], "data": state["data"]}

def analyze_fundamentals(metrics: list) -> dict[str, any]:
    """Evaluates company fundamentals using key financial ratios"""
    if not metrics:
        return {"score": 0, "details": "Insufficient fundamental data"}

    # Use most recent financial metrics
    latest_metrics = metrics[0]
    score = 0
    reasoning = []

    # 1. Check Return on Equity (ROE) - measures profit generation
    if latest_metrics.return_on_equity and latest_metrics.return_on_equity > 0.15:
        score += 2
        reasoning.append(f"Strong ROE of {latest_metrics.return_on_equity:.1%}")
    elif latest_metrics.return_on_equity:
        reasoning.append(f"Weak ROE of {latest_metrics.return_on_equity:.1%}")
    else:
        reasoning.append("ROE data not available")

    # 2. Check Debt-to-Equity Ratio - measures financial leverage
    if latest_metrics.debt_to_equity and latest_metrics.debt_to_equity < 0.5:
        score += 2
        reasoning.append("Conservative debt levels")
    elif latest_metrics.debt_to_equity:
        reasoning.append(f"High debt to equity ratio of {latest_metrics.debt_to_equity:.1f}")
    else:
        reasoning.append("Debt to equity data not available")

    # 3. Check Operating Margin - measures profitability
    if latest_metrics.operating_margin and latest_metrics.operating_margin > 0.15:
        score += 2
        reasoning.append("Strong operating margins")
    elif latest_metrics.operating_margin:
        reasoning.append(f"Weak operating margin of {latest_metrics.operating_margin:.1%}")
    else:
        reasoning.append("Operating margin data not available")

    # 4. Check Current Ratio - measures short-term liquidity
    if latest_metrics.current_ratio and latest_metrics.current_ratio > 1.5:
        score += 1
        reasoning.append("Good liquidity position")
    elif latest_metrics.current_ratio:
        reasoning.append(f"Weak liquidity with current ratio of {latest_metrics.current_ratio:.1f}")
    else:
        reasoning.append("Current ratio data not available")

    return {
        "score": score,
        "details": "; ".join(reasoning),
        "metrics": latest_metrics.model_dump()
    }

def analyze_consistency(financial_line_items: list) -> dict[str, any]:
    """Checks for consistent earnings growth over time"""
    if len(financial_line_items) < 4:
        return {"score": 0, "details": "Insufficient historical data"}

    score = 0
    reasoning = []

    # Look at net income history
    earnings_values = [item.net_income for item in financial_line_items if item.net_income]
    
    # Check for consistent growth trend
    if len(earnings_values) >= 4:
        # Verify each year is better than previous
        earnings_growth = all(earnings_values[i] > earnings_values[i + 1] 
                          for i in range(len(earnings_values) - 1))
        
        if earnings_growth:
            score += 3
            reasoning.append("Consistent earnings growth over past periods")
        else:
            reasoning.append("Inconsistent earnings growth pattern")

        # Calculate total growth percentage
        if len(earnings_values) >= 2:
            growth_rate = (earnings_values[0] - earnings_values[-1]) / abs(earnings_values[-1])
            reasoning.append(f"Total earnings growth of {growth_rate:.1%} over past periods")

    return {"score": score, "details": "; ".join(reasoning)}

def calculate_owner_earnings(financial_line_items: list) -> dict[str, any]:
    """Calculates Buffett's preferred earnings metric"""
    if not financial_line_items:
        return {"owner_earnings": None, "details": ["Insufficient data"]}

    latest = financial_line_items[0]
    
    # Owner Earnings = Net Income + Depreciation - Maintenance Capital Expenditures
    net_income = latest.net_income
    depreciation = latest.depreciation_and_amortization
    capex = latest.capital_expenditure

    if not all([net_income, depreciation, capex]):
        return {"owner_earnings": None, "details": ["Missing data components"]}

    # Estimate maintenance capex (75% of total capital expenditures)
    maintenance_capex = capex * 0.75
    owner_earnings = net_income + depreciation - maintenance_capex

    return {
        "owner_earnings": owner_earnings,
        "components": {
            "net_income": net_income,
            "depreciation": depreciation,
            "maintenance_capex": maintenance_capex
        },
        "details": ["Owner earnings calculated successfully"]
    }

def calculate_intrinsic_value(financial_line_items: list) -> dict[str, any]:
    """Calculates company's intrinsic value using discounted cash flow (DCF)"""
    if not financial_line_items:
        return {"value": None, "details": ["Insufficient data for valuation"]}

    # Get owner earnings from previous calculation
    earnings_data = calculate_owner_earnings(financial_line_items)
    if not earnings_data["owner_earnings"]:
        return earnings_data  # Pass through the error details

    owner_earnings = earnings_data["owner_earnings"]
    shares_outstanding = financial_line_items[0].outstanding_shares

    if not shares_outstanding:
        return {"value": None, "details": ["Missing shares data"]}

    # DCF calculation parameters (conservative estimates)
    growth_rate = 0.05     # 5% annual growth
    discount_rate = 0.09   # 9% required return
    terminal_multiple = 12 # Final valuation multiple
    projection_years = 10  # 10-year projection

    # Calculate present value of future cash flows
    future_value = 0
    for year in range(1, projection_years + 1):
        future_earnings = owner_earnings * (1 + growth_rate) ** year
        present_value = future_earnings / (1 + discount_rate) ** year
        future_value += present_value

    # Add terminal value (company value at end of projection period)
    terminal_value = (owner_earnings * (1 + growth_rate) ** projection_years *
                     terminal_multiple) / (1 + discount_rate) ** projection_years
    intrinsic_value = future_value + terminal_value

    return {
        "intrinsic_value": intrinsic_value,
        "owner_earnings": owner_earnings,
        "assumptions": {
            "growth_rate": growth_rate,
            "discount_rate": discount_rate,
            "terminal_multiple": terminal_multiple,
            "projection_years": projection_years
        },
        "details": ["Intrinsic value calculated using DCF model"]
    }

def generate_buffett_output(
    ticker: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> WarrenBuffettSignal:
    """Uses LLM to generate final investment signal following Buffett's principles"""
    # Create prompt template with investment guidelines
    template = ChatPromptTemplate.from_messages([
        ("system", """You are Warren Buffett's AI assistant. Follow these rules:
        1. Only invest in understandable businesses
        2. Require >30% margin of safety
        3. Look for durable competitive advantages
        4. Prefer consistent earnings growth
        5. Avoid companies with high debt
        6. Long-term investment horizon"""),
        
        ("human", """Analyze this data for {ticker}:
        {analysis_data}
        
        Return JSON with:
        - signal (bullish/bearish/neutral)
        - confidence (0-100)
        - reasoning (short explanation)""")
    ])

    # Create the actual prompt with our data
    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "ticker": ticker
    })

    # Default response if something goes wrong
    def create_default_signal():
        return WarrenBuffettSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="Analysis error"
        )

    # Call the LLM and return formatted response
    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=WarrenBuffettSignal,
        agent_name="warren_buffett_agent",
        default_factory=create_default_signal,
    )