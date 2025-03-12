class Cache:
    """
    In-memory cache for API responses to reduce redundant API calls.
    
    This cache stores financial data by ticker symbol, enabling the system to:
    1. Reduce API usage and costs
    2. Improve performance by avoiding redundant network requests
    3. Work with previously fetched data even when offline
    
    The cache maintains separate dictionaries for different types of financial data,
    each indexed by ticker symbol.
    """

    def __init__(self):
        """
        Initialize the cache with empty dictionaries for each data type.
        
        Each cache dictionary uses ticker symbols as keys and lists of data items as values.
        Data is stored as dictionaries rather than Pydantic models to simplify serialization.
        """
        self._prices_cache: dict[str, list[dict[str, any]]] = {}           # Stock price data (OHLCV)
        self._financial_metrics_cache: dict[str, list[dict[str, any]]] = {} # Financial ratios and metrics
        self._line_items_cache: dict[str, list[dict[str, any]]] = {}        # Financial statement line items 
        self._insider_trades_cache: dict[str, list[dict[str, any]]] = {}    # Insider trading activity
        self._company_news_cache: dict[str, list[dict[str, any]]] = {}      # News articles and sentiment

    def _merge_data(self, existing: list[dict] | None, new_data: list[dict], key_field: str) -> list[dict]:
        """
        Merge existing and new data, avoiding duplicates based on a key field.
        
        This utility function ensures we don't store duplicate data when adding
        new items to the cache. It identifies duplicates using a specified key field
        (e.g., "time" for prices, "report_period" for financial metrics).
        
        Args:
            existing: Current data in the cache (if any)
            new_data: New data to be added to the cache
            key_field: Field name to use for identifying duplicates
            
        Returns:
            A merged list containing all unique items from both sources
        """
        # If there's no existing data, simply return the new data
        if not existing:
            return new_data
        
        # Create a set of existing keys for O(1) lookup efficiency
        # This is much faster than checking each new item against all existing items
        existing_keys = {item[key_field] for item in existing}
        
        # Start with a copy of existing data
        merged = existing.copy()
        
        # Add only items that don't already exist in the cache
        # This uses the set of keys for fast lookups
        merged.extend([item for item in new_data if item[key_field] not in existing_keys])
        
        return merged

    def get_prices(self, ticker: str) -> list[dict[str, any]] | None:
        """
        Get cached price data for a specific ticker if available.
        
        Args:
            ticker: Stock symbol to retrieve data for
            
        Returns:
            List of price data dictionaries or None if not in cache
        """
        return self._prices_cache.get(ticker)

    def set_prices(self, ticker: str, data: list[dict[str, any]]):
        """
        Add or update price data in the cache for a specific ticker.
        
        This merges new data with existing data, avoiding duplicates
        based on the 'time' field.
        
        Args:
            ticker: Stock symbol to store data for
            data: List of price data dictionaries to cache
        """
        self._prices_cache[ticker] = self._merge_data(
            self._prices_cache.get(ticker),
            data,
            key_field="time"  # Prices are uniquely identified by timestamp
        )

    def get_financial_metrics(self, ticker: str) -> list[dict[str, any]]:
        """
        Get cached financial metrics for a specific ticker if available.
        
        Args:
            ticker: Stock symbol to retrieve data for
            
        Returns:
            List of financial metrics dictionaries or None if not in cache
        """
        return self._financial_metrics_cache.get(ticker)

    def set_financial_metrics(self, ticker: str, data: list[dict[str, any]]):
        """
        Add or update financial metrics in the cache for a specific ticker.
        
        This merges new data with existing data, avoiding duplicates
        based on the 'report_period' field.
        
        Args:
            ticker: Stock symbol to store data for
            data: List of financial metrics dictionaries to cache
        """
        self._financial_metrics_cache[ticker] = self._merge_data(
            self._financial_metrics_cache.get(ticker),
            data,
            key_field="report_period"  # Financial metrics are unique by reporting period
        )

    def get_line_items(self, ticker: str) -> list[dict[str, any]] | None:
        """
        Get cached financial statement line items for a specific ticker if available.
        
        Args:
            ticker: Stock symbol to retrieve data for
            
        Returns:
            List of line item dictionaries or None if not in cache
        """
        return self._line_items_cache.get(ticker)

    def set_line_items(self, ticker: str, data: list[dict[str, any]]):
        """
        Add or update financial statement line items in the cache for a specific ticker.
        
        This merges new data with existing data, avoiding duplicates
        based on the 'report_period' field.
        
        Args:
            ticker: Stock symbol to store data for
            data: List of line item dictionaries to cache
        """
        self._line_items_cache[ticker] = self._merge_data(
            self._line_items_cache.get(ticker),
            data,
            key_field="report_period"  # Line items are unique by reporting period
        )

    def get_insider_trades(self, ticker: str) -> list[dict[str, any]] | None:
        """
        Get cached insider trades for a specific ticker if available.
        
        Args:
            ticker: Stock symbol to retrieve data for
            
        Returns:
            List of insider trade dictionaries or None if not in cache
        """
        return self._insider_trades_cache.get(ticker)

    def set_insider_trades(self, ticker: str, data: list[dict[str, any]]):
        """
        Add or update insider trades in the cache for a specific ticker.
        
        This merges new data with existing data, avoiding duplicates
        based on the 'filing_date' field.
        
        Args:
            ticker: Stock symbol to store data for
            data: List of insider trade dictionaries to cache
        """
        self._insider_trades_cache[ticker] = self._merge_data(
            self._insider_trades_cache.get(ticker),
            data,
            key_field="filing_date"  # Using filing_date as the unique identifier
            # Could also use transaction_date if preferred, but filing_date is always present
        )

    def get_company_news(self, ticker: str) -> list[dict[str, any]] | None:
        """
        Get cached company news for a specific ticker if available.
        
        Args:
            ticker: Stock symbol to retrieve data for
            
        Returns:
            List of company news dictionaries or None if not in cache
        """
        return self._company_news_cache.get(ticker)

    def set_company_news(self, ticker: str, data: list[dict[str, any]]):
        """
        Add or update company news in the cache for a specific ticker.
        
        This merges new data with existing data, avoiding duplicates
        based on the 'date' field.
        
        Args:
            ticker: Stock symbol to store data for
            data: List of company news dictionaries to cache
        """
        self._company_news_cache[ticker] = self._merge_data(
            self._company_news_cache.get(ticker),
            data,
            key_field="date"  # News articles are unique by publication date
        )


# Create a singleton global cache instance
# This ensures all parts of the application share the same cache
_cache = Cache()


def get_cache() -> Cache:
    """
    Get the global cache instance.
    
    This function provides access to the singleton cache instance,
    allowing different parts of the application to share the same cache.
    
    Returns:
        The global Cache instance
    """
    return _cache