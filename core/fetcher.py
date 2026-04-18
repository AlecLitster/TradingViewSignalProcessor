"""
fetcher.py
----------
Loads the watchlist and fetches raw technical analysis
from TradingView for all tickers and multiple timeframes.
Includes retry logic and delay between calls to avoid rate limiting.
"""

import os
import time
from tradingview_ta import get_multiple_analysis
from config.settings import (
    WATCHLIST_FILE,
    SCREENER,
    DEFAULT_EXCHANGE,
    EXCHANGE_MAP,
    TIMEFRAMES,
)

RETRY_ATTEMPTS = 3       # number of retries on failure
RETRY_DELAY    = 3       # seconds between retries
CALL_DELAY     = 2       # seconds between each timeframe API call


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


def fetch_timeframe(symbols: list, interval, label: str) -> dict:
    """
    Fetch one timeframe with retry logic.
    Returns the raw analyses dict or empty dict on failure.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            analyses = get_multiple_analysis(
                screener=SCREENER,
                interval=interval,
                symbols=symbols,
            )
            return analyses
        except Exception as e:
            print(f"[WARN] {label} fetch attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}")
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY)

    print(f"[ERROR] Could not fetch {label} data after {RETRY_ATTEMPTS} attempts -- skipping.")
    return {}


def fetch_raw_analysis(tickers: list) -> dict:
    """
    Fetch TradingView analysis for all tickers across all configured timeframes.
    Returns a dict: { ticker: { interval_label: analysis_object } }
    """
    if not tickers:
        return {}

    results = {ticker: {} for ticker in tickers}
    symbols = [build_symbol(t) for t in tickers]

    for label, interval in TIMEFRAMES.items():
        print(f"  Fetching {label} data...", end=" ", flush=True)

        analyses = fetch_timeframe(symbols, interval, label)

        # TEMP DEBUG
        if label == "daily":
            print(f"\nDEBUG daily keys returned: {list(analyses.keys())}")
            for ticker in tickers:
                exchange = EXCHANGE_MAP.get(ticker, DEFAULT_EXCHANGE)
                key = f"{exchange}:{ticker}"
                print(f"DEBUG looking for '{key}' -> found: {analyses.get(key) is not None}")

        for ticker in tickers:
            exchange = EXCHANGE_MAP.get(ticker, DEFAULT_EXCHANGE)
            key      = f"{exchange}:{ticker}"
            results[ticker][label] = analyses.get(key)

        ok_count = sum(1 for t in tickers if results[t][label] is not None)
        print(f"{ok_count}/{len(tickers)} tickers OK")

        # Delay between timeframe calls to avoid rate limiting
        time.sleep(CALL_DELAY)

    return results
