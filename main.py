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
from datetime import datetime
import pytz

from config.settings import INTERVAL_MINUTES
from core.fetcher    import load_watchlist, fetch_raw_analysis
from core.analyzer   import analyze
from core.reporter   import print_report, log_report, print_startup, detect_signal_changes


def is_market_open():
    """Check if the US stock market is currently open (9:30 AM - 4:00 PM ET, Mon-Fri)."""
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Market hours: 9:30 AM to 4:00 PM ET
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def run_analysis():
    """Single analysis cycle -- fetch, analyze, report."""
    if not is_market_open():
        return
    
    tickers = load_watchlist()
    if not tickers:
        return

    raw_analyses = fetch_raw_analysis(tickers)
    results      = analyze(tickers, raw_analyses)

    print_report(results)
    log_report(results)

    changes = detect_signal_changes(results)
    if changes["significant_changes"]:
        print("\n🚨 SIGNIFICANT SIGNAL CHANGES DETECTED")
        print(f"   {changes['message']}")
        for change in changes["significant_changes"]:
            labels = []
            if change["signal_changed"]:
                labels.append("signal change")
            if change.get("swing_label"):
                labels.append(change["swing_label"])
            else:
                if change["strong_score_change"]:
                    labels.append("strong swing")
                elif change["weak_score_change"]:
                    labels.append("weak swing")
                elif change["significant_score_change"]:
                    labels.append("score swing")
            change_label = ", ".join(labels) if labels else "change"
            print(
                f"   {change['ticker']}: {change['current_signal']} "
                f"(score: {change['current_score']:+.3f}, "
                f"delta: {change['score_change']:+.3f}, {change_label})"
            )
        print()


def main():
    tickers = load_watchlist()
    if not tickers:
        print("[ERROR] No tickers found. Add symbols to data/WatchList.txt and restart.")
        return

    print_startup(tickers)
    
    # Always run initial analysis on startup, regardless of market hours
    # Subsequent scheduled runs will still respect market hours
    run_analysis()

    schedule.every(INTERVAL_MINUTES).minutes.do(run_analysis)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
