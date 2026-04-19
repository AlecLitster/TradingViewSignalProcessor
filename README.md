# 📈 Trading View Signal Processor
Automatically fetches TradingView technical analysis for your watchlist and provides intelligent **BUY / SELL / HOLD** signals with market-aware scheduling and change detection.

## ✨ Features

- **🕒 Market Hours Scheduling**: Only runs during US stock market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
- **📊 Signal Change Detection**: Tracks and alerts on significant signal changes with swing analysis
- **💾 Structured History**: JSON-based signal history for programmatic analysis
- **📋 Multiple Analysis Levels**: Strong, weak, and score swing detection
- **🔄 Real-time Monitoring**: Polls every 15 minutes during market hours
- **📝 Comprehensive Logging**: Both human-readable and machine-readable outputs

---

## 📁 Project Structure

```
trading_watchlist/
├── data/
│   └── WatchList.txt           ← add/remove tickers here
├── logs/
│   ├── tv_signals_log.txt      ← detailed human-readable logs
│   ├── tv_signals_history.json ← structured signal history
│   ├── tv_signals_ai_features.csv  ← ML-ready feature vectors
│   └── tv_signals_ai_features.json ← structured AI features
├── config/
│   └── settings.py             ← all configuration in one place
├── core/
│   ├── fetcher.py              ← TradingView data retrieval
│   ├── analyzer.py             ← BUY/SELL/HOLD decision logic
│   └── reporter.py             ← console & file output formatting
├── main.py                     ← main analyzer (run this)
├── analyze_signals.py          ← historical analysis tool
├── requirements.txt
└── README.md
```

---

## 🤖 AI/ML Features

The analyzer generates **machine learning-ready datasets** in addition to human-readable reports:

### **AI Features Output:**
- **`tv_signals_ai_features.csv`** - CSV format with flattened feature vectors
- **`tv_signals_ai_features.json`** - Structured JSON with complete feature sets

### **Feature Engineering:**
- **100+ technical indicators** flattened into numerical features
- **Multi-timeframe signals** (daily, weekly, monthly) as numeric scores
- **Moving averages, oscillators, trend indicators** with signal encodings
- **Pivot points** from multiple calculation methods
- **Target labels** (BUY/SELL/HOLD) for supervised learning

### **Use Cases:**
- Train ML models for automated trading
- Pattern recognition and signal prediction
- Feature importance analysis
- Backtesting trading strategies
- AI-powered market analysis

---

## 🤖 AI Interpreters

The system supports **multiple AI providers** for diverse analysis perspectives:

### **Supported Interpreters:**
- **Claude (Anthropic)** - Deep reasoning and market analysis
- **Copilot (GitHub)** - Code-aware technical analysis
- **GPT-4 (OpenAI)** - Broad market intelligence *(future)*
- **Gemini (Google)** - Alternative AI perspective *(future)*

### **AI Output Files:**
- **`tv_claude_interpretations.json`** - Claude's detailed analysis
- **`tv_claude_interpretations.txt`** - Human-readable Claude reports
- **`tv_copilot_interpretations.json`** - Copilot analysis *(when implemented)*
- Similar files for other interpreters

### **Configuration:**
Add API keys to your `.env` file:
```bash
CLAUDE_API_KEY=your_anthropic_key_here
COPILOT_API_KEY=your_github_key_here
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_google_key_here
```

