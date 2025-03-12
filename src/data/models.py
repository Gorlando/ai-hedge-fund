from pydantic import BaseModel


class Price(BaseModel):
    """
    Represents daily stock price data with OHLCV values.
    
    This model contains the standard Open-High-Low-Close-Volume data points
    used in financial analysis and charting.
    """
    open: float    # Opening price for the period
    close: float   # Closing price for the period
    high: float    # Highest price reached during the period
    low: float     # Lowest price reached during the period
    volume: int    # Trading volume (number of shares)
    time: str      # Timestamp in ISO format (YYYY-MM-DD)


class PriceResponse(BaseModel):
    """
    Container for price data API responses.
    
    This model wraps a list of Price objects along with the ticker symbol,
    making it suitable for API responses that return historical price data.
    """
    ticker: str           # Stock symbol (e.g., "AAPL")
    prices: list[Price]   # List of price data points


class FinancialMetrics(BaseModel):
    """
    Comprehensive collection of financial metrics and ratios for a company.
    
    This model contains a wide range of financial indicators organized by category:
    - Valuation ratios (P/E, EV/EBITDA, etc.)
    - Profitability metrics (margins, returns)
    - Efficiency metrics (turnover ratios)
    - Liquidity ratios
    - Solvency ratios
    - Growth metrics
    - Per-share metrics
    
    These metrics are commonly used in fundamental analysis to assess
    a company's financial health, performance, and valuation.
    """
    ticker: str          # Stock symbol
    report_period: str   # Date of the report period (e.g., "2023-12-31")
    period: str          # Type of period (e.g., "ttm" for trailing twelve months, "annual", "quarterly")
    currency: str        # Currency of the financial data (e.g., "USD")
    
    # Valuation metrics
    market_cap: float | None                      # Total market value of shares outstanding
    enterprise_value: float | None                # Market cap + debt - cash (total company value)
    price_to_earnings_ratio: float | None         # P/E ratio (price / earnings per share)
    price_to_book_ratio: float | None             # P/B ratio (price / book value per share)
    price_to_sales_ratio: float | None            # P/S ratio (price / sales per share)
    enterprise_value_to_ebitda_ratio: float | None # EV/EBITDA ratio
    enterprise_value_to_revenue_ratio: float | None # EV/Revenue ratio
    free_cash_flow_yield: float | None            # FCF / Market Cap
    peg_ratio: float | None                       # P/E ratio divided by growth rate
    
    # Profitability metrics
    gross_margin: float | None                    # Gross profit / Revenue
    operating_margin: float | None                # Operating income / Revenue
    net_margin: float | None                      # Net income / Revenue
    return_on_equity: float | None                # Net income / Shareholders' equity (ROE)
    return_on_assets: float | None                # Net income / Total assets (ROA)
    return_on_invested_capital: float | None      # NOPAT / Invested capital (ROIC)
    
    # Efficiency metrics
    asset_turnover: float | None                  # Revenue / Average total assets
    inventory_turnover: float | None              # COGS / Average inventory
    receivables_turnover: float | None            # Revenue / Average accounts receivable
    days_sales_outstanding: float | None          # 365 / Receivables turnover
    operating_cycle: float | None                 # Days inventory + Days receivables
    working_capital_turnover: float | None        # Revenue / Average working capital
    
    # Liquidity ratios
    current_ratio: float | None                   # Current assets / Current liabilities
    quick_ratio: float | None                     # (Current assets - Inventory) / Current liabilities
    cash_ratio: float | None                      # Cash & equivalents / Current liabilities
    operating_cash_flow_ratio: float | None       # OCF / Current liabilities
    
    # Solvency ratios
    debt_to_equity: float | None                  # Total debt / Shareholders' equity
    debt_to_assets: float | None                  # Total debt / Total assets
    interest_coverage: float | None               # EBIT / Interest expense
    
    # Growth metrics
    revenue_growth: float | None                  # YoY revenue growth rate
    earnings_growth: float | None                 # YoY earnings growth rate
    book_value_growth: float | None               # YoY book value growth rate
    earnings_per_share_growth: float | None       # YoY EPS growth rate
    free_cash_flow_growth: float | None           # YoY FCF growth rate
    operating_income_growth: float | None         # YoY operating income growth rate
    ebitda_growth: float | None                   # YoY EBITDA growth rate
    
    # Per-share metrics
    payout_ratio: float | None                    # Dividends / Net income
    earnings_per_share: float | None              # Net income / Shares outstanding
    book_value_per_share: float | None            # Shareholders' equity / Shares outstanding
    free_cash_flow_per_share: float | None        # Free cash flow / Shares outstanding


class FinancialMetricsResponse(BaseModel):
    """
    Container for financial metrics API responses.
    
    This model wraps a list of FinancialMetrics objects, making it
    suitable for API responses that return financial data.
    """
    financial_metrics: list[FinancialMetrics]  # List of financial metrics


