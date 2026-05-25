"""
AI Signal Scorer — Claude API Integration
Sends pattern + indicator data to Claude for trade confidence scoring.
Returns a score 0-100 and reasoning.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

import anthropic

from config import ANTHROPIC_API_KEY, AI_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


SYSTEM_PROMPT = """You are an expert crypto trading analyst. You analyze candlestick patterns,
technical indicators, and market context to evaluate trade signals.

Your job is to score a potential trade from 0 to 100 based on:
- Quality and reliability of the detected candlestick pattern(s)
- Alignment of technical indicators (RSI, MACD, EMA trend, Bollinger Bands)
- Volume confirmation
- Price position relative to support/resistance and VWAP
- Multi-timeframe trend alignment
- Overall risk/reward context

Respond ONLY with a valid JSON object in this exact format:
{
  "confidence_score": <integer 0-100>,
  "direction": "<bullish|bearish|skip>",
  "reasoning": "<2-3 sentence explanation>",
  "entry_price": <float>,
  "stop_loss": <float>,
  "take_profit": <float>,
  "risk_reward": <float>
}

Score guidelines:
- 85-100: Exceptional setup, multiple confluences
- 70-84: Good setup, worth trading
- 50-69: Weak setup, skip
- 0-49: Poor setup, do not trade

If direction is "skip", set entry/sl/tp to 0."""


def build_analysis_prompt(
    symbol: str,
    timeframe: str,
    patterns: List[Dict],
    indicators: Dict[str, Any],
    trend_indicators: Dict[str, Any],
) -> str:
    pattern_text = ", ".join([f"{p['pattern']} ({p['direction']}, strength {p['strength']}/3)" for p in patterns]) or "None detected"

    return f"""Analyze this crypto trade signal:

SYMBOL: {symbol}
TIMEFRAME: {timeframe}
CURRENT PRICE: {indicators.get('current_price', 'N/A')}

DETECTED PATTERNS ({timeframe}):
{pattern_text}

TECHNICAL INDICATORS ({timeframe}):
- RSI(14): {indicators.get('rsi', 'N/A')} (prev: {indicators.get('rsi_prev', 'N/A')})
- MACD: {indicators.get('macd', 'N/A')} | Signal: {indicators.get('macd_signal', 'N/A')} | Hist: {indicators.get('macd_hist', 'N/A')}
- MACD Crossover: {indicators.get('macd_crossover', 'N/A')}
- EMA 9/21/50/200: {indicators.get('ema_9')}/{indicators.get('ema_21')}/{indicators.get('ema_50')}/{indicators.get('ema_200')}
- EMA Trend: {indicators.get('ema_trend', 'N/A')}
- Bollinger Bands: Upper={indicators.get('bb_upper')} Mid={indicators.get('bb_mid')} Lower={indicators.get('bb_lower')}
- BB Position (0=lower, 1=upper): {indicators.get('bb_position', 'N/A')}
- ATR: {indicators.get('atr', 'N/A')}
- VWAP: {indicators.get('vwap', 'N/A')} | Price vs VWAP: {indicators.get('price_vs_vwap', 'N/A')}
- Supertrend: {indicators.get('supertrend')} | Direction: {indicators.get('supertrend_direction', 'N/A')}
- Volume: {indicators.get('volume')} | Avg Volume: {indicators.get('volume_avg')} | Spike: {indicators.get('volume_spike')}
- Support: {indicators.get('support')} | Resistance: {indicators.get('resistance')}

HIGHER TIMEFRAME TREND (1h):
- EMA Trend: {trend_indicators.get('ema_trend', 'N/A')}
- RSI: {trend_indicators.get('rsi', 'N/A')}
- Supertrend Direction: {trend_indicators.get('supertrend_direction', 'N/A')}
- Price vs VWAP: {trend_indicators.get('price_vs_vwap', 'N/A')}

Based on this data, provide your trade evaluation as JSON."""


async def score_signal(
    symbol: str,
    timeframe: str,
    patterns: List[Dict],
    indicators: Dict[str, Any],
    trend_indicators: Dict[str, Any],
) -> Optional[Dict]:
    """
    Ask Claude to evaluate the trade signal.
    Returns dict with confidence_score, direction, reasoning, entry, sl, tp.
    Returns None if API call fails.
    """
    if not patterns:
        return None

    prompt = build_analysis_prompt(symbol, timeframe, patterns, indicators, trend_indicators)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Extract JSON from response (handles extra text around it)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            logger.error(f"No JSON found in Claude response: {raw[:200]}")
            return None
        result = json.loads(match.group())
        result["symbol"] = symbol
        result["patterns"] = [p["pattern"] for p in patterns]
        result["above_threshold"] = result.get("confidence_score", 0) >= AI_CONFIDENCE_THRESHOLD

        logger.info(
            f"AI Score for {symbol}: {result['confidence_score']} | "
            f"Direction: {result['direction']} | Above threshold: {result['above_threshold']}"
        )
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None
