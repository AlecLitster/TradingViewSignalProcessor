"""
analyzer.py
-----------
Converts raw multi-timeframe TradingView analysis into weighted
BUY / SELL / HOLD signals with full indicator breakdown.
"""

from config.settings import (
    SIGNAL_MAP,
    TIMEFRAME_WEIGHTS,
    BUY_THRESHOLD,
    SELL_THRESHOLD,
)


def score_recommendation(recommendation: str) -> float:
    """Convert a TradingView recommendation string to a numeric score."""
    return SIGNAL_MAP.get(recommendation.upper(), 0.0)


def compute_weighted_signal(timeframe_analyses: dict) -> tuple:
    """
    Compute a weighted signal score across all timeframes.
    Returns (signal, weighted_score, per_timeframe_signals).
    """
    weighted_score = 0.0
    per_timeframe  = {}

    for label, analysis in timeframe_analyses.items():
        weight = TIMEFRAME_WEIGHTS.get(label, 0.0)
        if analysis is None:
            per_timeframe[label] = "N/A"
            continue

        rec   = analysis.summary.get("RECOMMENDATION", "NEUTRAL")
        score = score_recommendation(rec)
        weighted_score += score * weight
        per_timeframe[label] = rec.replace("_", " ").title()

    if weighted_score >= BUY_THRESHOLD:
        signal = "BUY"
    elif weighted_score <= SELL_THRESHOLD:
        signal = "SELL"
    else:
        signal = "HOLD"

    return signal, round(weighted_score, 4), per_timeframe


def count_indicators_manually(indicators: dict) -> tuple:
    """Manually count BUY/SELL/NEUTRAL signals from indicators when summary is missing."""
    buy_count = 0
    sell_count = 0
    neutral_count = 0

    # Moving averages
    close = indicators.get("close")
    for period in [5, 10, 20, 50, 100, 200]:
        sma_key = f"SMA{period}"
        ema_key = f"EMA{period}"
        sma_val = indicators.get(sma_key)
        ema_val = indicators.get(ema_key)

        if sma_val is not None and close is not None:
            if close > sma_val:
                buy_count += 1
            else:
                sell_count += 1

        if ema_val is not None and close is not None:
            if close > ema_val:
                buy_count += 1
            else:
                sell_count += 1

    # Oscillators
    rsi = indicators.get("RSI")
    if rsi is not None:
        if rsi >= 55:
            buy_count += 1
        elif rsi <= 45:
            sell_count += 1
        else:
            neutral_count += 1

    stoch_k = indicators.get("Stoch.K")
    if stoch_k is not None:
        if stoch_k >= 80:
            sell_count += 1  # Overbought
        elif stoch_k <= 20:
            buy_count += 1   # Oversold
        else:
            neutral_count += 1

    cci = indicators.get("CCI20")
    if cci is not None:
        if cci > 100:
            buy_count += 1
        elif cci < -100:
            sell_count += 1
        else:
            neutral_count += 1

    williams = indicators.get("W.R")
    if williams is not None:
        if williams > -20:
            sell_count += 1  # Overbought
        elif williams < -80:
            buy_count += 1   # Oversold
        else:
            neutral_count += 1

    # Trend indicators
    macd = indicators.get("MACD.macd")
    macd_signal = indicators.get("MACD.signal")
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            buy_count += 1
        else:
            sell_count += 1

    adx = indicators.get("ADX")
    adx_pos = indicators.get("ADX+DI")
    adx_neg = indicators.get("ADX-DI")
    if adx is not None and adx_pos is not None and adx_neg is not None and adx > 25:
        if adx_pos > adx_neg:
            buy_count += 1
        else:
            sell_count += 1

    return buy_count, sell_count, neutral_count
    """Extract all MA values from the daily indicators."""
    mas = {}
    for period in [5, 10, 20, 50, 100, 200]:
        sma_key = f"SMA{period}"
        ema_key = f"EMA{period}"
        sma_val = indicators.get(sma_key)
        ema_val = indicators.get(ema_key)
        close   = indicators.get("close")

        if sma_val is not None and close is not None:
            mas[f"MA{period}_SMA"] = {
                "value":  round(sma_val, 4),
                "signal": "BUY" if close > sma_val else "SELL",
            }
        if ema_val is not None and close is not None:
            mas[f"MA{period}_EMA"] = {
                "value":  round(ema_val, 4),
                "signal": "BUY" if close > ema_val else "SELL",
            }
    return mas


