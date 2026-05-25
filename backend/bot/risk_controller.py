"""
Risk Controller
Enforces daily loss limits, position sizing, max open trades.
"""

import logging
from datetime import date
from typing import Dict, Optional

from config import CAPITAL_USDT, RISK_PER_TRADE_PERCENT, DAILY_LOSS_LIMIT_USDT, MAX_OPEN_TRADES

logger = logging.getLogger(__name__)

# In-memory daily state (resets each day)
_state = {
    "date": date.today().isoformat(),
    "daily_pnl": 0.0,
    "trades_today": 0,
    "open_trades": 0,
    "trading_halted": False,
    "halt_reason": "",
}


def _reset_if_new_day():
    today = date.today().isoformat()
    if _state["date"] != today:
        _state["date"] = today
        _state["daily_pnl"] = 0.0
        _state["trades_today"] = 0
        _state["open_trades"] = 0
        _state["trading_halted"] = False
        _state["halt_reason"] = ""
        logger.info("New trading day — daily state reset.")


def can_trade() -> tuple[bool, str]:
    _reset_if_new_day()
    if _state["trading_halted"]:
        return False, f"Trading halted: {_state['halt_reason']}"
    if _state["open_trades"] >= MAX_OPEN_TRADES:
        return False, f"Max open trades ({MAX_OPEN_TRADES}) reached"
    return True, "OK"


def calculate_position_size(entry_price: float, stop_loss: float) -> float:
    """
    Risk-based position sizing.
    Risk RISK_PER_TRADE_PERCENT% of capital per trade.
    Returns quantity to buy/sell.
    """
    _reset_if_new_day()
    risk_amount = CAPITAL_USDT * (RISK_PER_TRADE_PERCENT / 100)
    price_risk = abs(entry_price - stop_loss)
    if price_risk == 0:
        return 0.0
    quantity = risk_amount / price_risk
    return round(quantity, 6)


def on_trade_opened():
    _state["open_trades"] += 1
    _state["trades_today"] += 1
    logger.info(f"Trade opened. Open: {_state['open_trades']}, Today: {_state['trades_today']}")


def on_trade_closed(pnl: float):
    _state["open_trades"] = max(0, _state["open_trades"] - 1)
    _state["daily_pnl"] += pnl

    logger.info(f"Trade closed. PnL: {pnl:+.2f} USDT | Daily PnL: {_state['daily_pnl']:+.2f} USDT")

    if _state["daily_pnl"] <= -abs(DAILY_LOSS_LIMIT_USDT):
        _state["trading_halted"] = True
        _state["halt_reason"] = f"Daily loss limit hit ({_state['daily_pnl']:.2f} USDT)"
        logger.warning(f"TRADING HALTED — {_state['halt_reason']}")


def init_daily_state(daily_pnl: float, open_trades: int):
    """Restore daily state from DB on startup — prevents PnL reset bug on restart."""
    _reset_if_new_day()
    _state["daily_pnl"] = daily_pnl
    _state["open_trades"] = open_trades
    if daily_pnl <= -abs(DAILY_LOSS_LIMIT_USDT):
        _state["trading_halted"] = True
        _state["halt_reason"] = f"Daily loss limit hit ({daily_pnl:.2f} USDT)"
    logger.info(f"Daily state restored from DB: PnL={daily_pnl:+.2f} USDT, Open trades={open_trades}")


def get_state() -> Dict:
    _reset_if_new_day()
    return {
        **_state,
        "capital_usdt": CAPITAL_USDT,
        "max_open": MAX_OPEN_TRADES,
        "daily_loss_limit": DAILY_LOSS_LIMIT_USDT,
        "testnet": True,
    }
