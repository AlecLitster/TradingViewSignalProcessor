#!/usr/bin/env python3
"""
demo_interpreters.py
--------------------
Demonstration of the multi-AI interpreter system.
Shows how different AI providers would analyze trading signals.
"""

import json
from datetime import datetime
from core.interpreters import BaseInterpreter, get_available_interpreters


class MockClaudeInterpreter(BaseInterpreter):
    """Mock Claude interpreter for demonstration."""

    def __init__(self):
        super().__init__("claude", "claude-sonnet-4-20250514", "mock_key")

    def is_available(self) -> bool:
        return True  # Always available for demo

    def interpret_signals(self, results):
        """Mock Claude analysis."""
        interpretations = []
        for result in results:
            if result['signal'] == 'N/A':
                continue

            interpretations.append({
                "ticker": result['ticker'],
                "signal": result['signal'],
                "confidence": 82,
                "reasoning": f"Claude analysis: {result['ticker']} shows strong {result['signal'].lower()} momentum across multiple timeframes. Technical indicators suggest favorable risk-reward profile.",
                "risks": [
                    "Market volatility could impact short-term performance",
                    "Economic data releases may cause temporary fluctuations",
                    "Sector-specific news could affect price action"
                ],
                "action": f"Consider {result['signal'].lower()} position with appropriate stop loss. Monitor closely for confirmation."
            })
        return interpretations


class MockCopilotInterpreter(BaseInterpreter):
    """Mock Copilot interpreter for demonstration."""

    def __init__(self):
        super().__init__("copilot", "gpt-4", "mock_key")

    def is_available(self) -> bool:
        return True  # Always available for demo

    def interpret_signals(self, results):
        """Mock Copilot analysis."""
        interpretations = []
        for result in results:
            if result['signal'] == 'N/A':
                continue

            interpretations.append({
                "ticker": result['ticker'],
                "signal": result['signal'],
                "confidence": 76,
                "reasoning": f"Copilot analysis: Code-driven technical assessment indicates {result['signal'].lower()} bias. Pattern recognition algorithms detect convergence of multiple indicators.",
                "risks": [
                    "Algorithm may not account for fundamental factors",
                    "Historical patterns don't guarantee future results",
                    "Black swan events could invalidate technical analysis"
                ],
                "action": f"Execute {result['signal'].lower()} order with algorithmic stop loss placement. Implement trailing stop for profit protection."
            })
        return interpretations


def demo_multi_interpreter_analysis():
    """Demonstrate the multi-interpreter system with sample data."""

    print("🤖 Multi-AI Interpreter System Demo")
    print("=" * 50)

    # Sample trading results (simulating real analyzer output)
    sample_results = [
        {
            "ticker": "AAPL",
            "signal": "BUY",
            "weighted_score": 0.75,
            "price": 185.50,
            "buy": 18,
            "sell": 2,
            "neutral": 6,
            "per_timeframe": {"daily": "Strong Buy", "weekly": "Buy", "monthly": "Buy"}
        },
        {
            "ticker": "TSLA",
            "signal": "SELL",
            "weighted_score": -0.45,
            "price": 245.80,
            "buy": 4,
            "sell": 15,
            "neutral": 7,
            "per_timeframe": {"daily": "Sell", "weekly": "Strong Sell", "monthly": "Sell"}
        },
        {
            "ticker": "NVDA",
            "signal": "HOLD",
            "weighted_score": 0.05,
            "price": 875.20,
            "buy": 8,
            "sell": 8,
            "neutral": 10,
            "per_timeframe": {"daily": "Hold", "weekly": "Buy", "monthly": "Hold"}
        }
    ]

    # Create mock interpreters for demo
    interpreters = [MockClaudeInterpreter(), MockCopilotInterpreter()]

    print(f"📊 Analyzing {len(sample_results)} signals with {len(interpreters)} AI interpreters")
    print()

    all_interpretations = {}

    for interpreter in interpreters:
        print(f"🔄 Running {interpreter.name.title()} analysis...")
        try:
            interpretations = interpreter.interpret_signals(sample_results)
            if interpretations:
                # Save interpretations
                interpreter.save_interpretations(interpretations)

                all_interpretations[interpreter.name] = interpretations
                print(f"  ✅ {interpreter.name.title()}: {len(interpretations)} analyses saved")
                print(f"     📄 JSON: {interpreter.log_file}")
                print(f"     📄 Text: {interpreter.text_log_file}")
            else:
                print(f"  ⚠️  {interpreter.name.title()}: No interpretations generated")
        except Exception as e:
            print(f"  ❌ {interpreter.name.title()}: Failed - {e}")
        print()

    # Show sample output
    if all_interpretations:
        print("📋 Sample Analysis Output:")
        print("-" * 30)

        # Show first interpretation from each AI
        for ai_name, interpretations in all_interpretations.items():
            if interpretations:
                interp = interpretations[0]
                print(f"{ai_name.upper()} Analysis for {interp['ticker']}:")
                print(f"  Signal: {interp['signal']}")
                print(f"  Confidence: {interp['confidence']}%")
                print(f"  Action: {interp['action']}")
                print()

    print("🎯 Key Benefits of Multi-Interpreter System:")
    print("  • Diverse AI perspectives reduce single-point-of-failure")
    print("  • Each AI can specialize in different analysis aspects")
    print("  • Independent logging allows comparison of interpretations")
    print("  • Fallback capability if one AI provider is unavailable")
    print("  • Richer analysis through multiple cognitive approaches")

    print()
    print("📁 Check the logs/ directory for generated analysis files!")


if __name__ == "__main__":
    demo_multi_interpreter_analysis()