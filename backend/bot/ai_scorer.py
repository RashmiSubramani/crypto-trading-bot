"""
AI Signal Scorer — DISABLED

Claude API integration has been disabled to avoid API key usage/cost.
`score_signal` is a no-op that returns None, so the engine will not act on
any signal. Re-enable by restoring the anthropic client and the API call
in `score_signal`.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


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
    DISABLED — Claude API scoring is turned off to avoid API key usage.

    Always returns None. The engine treats a None result as "AI scoring
    failed" and does not act on the signal, so no Claude API calls are made.
    """
    logger.info(f"{symbol}: AI scoring disabled — no Claude API call made.")
    return None
