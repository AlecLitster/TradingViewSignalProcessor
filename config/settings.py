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
LOG_FILE       = os.path.join(BASE_DIR, "logs", "tv_signals_log.txt")
SIGNALS_JSON   = os.path.join(BASE_DIR, "logs", "tv_signals_history.json")
LOG_DIR        = os.path.join(BASE_DIR, "logs")

# -- Polling ------------------------------------------------------------------

INTERVAL_MINUTES = 15

# -- Signal history tracking --------------------------------------------------

SIGNAL_HISTORY_FILE               = os.path.join(BASE_DIR, "logs", "signals_history.json")
SIGNAL_HISTORY_WINDOW             = 5
SIGNAL_SCORE_DELTA_THRESHOLD      = 0.25
SIGNAL_SCORE_WEAK_DELTA_THRESHOLD  = 0.35
SIGNAL_SCORE_STRONG_DELTA_THRESHOLD = 0.50
SIGNAL_MIN_HISTORY_ENTRIES        = 2

# -- TradingView --------------------------------------------------------------

SCREENER         = "america"
DEFAULT_EXCHANGE = "NYSE"

# Per-ticker exchange overrides
EXCHANGE_MAP = {
    "AIQ":   "NASDAQ",
    "BOTZ":  "NASDAQ",
    "COMB":  "AMEX",
    "FXE":   "AMEX",
    "GDX":   "AMEX",
    "GLD":   "AMEX",
    "SLV":   "AMEX",
    "URA":   "AMEX",
    "VCMDX": "NASDAQ",
}

# -- Timeframes to fetch (label -> Interval) ----------------------------------
# Weights are applied in analyzer.py -- daily is weighted highest

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

# -- AI Interpreters -------------------------------------------------------
# Multiple AI providers for diverse analysis perspectives
# Get API keys from respective providers and store in .env file
# The .env file is in .gitignore -- never commit API keys to GitHub

# Claude (Anthropic)
CLAUDE_API_KEY    = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_MODEL      = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 2000
CLAUDE_ENABLED    = bool(CLAUDE_API_KEY)

# GitHub Copilot (future implementation)
COPILOT_API_KEY   = os.environ.get("COPILOT_API_KEY", "")
COPILOT_MODEL     = "gpt-4"
COPILOT_ENABLED   = bool(COPILOT_API_KEY)

# OpenAI GPT-4 (future implementation)
OPENAI_API_KEY    = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL      = "gpt-4-turbo"
OPENAI_ENABLED    = bool(OPENAI_API_KEY)

# Google Gemini (future implementation)
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL      = "gemini-pro"
GEMINI_ENABLED    = bool(GEMINI_API_KEY)

# Global AI settings
AI_INTERPRETATION_ENABLED = True  # Master switch for all AI interpretations
AI_MAX_RETRIES            = 3     # Retry failed API calls
AI_TIMEOUT_SECONDS        = 30    # API call timeout

# Set to False to skip AI interpretation and save API costs
CLAUDE_ENABLED    = True
