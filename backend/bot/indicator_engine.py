"""
Technical Indicator Engine
Calculates RSI, MACD, EMA, Bollinger Bands, ATR, VWAP, Supertrend
Returns a flat dict of latest indicator values for signal analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0):
    middle = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, min_periods=period).mean()


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cumulative_tp_vol = (typical_price * df["volume"]).cumsum()
    cumulative_vol = df["volume"].cumsum()
    return cumulative_tp_vol / cumulative_vol.replace(0, np.nan)


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    atr = calculate_atr(df, period)
    hl2 = (df["high"] + df["low"]) / 2
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)  # 1=bullish, -1=bearish

    for i in range(1, len(df)):
        curr_close = df["close"].iloc[i]
        prev_close = df["close"].iloc[i - 1]
        curr_upper = upper_band.iloc[i]
        curr_lower = lower_band.iloc[i]
        prev_upper = upper_band.iloc[i - 1]
        prev_lower = lower_band.iloc[i - 1]

        # Adjust bands
        if curr_upper < prev_upper or prev_close > prev_upper:
            upper_band.iloc[i] = curr_upper
        else:
            upper_band.iloc[i] = prev_upper

        if curr_lower > prev_lower or prev_close < prev_lower:
            lower_band.iloc[i] = curr_lower
        else:
            lower_band.iloc[i] = prev_lower

        prev_dir = direction.iloc[i - 1] if i > 1 else 1
        if prev_dir == -1 and curr_close > upper_band.iloc[i]:
            direction.iloc[i] = 1
        elif prev_dir == 1 and curr_close < lower_band.iloc[i]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = prev_dir

        supertrend.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]

    return supertrend, direction


def detect_support_resistance(df: pd.DataFrame, lookback: int = 50) -> Dict[str, float]:
    """Find nearest support and resistance levels."""
    recent = df.tail(lookback)
    highs = recent["high"].values
    lows = recent["low"].values

    resistance = float(np.percentile(highs, 90))
    support = float(np.percentile(lows, 10))

    return {"support": round(support, 4), "resistance": round(resistance, 4)}


def get_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate all indicators and return latest values as a flat dict."""
    if len(df) < 30:
        return {}

    close = df["close"]
    indicators = {}

    # RSI
    rsi = calculate_rsi(close)
    indicators["rsi"] = round(float(rsi.iloc[-1]), 2)
    indicators["rsi_prev"] = round(float(rsi.iloc[-2]), 2)

    # MACD
    macd_line, signal_line, histogram = calculate_macd(close)
    indicators["macd"] = round(float(macd_line.iloc[-1]), 6)
    indicators["macd_signal"] = round(float(signal_line.iloc[-1]), 6)
    indicators["macd_hist"] = round(float(histogram.iloc[-1]), 6)
    indicators["macd_hist_prev"] = round(float(histogram.iloc[-2]), 6)
    indicators["macd_crossover"] = (
        "bullish" if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0
        else "bearish" if histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0
        else "none"
    )

    # EMAs
    for period in [9, 21, 50, 200]:
        ema = calculate_ema(close, period)
        indicators[f"ema_{period}"] = round(float(ema.iloc[-1]), 4)

    # EMA trend
    indicators["ema_trend"] = (
        "bullish" if indicators["ema_9"] > indicators["ema_21"] > indicators["ema_50"]
        else "bearish" if indicators["ema_9"] < indicators["ema_21"] < indicators["ema_50"]
        else "sideways"
    )

    # Bollinger Bands
    bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(close)
    indicators["bb_upper"] = round(float(bb_upper.iloc[-1]), 4)
    indicators["bb_mid"] = round(float(bb_mid.iloc[-1]), 4)
    indicators["bb_lower"] = round(float(bb_lower.iloc[-1]), 4)
    bb_width = bb_upper.iloc[-1] - bb_lower.iloc[-1]
    indicators["bb_position"] = round(
        (close.iloc[-1] - bb_lower.iloc[-1]) / bb_width if bb_width > 0 else 0.5, 3
    )  # 0=at lower, 1=at upper

    # ATR
    atr = calculate_atr(df)
    indicators["atr"] = round(float(atr.iloc[-1]), 4)

    # VWAP
    vwap = calculate_vwap(df)
    indicators["vwap"] = round(float(vwap.iloc[-1]), 4)
    indicators["price_vs_vwap"] = "above" if close.iloc[-1] > vwap.iloc[-1] else "below"

    # Supertrend
    st_val, st_dir = calculate_supertrend(df)
    indicators["supertrend"] = round(float(st_val.iloc[-1]), 4) if not pd.isna(st_val.iloc[-1]) else None
    indicators["supertrend_direction"] = "bullish" if st_dir.iloc[-1] == 1 else "bearish"

    # Volume analysis
    avg_vol = df["volume"].rolling(20).mean().iloc[-1]
    indicators["volume"] = round(float(df["volume"].iloc[-1]), 2)
    indicators["volume_avg"] = round(float(avg_vol), 2)
    indicators["volume_spike"] = df["volume"].iloc[-1] > avg_vol * 1.5

    # Support / Resistance
    sr = detect_support_resistance(df)
    indicators["support"] = sr["support"]
    indicators["resistance"] = sr["resistance"]
    indicators["current_price"] = round(float(close.iloc[-1]), 4)

    return indicators
