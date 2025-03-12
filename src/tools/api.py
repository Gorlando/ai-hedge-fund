import os
import pandas as pd
import requests

from data.cache import get_cache  # Import a caching mechanism to store API responses
from data.models import (
    # Import Pydantic data models that provide structure and validation for financial data
    CompanyNews,          # News articles about companies
    CompanyNewsResponse,  # Container for news API responses
    FinancialMetrics,     # Key financial indicators (P/E, EV/EBITDA, etc.)
    FinancialMetricsResponse,  # Container for metrics API responses
    Price,                # Stock price data (OHLCV)
    PriceResponse,        # Container for price API responses
    LineItem,             # Specific financial statement line items
    LineItemResponse,     # Container for line item API responses
    InsiderTrade,         # Insider trading information
    InsiderTradeResponse, # Container for insider trading API responses
)

# Create a global cache instance to store API responses and reduce redundant API calls
# This is like having a local database of previously retrieved financial data
_cache = get_cache()


def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """
    Fetch historical stock price data for a company.
    
    This function first checks if the data is already cached locally.
    If not, it calls the financial data API to retrieve the data.
    
    Parameters:
    - ticker: Stock symbol (e.g., "AAPL" for Apple)
    - start_date: Beginning of date range in ISO format (YYYY-MM-DD)
    - end_date: End of date range in ISO format (YYYY-MM-DD)
    
    Returns:
    - List of Price objects containing OHLCV (Open, High, Low, Close, Volume) data
    """
    # First check if we already have this data cached locally
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by the requested date range and convert to Price objects
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data  # Return cached data if available

    # If data isn't cached or doesn't cover the requested range, fetch from API
    headers = {}
    # Add API key to headers if it exists in environment variables
    if api_key := os.environ.get("FINANCIAL_DATASETS_API_KEY"):
        headers["X-API-KEY"] = api_key

    # Construct API URL with query parameters
    url = f"https://api.financialdatasets.ai/prices/?ticker={ticker}&interval=day&interval_multiplier=1&start_date={start_date}&end_date={end_date}"
    response = requests.get(url, headers=headers)
    
    # Raise an exception if the API request fails
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

    # Parse API response into a structured Pydantic model
    price_response = PriceResponse(**response.json())
    prices = price_response.prices

    if not prices:
        return []  # Return empty list if no data available

    # Cache the results for future use (converts Price objects to dictionaries for storage)
    _cache.set_prices(ticker, [p.model_dump() for p in prices])
    return prices


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",  # ttm = trailing twelve months
    limit: int = 10,
) -> list[FinancialMetrics]:
    """
    Fetch key financial metrics for a company.
    
    These metrics typically include valuation ratios (P/E, EV/EBITDA), profitability 
    measures (ROE, ROA), and debt ratios among others.
    
    Parameters:
    - ticker: Stock symbol
    - end_date: Only return metrics up to this date
    - period: Financial reporting period (e.g., "ttm" for trailing twelve months)
    - limit: Maximum number of reporting periods to return
    
    Returns:
    - List of FinancialMetrics objects sorted by reporting date (newest first)
    """
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        # Filter cached data by date and limit
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)  # Sort newest first
        if filtered_data:
            return filtered_data[:limit]  # Return limited number of metrics

    # If not in cache or insufficient data, fetch from API
    headers = {}
    if api_key := os.environ.get("FINANCIAL_DATASETS_API_KEY"):
        headers["X-API-KEY"] = api_key

    # Construct API URL with query parameters
    url = f"https://api.financialdatasets.ai/financial-metrics/?ticker={ticker}&report_period_lte={end_date}&limit={limit}&period={period}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

    # Parse response with Pydantic model
    metrics_response = FinancialMetricsResponse(**response.json())
    financial_metrics = metrics_response.financial_metrics

    if not financial_metrics:
        return []  # Return empty list if no data available

    # Cache the results as dictionaries
    _cache.set_financial_metrics(ticker, [m.model_dump() for m in financial_metrics])
    return financial_metrics


