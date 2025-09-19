"""Indicator computation registry operating on plain Python sequences."""
from __future__ import annotations

from typing import Callable, Dict, List, Sequence

from app.data.providers import PriceBar

IndicatorFunc = Callable[[Sequence[PriceBar], Dict[str, float]], List[float]]


def _get_prices(bars: Sequence[PriceBar], field: str) -> List[float]:
    return [getattr(bar, field) for bar in bars]


def _rolling_mean(values: Sequence[float], window: int) -> List[float]:
    results: List[float] = []
    for i in range(len(values)):
        if i + 1 < window:
            results.append(float("nan"))
            continue
        window_slice = values[i + 1 - window : i + 1]
        results.append(sum(window_slice) / window)
    return results


def _ema(values: Sequence[float], window: int) -> List[float]:
    results: List[float] = []
    alpha = 2 / (window + 1)
    ema_value = None
    for value in values:
        if ema_value is None:
            ema_value = value
        else:
            ema_value = alpha * value + (1 - alpha) * ema_value
        results.append(ema_value)
    return results


def _std(values: Sequence[float], window: int) -> List[float]:
    results: List[float] = []
    for i in range(len(values)):
        if i + 1 < window:
            results.append(float("nan"))
            continue
        window_slice = values[i + 1 - window : i + 1]
        mean = sum(window_slice) / window
        variance = sum((x - mean) ** 2 for x in window_slice) / window
        results.append(variance**0.5)
    return results


def _true_range(bars: Sequence[PriceBar]) -> List[float]:
    results: List[float] = []
    prev_close = None
    for bar in bars:
        high_low = bar.high - bar.low
        if prev_close is None:
            tr = high_low
        else:
            high_close = abs(bar.high - prev_close)
            low_close = abs(bar.low - prev_close)
            tr = max(high_low, high_close, low_close)
        results.append(tr)
        prev_close = bar.close
    return results


def _sma(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    window = int(params.get("window", 14))
    closes = _get_prices(bars, "close")
    return _rolling_mean(closes, window)


def _ema_indicator(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    window = int(params.get("window", 14))
    closes = _get_prices(bars, "close")
    ema_values = _ema(closes, window)
    return [float("nan") if i + 1 < window else v for i, v in enumerate(ema_values)]


def _rsi(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    window = int(params.get("window", 14))
    closes = _get_prices(bars, "close")
    gains: List[float] = [0.0]
    losses: List[float] = [0.0]
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = _ema(gains, window)
    avg_loss = _ema(losses, window)
    rsi_values: List[float] = []
    for i in range(len(closes)):
        if i + 1 < window:
            rsi_values.append(float("nan"))
            continue
        if avg_loss[i] == 0:
            rsi_values.append(100.0)
            continue
        rs = avg_gain[i] / avg_loss[i]
        rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values


def _atr(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    window = int(params.get("window", 14))
    tr = _true_range(bars)
    atr_raw = _ema(tr, window)
    return [float("nan") if i + 1 < window else value for i, value in enumerate(atr_raw)]


def _roc(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    window = int(params.get("window", 12))
    closes = _get_prices(bars, "close")
    results: List[float] = []
    for i, price in enumerate(closes):
        if i < window:
            results.append(float("nan"))
            continue
        prev = closes[i - window]
        results.append(((price - prev) / prev) * 100 if prev else float("nan"))
    return results


def _macd(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    fast = int(params.get("fast", 12))
    slow = int(params.get("slow", 26))
    closes = _get_prices(bars, "close")
    fast_ema = _ema(closes, fast)
    slow_ema = _ema(closes, slow)
    return [f - s for f, s in zip(fast_ema, slow_ema)]


def _bollinger_pct(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    window = int(params.get("window", 20))
    std_mult = float(params.get("std", 2.0))
    closes = _get_prices(bars, "close")
    sma = _rolling_mean(closes, window)
    std = _std(closes, window)
    pct: List[float] = []
    for i in range(len(closes)):
        if i + 1 < window:
            pct.append(float("nan"))
            continue
        upper = sma[i] + std_mult * std[i]
        lower = sma[i] - std_mult * std[i]
        pct.append((closes[i] - lower) / (upper - lower) if upper != lower else float("nan"))
    return pct


def _adx(bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    window = int(params.get("window", 14))
    plus_dm: List[float] = [0.0]
    minus_dm: List[float] = [0.0]
    tr = _true_range(bars)
    for i in range(1, len(bars)):
        up_move = bars[i].high - bars[i - 1].high
        down_move = bars[i - 1].low - bars[i].low
        plus_dm.append(max(up_move, 0.0) if up_move > down_move else 0.0)
        minus_dm.append(max(down_move, 0.0) if down_move > up_move else 0.0)
    plus_di_raw = _ema(plus_dm, window)
    minus_di_raw = _ema(minus_dm, window)
    adx_values: List[float] = []
    for i in range(len(bars)):
        if tr[i] == 0:
            adx_values.append(float("nan"))
            continue
        plus_di = 100 * plus_di_raw[i] / tr[i]
        minus_di = 100 * minus_di_raw[i] / tr[i]
        denom = plus_di + minus_di
        if denom == 0:
            adx_values.append(float("nan"))
        else:
            adx_values.append(abs(plus_di - minus_di) / denom * 100)
    return _ema(adx_values, window)


INDICATOR_REGISTRY: Dict[str, IndicatorFunc] = {
    "sma": _sma,
    "ema": _ema_indicator,
    "rsi": _rsi,
    "atr": _atr,
    "roc": _roc,
    "macd": _macd,
    "bollinger_pct": _bollinger_pct,
    "adx": _adx,
}


def compute_indicator(kind: str, bars: Sequence[PriceBar], params: Dict[str, float]) -> List[float]:
    try:
        func = INDICATOR_REGISTRY[kind]
    except KeyError as exc:
        msg = f"Unknown indicator kind: {kind}"
        raise KeyError(msg) from exc
    return func(bars, params)


__all__ = ["compute_indicator", "INDICATOR_REGISTRY"]
