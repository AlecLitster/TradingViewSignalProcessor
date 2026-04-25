"""
reporter.py
-----------
Handles console output and normalized log file writing
with full indicator breakdown per ticker.
"""

import gzip
import json
import os
import shutil
import csv
from datetime import datetime
from config.settings import (
    LOG_FILE,
    SIGNAL_HISTORY_FILE,
    SIGNAL_HISTORY_WINDOW,
    SIGNAL_SCORE_DELTA_THRESHOLD,
    SIGNAL_SCORE_WEAK_DELTA_THRESHOLD,
    SIGNAL_SCORE_STRONG_DELTA_THRESHOLD,
    SIGNAL_MIN_HISTORY_ENTRIES,
    SIGNAL_ICONS,
    INTERVAL_MINUTES,
    TIMEFRAME_WEIGHTS,
    LOG_DIR,
)

LINE_WIDE   = "=" * 80
LINE_NARROW = "-" * 80
LINE_MED    = "-" * 40

# -- Log rotation -------------------------------------------------------------

LOG_MAX_BYTES    = 5 * 1024 * 1024   # rotate at 5 MB
LOG_BACKUP_COUNT = 5                  # keep .1.gz .. .5.gz


def rotate_log(path: str) -> None:
    """
    Rotate 'path' if it exceeds LOG_MAX_BYTES.
    Keeps LOG_BACKUP_COUNT compressed backups (.1.gz is newest).
    Shifts existing backups up by one, dropping the oldest if full.
    """
    if not os.path.exists(path) or os.path.getsize(path) < LOG_MAX_BYTES:
        return

    # Drop the oldest backup if we're already at the limit
    oldest = f"{path}.{LOG_BACKUP_COUNT}.gz"
    if os.path.exists(oldest):
        os.remove(oldest)

    # Shift .4.gz -> .5.gz, .3.gz -> .4.gz, ...
    for n in range(LOG_BACKUP_COUNT - 1, 0, -1):
        src = f"{path}.{n}.gz"
        dst = f"{path}.{n + 1}.gz"
        if os.path.exists(src):
            shutil.move(src, dst)

    # Compress the current log into .1.gz and start fresh
    with open(path, "rb") as f_in, gzip.open(f"{path}.1.gz", "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    open(path, "w").close()   # truncate to zero bytes


# -----------------------------------------------------------------------------


def _fv(value, fmt="{:.4f}", fallback="N/A"):
    """Safely format a numeric value."""
    if value is None:
        return fallback
    try:
        return fmt.format(value)
    except (ValueError, TypeError):
        return fallback


def load_signals_history():
    """Load historical signals from JSON file."""
    if not os.path.exists(SIGNAL_HISTORY_FILE):
        return {}
    try:
        with open(SIGNAL_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_signals_history(signals_data):
    """Save current signals to JSON history file."""
    os.makedirs(os.path.dirname(SIGNAL_HISTORY_FILE), exist_ok=True)
    history = load_signals_history()
    timestamp = datetime.now().isoformat()
    history[timestamp] = signals_data

    if len(history) > 100:
        sorted_timestamps = sorted(history.keys())
        history = {ts: history[ts] for ts in sorted_timestamps[-100:]}

    with open(SIGNAL_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    # Save to CSV files per ticker
    for ticker, data in signals_data.items():
        csv_file = os.path.join(LOG_DIR, f"{ticker}.csv")
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'signal', 'score', 'price', 'buy', 'sell', 'neutral'])
            writer.writerow([
                timestamp,
                data['signal'],
                data['score'],
                data.get('price', ''),
                data.get('buy', 0),
                data.get('sell', 0),
                data.get('neutral', 0)
            ])


def detect_signal_changes(current_results, history_window=SIGNAL_HISTORY_WINDOW):
    """Detect significant changes in signals compared to recent history."""
    history = load_signals_history()
    recent_timestamps = sorted(history.keys())[-history_window:]
    if len(recent_timestamps) < SIGNAL_MIN_HISTORY_ENTRIES:
        return {"significant_changes": [], "message": "Not enough history to compare."}

    changes = []
    for result in current_results:
        ticker = result['ticker']
        current_signal = result['signal']
        current_score = result.get('weighted_score', 0)

        historical_scores = []
        historical_signals = []
        for ts in recent_timestamps:
            entry = history.get(ts, {})
            ticker_data = entry.get(ticker)
            if ticker_data:
                historical_scores.append(ticker_data.get('score', 0))
                historical_signals.append(ticker_data.get('signal'))

        if len(historical_scores) < SIGNAL_MIN_HISTORY_ENTRIES:
            continue

        avg_score = sum(historical_scores) / len(historical_scores)
        score_change = current_score - avg_score
        strong_score_change = abs(score_change) >= SIGNAL_SCORE_STRONG_DELTA_THRESHOLD
        weak_score_change = abs(score_change) >= SIGNAL_SCORE_WEAK_DELTA_THRESHOLD
        significant_score_change = abs(score_change) >= SIGNAL_SCORE_DELTA_THRESHOLD
        signal_changed = len(historical_signals) >= 1 and current_signal != historical_signals[-1]

        swing_label = None
        if strong_score_change:
            swing_label = "strong swing"
        elif weak_score_change:
            swing_label = "weak swing"
        elif significant_score_change:
            swing_label = "score swing"

        if signal_changed and swing_label is None:
            swing_label = "signal change"

        if signal_changed or significant_score_change:
            changes.append({
                "ticker": ticker,
                "current_signal": current_signal,
                "current_score": current_score,
                "previous_signals": historical_signals[-3:],
                "average_score": avg_score,
                "score_change": score_change,
                "signal_changed": signal_changed,
                "significant_score_change": significant_score_change,
                "weak_score_change": weak_score_change,
                "strong_score_change": strong_score_change,
                "swing_label": swing_label,
            })

    return {"significant_changes": changes, "message": f"Found {len(changes)} significant changes."}


def format_console_row(result):
    """Format one ticker for console output."""
    icon   = SIGNAL_ICONS.get(result["signal"], "[???]")
    ticker = result["ticker"]
    signal = result["signal"]
    price  = _fv(result["price"], "${:.2f}")
    score  = _fv(result["weighted_score"], "{:+.4f}")
    reason = result["reason"]
    return f"  {icon} {ticker:<6} -> {signal:<5} | Price: {price:<10} Score: {score:<8} | {reason}"


def format_console_report(results):
    """Assemble a console report block."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["", LINE_WIDE, f"  Watchlist Signals  |  {timestamp}", LINE_WIDE]
    for result in results:
        lines.append(format_console_row(result))
    lines += [LINE_WIDE, f"  Next check in {INTERVAL_MINUTES} minutes.", ""]
    return "\n".join(lines)


def format_log_report(results):
    """Assemble a full normalized log report with all indicators."""
    now      = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    lines    = []

    lines += [
        "",
        LINE_WIDE,
        "WATCHLIST SIGNAL REPORT",
        f"Date         : {date_str}",
        f"Time         : {time_str}",
        f"Tickers      : {', '.join(r['ticker'] for r in results)}",
        f"Poll Interval: Every {INTERVAL_MINUTES} minutes",
        LINE_WIDE,
    ]

    # Summary table
    change_summary = detect_signal_changes(results)
    swing_labels = {change['ticker']: change.get('swing_label', 'N/A') for change in change_summary['significant_changes']}

    lines += [
        "SIGNAL SUMMARY",
        LINE_NARROW,
        f"{'TICKER':<8} {'SIGNAL':<8} {'SCORE':<10} {'PRICE':<14} {'BUY':>4} {'SELL':>5} {'NEUT':>5} {'SWING':<18}",
        LINE_NARROW,
    ]
    for r in results:
        lines.append(
            f"{r['ticker']:<8} {r['signal']:<8} {_fv(r['weighted_score'], '{:+.4f}'):<10} "
            f"{_fv(r['price'], '${:.2f}'):<14} {r.get('buy',0):>4} {r.get('sell',0):>5} {r.get('neutral',0):>5} "
            f"{swing_labels.get(r['ticker'], 'N/A'):<18}"
        )
    lines += ["", "SWING SUMMARY", LINE_NARROW]
    if change_summary["significant_changes"]:
        lines.append(f"{'TICKER':<8} {'SIGNAL':<8} {'DELTA':<10} {'LABEL':<14}")
        lines.append(LINE_NARROW)
        for change in change_summary["significant_changes"]:
            lines.append(
                f"{change['ticker']:<8} {change['current_signal']:<8} "
                f"{change['score_change']:+.3f}     {change.get('swing_label', 'N/A'):<14}"
            )
    else:
        lines.append("No significant swings or signal changes detected in this run.")

    # Per-ticker detailed breakdown
    for r in results:
        lines += [
            "",
            LINE_WIDE,
            f"TICKER: {r['ticker']}  |  SIGNAL: {r['signal']}  |  WEIGHTED SCORE: {_fv(r['weighted_score'], '{:+.4f}')}",
            f"PRICE : {_fv(r['price'], '${:.4f}')}",
            LINE_NARROW,
        ]

        # Timeframe signals
        lines += ["", "TIMEFRAME SIGNALS", LINE_MED]
        weights = TIMEFRAME_WEIGHTS
        for tf, sig in r.get("per_timeframe", {}).items():
            w = weights.get(tf, 0)
            lines.append(f"  {tf:<10} {sig:<20} (weight: {w:.0%})")

        # Moving averages
        lines += ["", "MOVING AVERAGES", LINE_MED]
        mas = r.get("moving_avgs", {})
        if mas:
            lines.append(f"  {'NAME':<16} {'VALUE':<12} {'SIGNAL'}")
            for name, data in mas.items():
                lines.append(f"  {name:<16} {_fv(data['value'], '{:.4f}'):<12} {data['signal']}")
        else:
            lines.append("  No data available.")

        # Oscillators
        lines += ["", "OSCILLATORS", LINE_MED]
        oscs = r.get("oscillators", {})
        if oscs:
            lines.append(f"  {'NAME':<16} {'VALUE':<12} {'SIGNAL'}")
            for name, data in oscs.items():
                lines.append(f"  {name:<16} {_fv(data['value'], '{:.4f}'):<12} {data['signal']}")
        else:
            lines.append("  No data available.")

        # Trend indicators
        lines += ["", "TREND INDICATORS", LINE_MED]
        trend = r.get("trend", {})
        if trend:
            lines.append(f"  {'NAME':<16} {'VALUE':<12} {'SIGNAL'}")
            for name, data in trend.items():
                lines.append(f"  {name:<16} {_fv(data['value'], '{:.4f}'):<12} {data['signal']}")
        else:
            lines.append("  No data available.")

        # Pivot points
        lines += ["", "PIVOT POINTS", LINE_MED]
        pivots = r.get("pivots", {})
        if pivots:
            lines.append(f"  {'TYPE':<12} {'S3':<10} {'S2':<10} {'S1':<10} {'PP':<10} {'R1':<10} {'R2':<10} {'R3'}")
            for ptype, vals in pivots.items():
                lines.append(
                    f"  {ptype:<12} "
                    f"{_fv(vals.get('S3'), '{:.2f}'):<10} "
                    f"{_fv(vals.get('S2'), '{:.2f}'):<10} "
                    f"{_fv(vals.get('S1'), '{:.2f}'):<10} "
                    f"{_fv(vals.get('PP'), '{:.2f}'):<10} "
                    f"{_fv(vals.get('R1'), '{:.2f}'):<10} "
                    f"{_fv(vals.get('R2'), '{:.2f}'):<10} "
                    f"{_fv(vals.get('R3'), '{:.2f}')}"
                )
        else:
            lines.append("  No data available.")

    # Final summary
    buy_count  = sum(1 for r in results if r["signal"] == "BUY")
    sell_count = sum(1 for r in results if r["signal"] == "SELL")
    hold_count = sum(1 for r in results if r["signal"] == "HOLD")

    lines += [
        "",
        LINE_WIDE,
        f"OVERALL SUMMARY : {buy_count} BUY  |  {sell_count} SELL  |  {hold_count} HOLD",
        LINE_WIDE,
        "END OF REPORT",
        LINE_WIDE,
        "",
    ]

    return "\n".join(lines)


def print_report(results):
    """Print the console report (ASCII safe for Windows)."""
    report = format_console_report(results)
    print(report.encode("ascii", errors="replace").decode("ascii"))


def log_report(results):
    """Append the full normalized report to the log file and save structured signal history."""
    if not LOG_FILE:
        return
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    rotate_log(LOG_FILE)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(format_log_report(results))

    signals_data = {}
    for result in results:
        signals_data[result['ticker']] = {
            "signal": result['signal'],
            "score": result.get('weighted_score', 0),
            "price": result.get('price'),
            "buy": result.get('buy', 0),
            "sell": result.get('sell', 0),
            "neutral": result.get('neutral', 0),
        }
    save_signals_history(signals_data)


def print_startup(tickers):
    """Print a startup banner."""
    print("\n" + LINE_WIDE)
    print("  Watchlist Analyzer")
    print(f"  Watching : {', '.join(tickers)}")
    print(f"  Polling  : every {INTERVAL_MINUTES} minutes")
    print(f"  Log file : {LOG_FILE}")
    print("  Press Ctrl+C to stop.")
    print(LINE_WIDE + "\n")