def extract_oscillators(indicators: dict) -> dict:
    """Extract oscillator values and signals."""
    def safe(key, decimals=4):
        v = indicators.get(key)
        return round(v, decimals) if v is not None else None

    rsi        = safe("RSI")
    stoch_k    = safe("Stoch.K")
    stoch_d    = safe("Stoch.D")
    stochrsi_k = safe("Stoch.RSI.K")
    cci        = safe("CCI20")
    williams   = safe("W.R")
    roc        = safe("ROC")
    ult_osc    = safe("UO")

    def rsi_signal(v):
        if v is None: return "N/A"
        if v >= 70: return "OVERBOUGHT"
        if v <= 30: return "OVERSOLD"
        if v >= 55: return "BUY"
        if v <= 45: return "SELL"
        return "NEUTRAL"

    def stoch_signal(v):
        if v is None: return "N/A"
        if v >= 80: return "OVERBOUGHT"
        if v <= 20: return "OVERSOLD"
        return "NEUTRAL"

    def cci_signal(v):
        if v is None: return "N/A"
        if v > 100: return "BUY"
        if v < -100: return "SELL"
        return "NEUTRAL"

    def williams_signal(v):
        if v is None: return "N/A"
        if v > -20: return "OVERBOUGHT"
        if v < -80: return "OVERSOLD"
        return "NEUTRAL"

    def ult_signal(v):
        if v is None: return "N/A"
        if v > 70: return "BUY"
        if v < 30: return "SELL"
        return "NEUTRAL"

    return {
        "RSI_14":       {"value": rsi,        "signal": rsi_signal(rsi)},
        "STOCH_K":      {"value": stoch_k,    "signal": stoch_signal(stoch_k)},
        "STOCH_D":      {"value": stoch_d,    "signal": stoch_signal(stoch_d)},
        "STOCHRSI_K":   {"value": stochrsi_k, "signal": stoch_signal(stochrsi_k)},
        "CCI_20":       {"value": cci,        "signal": cci_signal(cci)},
        "WILLIAMS_R":   {"value": williams,   "signal": williams_signal(williams)},
        "ROC":          {"value": roc,        "signal": "BUY" if roc and roc > 0 else "SELL" if roc and roc < 0 else "NEUTRAL"},
        "ULTIMATE_OSC": {"value": ult_osc,    "signal": ult_signal(ult_osc)},
    }


def extract_trend(indicators: dict) -> dict:
    """Extract trend indicator values and signals."""
    def safe(key, decimals=4):
        v = indicators.get(key)
        return round(v, decimals) if v is not None else None

    macd        = safe("MACD.macd")
    macd_signal = safe("MACD.signal")
    adx         = safe("ADX")
    adx_pos     = safe("ADX+DI")
    adx_neg     = safe("ADX-DI")
    bull_bear   = safe("Bulls.Bears.Power") or safe("BullBear.Power")

    macd_sig = "N/A"
    if macd is not None and macd_signal is not None:
        macd_sig = "BUY" if macd > macd_signal else "SELL"

    adx_sig = "N/A"
    if adx is not None and adx_pos is not None and adx_neg is not None:
        if adx > 25:
            adx_sig = "BUY" if adx_pos > adx_neg else "SELL"
        else:
            adx_sig = "WEAK TREND"

    bb_sig = "N/A"
    if bull_bear is not None:
        bb_sig = "BUY" if bull_bear > 0 else "SELL"

    return {
        "MACD":           {"value": macd,      "signal": macd_sig},
        "MACD_SIGNAL":    {"value": macd_signal,"signal": macd_sig},
        "ADX":            {"value": adx,       "signal": adx_sig},
        "ADX_PLUS_DI":    {"value": adx_pos,   "signal": "N/A"},
        "ADX_MINUS_DI":   {"value": adx_neg,   "signal": "N/A"},
        "BULL_BEAR_POWER":{"value": bull_bear,  "signal": bb_sig},
    }


