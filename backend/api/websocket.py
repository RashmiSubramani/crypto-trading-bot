import asyncio
import json
import logging
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from bot.engine import latest_analysis, current_prices
from bot.risk_controller import get_state
from bot.trade_logger import get_daily_pnl_summary, get_alltime_pnl_summary, get_trade_history, get_signal_history
from bot.order_manager import get_active_trades

logger = logging.getLogger(__name__)
_connections: list[WebSocket] = []


async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _connections.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_connections)}")
    try:
        while True:
            summary = await get_daily_pnl_summary()
            alltime = await get_alltime_pnl_summary()
            history = await get_trade_history(20)
            signals = await get_signal_history(100)
            payload = {
                "type": "update",
                "prices": current_prices,
                "analysis": list(latest_analysis.values()),
                "active_trades": list(get_active_trades().values()),
                "risk": get_state(),
                "daily_summary": summary,
                "alltime_summary": alltime,
                "recent_trades": history,
                "signal_history": signals,
            }
            await websocket.send_text(json.dumps(payload, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o) if isinstance(o, (np.floating, np.integer)) else str(o)))
            await asyncio.sleep(2)  # Push update every 2 seconds
    except WebSocketDisconnect:
        _connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in _connections:
            _connections.remove(websocket)
