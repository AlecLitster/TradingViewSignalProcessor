# Watchlist Analyzer

Automatically fetches TradingView technical analysis for your watchlist
every 15 minutes and outputs a clean **BUY / SELL / HOLD** signal for each ticker.

---

## Project Structure

```
trading_watchlist/
├── data/
│   └── WatchList.txt       ← add/remove tickers here
├── logs/
│   └── signals_log.txt     ← auto-generated signal history
├── config/
│   └── settings.py         ← all configuration in one place
├── core/
│   ├── fetcher.py          ← TradingView data retrieval
│   ├── analyzer.py         ← BUY/SELL/HOLD decision logic
│   └── reporter.py         ← console & file output formatting
├── main.py                 ← entry point — run this
└── requirements.txt
```

---

## Setup

**1. Install Python 3.10+**
Download from https://python.org

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Edit your watchlist**
Open `data/WatchList.txt` and add one ticker per line:
```
SLV
GLD
GDX
COMB
```

**4. Run**
```bash
python main.py
```

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
