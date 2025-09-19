"""Market data provider abstractions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class PriceBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class DataProvider:
    """Interface for price and fundamentals data."""

    def get_price_history(
        self,
        symbols: Iterable[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, List[PriceBar]]:
        raise NotImplementedError


@dataclass
class CSVPriceProvider(DataProvider):
    """Loads OHLCV data from CSV files in ``root``.

    Files must be named ``<symbol>.csv`` with OHLCV columns.
    """

    root: Path

    def _read_symbol(self, symbol: str) -> List[PriceBar]:
        path = self.root / f"{symbol}.csv"
        if not path.exists():
            return []
        rows: List[PriceBar] = []
        with path.open("r", encoding="utf-8") as handle:
            next(handle)  # skip header
            for line in handle:
                if not line.strip():
                    continue
                date_str, open_, high, low, close, volume = line.strip().split(",")
                rows.append(
                    PriceBar(
                        timestamp=datetime.fromisoformat(date_str),
                        open=float(open_),
                        high=float(high),
                        low=float(low),
                        close=float(close),
                        volume=float(volume),
                    )
                )
        rows.sort(key=lambda bar: bar.timestamp)
        return rows

    def get_price_history(
        self,
        symbols: Iterable[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, List[PriceBar]]:
        data: Dict[str, List[PriceBar]] = {}
        for symbol in symbols:
            series = self._read_symbol(symbol)
            if start is not None:
                series = [bar for bar in series if bar.timestamp >= start]
            if end is not None:
                series = [bar for bar in series if bar.timestamp <= end]
            data[symbol] = series
        return data

    def average_dollar_volume(self, symbol: str, window: int = 20) -> Optional[float]:
        history = self._read_symbol(symbol)
        if not history:
            return None
        window = min(window, len(history))
        subset = history[-window:]
        return sum(bar.close * bar.volume for bar in subset) / window


__all__ = ["CSVPriceProvider", "DataProvider", "PriceBar"]
