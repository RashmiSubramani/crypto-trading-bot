import asyncio
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.websocket import ws_endpoint
from bot.data_feed import start_data_feed, register_callback, restart_streams
from bot.engine import on_candle_closed
from bot.trade_logger import init_db, get_daily_pnl_summary, get_open_trades
from bot.order_manager import reload_open_trades
from bot.risk_controller import init_daily_state
from bot.market_scanner import get_top_coins, get_top_volatile_coins
from config import AUTO_SCAN, AUTO_SCAN_COUNT, AUTO_SCAN_MODE, TRADING_PAIRS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Trading Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.add_api_websocket_route("/ws", ws_endpoint)


def _resolve_pairs() -> list:
    if not AUTO_SCAN:
        logger.info(f"Auto-scan disabled. Using config pairs: {TRADING_PAIRS}")
        return TRADING_PAIRS
    if AUTO_SCAN_MODE == "volatile":
        pairs = get_top_volatile_coins(AUTO_SCAN_COUNT)
    else:
        pairs = get_top_coins(AUTO_SCAN_COUNT)
    return pairs


async def _refresh_pairs_loop():
    """Re-scan top coins every hour and restart streams if list changed."""
    while True:
        await asyncio.sleep(3600)  # wait 1 hour
        if not AUTO_SCAN:
            continue
        logger.info("Refreshing top coins list...")
        new_pairs = _resolve_pairs()
        await restart_streams(new_pairs)


@app.on_event("startup")
async def startup():
    logger.info("Starting Crypto Trading Bot...")
    await init_db()

    # Restore today's PnL and open trade count from DB (fixes PnL bug on restart)
    summary = await get_daily_pnl_summary()
    open_db = await get_open_trades()
    init_daily_state(
        daily_pnl=float(summary.get("total_pnl") or 0.0),
        open_trades=len(open_db),
    )

    await reload_open_trades()
    register_callback(on_candle_closed)

    pairs = _resolve_pairs()
    logger.info(f"Scanning {len(pairs)} coins: {pairs}")

    asyncio.create_task(start_data_feed(pairs))
    asyncio.create_task(_refresh_pairs_loop())
    logger.info("Bot running. Listening for market data...")


@app.get("/")
async def root():
    return {"status": "running", "message": "Crypto Trading Bot API"}
