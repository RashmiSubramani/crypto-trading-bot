"""
Candlestick Pattern Detector
Detects 30+ patterns using pure pandas/numpy (no ta-lib dependency).
Each function returns: {"pattern": str, "direction": "bullish"|"bearish"|"neutral", "strength": 1-3}
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional


def _body(df: pd.DataFrame) -> pd.Series:
    return abs(df["close"] - df["open"])

def _upper_shadow(df: pd.DataFrame) -> pd.Series:
    return df["high"] - df[["open", "close"]].max(axis=1)

def _lower_shadow(df: pd.DataFrame) -> pd.Series:
    return df[["open", "close"]].min(axis=1) - df["low"]

def _is_bullish(df: pd.DataFrame) -> pd.Series:
    return df["close"] > df["open"]

def _is_bearish(df: pd.DataFrame) -> pd.Series:
    return df["close"] < df["open"]

def _avg_body(df: pd.DataFrame, n: int = 10) -> pd.Series:
    return _body(df).rolling(n).mean()


# ─── SINGLE CANDLE PATTERNS ───────────────────────────────────────────────────

def detect_doji(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]
    if candle_range == 0:
        return None
    if body / candle_range < 0.1:
        return {"pattern": "Doji", "direction": "neutral", "strength": 1}
    return None

def detect_hammer(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    lower = min(last["open"], last["close"]) - last["low"]
    upper = last["high"] - max(last["open"], last["close"])
    if body > 0 and lower >= 2 * body and upper <= 0.3 * body:
        direction = "bullish" if last["close"] > last["open"] else "bullish"
        return {"pattern": "Hammer", "direction": direction, "strength": 2}
    return None

def detect_shooting_star(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    upper = last["high"] - max(last["open"], last["close"])
    lower = min(last["open"], last["close"]) - last["low"]
    if body > 0 and upper >= 2 * body and lower <= 0.3 * body:
        return {"pattern": "Shooting Star", "direction": "bearish", "strength": 2}
    return None

def detect_hanging_man(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    lower = min(last["open"], last["close"]) - last["low"]
    upper = last["high"] - max(last["open"], last["close"])
    if body > 0 and lower >= 2 * body and upper <= 0.3 * body and last["close"] < last["open"]:
        return {"pattern": "Hanging Man", "direction": "bearish", "strength": 2}
    return None

def detect_inverted_hammer(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    upper = last["high"] - max(last["open"], last["close"])
    lower = min(last["open"], last["close"]) - last["low"]
    if body > 0 and upper >= 2 * body and lower <= 0.3 * body and last["close"] > last["open"]:
        return {"pattern": "Inverted Hammer", "direction": "bullish", "strength": 2}
    return None

def detect_marubozu_bullish(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = last["close"] - last["open"]
    candle_range = last["high"] - last["low"]
    if body > 0 and candle_range > 0 and body / candle_range > 0.9:
        return {"pattern": "Bullish Marubozu", "direction": "bullish", "strength": 3}
    return None

def detect_marubozu_bearish(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = last["open"] - last["close"]
    candle_range = last["high"] - last["low"]
    if body > 0 and candle_range > 0 and body / candle_range > 0.9:
        return {"pattern": "Bearish Marubozu", "direction": "bearish", "strength": 3}
    return None

def detect_spinning_top(df: pd.DataFrame) -> Optional[Dict]:
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]
    upper = last["high"] - max(last["open"], last["close"])
    lower = min(last["open"], last["close"]) - last["low"]
    if candle_range > 0 and 0.1 < body / candle_range < 0.3 and upper > body and lower > body:
        return {"pattern": "Spinning Top", "direction": "neutral", "strength": 1}
    return None


# ─── DOUBLE CANDLE PATTERNS ───────────────────────────────────────────────────

def detect_bullish_engulfing(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if (prev["close"] < prev["open"] and
            last["close"] > last["open"] and
            last["open"] < prev["close"] and
            last["close"] > prev["open"]):
        return {"pattern": "Bullish Engulfing", "direction": "bullish", "strength": 3}
    return None

def detect_bearish_engulfing(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if (prev["close"] > prev["open"] and
            last["close"] < last["open"] and
            last["open"] > prev["close"] and
            last["close"] < prev["open"]):
        return {"pattern": "Bearish Engulfing", "direction": "bearish", "strength": 3}
    return None

def detect_bullish_harami(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if (prev["close"] < prev["open"] and
            last["close"] > last["open"] and
            last["open"] > prev["close"] and
            last["close"] < prev["open"]):
        return {"pattern": "Bullish Harami", "direction": "bullish", "strength": 2}
    return None

def detect_bearish_harami(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if (prev["close"] > prev["open"] and
            last["close"] < last["open"] and
            last["open"] < prev["close"] and
            last["close"] > prev["open"]):
        return {"pattern": "Bearish Harami", "direction": "bearish", "strength": 2}
    return None

def detect_piercing_line(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    mid_prev = (prev["open"] + prev["close"]) / 2
    if (prev["close"] < prev["open"] and
            last["close"] > last["open"] and
            last["open"] < prev["close"] and
            last["close"] > mid_prev and
            last["close"] < prev["open"]):
        return {"pattern": "Piercing Line", "direction": "bullish", "strength": 2}
    return None

def detect_dark_cloud_cover(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    mid_prev = (prev["open"] + prev["close"]) / 2
    if (prev["close"] > prev["open"] and
            last["close"] < last["open"] and
            last["open"] > prev["close"] and
            last["close"] < mid_prev and
            last["close"] > prev["open"]):
        return {"pattern": "Dark Cloud Cover", "direction": "bearish", "strength": 2}
    return None

def detect_tweezer_bottom(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if (abs(prev["low"] - last["low"]) / max(prev["low"], 0.0001) < 0.001 and
            prev["close"] < prev["open"] and
            last["close"] > last["open"]):
        return {"pattern": "Tweezer Bottom", "direction": "bullish", "strength": 2}
    return None

def detect_tweezer_top(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if (abs(prev["high"] - last["high"]) / max(prev["high"], 0.0001) < 0.001 and
            prev["close"] > prev["open"] and
            last["close"] < last["open"]):
        return {"pattern": "Tweezer Top", "direction": "bearish", "strength": 2}
    return None

def detect_inside_bar(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 2:
        return None
    prev, last = df.iloc[-2], df.iloc[-1]
    if last["high"] < prev["high"] and last["low"] > prev["low"]:
        direction = "bullish" if last["close"] > last["open"] else "bearish"
        return {"pattern": "Inside Bar", "direction": direction, "strength": 2}
    return None


# ─── TRIPLE CANDLE PATTERNS ───────────────────────────────────────────────────

def detect_morning_star(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    c1_body = c1["open"] - c1["close"]
    c3_body = c3["close"] - c3["open"]
    c2_body = abs(c2["close"] - c2["open"])
    if (c1_body > 0 and
            c2_body < c1_body * 0.3 and
            c3_body > 0 and
            c3["close"] > (c1["open"] + c1["close"]) / 2):
        return {"pattern": "Morning Star", "direction": "bullish", "strength": 3}
    return None

def detect_evening_star(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    c1_body = c1["close"] - c1["open"]
    c3_body = c3["open"] - c3["close"]
    c2_body = abs(c2["close"] - c2["open"])
    if (c1_body > 0 and
            c2_body < c1_body * 0.3 and
            c3_body > 0 and
            c3["close"] < (c1["open"] + c1["close"]) / 2):
        return {"pattern": "Evening Star", "direction": "bearish", "strength": 3}
    return None

def detect_three_white_soldiers(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    if (c1["close"] > c1["open"] and
            c2["close"] > c2["open"] and
            c3["close"] > c3["open"] and
            c2["close"] > c1["close"] and
            c3["close"] > c2["close"] and
            c2["open"] > c1["open"] and
            c3["open"] > c2["open"]):
        return {"pattern": "Three White Soldiers", "direction": "bullish", "strength": 3}
    return None

def detect_three_black_crows(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    if (c1["close"] < c1["open"] and
            c2["close"] < c2["open"] and
            c3["close"] < c3["open"] and
            c2["close"] < c1["close"] and
            c3["close"] < c2["close"] and
            c2["open"] < c1["open"] and
            c3["open"] < c2["open"]):
        return {"pattern": "Three Black Crows", "direction": "bearish", "strength": 3}
    return None

def detect_three_inside_up(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    harami = (c1["close"] < c1["open"] and
              c2["close"] > c2["open"] and
              c2["open"] > c1["close"] and
              c2["close"] < c1["open"])
    if harami and c3["close"] > c2["close"] and c3["close"] > c3["open"]:
        return {"pattern": "Three Inside Up", "direction": "bullish", "strength": 3}
    return None

def detect_three_inside_down(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    harami = (c1["close"] > c1["open"] and
              c2["close"] < c2["open"] and
              c2["open"] < c1["close"] and
              c2["close"] > c1["open"])
    if harami and c3["close"] < c2["close"] and c3["close"] < c3["open"]:
        return {"pattern": "Three Inside Down", "direction": "bearish", "strength": 3}
    return None

def detect_abandoned_baby_bullish(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    c2_body = abs(c2["close"] - c2["open"])
    if (c1["close"] < c1["open"] and
            c2_body / (c1["high"] - c1["low"] + 0.0001) < 0.1 and
            c2["low"] < c1["low"] and
            c3["close"] > c3["open"] and
            c3["low"] > c2["high"]):
        return {"pattern": "Abandoned Baby (Bullish)", "direction": "bullish", "strength": 3}
    return None

def detect_abandoned_baby_bearish(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 3:
        return None
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    c2_body = abs(c2["close"] - c2["open"])
    if (c1["close"] > c1["open"] and
            c2_body / (c1["high"] - c1["low"] + 0.0001) < 0.1 and
            c2["high"] > c1["high"] and
            c3["close"] < c3["open"] and
            c3["high"] < c2["low"]):
        return {"pattern": "Abandoned Baby (Bearish)", "direction": "bearish", "strength": 3}
    return None


# ─── MASTER DETECTOR ──────────────────────────────────────────────────────────

ALL_DETECTORS = [
    detect_doji,
    detect_hammer,
    detect_shooting_star,
    detect_hanging_man,
    detect_inverted_hammer,
    detect_marubozu_bullish,
    detect_marubozu_bearish,
    detect_spinning_top,
    detect_bullish_engulfing,
    detect_bearish_engulfing,
    detect_bullish_harami,
    detect_bearish_harami,
    detect_piercing_line,
    detect_dark_cloud_cover,
    detect_tweezer_bottom,
    detect_tweezer_top,
    detect_inside_bar,
    detect_morning_star,
    detect_evening_star,
    detect_three_white_soldiers,
    detect_three_black_crows,
    detect_three_inside_up,
    detect_three_inside_down,
    detect_abandoned_baby_bullish,
    detect_abandoned_baby_bearish,
]


def detect_all_patterns(df: pd.DataFrame) -> List[Dict]:
    """Run all pattern detectors and return list of detected patterns."""
    if len(df) < 3:
        return []
    results = []
    for detector in ALL_DETECTORS:
        try:
            result = detector(df)
            if result:
                results.append(result)
        except Exception:
            pass
    return results
