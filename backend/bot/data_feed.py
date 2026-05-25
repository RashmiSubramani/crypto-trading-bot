import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import pandas as pd
import websockets
from binance.client import Client
from binance.exceptions import BinanceAPIException

from config import (
    BINANCE_API_KEY,
    BINANCE_SECRET_KEY,
    BINANCE_WS_URL,
    TESTNET,
    PRIMARY_TIMEFRAME,
    TREND_TIMEFRAME,
    TRADING_PAIRS,
)

logger = logging.getLogger(__name__)

# In-memory candle store: { "BTCUSDT_15m": DataFrame, ... }
candle_store: Dict[str, pd.DataFrame] = {}
_callbacks: List[Callable] = []
_stream_tasks: List[asyncio.Task] = []
_active_pairs: List[str] = []


def get_binance_client() -> Client:
    client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY, testnet=TESTNET)
    return client


def fetch_historical_candles(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    """Fetch historical OHLCV candles from Binance REST API."""
    client = get_binance_client()
    try:
        raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = _parse_candles(raw)
        key = f"{symbol}_{interval}"
        candle_store[key] = df
        logger.info(f"Fetched {len(df)} historical candles for {symbol} {interval}")
        return df
    except BinanceAPIException as e:
        logger.error(f"Binance API error fetching {symbol}: {e}")
        return pd.DataFrame()


def _parse_candles(raw: list) -> pd.DataFrame:
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df = df[["open_time", "open", "high", "low", "close", "volume", "close_time", "trades"]]
    df.set_index("open_time", inplace=True)
    return df


def register_callback(fn: Callable):
    """Register a function to be called whenever a new candle closes."""
    _callbacks.append(fn)


def get_candles(symbol: str, interval: str) -> Optional[pd.DataFrame]:
    return candle_store.get(f"{symbol}_{interval}")


async def _handle_kline_message(symbol: str, interval: str, msg: dict):
    kline = msg.get("k", {})
    is_closed = kline.get("x", False)

    # Update live price on every tick (not just candle close)
    from bot.engine import current_prices
    current_prices[symbol] = float(kline["c"])

    candle = {
        "open": float(kline["o"]),
        "high": float(kline["h"]),
        "low": float(kline["l"]),
        "close": float(kline["c"]),
        "volume": float(kline["v"]),
        "close_time": pd.to_datetime(kline["T"], unit="ms", utc=True),
        "trades": int(kline["n"]),
    }
    open_time = pd.to_datetime(kline["t"], unit="ms", utc=True)
    key = f"{symbol}_{interval}"

    if key not in candle_store or candle_store[key].empty:
        fetch_historical_candles(symbol, interval)

    df = candle_store.get(key, pd.DataFrame())

    # Update the last (live) candle
    new_row = pd.DataFrame([candle], index=[open_time])
    new_row.index.name = "open_time"

    if open_time in df.index:
        df.loc[open_time] = new_row.iloc[0]
    else:
        df = pd.concat([df, new_row])

    # Keep last 500 candles
    candle_store[key] = df.tail(500)

    # Fire callbacks only on closed candles
    if is_closed:
        logger.info(f"Candle closed: {symbol} {interval} @ {open_time}")
        for cb in _callbacks:
            try:
                await cb(symbol, interval, candle_store[key].copy())
            except Exception as e:
                logger.error(f"Callback error: {e}")


async def _stream_symbol(symbol: str, interval: str):
    stream = f"{symbol.lower()}@kline_{interval}"
    url = f"{BINANCE_WS_URL}/{stream}"
    logger.info(f"Connecting WebSocket: {url}")

    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                logger.info(f"WebSocket connected: {symbol} {interval}")
                async for raw_msg in ws:
                    msg = json.loads(raw_msg)
                    await _handle_kline_message(symbol, interval, msg)
        except Exception as e:
            logger.error(f"WebSocket error ({symbol} {interval}): {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)


async def start_data_feed(pairs: List[str] = None):
    """Start WebSocket streams for all pairs and timeframes."""
    global _stream_tasks, _active_pairs

    if pairs is None:
        pairs = TRADING_PAIRS

    _active_pairs = pairs

    # Pre-load historical data
    for pair in pairs:
        for tf in [PRIMARY_TIMEFRAME, TREND_TIMEFRAME]:
            fetch_historical_candles(pair, tf)

    # Start live streams
    _stream_tasks = []
    for pair in pairs:
        for tf in [PRIMARY_TIMEFRAME, TREND_TIMEFRAME]:
            _stream_tasks.append(asyncio.create_task(_stream_symbol(pair, tf)))

    await asyncio.gather(*_stream_tasks)


async def restart_streams(new_pairs: List[str]):
    """Cancel existing streams and restart with new pairs."""
    global _stream_tasks, _active_pairs

    added = [p for p in new_pairs if p not in _active_pairs]
    removed = [p for p in _active_pairs if p not in new_pairs]

    if not added and not removed:
        logger.info("Pairs unchanged, no restart needed.")
        return

    logger.info(f"Updating pairs — Added: {added}, Removed: {removed}")

    # Cancel all existing tasks
    for task in _stream_tasks:
        task.cancel()
    _stream_tasks = []
    _active_pairs = new_pairs

    # Pre-load historical for new pairs
    for pair in added:
        for tf in [PRIMARY_TIMEFRAME, TREND_TIMEFRAME]:
            fetch_historical_candles(pair, tf)

    # Restart all streams
    for pair in new_pairs:
        for tf in [PRIMARY_TIMEFRAME, TREND_TIMEFRAME]:
            _stream_tasks.append(asyncio.create_task(_stream_symbol(pair, tf)))

    logger.info(f"Streams restarted for {len(new_pairs)} pairs.")
