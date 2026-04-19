"""
main.py
-------
Entry point for the Watchlist Analyzer.
Run this file to start the service:

    python main.py

Pipeline:
  Stage 1 -- fetcher.py            : fetch raw TradingView data
  Stage 2 -- analyzer.py           : process into structured signals
           -- reporter.py          : write signals_log.txt + history
  Stage 3 -- claude_interpreter.py : AI interpretation & reasoning
                                   : write signals_interpreted.txt
                                   : write signals_interpreted.json
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

# Load .env file (CLAUDE_API_KEY etc.) before any config imports
from dotenv import load_dotenv
load_dotenv()

import schedule
import time
from datetime import datetime
import pytz

from config.settings import INTERVAL_MINUTES, CLAUDE_ENABLED
from core.fetcher      import load_watchlist, fetch_raw_analysis
from core.analyzer     import analyze
from core.reporter     import (
    print_report,
    log_report,
    print_startup,
    detect_signal_changes,
)
from core.claude_interpreter import interpret, print_interpretations


def is_market_open():
    """Check if the US stock market is currently open (9:30 AM - 4:00 PM ET, Mon-Fri)."""
    eastern = pytz.timezone('US/Eastern')
    now     = datetime.now(eastern)

    if now.weekday() >= 5:  # Saturday or Sunday
        return False

    market_open  = now.replace(hour=9,  minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0,  second=0, microsecond=0)

    return market_open <= now <= market_close


def run_analysis():
    """Single analysis cycle -- fetch, analyze, report, interpret."""
    if not is_market_open():
        return

    tickers = load_watchlist()
    if not tickers:
        return

    # Stage 1 & 2: fetch and analyze
    raw_analyses = fetch_raw_analysis(tickers)
    results      = analyze(tickers, raw_analyses)

    # Stage 2 output: console + log file + signal history
    print_report(results)
    log_report(results)

    # Stage 3: Claude AI interpretation
    if CLAUDE_ENABLED:
        interpretations = interpret(results)
        print_interpretations(interpretations)

    # Signal change detection and alerts
    changes = detect_signal_changes(results)
    if changes["significant_changes"]:
        print("\n  SIGNIFICANT SIGNAL CHANGES DETECTED")
        print(f"  {changes['message']}")
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
                f"  {change['ticker']}: {change['current_signal']} "
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

    # Always run initial analysis on startup regardless of market hours
    run_analysis()

    # Then schedule every N minutes (respects market hours)
    schedule.every(INTERVAL_MINUTES).minutes.do(run_analysis)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
