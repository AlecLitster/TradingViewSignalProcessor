"""
claude_interpreter.py
---------------------
Stage 3 of the pipeline: reads the analyzed signal results,
sends them to the Claude API, and returns an intelligent
BUY / SELL / HOLD interpretation with reasoning, confidence,
key risks, and an actionable note for each ticker.

Pipeline:
  Stage 1 -- fetcher.py             : fetch raw TradingView data
  Stage 2 -- analyzer.py            : process into structured signals
           -- reporter.py           : write signals_log.txt
  Stage 3 -- claude_interpreter.py  : AI interpretation & reasoning
                                    : write signals_interpreted.txt
                                    : write signals_interpreted.json
"""

import os
import json
import requests
from datetime import datetime

from config.settings import (
    LOG_DIR,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    CLAUDE_MAX_TOKENS,
    TIMEFRAME_WEIGHTS,
)

INTERPRETED_LOG_FILE  = os.path.join(LOG_DIR, "signals_interpreted.txt")
INTERPRETED_JSON_FILE = os.path.join(LOG_DIR, "signals_interpreted.json")

LINE_WIDE   = "=" * 80
LINE_NARROW = "-" * 80
LINE_MED    = "-" * 40


# =============================================================================
# Helpers
# =============================================================================

def _fv(value, fmt="{:.4f}", fallback="N/A"):
    """Safely format a numeric value -- matches reporter.py convention."""
    if value is None:
        return fallback
    try:
        return fmt.format(value)
    except (ValueError, TypeError):
        return fallback


# =============================================================================
# Prompt builder
# =============================================================================

def build_prompt(results: list) -> str:
    """
    Build a structured prompt from the analyzed signal results.
    Sends all indicator data -- moving averages, oscillators,
    trend indicators, pivot points and timeframe breakdown.
    """
    lines = []
    lines.append(
        "You are an expert technical analyst specialising in ETFs and commodity funds. "
        "Analyze the following trading signals for each ticker and provide a clear "
        "BUY / SELL / HOLD recommendation."
    )
    lines.append("")
    lines.append("For EACH ticker respond with ALL of these fields:")
    lines.append("  SIGNAL     : BUY, SELL, or HOLD")
    lines.append("  CONFIDENCE : Low / Medium / High / Very High")
    lines.append("  REASONING  : 2-4 sentences covering the key drivers")
    lines.append("  KEY_RISKS  : 1-2 sentences on what could invalidate this signal")
    lines.append("  ACTION     : One specific actionable note (entry point, stop loss, or wait condition)")
    lines.append("")
    lines.append("Analytical guidelines:")
    lines.append("  - Timeframe alignment: signals consistent across daily/weekly/monthly carry more weight")
    lines.append("  - Oscillator divergence vs moving average trend direction matters")
    lines.append("  - Pivot point S1/R1 levels relative to current price define near-term risk/reward")
    lines.append("  - RSI > 70 = overbought caution, RSI < 30 = oversold opportunity")
    lines.append("  - ADX > 25 confirms a trend is in force; ADX < 20 = weak/ranging")
    lines.append("  - MACD above signal line = bullish momentum; below = bearish")
    lines.append("  - These tickers are correlated precious metals / commodity ETFs:")
    lines.append("    SLV (silver), GLD (gold), GDX (gold miners), COMB (commodities),")
    lines.append("    URA (uranium), FXE (euro), AIQ (AI ETF), BOTZ (robotics ETF)")
    lines.append("  - When multiple correlated tickers align, note the sector-wide signal")
    lines.append("")
    lines.append(
        "Respond ONLY with a valid JSON array -- no preamble, no markdown fences, "
        "no explanation outside the JSON."
    )
    lines.append("Required format:")
    lines.append(
        '[{"ticker":"X","signal":"BUY","confidence":"High",'
        '"reasoning":"...","key_risks":"...","action":"..."}]'
    )
    lines.append("")
    lines.append("SIGNAL DATA")
    lines.append("=" * 60)

    for r in results:
        ticker  = r.get("ticker", "N/A")
        signal  = r.get("signal", "N/A")
        score   = r.get("weighted_score", 0.0)
        price   = r.get("price")
        buy_ct  = r.get("buy", 0)
        sell_ct = r.get("sell", 0)
        neut_ct = r.get("neutral", 0)

        lines.append(f"\nTICKER         : {ticker}")
        lines.append(f"CURRENT PRICE  : {_fv(price, '${:.4f}')}")
        lines.append(f"WEIGHTED SCORE : {score:+.4f}")
        lines.append(f"CURRENT SIGNAL : {signal}")
        lines.append(f"INDICATOR VOTES: {buy_ct} BUY / {sell_ct} SELL / {neut_ct} NEUTRAL")

        # Timeframe breakdown
        tf = r.get("per_timeframe", {})
        if tf:
            lines.append("TIMEFRAMES:")
            for label, rec in tf.items():
                w = TIMEFRAME_WEIGHTS.get(label, 0)
                lines.append(f"  {label:<10} {rec:<22} (weight {w:.0%})")

        # Moving averages summary
        mas = r.get("moving_avgs", {})
        if mas:
            ma_buy  = sum(1 for v in mas.values() if v.get("signal") == "BUY")
            ma_sell = sum(1 for v in mas.values() if v.get("signal") == "SELL")
            lines.append(f"MOVING AVERAGES: {ma_buy} BUY / {ma_sell} SELL out of {len(mas)}")
            for name, data in mas.items():
                lines.append(
                    f"  {name:<16} {_fv(data.get('value'), '{:.4f}'):<12} [{data.get('signal','N/A')}]"
                )

        # Oscillators
        oscs = r.get("oscillators", {})
        if oscs:
            lines.append("OSCILLATORS:")
            for name, data in oscs.items():
                lines.append(
                    f"  {name:<16} {_fv(data.get('value'), '{:.4f}'):<12} [{data.get('signal','N/A')}]"
                )

        # Trend indicators
        trend = r.get("trend", {})
        if trend:
            lines.append("TREND INDICATORS:")
            for name, data in trend.items():
                lines.append(
                    f"  {name:<16} {_fv(data.get('value'), '{:.4f}'):<12} [{data.get('signal','N/A')}]"
                )

        # Pivot points
        pivots = r.get("pivots", {})
        if pivots:
            lines.append("PIVOT POINTS (PP / S1 / R1):")
            for ptype, vals in pivots.items():
                pp = _fv(vals.get("PP"), "{:.2f}")
                s1 = _fv(vals.get("S1"), "{:.2f}")
                s2 = _fv(vals.get("S2"), "{:.2f}")
                r1 = _fv(vals.get("R1"), "{:.2f}")
                r2 = _fv(vals.get("R2"), "{:.2f}")
                lines.append(
                    f"  {ptype:<12} PP={pp}  S1={s1}  S2={s2}  R1={r1}  R2={r2}"
                )

        lines.append("-" * 40)

    return "\n".join(lines)