def search_line_items(
    ticker: str,
    line_items: list[str],  # Specific financial statement items like "revenue", "net_income", etc.
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """
    Search for specific line items from financial statements.
    
    This is useful for extracting particular values like "Revenue" or "Net Income"
    rather than downloading entire financial statements.
    
    Parameters:
    - ticker: Stock symbol
    - line_items: List of financial statement items to retrieve
    - end_date: Only return data up to this date
    - period: Financial reporting period (e.g., "ttm" for trailing twelve months)
    - limit: Maximum number of reporting periods to return
    
    Returns:
    - List of LineItem objects containing the requested financial data
    """
    # This function doesn't check cache - always fetches fresh data
    headers = {}
    if api_key := os.environ.get("FINANCIAL_DATASETS_API_KEY"):
        headers["X-API-KEY"] = api_key

    # Using POST request since we're sending a more complex query
    url = "https://api.financialdatasets.ai/financials/search/line-items"

    # Create request body with search parameters
    body = {
        "tickers": [ticker],
        "line_items": line_items,  # List of specific items like "revenue", "net_income"
        "end_date": end_date,
        "period": period,
        "limit": limit,
    }
    
    # Send POST request with JSON body
    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")
    
    data = response.json()
    response_model = LineItemResponse(**data)
    search_results = response_model.search_results
    
    if not search_results:
        return []  # Return empty list if no data available

    # No caching implemented for line item searches
    return search_results[:limit]


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[InsiderTrade]:
    """
    Fetch insider trading data for a company.
    
    This retrieves information about stock purchases, sales, and option exercises
    by company executives, directors, and major shareholders.
    
    Parameters:
    - ticker: Stock symbol
    - end_date: End date for insider trade data
    - start_date: Optional start date for insider trade data
    - limit: Maximum number of trades to return per API call
    
    Returns:
    - List of InsiderTrade objects sorted by transaction date (newest first)
    """
    # Check cache first
    if cached_data := _cache.get_insider_trades(ticker):
        # Filter cached data by date range
        filtered_data = [InsiderTrade(**trade) for trade in cached_data 
                        if (start_date is None or (trade.get("transaction_date") or trade["filing_date"]) >= start_date)
                        and (trade.get("transaction_date") or trade["filing_date"]) <= end_date]
        
        # Sort by transaction date or filing date if transaction date is not available
        filtered_data.sort(key=lambda x: x.transaction_date or x.filing_date, reverse=True)
        if filtered_data:
            return filtered_data

    # If not in cache or insufficient data, fetch from API
    headers = {}
    if api_key := os.environ.get("FINANCIAL_DATASETS_API_KEY"):
        headers["X-API-KEY"] = api_key

    all_trades = []
    current_end_date = end_date
    
    # Pagination loop to handle large datasets that require multiple API calls
    while True:
        # Build URL with query parameters
        url = f"https://api.financialdatasets.ai/insider-trades/?ticker={ticker}&filing_date_lte={current_end_date}"
        if start_date:
            url += f"&filing_date_gte={start_date}"
        url += f"&limit={limit}"
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")
        
        data = response.json()
        response_model = InsiderTradeResponse(**data)
        insider_trades = response_model.insider_trades
        
        if not insider_trades:
            break  # Exit loop if no more data
            
        all_trades.extend(insider_trades)  # Add results to our collection
        
        # Only continue pagination if we have a start_date and got a full page of results
        if not start_date or len(insider_trades) < limit:
            break
            
        # Update end_date to the oldest filing date from current batch for next iteration
        # This creates a "moving window" approach to pagination
        current_end_date = min(trade.filing_date for trade in insider_trades).split('T')[0]
        
        # If we've reached or passed the start_date, we can stop paginating
        if current_end_date <= start_date:
            break

    if not all_trades:
        return []  # Return empty list if no data available

    # Cache all retrieved trades for future use
    _cache.set_insider_trades(ticker, [trade.model_dump() for trade in all_trades])
    return all_trades


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[CompanyNews]:
    """
    Fetch news articles about a company.
    
    This retrieves news headlines, sources, and links for a specific company.
    Useful for event studies or understanding market reactions to company news.
    
    Parameters:
    - ticker: Stock symbol
    - end_date: End date for news articles
    - start_date: Optional start date for news articles
    - limit: Maximum number of news items to return per API call
    
    Returns:
    - List of CompanyNews objects sorted by date (newest first)
    """
    # Check cache first
    if cached_data := _cache.get_company_news(ticker):
        # Filter cached data by date range
        filtered_data = [CompanyNews(**news) for news in cached_data 
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)  # Sort newest first
        if filtered_data:
            return filtered_data

    # If not in cache or insufficient data, fetch from API
    headers = {}
    if api_key := os.environ.get("FINANCIAL_DATASETS_API_KEY"):
        headers["X-API-KEY"] = api_key

    all_news = []
    current_end_date = end_date
    
    # Pagination loop to handle large datasets that require multiple API calls
    while True:
        # Build URL with query parameters
        url = f"https://api.financialdatasets.ai/news/?ticker={ticker}&end_date={current_end_date}"
        if start_date:
            url += f"&start_date={start_date}"
        url += f"&limit={limit}"
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")
        
        data = response.json()
        response_model = CompanyNewsResponse(**data)
        company_news = response_model.news
        
        if not company_news:
            break  # Exit loop if no more data
            
        all_news.extend(company_news)  # Add results to our collection
        
        # Only continue pagination if we have a start_date and got a full page of results
        if not start_date or len(company_news) < limit:
            break
            
        # Update end_date to the oldest date from current batch for next iteration
        # This creates a "moving window" approach to pagination
        current_end_date = min(news.date for news in company_news).split('T')[0]
        
        # If we've reached or passed the start_date, we can stop paginating
        if current_end_date <= start_date:
            break

    if not all_news:
        return []  # Return empty list if no data available

    # Cache all retrieved news for future use
    _cache.set_company_news(ticker, [news.model_dump() for news in all_news])
    return all_news


def get_market_cap(
    ticker: str,
    end_date: str,
) -> float | None:
    """
    Get the most recent market capitalization for a company.
    
    Market cap is a key valuation metric representing the total dollar value
    of all outstanding shares (price per share × shares outstanding).
    
    Parameters:
    - ticker: Stock symbol
    - end_date: Only return market cap up to this date
    
    Returns:
    - Market cap value as a float, or None if not available
    """
    # Uses the get_financial_metrics function to retrieve data
    financial_metrics = get_financial_metrics(ticker, end_date)
    
    # Extract market cap from the most recent metrics (index 0)
    market_cap = financial_metrics[0].market_cap if financial_metrics else None
    
    if not market_cap:
        return None

    return market_cap


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """
    Convert a list of Price objects to a pandas DataFrame.
    
    This transforms the API data into a format suitable for financial analysis,
    with proper date indexing and numeric data types.
    
    Parameters:
    - prices: List of Price objects
    
    Returns:
    - Pandas DataFrame with price data indexed by date
    """
    # Convert list of Price objects to a DataFrame
    df = pd.DataFrame([p.model_dump() for p in prices])
    
    # Convert 'time' column to datetime and set as index
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    
    # Ensure numeric columns have proper data types
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Sort by date (ascending)
    df.sort_index(inplace=True)
    return df


def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Convenience function to get price data as a DataFrame.
    
    This combines the get_prices and prices_to_df functions into a single call.
    
    Parameters:
    - ticker: Stock symbol
    - start_date: Beginning of date range in ISO format (YYYY-MM-DD)
    - end_date: End of date range in ISO format (YYYY-MM-DD)
    
    Returns:
    - Pandas DataFrame with OHLCV data indexed by date
    """
    # Get raw price data
    prices = get_prices(ticker, start_date, end_date)
    
    # Convert to DataFrame
    return prices_to_df(prices)