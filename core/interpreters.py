"""
interpreters/
-------------
Modular AI interpreter system supporting multiple AI providers.
Each interpreter provides independent analysis with its own strengths.

Supported Interpreters:
- Claude (Anthropic) - Deep reasoning and market analysis
- Copilot (GitHub) - Code-aware technical analysis
- Future: GPT-4, Gemini, etc.

Architecture:
- Base Interpreter class with common interface
- Provider-specific implementations
- Independent logging per interpreter
- Configurable activation per provider
"""

from abc import ABC, abstractmethod
import os
import json
from datetime import datetime
from typing import Dict, List, Any

from config.settings import LOG_DIR


class BaseInterpreter(ABC):
    """Abstract base class for AI interpreters."""

    def __init__(self, name: str, model: str, api_key: str = None):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.log_file = os.path.join(LOG_DIR, f"tv_{name.lower()}_interpretations.json")
        self.text_log_file = os.path.join(LOG_DIR, f"tv_{name.lower()}_interpretations.txt")

    @abstractmethod
    def interpret_signals(self, results: List[Dict]) -> List[Dict]:
        """Interpret trading signals using this AI provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this interpreter is properly configured and available."""
        pass

    def save_interpretations(self, interpretations: List[Dict], timestamp: str = None):
        """Save interpretations to both JSON and text formats."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        # JSON format
        data = {
            "timestamp": timestamp,
            "interpreter": self.name,
            "model": self.model,
            "interpretation_count": len(interpretations),
            "interpretations": interpretations
        }

        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Text format
        self._save_text_interpretations(interpretations, timestamp)

    def _save_text_interpretations(self, interpretations: List[Dict], timestamp: str):
        """Save interpretations in human-readable text format."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"AI INTERPRETATIONS - {self.name.upper()} ({self.model})")
        lines.append(f"Generated: {timestamp}")
        lines.append("=" * 80)
        lines.append("")

        for interp in interpretations:
            lines.append(f"TICKER: {interp['ticker']}")
            lines.append(f"SIGNAL: {interp['signal']}")
            lines.append(f"CONFIDENCE: {interp.get('confidence', 'N/A')}%")
            lines.append("")
            lines.append("REASONING:")
            lines.append(interp.get('reasoning', 'No reasoning provided'))
            lines.append("")
            lines.append("RISKS:")
            risks = interp.get('risks', [])
            if risks:
                for risk in risks:
                    lines.append(f"• {risk}")
            else:
                lines.append("• No specific risks identified")
            lines.append("")
            lines.append("ACTION:")
            lines.append(interp.get('action', 'No action recommended'))
            lines.append("")
            lines.append("-" * 60)
            lines.append("")

        with open(self.text_log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


class ClaudeInterpreter(BaseInterpreter):
    """Claude (Anthropic) interpreter for trading signals."""

    def __init__(self):
        from config.settings import CLAUDE_API_KEY, CLAUDE_MODEL
        super().__init__("claude", CLAUDE_MODEL, CLAUDE_API_KEY)

    def is_available(self) -> bool:
        """Check if Claude API is configured."""
        return bool(self.api_key)

    def interpret_signals(self, results: List[Dict]) -> List[Dict]:
        """Get Claude's interpretation of trading signals."""
        if not self.is_available():
            return []

        interpretations = []

        for result in results:
            if result['signal'] == 'N/A':
                continue

            # Create prompt for Claude
            prompt = self._create_claude_prompt(result)

            try:
                # Call Claude API (placeholder - implement actual API call)
                interpretation = self._call_claude_api(prompt)
                interpretations.append({
                    "ticker": result['ticker'],
                    "signal": result['signal'],
                    "confidence": interpretation.get('confidence', 75),
                    "reasoning": interpretation.get('reasoning', 'Analysis provided by Claude'),
                    "risks": interpretation.get('risks', ['Market volatility', 'Technical analysis limitations']),
                    "action": interpretation.get('action', f"Consider {result['signal'].lower()} position")
                })
            except Exception as e:
                print(f"Claude interpretation failed for {result['ticker']}: {e}")
                continue

        return interpretations

    def _create_claude_prompt(self, result: Dict) -> str:
        """Create a detailed prompt for Claude analysis."""
        return f"""
        Analyze this trading signal for {result['ticker']}:

        Current Signal: {result['signal']}
        Weighted Score: {result['weighted_score']}
        Price: ${result.get('price', 'N/A')}

        Technical Summary:
        - BUY indicators: {result.get('buy', 0)}
        - SELL indicators: {result.get('sell', 0)}
        - NEUTRAL indicators: {result.get('neutral', 0)}

        Timeframe Analysis:
        {self._format_timeframes(result.get('per_timeframe', {}))}

        Please provide:
        1. Confidence level (0-100%) in this signal
        2. Detailed reasoning for the signal
        3. Key risks to consider
        4. Recommended action

        Be specific and actionable in your analysis.
        """

    def _format_timeframes(self, timeframes: Dict) -> str:
        """Format timeframe analysis for the prompt."""
        lines = []
        for tf, signal in timeframes.items():
            lines.append(f"- {tf.title()}: {signal}")
        return '\n'.join(lines)

    def _call_claude_api(self, prompt: str) -> Dict:
        """Call Claude API (implement actual API integration)."""
        # Placeholder - implement actual Claude API call
        # This would use the Anthropic SDK
        return {
            "confidence": 78,
            "reasoning": "Based on strong technical indicators and positive momentum across multiple timeframes.",
            "risks": ["Market volatility", "Potential overbought conditions", "Economic data releases"],
            "action": "Consider entering long position with stop loss below recent support"
        }


class CopilotInterpreter(BaseInterpreter):
    """GitHub Copilot interpreter for trading signals."""

    def __init__(self):
        # Copilot might use different configuration
        super().__init__("copilot", "GPT-4", None)  # API key handling TBD

    def is_available(self) -> bool:
        """Check if Copilot is available (placeholder)."""
        # This would check for Copilot API access
        return False  # Not implemented yet

    def interpret_signals(self, results: List[Dict]) -> List[Dict]:
        """Get Copilot's interpretation (placeholder implementation)."""
        # Implement Copilot API integration
        return []


# Future interpreters can be added here:
# class GPT4Interpreter(BaseInterpreter): ...
# class GeminiInterpreter(BaseInterpreter): ...


def get_available_interpreters() -> List[BaseInterpreter]:
    """Get all configured and available interpreters."""
    interpreters = [
        ClaudeInterpreter(),
        CopilotInterpreter(),
        # Add more interpreters here
    ]

    return [interp for interp in interpreters if interp.is_available()]


def run_all_interpretations(results: List[Dict]) -> Dict[str, List[Dict]]:
    """Run all available interpreters and return their analyses."""
    interpreters = get_available_interpreters()
    all_interpretations = {}

    for interpreter in interpreters:
        print(f"Running {interpreter.name} interpretation...")
        try:
            interpretations = interpreter.interpret_signals(results)
            if interpretations:
                interpreter.save_interpretations(interpretations)
                all_interpretations[interpreter.name] = interpretations
                print(f"✅ {interpreter.name}: {len(interpretations)} interpretations saved")
            else:
                print(f"⚠️  {interpreter.name}: No interpretations generated")
        except Exception as e:
            print(f"❌ {interpreter.name}: Failed - {e}")

    return all_interpretations


# Example usage
if __name__ == "__main__":
    # Test available interpreters
    available = get_available_interpreters()
    print(f"Available interpreters: {[i.name for i in available]}")

    # Test with sample data
    sample_results = [
        {
            "ticker": "AAPL",
            "signal": "BUY",
            "weighted_score": 0.65,
            "price": 150.25,
            "buy": 16,
            "sell": 4,
            "neutral": 6,
            "per_timeframe": {"daily": "Buy", "weekly": "Strong Buy"}
        }
    ]

    if available:
        print("Testing interpretation with sample data...")
        interpretations = run_all_interpretations(sample_results)
        print(f"Generated interpretations from: {list(interpretations.keys())}")