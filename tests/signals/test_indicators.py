from datetime import datetime, timedelta

from app.data.providers import PriceBar
from app.signals.indicators import compute_indicator


def _bars(values):
    start = datetime(2024, 1, 1)
    bars = []
    for i, value in enumerate(values):
        bars.append(
            PriceBar(
                timestamp=start + timedelta(days=i),
                open=float(value),
                high=float(value) + 1,
                low=float(value) - 1,
                close=float(value),
                volume=1_000_000,
            )
        )
    return bars


def test_sma_indicator() -> None:
    bars = _bars([1, 2, 3, 4, 5, 6])
    sma = compute_indicator("sma", bars, {"window": 3})
    assert round(sma[-1], 2) == 5.0


def test_rsi_indicator() -> None:
    bars = _bars([1, 2, 3, 2, 3, 4, 5, 6])
    rsi = compute_indicator("rsi", bars, {"window": 2})
    assert 0 <= rsi[-1] <= 100
