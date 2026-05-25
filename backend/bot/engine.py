"""
Trading Engine — Main orchestrator.
Called on every closed candle. Runs full analysis pipeline.
"""

import asyncio
import logging
from typing import Dict

import pandas as pd

from bot.pattern_detector import detect_all_patterns
from bot.indicator_engine import get_all_indicators
from bot.ai_scorer import score_signal
from bot.order_manager import place_order, monitor_active_trades, get_active_trades
from bot.risk_controller import can_trade
from bot.trade_logger import log_signal
from bot.data_feed import get_candles
from config import PRIMARY_TIMEFRAME, TREND_TIMEFRAME

logger = logging.getLogger(__name__)

# Latest analysis results — exposed to API
latest_analysis: Dict = {}
current_prices: Dict[str, float] = {}


async def on_candle_closed(symbol: str, interval: str, df: pd.DataFrame):
    """Triggered on every closed candle."""
    price = float(df["close"].iloc[-1])
    current_prices[symbol] = price

    # Monitor SL/TP for active trades
    await monitor_active_trades(current_prices)

    # Only run full analysis on primary timeframe
    if interval != PRIMARY_TIMEFRAME:
        return

    logger.info(f"Analyzing {symbol} {interval} @ {price}")

    # 1. Detect patterns
    patterns = detect_all_patterns(df)

    # 2. Calculate indicators on primary timeframe
    indicators = get_all_indicators(df)

    # 3. Get trend context from higher timeframe
    trend_df = get_candles(symbol, TREND_TIMEFRAME)
    trend_indicators = get_all_indicators(trend_df) if trend_df is not None and len(trend_df) >= 30 else {}

    # 4. Store analysis for dashboard
    latest_analysis[symbol] = {
        "symbol": symbol,
        "price": price,
        "patterns": patterns,
        "indicators": indicators,
        "trend_indicators": trend_indicators,
        "active_trades": get_active_trades(),
    }

    if not patterns:
        logger.info(f"{symbol}: No patterns detected, skipping.")
        return

    logger.info(f"{symbol}: Patterns detected — {[p['pattern'] for p in patterns]}")

    # 5. Check if we can trade
    tradeable, reason = can_trade()
    if not tradeable:
        logger.info(f"{symbol}: Trading blocked — {reason}")
        return

    # 6. AI scoring
    ai_result = await score_signal(symbol, interval, patterns, indicators, trend_indicators)
    if not ai_result:
        logger.warning(f"{symbol}: AI scoring failed.")
        return

    score = ai_result.get("confidence_score", 0)
    direction = ai_result.get("direction", "skip")

    # Update analysis with AI result
    latest_analysis[symbol]["ai_score"] = score
    latest_analysis[symbol]["ai_direction"] = direction
    latest_analysis[symbol]["ai_reasoning"] = ai_result.get("reasoning", "")
    latest_analysis[symbol]["ai_above_threshold"] = ai_result.get("above_threshold", False)

    # 7. Log signal regardless of action
    await log_signal(
        symbol=symbol,
        timeframe=interval,
        patterns=[p["pattern"] for p in patterns],
        ai_score=score,
        direction=direction,
        acted_on=ai_result.get("above_threshold", False) and direction != "skip",
        skip_reason="" if ai_result.get("above_threshold") else f"Score {score} below threshold",
    )

    # 8. Place trade if score is high enough
    if ai_result.get("above_threshold") and direction in ("bullish", "bearish"):
        side = "BUY" if direction == "bullish" else "SELL"
        await place_order(
            symbol=symbol,
            side=side,
            entry_price=ai_result.get("entry_price", price),
            stop_loss=ai_result.get("stop_loss", 0),
            take_profit=ai_result.get("take_profit", 0),
            patterns=[p["pattern"] for p in patterns],
            ai_score=score,
            ai_reasoning=ai_result.get("reasoning", ""),
        )
    else:
        logger.info(f"{symbol}: Signal skipped — Score: {score}, Direction: {direction}")