### **Features:**
- **Independent Analysis**: Each AI provides unique insights
- **Fallback Support**: If one AI fails, others continue working
- **Structured Output**: JSON for programmatic use, text for human reading
- **Confidence Scoring**: Each interpretation includes confidence levels
- **Risk Assessment**: AI-identified risks and recommended actions

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** (Download from [python.org](https://python.org))

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your Watchlist
Edit `data/WatchList.txt` and add one ticker per line:
```
SLV
GLD
GDX
COMB
AIQ
BOTZ
```

### 4. Run the Analyzer
```bash
python main.py
```

The analyzer will:
- Run an initial analysis immediately (even outside market hours)
- Continue monitoring every 15 minutes during market hours
- Save all data to logs and detect significant changes

---

## 📊 Signal Analysis Features

### Swing Detection Levels
- **Strong Swing**: Score change ≥ 0.50 (major market moves)
- **Weak Swing**: Score change ≥ 0.35 (moderate changes)
- **Score Swing**: Score change ≥ 0.25 (notable changes)
- **Signal Change**: BUY ↔ SELL ↔ HOLD transitions

### Change Alerts
When significant changes are detected, you'll see alerts like:
```
🚨 SIGNIFICANT SIGNAL CHANGES DETECTED:
   Found 2 significant changes out of 6 tickers
   AIQ: BUY (score: +0.650, delta: +0.250, score swing)
   GDX: HOLD (score: +0.150, delta: -0.400, weak swing)
```

### Historical Analysis
Run the analysis tool to review recent changes:
```bash
python analyze_signals.py
```

---

## ⚙️ Configuration

All settings are in `config/settings.py`:

### Market Hours
```python
# US Stock Market Hours (Eastern Time)
# Monday-Friday, 9:30 AM - 4:00 PM ET
```

### Analysis Thresholds
```python
SIGNAL_SCORE_DELTA_THRESHOLD = 0.25      # Minimum change to track
SIGNAL_SCORE_WEAK_DELTA_THRESHOLD = 0.35 # Weak swing threshold
SIGNAL_SCORE_STRONG_DELTA_THRESHOLD = 0.50 # Strong swing threshold
```

### Scheduling
```python
INTERVAL_MINUTES = 15  # Check interval during market hours
```

---

## 📋 Usage Examples

### Basic Monitoring
```bash
python main.py
```
Starts the analyzer with market-aware scheduling.

### Historical Analysis
```bash
python analyze_signals.py
```
Shows significant changes over the last 24 hours.

### Custom Analysis Window
Modify `analyze_signals.py` to change the time window:
```python
main(hours_back=48)  # Analyze last 48 hours
```

---

## 📈 Signal Interpretation

### Overall Signal
- **BUY**: Weighted score ≥ 0.20
- **SELL**: Weighted score ≤ -0.20
- **HOLD**: -0.20 < score < 0.20

### Timeframe Weights
- Daily: 70% weight (most important)
- Weekly: 20% weight
- Monthly: 10% weight

### Indicator Breakdown
Each analysis includes:
- Moving averages (SMA/EMA for 5, 10, 20, 50, 100, 200 periods)
- Oscillators (RSI, Stochastic, CCI, Williams %R, etc.)
- Trend indicators (MACD, ADX, etc.)
- Pivot points (Classic, Fibonacci, Camarilla)

---

## 🔧 Troubleshooting

### No Data Issues
- Check internet connection
- Verify ticker symbols are correct
- Ensure TradingView API is accessible

### Market Hours
- Analyzer only runs during US market hours (9:30 AM - 4:00 PM ET)
- Initial run always executes regardless of time
- Use `analyze_signals.py` for historical analysis anytime

### Dependencies
```bash
pip install --upgrade -r requirements.txt
```

---

## 📝 License

This project is open source. Feel free to modify and distribute.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

*Built with TradingView TA API and Python schedule library*

---

## Configuration

All settings live in `config/settings.py`:

| Setting | Default | Description |
|---|---|---|
| `INTERVAL_MINUTES` | `15` | How often to poll TradingView |
| `SCREENER` | `america` | TradingView screener region |
| `DEFAULT_EXCHANGE` | `NYSE` | Default exchange for tickers |
| `EXCHANGE_MAP` | see file | Per-ticker exchange overrides |
| `ANALYSIS_INTERVAL` | `1 day` | Timeframe for signals |
| `LOG_FILE` | `logs/signals_log.txt` | Set to `None` to disable logging |

---

## Sample Output

```
────────────────────────────────────────────────────────────────────────────────
  Watchlist Signals  ·  2026-04-17 09:30:00
────────────────────────────────────────────────────────────────────────────────
  ▲ SLV    → BUY   | Price: $71.24    RSI: 55.94    MACD: 0.4400    | 9/17 indicators bullish — trend is up.
  ● GLD    → HOLD  | Price: $—        RSI: —         MACD: —         | Mixed signals — no clear direction.
  ▲ GDX    → BUY   | Price: $—        RSI: —         MACD: —         | 10/17 indicators bullish — trend is up.
  ● COMB   → HOLD  | Price: $—        RSI: —         MACD: —         | Mixed signals — no clear direction.
────────────────────────────────────────────────────────────────────────────────
  Next check in 15 minutes.
```

---

## Adding More Tickers

1. Add the ticker symbol to `data/WatchList.txt` (one per line)
2. If the ticker is **not on NYSE**, add it to `EXCHANGE_MAP` in `config/settings.py`
3. Restart `main.py`

## Notes

- Data is delayed ~15 minutes on a free TradingView account
- Daily signals are used by default — change `ANALYSIS_INTERVAL` in settings for shorter timeframes
- All signals are logged to `logs/signals_log.txt` for history tracking
- Press `Ctrl+C` to stop the service

The system will:
Check the current time in Eastern timezone
Only execute analysis cycles during market hours
Start running at market open if the script is launched during trading hours
Skip executions outside of market hours