# =============================================================================
# Claude API call
# =============================================================================

def call_claude_api(prompt: str) -> list:
    """
    Send the prompt to the Claude API and return parsed JSON interpretations.
    Returns an empty list on failure.
    """
    if not CLAUDE_API_KEY:
        print("[ERROR] CLAUDE_API_KEY not set. Add it to your .env file.")
        return []

    headers = {
        "Content-Type":      "application/json",
        "x-api-key":         CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model":      CLAUDE_MODEL,
        "max_tokens": CLAUDE_MAX_TOKENS,
        "messages":   [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("content", [])
        text = "".join(
            block.get("text", "")
            for block in content
            if block.get("type") == "text"
        ).strip()

        # Strip markdown fences if present
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except requests.exceptions.Timeout:
        print("[ERROR] Claude API request timed out.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Claude API request failed: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Could not parse Claude response as JSON: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error calling Claude API: {e}")
        return []


# =============================================================================
# Output formatting -- matches reporter.py style exactly
# =============================================================================

def format_interpreted_report(interpretations: list, results: list) -> str:
    """
    Format Claude interpretations as a normalized text report.
    Follows the same LINE_WIDE / LINE_NARROW style as reporter.py.
    """
    now      = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    result_map = {r["ticker"]: r for r in results}
    lines      = []

    lines += [
        "",
        LINE_WIDE,
        "STAGE 3 -- CLAUDE AI SIGNAL INTERPRETATION",
        f"Date         : {date_str}",
        f"Time         : {time_str}",
        f"Model        : {CLAUDE_MODEL}",
        f"Tickers      : {', '.join(r['ticker'] for r in results)}",
        LINE_WIDE,
    ]

    # Summary table
    lines += [
        "",
        "SIGNAL SUMMARY",
        LINE_NARROW,
        f"  {'TICKER':<8} {'SIGNAL':<8} {'CONFIDENCE':<14} {'SCORE':<12} {'PRICE'}",
        f"  {LINE_NARROW}",
    ]
    for interp in interpretations:
        ticker = interp.get("ticker", "N/A")
        signal = interp.get("signal", "N/A")
        conf   = interp.get("confidence", "N/A")
        r      = result_map.get(ticker, {})
        score  = r.get("weighted_score", 0.0)
        price  = r.get("price")
        lines.append(
            f"  {ticker:<8} {signal:<8} {conf:<14} "
            f"{score:+.4f}       {_fv(price, '${:.2f}')}"
        )

    # Per-ticker detailed interpretation
    for interp in interpretations:
        ticker = interp.get("ticker", "N/A")
        signal = interp.get("signal", "N/A")
        conf   = interp.get("confidence", "N/A")
        reason = interp.get("reasoning", "N/A")
        risks  = interp.get("key_risks", "N/A")
        action = interp.get("action", "N/A")
        r      = result_map.get(ticker, {})

        lines += [
            "",
            LINE_WIDE,
            f"TICKER         : {ticker}",
            f"SIGNAL         : {signal}",
            f"CONFIDENCE     : {conf}",
            f"WEIGHTED SCORE : {_fv(r.get('weighted_score'), '{:+.4f}')}",
            f"PRICE          : {_fv(r.get('price'), '${:.4f}')}",
            LINE_NARROW,
            "",
            f"REASONING  : {reason}",
            "",
            f"KEY RISKS  : {risks}",
            "",
            f"ACTION     : {action}",
        ]

    buy_count  = sum(1 for i in interpretations if i.get("signal") == "BUY")
    sell_count = sum(1 for i in interpretations if i.get("signal") == "SELL")
    hold_count = sum(1 for i in interpretations if i.get("signal") == "HOLD")

    lines += [
        "",
        LINE_WIDE,
        f"OVERALL SUMMARY : {buy_count} BUY  |  {sell_count} SELL  |  {hold_count} HOLD",
        LINE_WIDE,
        "END OF CLAUDE AI INTERPRETATION",
        LINE_WIDE,
        "",
    ]

    return "\n".join(lines)


# =============================================================================
# JSON persistence -- for Streamlit dashboard consumption
# =============================================================================

def save_interpreted_json(interpretations: list, results: list):
    """
    Append the latest interpretation to signals_interpreted.json.
    Keeps last 200 entries. Consumed by the Streamlit dashboard.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    entry = {
        "timestamp":       datetime.now().isoformat(),
        "interpretations": interpretations,
        "scores": {
            r["ticker"]: {
                "weighted_score": r.get("weighted_score", 0),
                "price":          r.get("price"),
                "signal":         r.get("signal"),
            }
            for r in results
        },
    }

    history = []
    if os.path.exists(INTERPRETED_JSON_FILE):
        try:
            with open(INTERPRETED_JSON_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    history.append(entry)
    history = history[-200:]

    with open(INTERPRETED_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# =============================================================================
# Console output -- matches reporter.py print_report style
# =============================================================================

def print_interpretations(interpretations: list):
    """Print Claude interpretations to the console (ASCII safe for Windows)."""
    if not interpretations:
        return

    lines = [
        "",
        LINE_WIDE,
        "  CLAUDE AI INTERPRETATION",
        LINE_WIDE,
    ]

    for interp in interpretations:
        ticker = interp.get("ticker", "N/A")
        signal = interp.get("signal", "N/A")
        conf   = interp.get("confidence", "N/A")
        reason = interp.get("reasoning", "")
        action = interp.get("action", "")
        lines += [
            f"\n  [{signal}] {ticker}  --  Confidence: {conf}",
            f"  {reason}",
            f"  >> {action}",
        ]

    lines += ["", LINE_WIDE, ""]
    output = "\n".join(lines)
    print(output.encode("ascii", errors="replace").decode("ascii"))


# =============================================================================
# Main entry point called from main.py
# =============================================================================

def interpret(results: list) -> list:
    """
    Main function called from main.py.
    Takes analyzed signal results, calls Claude API,
    writes both log files, and returns the interpretations list.
    """
    if not results:
        return []

    print(f"  Sending {len(results)} tickers to Claude AI...", end=" ", flush=True)

    prompt          = build_prompt(results)
    interpretations = call_claude_api(prompt)

    if not interpretations:
        print("FAILED")
        return []

    print(f"OK ({len(interpretations)} tickers interpreted)")

    # Write normalized text log
    os.makedirs(LOG_DIR, exist_ok=True)
    report = format_interpreted_report(interpretations, results)
    with open(INTERPRETED_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(report)

    # Write JSON for Streamlit dashboard
    save_interpreted_json(interpretations, results)

    return interpretations
