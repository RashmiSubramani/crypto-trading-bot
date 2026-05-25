"""
Market Scanner — Auto-discovers top coins by volume from Binance.
Replaces static TRADING_PAIRS with dynamic top N coins.
Filters out stablecoins, leveraged tokens, and low-volume pairs.
"""

import logging
from typing import List
from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_SECRET_KEY, TESTNET, TRADING_PAIRS

logger = logging.getLogger(__name__)

# Tokens to always exclude
STABLECOINS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "FDUSD"}
EXCLUDED_KEYWORDS = ["UP", "DOWN", "BULL", "BEAR", "3L", "3S", "2L", "2S"]  # leveraged tokens


def _is_valid_pair(symbol: str) -> bool:
    """Filter out stablecoins and leveraged tokens."""
    if not symbol.endswith("USDT"):
        return False
    base = symbol.replace("USDT", "")
    if base in STABLECOINS:
        return False
    if any(kw in base for kw in EXCLUDED_KEYWORDS):
        return False
    return True


def get_top_coins(n: int = 20) -> List[str]:
    """
    Fetch top N USDT pairs by 24h quote volume from Binance.
    Falls back to TRADING_PAIRS from config if API fails.
    """
    try:
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY, testnet=False)
        tickers = client.get_ticker()

        # Filter valid USDT pairs and sort by quote volume
        valid = [
            t for t in tickers
            if _is_valid_pair(t["symbol"]) and float(t.get("quoteVolume", 0)) > 0
        ]
        sorted_by_volume = sorted(valid, key=lambda x: float(x["quoteVolume"]), reverse=True)

        top = [t["symbol"] for t in sorted_by_volume[:n]]
        logger.info(f"Market scanner: Top {n} coins by volume: {top}")
        return top

    except Exception as e:
        logger.error(f"Market scanner failed: {e}. Falling back to config pairs.")
        return TRADING_PAIRS


def get_top_volatile_coins(n: int = 20) -> List[str]:
    """
    Fetch top N coins by price change % (most volatile = most opportunity).
    Only considers high-volume coins (top 100 by volume first).
    """
    try:
        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY, testnet=False)
        tickers = client.get_ticker()

        valid = [
            t for t in tickers
            if _is_valid_pair(t["symbol"]) and float(t.get("quoteVolume", 0)) > 10_000_000
        ]

        # Sort by absolute price change %
        sorted_by_volatility = sorted(
            valid,
            key=lambda x: abs(float(x.get("priceChangePercent", 0))),
            reverse=True
        )

        top = [t["symbol"] for t in sorted_by_volatility[:n]]
        logger.info(f"Market scanner (volatile): Top {n} coins: {top}")
        return top

    except Exception as e:
        logger.error(f"Market scanner (volatile) failed: {e}. Falling back to config pairs.")
        return TRADING_PAIRS
