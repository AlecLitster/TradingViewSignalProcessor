"""
dashboard_generator.py
-----------------------
Drop this file into your trading signal project.
Call generate_dashboard(json_path) after your model writes its JSON output,
or pass a dict directly via generate_dashboard_from_dict(data, output_path).

Usage in your existing script:
    from dashboard_generator import generate_dashboard
    # After you write your JSON:
    generate_dashboard("signals_2026-04-21.json")
"""

import json
import os
import csv
from datetime import datetime
from pathlib import Path


def generate_dashboard(json_path: str) -> str:
    """
    Load a signal JSON file and save an HTML dashboard alongside it.
    Returns the path to the generated HTML file.
    """
    json_path = Path(json_path)
    with open(json_path, "r") as f:
        data = json.load(f)

    output_path = json_path.with_suffix(".html")
    return generate_dashboard_from_dict(data, str(output_path))


def generate_dashboard_from_dict(data: dict, output_path: str) -> str:
    """
    Accept the signal dict directly and write the HTML dashboard.
    Returns the path to the generated HTML file.

    Expected dict shape (your model's existing output):
    {
      "2026-04-21T23:17:30.983228": {
        "COMB": { "signal": "BUY", "score": 0.95, "price": 26.125,
                  "buy": 16, "sell": 1, "neutral": 9 },
        ...
      }
    }
    """
    # Extract timestamp + tickers from whatever shape the dict has
    timestamp, tickers = _parse_data(data)

    # Sort: buys first (by score desc), holds middle, then sells (by score asc)
    buys  = sorted([t for t in tickers if t["signal"] == "BUY"],
                   key=lambda x: x["score"], reverse=True)
    holds = sorted([t for t in tickers if t["signal"] == "HOLD"],
                   key=lambda x: x["score"], reverse=True)
    sells = sorted([t for t in tickers if t["signal"] == "SELL"],
                   key=lambda x: x["score"])

    html = _build_html(timestamp, buys, holds, sells)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[dashboard] Saved → {output_path}")
    return str(output_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_data(data: dict) -> tuple[str, list[dict]]:
    """Normalise the JSON into a flat list of ticker dicts.

    Supports two shapes:
      A) ai_features shape:
           { "timestamp": "...", "features": [ { "ticker": ..., "target_signal": ... }, ... ] }
      B) simple shape:
           { "2026-...": { "TICKER": { "signal": ..., "score": ... }, ... } }
    """
    if not data:
        return "Unknown", []

    # Shape A — ai_features JSON (your actual file)
    if "features" in data and isinstance(data["features"], list):
        timestamp = data.get("timestamp", datetime.now().isoformat())
        tickers = []
        for f in data["features"]:
            tickers.append({
                "ticker":  f.get("ticker", "?"),
                "signal":  f.get("target_signal", "NEUTRAL"),
                "score":   float(f.get("target_score", 0)),
                "price":   float(f.get("price", 0)),
                "buy":     int(f.get("buy_count", 0)),
                "sell":    int(f.get("sell_count", 0)),
                "neutral": int(f.get("neutral_count", 0)),
            })
        return timestamp, tickers

    # Shape B — simple timestamp-keyed dict
    first_key = next(iter(data))
    if isinstance(data[first_key], dict):
        raw_tickers = data[first_key]
        timestamp = first_key
    else:
        raw_tickers = data
        timestamp = datetime.now().isoformat()

    tickers = []
    for ticker, vals in raw_tickers.items():
        tickers.append({
            "ticker":  ticker,
            "signal":  vals.get("signal", "NEUTRAL"),
            "score":   float(vals.get("score", 0)),
            "price":   float(vals.get("price", 0)),
            "buy":     int(vals.get("buy", 0)),
            "sell":    int(vals.get("sell", 0)),
            "neutral": int(vals.get("neutral", 0)),
        })
    return timestamp, tickers


def _score_bar(score: float, is_buy: bool) -> str:
    """Return an inline HTML progress bar for the score."""
    pct = abs(score) * 100
    color = "#639922" if is_buy else "#E24B4A"
    return (
        f'<div style="flex:1;height:6px;background:#e5e5e5;border-radius:3px;overflow:hidden;">'
        f'<div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:3px;"></div>'
        f'</div>'
    )


def _card(t: dict, history: list, is_top: bool = False) -> str:
    """Render a single ticker card."""
    sig = t["signal"]
    is_buy  = sig == "BUY"
    is_hold = sig == "HOLD"

    if is_buy:
        top_border = "3px solid #3B6D11"
        featured   = "2px solid #3B6D11" if is_top else "0.5px solid #ddd"
        sig_bg, sig_color = "#EAF3DE", "#27500A"
    elif is_hold:
        top_border = "3px solid #BA7517"
        featured   = "0.5px solid #ddd"
        sig_bg, sig_color = "#FAEEDA", "#633806"
    else:  # SELL
        top_border = "3px solid #A32D2D"
        featured   = "0.5px solid #ddd"
        sig_bg, sig_color = "#FCEBEB", "#791F1F"

    best_badge = '<div style="font-size:11px;background:#EAF3DE;color:#27500A;padding:2px 8px;border-radius:6px;margin-bottom:6px;display:inline-block;">strongest buy</div>' if is_top else ""

    if history:
        history_rows = "".join(f"<tr><td>{row['timestamp'][:16]}</td><td>{row['signal']}</td><td>{row['score']}</td></tr>" for row in history[-5:])
        history_html = f"""
    <details style="margin-top:8px;">
      <summary style="font-size:11px;color:#888;cursor:pointer;">History (last 5)</summary>
      <table style="font-size:10px;width:100%;border-collapse:collapse;">
        <tr><th style="border:1px solid #ddd;padding:2px;">Time</th><th style="border:1px solid #ddd;padding:2px;">Signal</th><th style="border:1px solid #ddd;padding:2px;">Score</th></tr>
        {history_rows}
      </table>
    </details>
    """
    else:
        history_html = ""

    return f"""
    <div style="background:#fff;border:{featured};border-top:{top_border};
                border-radius:12px;padding:1rem;min-width:0;">
      {best_badge}
      <p style="font-size:15px;font-weight:500;margin:0 0 4px;">{t['ticker']}</p>
      <span style="font-size:11px;font-weight:500;padding:2px 8px;border-radius:6px;
                   background:{sig_bg};color:{sig_color};display:inline-block;
                   margin-bottom:8px;">{sig}</span>
      <p style="font-size:20px;font-weight:500;margin:0 0 8px;">${t['price']:.2f}</p>
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
        <span style="font-size:11px;color:#888;">Score</span>
        {_score_bar(t['score'], is_buy)}
        <span style="font-size:13px;font-weight:500;">{t['score']:+.2f}</span>
      </div>
      <div style="display:flex;gap:8px;font-size:11px;color:#888;flex-wrap:wrap;">
        <span style="display:flex;align-items:center;gap:3px;">
          <span style="width:7px;height:7px;border-radius:50%;background:#639922;display:inline-block;"></span>
          {t['buy']} buy
        </span>
        <span style="display:flex;align-items:center;gap:3px;">
          <span style="width:7px;height:7px;border-radius:50%;background:#E24B4A;display:inline-block;"></span>
          {t['sell']} sell
        </span>
        <span style="display:flex;align-items:center;gap:3px;">
          <span style="width:7px;height:7px;border-radius:50%;background:#888;display:inline-block;"></span>
          {t['neutral']} neutral
        </span>
      </div>
      {history_html}
    </div>"""


def _build_html(timestamp: str, buys: list[dict], holds: list[dict], sells: list[dict]) -> str:
    """Assemble the full HTML page."""
    all_tickers = buys + holds + sells
    labels  = [t["ticker"] for t in all_tickers]
    scores  = [t["score"]  for t in all_tickers]
    colors  = ["#639922" if s > 0 else "#E24B4A" for s in scores]
    borders = ["#3B6D11" if s > 0 else "#A32D2D" for s in scores]

    # Load histories
    histories = {}
    for t in all_tickers:
        csv_path = Path("logs") / f"{t['ticker']}.csv"
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                histories[t['ticker']] = list(reader)
        else:
            histories[t['ticker']] = []

    # Chart.js data as JS literals
    labels_js  = json.dumps(labels)
    scores_js  = json.dumps(scores)
    colors_js  = json.dumps(colors)
    borders_js = json.dumps(borders)

    # Build cards
    buy_cards  = "".join(_card(t, histories.get(t['ticker'], []), is_top=(i == 0)) for i, t in enumerate(buys))
    hold_cards = "".join(_card(t, histories.get(t['ticker'], [])) for t in holds)
    sell_cards = "".join(_card(t, histories.get(t['ticker'], [])) for t in sells)

    hold_section = f"""
<div class="section-label">Hold signals ({len(holds)})</div>
<div class="grid">{hold_cards}</div>
""" if holds else ""

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trading Signals — {timestamp[:10]}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f5f3; color: #1a1a18; padding: 2rem; }}
  h1   {{ font-size: 20px; font-weight: 500; margin-bottom: 4px; }}
  .meta {{ font-size: 12px; color: #888; margin-bottom: 1.5rem; }}
  .section-label {{ font-size: 11px; color: #888; letter-spacing: 0.06em;
                    text-transform: uppercase; margin-bottom: 10px; margin-top: 1.5rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
           gap: 12px; }}
  .chart-wrap {{ margin-top: 2rem; background: #fff; border-radius: 12px;
                 border: 0.5px solid #ddd; padding: 1.25rem; }}
  .chart-title {{ font-size: 13px; color: #888; margin-bottom: 1rem; }}
  footer {{ margin-top: 2rem; font-size: 11px; color: #aaa; text-align: center; }}
</style>
</head>
<body>

<h1>Trading signals</h1>
<p class="meta">Signal timestamp: {timestamp} &nbsp;|&nbsp; Generated: {generated_at}</p>

<div class="section-label">Buy signals ({len(buys)})</div>
<div class="grid">{buy_cards}</div>

{hold_section}
<div class="section-label">Sell signals ({len(sells)})</div>
<div class="grid">{sell_cards}</div>

<div class="chart-wrap">
  <p class="chart-title">Signal score comparison</p>
  <div style="position:relative;width:100%;height:220px;">
    <canvas id="scoreChart"
            role="img"
            aria-label="Bar chart of signal scores for {', '.join(labels)}">
      Scores: {', '.join(f'{t["ticker"]} {t["score"]:+.2f}' for t in all_tickers)}
    </canvas>
  </div>
</div>

<footer>Not financial advice &mdash; for informational purposes only.</footer>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
new Chart(document.getElementById('scoreChart'), {{
  type: 'bar',
  data: {{
    labels: {labels_js},
    datasets: [{{
      label: 'Signal score',
      data: {scores_js},
      backgroundColor: {colors_js},
      borderColor: {borders_js},
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: ctx => ' Score: ' + ctx.parsed.y.toFixed(2) }} }}
    }},
    scales: {{
      x: {{ grid: {{ display: false }}, ticks: {{ color: '#888', font: {{ size: 12 }} }} }},
      y: {{
        min: -0.6, max: 1.1,
        grid: {{ color: 'rgba(0,0,0,0.06)' }},
        ticks: {{ color: '#888', font: {{ size: 11 }},
                  callback: v => v.toFixed(2) }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# CLI convenience: python dashboard_generator.py signals.json
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python dashboard_generator.py <path_to_signals.json>")
        sys.exit(1)
    out = generate_dashboard(sys.argv[1])
    print(f"Done. Open in browser: file://{os.path.abspath(out)}")
