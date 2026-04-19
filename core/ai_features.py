"""
ai_features.py
--------------
Extracts and formats complete signal data in AI/ML-optimized format.
Creates feature vectors suitable for machine learning analysis.
"""

import csv
import json
import os
from datetime import datetime
from config.settings import LOG_DIR

AI_FEATURES_FILE = os.path.join(LOG_DIR, "tv_signals_ai_features.csv")
AI_FEATURES_JSON_FILE = os.path.join(LOG_DIR, "tv_signals_ai_features.json")


def flatten_indicators(result: dict) -> dict:
    """Flatten nested indicator data into flat feature dictionary."""
    features = {}

    # Basic features
    features['price'] = result.get('price') or 0.0
    features['weighted_score'] = result.get('weighted_score', 0.0)
    features['buy_count'] = result.get('buy', 0)
    features['sell_count'] = result.get('sell', 0)
    features['neutral_count'] = result.get('neutral', 0)

    # Timeframe signals (convert to numeric)
    timeframe_signals = result.get('per_timeframe', {})
    for tf, signal in timeframe_signals.items():
        # Convert signal to numeric score
        if 'Strong Buy' in signal:
            score = 1.0
        elif 'Buy' in signal:
            score = 0.5
        elif 'Sell' in signal:
            score = -0.5
        elif 'Strong Sell' in signal:
            score = -1.0
        else:
            score = 0.0
        features[f'{tf}_signal'] = score

    # Moving averages
    mas = result.get('moving_avgs', {})
    for ma_name, ma_data in mas.items():
        features[f'{ma_name}_value'] = ma_data.get('value', 0.0)
        # Convert signal to numeric
        signal = ma_data.get('signal', 'N/A')
        features[f'{ma_name}_signal'] = 1.0 if signal == 'BUY' else (-1.0 if signal == 'SELL' else 0.0)

    # Oscillators
    oscs = result.get('oscillators', {})
    for osc_name, osc_data in oscs.items():
        features[f'{osc_name}_value'] = osc_data.get('value', 0.0)
        # Convert signal to numeric
        signal = osc_data.get('signal', 'N/A')
        if signal == 'OVERBOUGHT':
            score = -1.0
        elif signal == 'OVERSOLD':
            score = 1.0
        elif signal == 'BUY':
            score = 0.5
        elif signal == 'SELL':
            score = -0.5
        else:
            score = 0.0
        features[f'{osc_name}_signal'] = score

    # Trend indicators
    trends = result.get('trend', {})
    for trend_name, trend_data in trends.items():
        features[f'{trend_name}_value'] = trend_data.get('value', 0.0)
        # Convert signal to numeric
        signal = trend_data.get('signal', 'N/A')
        if 'BUY' in signal:
            score = 0.5
        elif 'SELL' in signal:
            score = -0.5
        elif 'WEAK' in signal:
            score = 0.0
        else:
            score = 0.0
        features[f'{trend_name}_signal'] = score

    # Pivot points (flatten all methods)
    pivots = result.get('pivots', {})
    for method, levels in pivots.items():
        for level_name, value in levels.items():
            features[f'pivot_{method.lower()}_{level_name.lower()}'] = value or 0.0

    return features


def create_ai_features(results: list) -> list:
    """Create AI-optimized feature vectors from analysis results."""
    timestamp = datetime.now().isoformat()

    feature_rows = []
    for result in results:
        if result['signal'] == 'N/A':
            continue  # Skip tickers with no data

        # Create base feature row
        row = {
            'timestamp': timestamp,
            'ticker': result['ticker'],
            'target_signal': result['signal'],
            'target_score': result['weighted_score'],
        }

        # Add all flattened indicators
        features = flatten_indicators(result)
        row.update(features)

        feature_rows.append(row)

    return feature_rows


def save_ai_features_csv(feature_rows: list):
    """Save features in CSV format optimized for ML."""
    if not feature_rows:
        return

    # Get all possible column names
    all_columns = set()
    for row in feature_rows:
        all_columns.update(row.keys())

    # Sort columns for consistency
    columns = sorted(all_columns)

    # Write CSV
    with open(AI_FEATURES_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(feature_rows)

    print(f"AI features saved to: {AI_FEATURES_FILE}")


def save_ai_features_json(feature_rows: list):
    """Save features in structured JSON format."""
    if not feature_rows:
        return

    # Group by timestamp for historical tracking
    timestamp = feature_rows[0]['timestamp'] if feature_rows else datetime.now().isoformat()

    data = {
        'timestamp': timestamp,
        'feature_count': len(feature_rows),
        'features': feature_rows
    }

    with open(AI_FEATURES_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"AI features JSON saved to: {AI_FEATURES_JSON_FILE}")


def export_ai_features(results: list):
    """Export analysis results in AI/ML-optimized formats."""
    feature_rows = create_ai_features(results)

    if feature_rows:
        save_ai_features_csv(feature_rows)
        save_ai_features_json(feature_rows)
    else:
        print("No valid data to export for AI features")


# Example usage for testing
if __name__ == "__main__":
    # Test with sample data structure
    sample_result = {
        "ticker": "AAPL",
        "signal": "BUY",
        "weighted_score": 0.65,
        "price": 150.25,
        "per_timeframe": {"daily": "Buy", "weekly": "Strong Buy", "monthly": "Buy"},
        "buy": 16,
        "sell": 4,
        "neutral": 6,
        "moving_avgs": {
            "MA5_SMA": {"value": 148.50, "signal": "BUY"},
            "MA20_EMA": {"value": 145.75, "signal": "BUY"}
        },
        "oscillators": {
            "RSI_14": {"value": 65.5, "signal": "BUY"},
            "STOCH_K": {"value": 75.2, "signal": "NEUTRAL"}
        },
        "trend": {
            "MACD": {"value": 2.15, "signal": "BUY"},
            "ADX": {"value": 28.5, "signal": "BUY"}
        },
        "pivots": {
            "Classic": {"PP": 149.0, "R1": 152.0, "S1": 146.0}
        }
    }

    features = flatten_indicators(sample_result)
    print("Sample flattened features:")
    for k, v in list(features.items())[:10]:  # Show first 10
        print(f"  {k}: {v}")