"""
Trade Logger — SQLite persistence for all trades and signals.
"""

import aiosqlite
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
DB_PATH = "trades.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL,
                exit_price REAL,
                quantity REAL,
                stop_loss REAL,
                take_profit REAL,
                pnl REAL,
                status TEXT DEFAULT 'open',
                patterns TEXT,
                ai_score INTEGER,
                ai_reasoning TEXT,
                opened_at TEXT,
                closed_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT,
                patterns TEXT,
                ai_score INTEGER,
                direction TEXT,
                acted_on INTEGER DEFAULT 0,
                skip_reason TEXT,
                detected_at TEXT
            )
        """)
        await db.commit()
    logger.info("Database initialized.")


async def log_signal(
    symbol: str, timeframe: str, patterns: List[str],
    ai_score: int, direction: str, acted_on: bool, skip_reason: str = ""
):
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute(
            """INSERT INTO signals (symbol, timeframe, patterns, ai_score, direction, acted_on, skip_reason, detected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (symbol, timeframe, ", ".join(patterns), ai_score, direction,
             1 if acted_on else 0, skip_reason, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()


async def open_trade(
    symbol: str, side: str, entry_price: float, quantity: float,
    stop_loss: float, take_profit: float, patterns: List[str],
    ai_score: int, ai_reasoning: str
) -> int:
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        cursor = await db.execute(
            """INSERT INTO trades (symbol, side, entry_price, quantity, stop_loss, take_profit,
               patterns, ai_score, ai_reasoning, status, opened_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)""",
            (symbol, side, entry_price, quantity, stop_loss, take_profit,
             ", ".join(patterns), ai_score, ai_reasoning, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()
        trade_id = cursor.lastrowid
        logger.info(f"Trade #{trade_id} opened: {side} {symbol} @ {entry_price}")
        return trade_id


async def close_trade(trade_id: int, exit_price: float, pnl: float):
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute(
            """UPDATE trades SET exit_price=?, pnl=?, status='closed', closed_at=?
               WHERE id=?""",
            (exit_price, pnl, datetime.now(timezone.utc).isoformat(), trade_id)
        )
        await db.commit()
        logger.info(f"Trade #{trade_id} closed @ {exit_price} | PnL: {pnl:+.4f}")


async def get_open_trades() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM trades WHERE status='open' ORDER BY opened_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_trade_history(limit: int = 50) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trades ORDER BY opened_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_signal_history(limit: int = 100) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM signals ORDER BY detected_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_daily_pnl_summary() -> Dict:
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        db.row_factory = aiosqlite.Row
        today = datetime.now(timezone.utc).date().isoformat()
        async with db.execute(
            """SELECT COUNT(*) as total, SUM(pnl) as total_pnl,
               SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses
               FROM trades WHERE status='closed' AND date(opened_at)=?""",
            (today,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {"total": 0, "total_pnl": 0, "wins": 0, "losses": 0}
