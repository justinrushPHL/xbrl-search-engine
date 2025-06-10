# backend/src/sp500_list.py
"""
S&P 500 company list for analysis
You can update this list or load it from an external source
"""

SP500_LIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "UNH", "JNJ", "JPM", "V", "PG", "XOM", "HD", "CVX", "MA", "PFE",
    "ABBV", "BAC", "COST", "KO", "AVGO", "WMT", "PEP", "TMO", "MRK",
    "CSCO", "ACN", "LLY", "ABT", "CRM", "DHR", "TXN", "NFLX", "VZ",
    "ADBE", "CMCSA", "NKE", "INTC", "QCOM", "WFC", "AMD", "PM", "UPS",
    "RTX", "T", "AMGN", "SPGI", "LOW", "IBM", "CAT", "CVS", "SBUX",
    "GS", "HON", "NEE", "INTU", "AXP", "BKNG", "MDT", "BLK", "LMT",
    "DE", "GILD", "MU", "NOW", "BA", "SYK", "TJX", "AMAT", "ELV",
    "ADP", "ADI", "VRTX", "MDLZ", "C", "CI", "LRCX", "CB", "REGN",
    "MO", "ZTS", "PLD", "MMC", "SO", "SHW", "PYPL", "DUK", "ISRG",
    "TGT", "BSX", "AON", "FCX", "ITW", "EQIX", "APD", "CL", "CME",
    "USB", "PNC", "GE", "EMR", "NSC", "MMM", "FISV", "CSX", "TFC",
    "ICE", "MCO", "WM", "KLAC", "DG", "SNPS", "HUM", "F", "SLB"
]

# For testing, use a smaller subset
SP500_TEST_LIST = SP500_LIST[:20]