def extract_pivots(indicators: dict) -> dict:
    """Extract pivot point values."""
    def safe(key, decimals=4):
        v = indicators.get(key)
        return round(v, decimals) if v is not None else None

    return {
        "Classic": {
            "S1": safe("Pivot.M.Classic.S1"),
            "S2": safe("Pivot.M.Classic.S2"),
            "S3": safe("Pivot.M.Classic.S3"),
            "PP": safe("Pivot.M.Classic.Middle"),
            "R1": safe("Pivot.M.Classic.R1"),
            "R2": safe("Pivot.M.Classic.R2"),
            "R3": safe("Pivot.M.Classic.R3"),
        },
        "Fibonacci": {
            "S1": safe("Pivot.M.Fibonacci.S1"),
            "S2": safe("Pivot.M.Fibonacci.S2"),
            "S3": safe("Pivot.M.Fibonacci.S3"),
            "PP": safe("Pivot.M.Fibonacci.Middle"),
            "R1": safe("Pivot.M.Fibonacci.R1"),
            "R2": safe("Pivot.M.Fibonacci.R2"),
            "R3": safe("Pivot.M.Fibonacci.R3"),
        },
        "Camarilla": {
            "S1": safe("Pivot.M.Camarilla.S1"),
            "S2": safe("Pivot.M.Camarilla.S2"),
            "S3": safe("Pivot.M.Camarilla.S3"),
            "PP": safe("Pivot.M.Camarilla.Middle"),
            "R1": safe("Pivot.M.Camarilla.R1"),
            "R2": safe("Pivot.M.Camarilla.R2"),
            "R3": safe("Pivot.M.Camarilla.R3"),
        },
    }


def build_reason(signal: str, weighted_score: float, per_timeframe: dict) -> str:
    """Build a concise reason string."""
    bullish = sum(1 for v in per_timeframe.values() if "Buy" in v)
    bearish = sum(1 for v in per_timeframe.values() if "Sell" in v)
    total   = len(per_timeframe)
    return (
        f"Weighted score: {weighted_score:+.4f} | "
        f"{bullish}/{total} timeframes bullish, {bearish}/{total} bearish."
    )


def parse_result(ticker: str, timeframe_analyses: dict) -> dict:
    """Parse all timeframe analyses for one ticker into a full result dict."""
    signal, weighted_score, per_timeframe = compute_weighted_signal(timeframe_analyses)

    # Use daily analysis for detailed indicators
    daily = timeframe_analyses.get("daily")

    if daily is None:
        return {
            "ticker":       ticker,
            "signal":       "N/A",
            "reason":       "No daily data returned.",
            "weighted_score": 0.0,
            "per_timeframe": per_timeframe,
            "price":        None,
            "moving_avgs":  {},
            "oscillators":  {},
            "trend":        {},
            "pivots":       {},
            "buy":          0,
            "sell":         0,
            "neutral":      0,
        }

    indicators = daily.indicators
    summary    = daily.summary

    return {
        "ticker":         ticker,
        "signal":         signal,
        "reason":         build_reason(signal, weighted_score, per_timeframe),
        "weighted_score": weighted_score,
        "per_timeframe":  per_timeframe,
        "price":          indicators.get("close"),
        "moving_avgs":    extract_moving_averages(indicators),
        "oscillators":    extract_oscillators(indicators),
        "trend":          extract_trend(indicators),
        "pivots":         extract_pivots(indicators),
        "buy":            summary.get("BUY", 0),
        "sell":           summary.get("SELL", 0),
        "neutral":        summary.get("NEUTRAL", 0),
    }


def analyze(tickers: list, raw_analyses: dict) -> list:
    """Convert raw multi-timeframe analyses into full result dicts."""
    return [parse_result(ticker, raw_analyses.get(ticker, {})) for ticker in tickers]