class LineItem(BaseModel):
    """
    Represents a specific financial statement line item.
    
    This model is flexible and can represent any line item from financial statements
    (income statement, balance sheet, cash flow statement). Additional fields
    can be added dynamically since it allows extra fields.
    """
    ticker: str         # Stock symbol
    report_period: str  # Date of the report period
    period: str         # Type of period (e.g., "ttm", "annual", "quarterly")
    currency: str       # Currency of the financial data

    # Allow additional fields dynamically
    # This enables adding specific line items like "revenue", "net_income", etc.
    model_config = {"extra": "allow"}


class LineItemResponse(BaseModel):
    """
    Container for line item search API responses.
    
    This model wraps a list of LineItem objects, making it suitable for
    API responses that return searches for specific financial statement items.
    """
    search_results: list[LineItem]  # List of line item search results


class InsiderTrade(BaseModel):
    """
    Represents an insider trading transaction.
    
    This model contains information about stock transactions made by company
    insiders (executives, directors, major shareholders), including details
    about who made the trade, how many shares, at what price, and when.
    
    Insider trading patterns can be useful indicators for investment analysis.
    """
    ticker: str                               # Stock symbol
    issuer: str | None                        # Issuing company name
    name: str | None                          # Name of the insider
    title: str | None                         # Job title of the insider
    is_board_director: bool | None            # Whether the insider is a board director
    transaction_date: str | None              # Date of the transaction
    transaction_shares: float | None          # Number of shares in the transaction
    transaction_price_per_share: float | None # Price per share in the transaction
    transaction_value: float | None           # Total value of the transaction
    shares_owned_before_transaction: float | None  # Shares owned before the transaction
    shares_owned_after_transaction: float | None   # Shares owned after the transaction
    security_title: str | None                # Type of security (e.g., "Common Stock")
    filing_date: str                          # Date the insider filing was submitted


class InsiderTradeResponse(BaseModel):
    """
    Container for insider trade API responses.
    
    This model wraps a list of InsiderTrade objects, making it suitable
    for API responses that return insider trading data.
    """
    insider_trades: list[InsiderTrade]  # List of insider trades


class CompanyNews(BaseModel):
    """
    Represents a news article about a company.
    
    This model contains information about news articles related to a company,
    including the title, source, date, and URL. It can also include sentiment
    analysis of the article (positive, negative, neutral).
    
    News sentiment can be a valuable input for investment analysis.
    """
    ticker: str           # Stock symbol the news relates to
    title: str            # Title of the news article
    author: str           # Author of the article
    source: str           # News source (e.g., "Bloomberg", "CNBC")
    date: str             # Publication date
    url: str              # URL to the full article
    sentiment: str | None = None  # Sentiment classification (positive/negative/neutral)


class CompanyNewsResponse(BaseModel):
    """
    Container for company news API responses.
    
    This model wraps a list of CompanyNews objects, making it suitable
    for API responses that return news data about companies.
    """
    news: list[CompanyNews]  # List of news articles


class Position(BaseModel):
    """
    Represents a position in a portfolio.
    
    This model tracks the details of a position in a specific security,
    including the number of shares owned and any associated cash.
    """
    cash: float = 0.0     # Cash associated with this position (e.g., for partial shares)
    shares: int = 0       # Number of shares owned
    ticker: str           # Stock symbol


class Portfolio(BaseModel):
    """
    Represents an investment portfolio.
    
    This model tracks all positions across different securities, as well as
    the total cash available in the portfolio.
    """
    positions: dict[str, Position]  # Mapping of ticker -> Position
    total_cash: float = 0.0         # Total cash available in the portfolio


class AnalystSignal(BaseModel):
    """
    Represents an investment signal from an analyst.
    
    This model captures the outputs from analyst agents, including their
    bullish/bearish/neutral signal, confidence level, reasoning, and
    position size recommendations.
    """
    signal: str | None = None           # BULLISH, BEARISH, or NEUTRAL
    confidence: float | None = None     # Confidence level (0-100%)
    reasoning: dict | str | None = None # Explanation for the signal
    max_position_size: float | None = None  # Recommended maximum position size (for risk management)


class TickerAnalysis(BaseModel):
    """
    Aggregates analyst signals for a specific ticker.
    
    This model collects signals from multiple analysts for a single stock,
    allowing for comparison and aggregation of different perspectives.
    """
    ticker: str                                  # Stock symbol
    analyst_signals: dict[str, AnalystSignal]    # Mapping of agent_name -> signal


class AgentStateData(BaseModel):
    """
    Represents the current state of the agent system.
    
    This model stores the overall state of the analysis system, including
    the tickers being analyzed, portfolio status, date range, and all
    the ticker analyses that have been completed.
    """
    tickers: list[str]                          # List of tickers being analyzed
    portfolio: Portfolio                        # Current portfolio state
    start_date: str                             # Start date of analysis period
    end_date: str                               # End date of analysis period
    ticker_analyses: dict[str, TickerAnalysis]  # Mapping of ticker -> analysis results


class AgentStateMetadata(BaseModel):
    """
    Configuration metadata for the agent system.
    
    This model stores additional configuration options that control
    how the agent system operates, such as whether to show detailed
    reasoning in outputs.
    """
    show_reasoning: bool = False  # Whether to include reasoning in outputs
    model_config = {"extra": "allow"}  # Allow additional configuration fields