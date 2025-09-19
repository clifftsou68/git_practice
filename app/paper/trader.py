"""Paper trading loop for generating alerts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.config.models import StrategyConfig
from app.data.providers import DataProvider
from app.notify.channels import Alert, NotificationManager
from app.signals.pipeline import compute_indicator_frame, generate_signals


@dataclass
class PaperTradeEvent:
    symbol: str
    timestamp: str
    action: str
    price: float
    reason: str


class PaperTrader:
    def __init__(self, data_provider: DataProvider, notifier: NotificationManager):
        self.data_provider = data_provider
        self.notifier = notifier

    def evaluate_strategy(self, strategy: StrategyConfig) -> List[PaperTradeEvent]:
        start_dt = datetime.combine(strategy.backtest.start, datetime.min.time())
        end_dt = datetime.combine(strategy.backtest.end, datetime.min.time())
        history = self.data_provider.get_price_history(
            strategy.universe.symbols,
            start=start_dt,
            end=end_dt,
        )
        events: List[PaperTradeEvent] = []
        for symbol, series in history.items():
            if not series:
                continue
            indicators = compute_indicator_frame(series, strategy.indicators)
            signals = generate_signals(series, indicators, strategy.rules)
            latest = signals[-1]
            price = series[-1].close
            timestamp = series[-1].timestamp.isoformat()
            if latest["entry"]:
                reason = "Entry conditions satisfied"
                events.append(
                    PaperTradeEvent(
                        symbol=symbol,
                        timestamp=timestamp,
                        action="BUY",
                        price=price,
                        reason=reason,
                    )
                )
                self.notifier.dispatch(
                    Alert(
                        title=f"Buy Alert: {symbol}",
                        message=f"Price {price:.2f} met entry conditions",
                        level="info",
                    )
                )
            elif latest["exit_reasons"]:
                reason = ",".join(latest["exit_reasons"])
                events.append(
                    PaperTradeEvent(
                        symbol=symbol,
                        timestamp=timestamp,
                        action="SELL",
                        price=price,
                        reason=reason,
                    )
                )
                self.notifier.dispatch(
                    Alert(
                        title=f"Sell Alert: {symbol}",
                        message=f"Price {price:.2f} triggered exit {reason}",
                        level="warning",
                    )
                )
        return events


__all__ = ["PaperTrader", "PaperTradeEvent"]
