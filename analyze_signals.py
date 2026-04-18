#!/usr/bin/env python3
"""
analyze_signals.py
------------------
Standalone helper to inspect recent signal history and detect meaningful changes.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.reporter import load_signals_history
from config.settings import SIGNAL_SCORE_DELTA_THRESHOLD, SIGNAL_SCORE_WEAK_DELTA_THRESHOLD, SIGNAL_SCORE_STRONG_DELTA_THRESHOLD


def main(hours_back=24):
    history = load_signals_history()
    if not history:
        print("No signal history available. Run the analyzer at least once to generate history.")
        return

    cutoff = None
    try:
        from datetime import datetime, timedelta
        cutoff = datetime.now().timestamp() - (hours_back * 3600)
    except Exception:
        cutoff = None

    recent = {}
    for ts, data in history.items():
        try:
            timestamp = datetime.fromisoformat(ts).timestamp()
        except Exception:
            continue
        if cutoff is None or timestamp >= cutoff:
            recent[ts] = data

    if not recent:
        print(f"No entries found in the last {hours_back} hours.")
        return

    sorted_ts = sorted(recent.keys())
    first_ts = sorted_ts[0]
    last_ts = sorted_ts[-1]
    first_data = recent[first_ts]
    last_data = recent[last_ts]

    print("Recent Signal History Analysis")
    print("=" * 40)
    print(f"Window: last {hours_back} hours")
    print(f"Entries found: {len(recent)}")
    print(f"Start: {first_ts}")
    print(f"End:   {last_ts}")
    print()

    changes = []
    for ticker, current in last_data.items():
        previous = first_data.get(ticker)
        if not previous:
            continue

        signal_changed = current["signal"] != previous["signal"]
        score_delta = current["score"] - previous["score"]
        strong_change = abs(score_delta) >= SIGNAL_SCORE_STRONG_DELTA_THRESHOLD
        weak_change = abs(score_delta) >= SIGNAL_SCORE_WEAK_DELTA_THRESHOLD
        if signal_changed or strong_change or weak_change or abs(score_delta) >= SIGNAL_SCORE_DELTA_THRESHOLD:
            changes.append((ticker, previous, current, signal_changed, score_delta, weak_change, strong_change))

    if not changes:
        print("No significant changes detected.")
        return

    print("Significant changes detected:")
    for ticker, previous, current, signal_changed, score_delta, weak_change, strong_change in changes:
        change_str = []
        if signal_changed:
            change_str.append(f"signal {previous['signal']} -> {current['signal']}")
        if strong_change:
            change_str.append(f"strong swing {score_delta:+.3f}")
        elif weak_change:
            change_str.append(f"weak swing {score_delta:+.3f}")
        elif abs(score_delta) >= SIGNAL_SCORE_DELTA_THRESHOLD:
            change_str.append(f"score swing {score_delta:+.3f}")
        print(f" - {ticker}: {', '.join(change_str)}")


if __name__ == "__main__":
    main()
