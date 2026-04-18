"""
fetcher.py
----------
Loads the watchlist and fetches raw technical analysis
from TradingView for all tickers and multiple timeframes.
"""

import os
from tradingview_ta import TA_Handler, Interval, get_multiple_analysis
from config.settings import (
    WATCHLIST_FILE,
    SCREENER,
    DEFAULT_EXCHANGE,
    EXCHANGE_MAP,
    ANALYSIS_INTERVAL,
    TIMEFRAMES,
)


def load_watchlist() -> list:
    """Read tickers from WatchList.txt, one per line."""
    if not os.path.exists(WATCHLIST_FILE):
        print(f"[ERROR] Watchlist file not found: {WATCHLIST_FILE}")
        return []

    with open(WATCHLIST_FILE, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    if not tickers:
        print("[WARN] Watchlist is empty. Add tickers to data/WatchList.txt.")

    return tickers


def build_symbol(ticker: str) -> str:
    """Return the 'EXCHANGE:TICKER' string TradingView expects."""
    exchange = EXCHANGE_MAP.get(ticker, DEFAULT_EXCHANGE)
    return f"{exchange}:{ticker}"


def fetch_raw_analysis(tickers: list) -> dict:
    """
    Fetch TradingView analysis for all tickers across all configured timeframes.
    Returns a dict: { ticker: { interval_label: analysis_object } }
    """
    if not tickers:
        return {}

    results = {ticker: {} for ticker in tickers}

    for label, interval in TIMEFRAMES.items():
        symbols = [build_symbol(t) for t in tickers]
        try:
            analyses = get_multiple_analysis(
                screener=SCREENER,
                interval=interval,
                symbols=symbols,
            )
            for ticker in tickers:
                exchange = EXCHANGE_MAP.get(ticker, DEFAULT_EXCHANGE)
                key = f"{exchange}:{ticker}"
                results[ticker][label] = analyses.get(key)

        except Exception as e:
            print(f"[ERROR] Could not fetch {label} data: {e}")
            for ticker in tickers:
                results[ticker][label] = None

    return results
