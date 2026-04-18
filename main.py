"""
main.py
-------
Entry point for the Watchlist Analyzer.
Run this file to start the service:

    python main.py
"""

import sys
import os

# Force UTF-8 output on Windows to avoid encoding errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import schedule
import time

from config.settings import INTERVAL_MINUTES
from core.fetcher    import load_watchlist, fetch_raw_analysis
from core.analyzer   import analyze
from core.reporter   import print_report, log_report, print_startup


def run_analysis():
    """Single analysis cycle -- fetch, analyze, report."""
    tickers = load_watchlist()
    if not tickers:
        return

    raw_analyses = fetch_raw_analysis(tickers)
    results      = analyze(tickers, raw_analyses)

    print_report(results)
    log_report(results)


def main():
    tickers = load_watchlist()
    if not tickers:
        print("[ERROR] No tickers found. Add symbols to data/WatchList.txt and restart.")
        return

    print_startup(tickers)
    run_analysis()

    schedule.every(INTERVAL_MINUTES).minutes.do(run_analysis)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
