"""
Order Manager — Places, monitors and closes orders on Binance (Testnet).
"""

import asyncio
import logging
import math
from typing import Dict, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException

from config import BINANCE_API_KEY, BINANCE_SECRET_KEY, TESTNET
from bot.risk_controller import on_trade_opened, on_trade_closed, calculate_position_size
from bot.trade_logger import open_trade, close_trade, get_open_trades

logger = logging.getLogger(__name__)

# Active trade tracking: {trade_id: {symbol, side, entry, sl, tp, order_id, quantity}}
_active_trades: Dict[int, Dict] = {}
_lot_size_cache: Dict[str, Dict] = {}


def _get_client() -> Client:
    return Client(BINANCE_API_KEY, BINANCE_SECRET_KEY, testnet=TESTNET)


def _get_lot_size(client: Client, symbol: str) -> Dict:
    if symbol in _lot_size_cache:
        return _lot_size_cache[symbol]
    try:
        info = client.get_symbol_info(symbol)
        for f in info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                _lot_size_cache[symbol] = f
                return f
    except Exception as e:
        logger.warning(f"Could not fetch lot size for {symbol}: {e}")
    return {"minQty": "0.00001", "stepSize": "0.00001"}


def _round_step(quantity: float, step_size: str) -> float:
    step = float(step_size)
    precision = max(0, -int(math.floor(math.log10(step))))
    return round(math.floor(quantity / step) * step, precision)


async def place_order(
    symbol: str,
    side: str,          # "BUY" or "SELL"
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    patterns: list,
    ai_score: int,
    ai_reasoning: str,
) -> Optional[int]:
    """Place a market order on Binance and register the trade."""
    client = _get_client()

    quantity = calculate_position_size(entry_price, stop_loss)
    if quantity <= 0:
        logger.warning(f"Invalid quantity for {symbol}, skipping order.")
        return None

    # Round to Binance lot size rules
    lot = _get_lot_size(client, symbol)
    quantity = _round_step(quantity, lot["stepSize"])
    if quantity < float(lot["minQty"]):
        logger.warning(f"Quantity {quantity} below minQty {lot['minQty']} for {symbol}, skipping.")
        return None

    fill_price = entry_price
    order_id = None

    try:
        # Place market order
        order = client.create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )
        fill_price = float(order["fills"][0]["price"]) if order.get("fills") else entry_price
        order_id = order["orderId"]
        logger.info(f"Order placed: {side} {quantity} {symbol} @ {fill_price} | OrderID: {order_id}")
    except BinanceAPIException as e:
        logger.warning(f"Binance order error ({e}) — recording as paper trade @ {fill_price}")

    # Always log to DB (paper trading fallback)
    trade_id = await open_trade(
        symbol=symbol,
        side=side,
        entry_price=fill_price,
        quantity=quantity,
        stop_loss=stop_loss,
        take_profit=take_profit,
        patterns=patterns,
        ai_score=ai_score,
        ai_reasoning=ai_reasoning,
    )

    _active_trades[trade_id] = {
        "symbol": symbol,
        "side": side,
        "entry": fill_price,
        "sl": stop_loss,
        "tp": take_profit,
        "quantity": quantity,
        "order_id": order_id,
    }

    on_trade_opened()
    return trade_id


async def close_order(trade_id: int, exit_price: float, reason: str = ""):
    """Close an active trade with a market order."""
    if trade_id not in _active_trades:
        logger.warning(f"Trade #{trade_id} not found in active trades.")
        return

    trade = _active_trades[trade_id]
    client = _get_client()

    # Opposite side to close
    close_side = "SELL" if trade["side"] == "BUY" else "BUY"

    if trade["side"] == "BUY":
        pnl = (exit_price - trade["entry"]) * trade["quantity"]
    else:
        pnl = (trade["entry"] - exit_price) * trade["quantity"]

    try:
        client.create_order(
            symbol=trade["symbol"],
            side=close_side,
            type="MARKET",
            quantity=trade["quantity"],
        )
    except BinanceAPIException as e:
        logger.warning(f"Binance close order failed ({e}) — recording trade as paper close.")

    # Always record the close in DB regardless of Binance order result (paper trading)
    await close_trade(trade_id, exit_price, pnl)
    on_trade_closed(pnl)
    del _active_trades[trade_id]
    logger.info(f"Trade #{trade_id} closed. Reason: {reason} | PnL: {pnl:+.4f} USDT")


async def monitor_active_trades(current_prices: Dict[str, float]):
    """Check all active trades against current prices for SL/TP hits."""
    for trade_id, trade in list(_active_trades.items()):
        symbol = trade["symbol"]
        price = current_prices.get(symbol)
        if price is None:
            continue

        if trade["side"] == "BUY":
            if price <= trade["sl"]:
                await close_order(trade_id, price, reason="Stop Loss hit")
            elif price >= trade["tp"]:
                await close_order(trade_id, price, reason="Take Profit hit")
        else:  # SELL/SHORT
            if price >= trade["sl"]:
                await close_order(trade_id, price, reason="Stop Loss hit")
            elif price <= trade["tp"]:
                await close_order(trade_id, price, reason="Take Profit hit")


def get_active_trades() -> Dict:
    return dict(_active_trades)


async def reload_open_trades():
    """On startup, reload open trades from DB into memory so SL/TP monitoring resumes."""
    from bot.trade_logger import get_open_trades
    open_trades = await get_open_trades()
    for trade in open_trades:
        _active_trades[trade["id"]] = {
            "symbol": trade["symbol"],
            "side": trade["side"],
            "entry": trade["entry_price"],
            "sl": trade["stop_loss"],
            "tp": trade["take_profit"],
            "quantity": trade["quantity"],
            "order_id": None,
        }
    if open_trades:
        logger.info(f"Reloaded {len(open_trades)} open trade(s) from database into memory.")
