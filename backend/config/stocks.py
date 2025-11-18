"""
STOCK CONFIGURATION - Static list of 50 stocks we track
- Master list of symbols, names, and sectors
- Used for validation and filtering
- NO database calls - just a Python list
"""

AVAILABLE_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive"},
    {"symbol": "BRK.B", "name": "Berkshire Hathaway Inc.", "sector": "Financial"},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financial"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Defensive"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial"},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "Financial"},
    {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Defensive"},
    {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "sector": "Healthcare"},
    {"symbol": "HD", "name": "Home Depot Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "DIS", "name": "Walt Disney Co.", "sector": "Communication"},
    {"symbol": "BAC", "name": "Bank of America Corp.", "sector": "Financial"},
    {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication"},
    {"symbol": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy"},
    {"symbol": "COST", "name": "Costco Wholesale Corp.", "sector": "Consumer Defensive"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"symbol": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology"},
    {"symbol": "TMO", "name": "Thermo Fisher Scientific", "sector": "Healthcare"},
    {"symbol": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare"},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Technology"},
    {"symbol": "CVX", "name": "Chevron Corp.", "sector": "Energy"},
    {"symbol": "MRK", "name": "Merck & Co. Inc.", "sector": "Healthcare"},
    {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Technology"},
    {"symbol": "KO", "name": "Coca-Cola Co.", "sector": "Consumer Defensive"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer Defensive"},
    {"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
    {"symbol": "NKE", "name": "Nike Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "T", "name": "AT&T Inc.", "sector": "Communication"},
    {"symbol": "VZ", "name": "Verizon Communications", "sector": "Communication"},
    {"symbol": "CMCSA", "name": "Comcast Corporation", "sector": "Communication"},
    {"symbol": "MCD", "name": "McDonald's Corp.", "sector": "Consumer Cyclical"},
    {"symbol": "IBM", "name": "IBM Corp.", "sector": "Technology"},
    {"symbol": "GE", "name": "General Electric Co.", "sector": "Industrial"},
    {"symbol": "BA", "name": "Boeing Co.", "sector": "Industrial"},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "sector": "Industrial"},
    {"symbol": "GS", "name": "Goldman Sachs Group", "sector": "Financial"},
    {"symbol": "AXP", "name": "American Express Co.", "sector": "Financial"},
    {"symbol": "SBUX", "name": "Starbucks Corporation", "sector": "Consumer Cyclical"},
    {"symbol": "PYPL", "name": "PayPal Holdings Inc.", "sector": "Financial"},
    {"symbol": "QCOM", "name": "QUALCOMM Inc.", "sector": "Technology"},
    {"symbol": "TXN", "name": "Texas Instruments Inc.", "sector": "Technology"},
]


def get_all_stocks():
    """Returns all available stocks."""
    return AVAILABLE_STOCKS


def get_stock_by_symbol(symbol: str):
    """Get stock info by symbol."""
    return next((s for s in AVAILABLE_STOCKS if s["symbol"] == symbol.upper()), None)


def get_stocks_by_sector(sector: str):
    """Get all stocks in a specific sector."""
    return [s for s in AVAILABLE_STOCKS if s["sector"] == sector]


def get_all_sectors():
    """Get unique list of sectors."""
    return list(set(s["sector"] for s in AVAILABLE_STOCKS))


def is_valid_symbol(symbol: str):
    """Check if a symbol is in our available stocks."""
    return any(s["symbol"] == symbol.upper() for s in AVAILABLE_STOCKS)
