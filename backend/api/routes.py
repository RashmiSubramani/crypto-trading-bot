from fastapi import APIRouter
from bot.trade_logger import get_trade_history, get_open_trades, get_daily_pnl_summary, get_signal_history
from bot.risk_controller import get_state
from bot.engine import latest_analysis, current_prices
from bot.order_manager import get_active_trades

router = APIRouter()


@router.get("/status")
async def get_status():
    risk = get_state()
    return {
        "bot_running": True,
        "testnet": True,
        "risk": risk,
        "current_prices": current_prices,
    }


@router.get("/analysis")
async def get_analysis():
    return {"data": list(latest_analysis.values())}


@router.get("/trades/open")
async def open_trades():
    return {"data": await get_open_trades()}


@router.get("/trades/history")
async def trade_history():
    return {"data": await get_trade_history(50)}


@router.get("/trades/summary")
async def daily_summary():
    return {"data": await get_daily_pnl_summary()}


@router.get("/active")
async def active_positions():
    return {"data": get_active_trades()}


@router.get("/signals/history")
async def signal_history():
    return {"data": await get_signal_history(100)}


@router.get("/scanner/pairs")
async def active_pairs():
    from bot.data_feed import _active_pairs
    return {"data": _active_pairs, "count": len(_active_pairs)}
