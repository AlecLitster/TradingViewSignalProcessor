"""
settings.py
-----------
Central configuration for the Watchlist Analyzer.
"""

import os
from tradingview_ta import Interval

# -- Paths --------------------------------------------------------------------

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHLIST_FILE = os.path.join(BASE_DIR, "data", "WatchList.txt")
LOG_FILE       = os.path.join(BASE_DIR, "logs", "signals_log.txt")
SIGNALS_JSON   = os.path.join(BASE_DIR, "logs", "signals_history.json")

# -- Polling ------------------------------------------------------------------

INTERVAL_MINUTES = 15

# -- Signal history tracking --------------------------------------------------

SIGNAL_HISTORY_FILE = os.path.join(BASE_DIR, "logs", "signals_history.json")
SIGNAL_HISTORY_WINDOW = 5
SIGNAL_SCORE_DELTA_THRESHOLD = 0.25
SIGNAL_SCORE_WEAK_DELTA_THRESHOLD = 0.35
SIGNAL_SCORE_STRONG_DELTA_THRESHOLD = 0.50
SIGNAL_MIN_HISTORY_ENTRIES = 2

# -- TradingView --------------------------------------------------------------

SCREENER         = "america"
DEFAULT_EXCHANGE = "NYSE"

# Per-ticker exchange overrides
EXCHANGE_MAP = {
    "AIQ":  "NASDAQ",   
    "BOTZ":  "NASDAQ",
    "COMB": "AMEX",
    "FXE":  "AMEX",
    "GDX":  "AMEX",
    "GLD":  "AMEX",
    "SLV":  "AMEX",
    "URA":  "AMEX",
}

# -- Timeframes to fetch (label -> Interval) ----------------------------------
# Weights are applied in analyzer.py — daily is weighted highest

TIMEFRAMES = {
    "daily":   Interval.INTERVAL_1_DAY,
    "weekly":  Interval.INTERVAL_1_WEEK,
    "monthly": Interval.INTERVAL_1_MONTH,
}

# Primary interval (used for detailed indicator extraction)
ANALYSIS_INTERVAL = Interval.INTERVAL_1_DAY

# -- Timeframe weights for final signal (must sum to 1.0) --------------------

TIMEFRAME_WEIGHTS = {
    "daily":   0.70,   # daily carries the most weight
    "weekly":  0.20,
    "monthly": 0.10,
}

# -- Signal mapping -----------------------------------------------------------

SIGNAL_MAP = {
    "STRONG_BUY":  1.0,
    "BUY":         0.5,
    "NEUTRAL":     0.0,
    "SELL":        -0.5,
    "STRONG_SELL": -1.0,
}

# Score thresholds for final BUY/SELL/HOLD decision
BUY_THRESHOLD  =  0.2   # weighted score above this -> BUY
SELL_THRESHOLD = -0.2   # weighted score below this -> SELL
                         # anything in between       -> HOLD

# -- Display ------------------------------------------------------------------

SIGNAL_ICONS = {
    "BUY":  "[BUY ]",
    "SELL": "[SELL]",
    "HOLD": "[HOLD]",
    "N/A":  "[N/A ]",
}
