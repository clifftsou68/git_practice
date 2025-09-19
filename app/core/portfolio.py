"""Portfolio and position management utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class Order:
    symbol: str
    quantity: float
    price: float
    side: str  # "buy" or "sell"
    reason: str = ""


@dataclass
class Position:
    symbol: str
    quantity: float
    avg_price: float
    stop_price: Optional[float] = None
    trailing_multiple: Optional[float] = None

    def market_value(self, last_price: float) -> float:
        return self.quantity * last_price

    def update_stop(self, new_stop: float) -> None:
        if self.stop_price is None or new_stop > self.stop_price:
            self.stop_price = new_stop


@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    equity_history: List[Tuple[object, float]] = field(default_factory=list)

    def position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)

    def add_position(self, order: Order) -> None:
        if order.side != "buy":
            msg = "Can only add positions from buy orders"
            raise ValueError(msg)
        existing = self.positions.get(order.symbol)
        if existing:
            total_qty = existing.quantity + order.quantity
            if total_qty <= 0:
                del self.positions[order.symbol]
                return
            new_avg = (
                existing.avg_price * existing.quantity + order.price * order.quantity
            ) / total_qty
            existing.quantity = total_qty
            existing.avg_price = new_avg
        else:
            self.positions[order.symbol] = Position(
                symbol=order.symbol,
                quantity=order.quantity,
                avg_price=order.price,
            )
        self.cash -= order.quantity * order.price

    def remove_position(self, order: Order) -> None:
        if order.side != "sell":
            msg = "Can only remove positions from sell orders"
            raise ValueError(msg)
        existing = self.positions.get(order.symbol)
        if not existing:
            return
        sell_qty = min(order.quantity, existing.quantity)
        existing.quantity -= sell_qty
        proceeds = sell_qty * order.price
        self.cash += proceeds
        if existing.quantity <= 0:
            del self.positions[order.symbol]

    def market_value(self, prices: Dict[str, float]) -> float:
        value = self.cash
        for symbol, position in self.positions.items():
            price = prices.get(symbol)
            if price is None:
                continue
            value += position.market_value(price)
        return value

    def update_equity(self, timestamp: object, value: float) -> None:
        self.equity_history.append((timestamp, value))

    def total_allocation(self) -> float:
        return sum(pos.quantity for pos in self.positions.values())

    def iter_positions(self) -> Iterable[Position]:
        return self.positions.values()


__all__ = ["Order", "Portfolio", "Position"]
