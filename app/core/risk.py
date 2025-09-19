"""Risk management helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskParameters:
    max_positions: int
    max_gross_exposure: float
    max_position_pct: float


def position_size_vol_target(
    equity: float,
    price: float,
    atr: float,
    risk_per_trade: float,
    atr_multiple: float,
) -> float:
    if price <= 0 or atr <= 0:
        return 0.0
    dollar_risk = equity * risk_per_trade
    stop_distance = atr * atr_multiple
    if stop_distance <= 0:
        return 0.0
    shares = dollar_risk / stop_distance
    return max(shares, 0.0)


def apply_position_limits(
    desired_qty: float,
    price: float,
    equity: float,
    params: RiskParameters,
    current_positions: int,
    gross_exposure: float,
) -> float:
    if params.max_positions and current_positions >= params.max_positions:
        return 0.0
    if equity <= 0:
        return 0.0
    max_position_value = equity * params.max_position_pct
    desired_value = desired_qty * price
    if desired_value > max_position_value:
        desired_qty = max_position_value / price
    projected_exposure = gross_exposure + abs(desired_qty * price) / equity
    if projected_exposure > params.max_gross_exposure:
        allowed_value = max(params.max_gross_exposure - gross_exposure, 0) * equity
        desired_qty = allowed_value / price
    return max(desired_qty, 0.0)


def stop_from_atr(entry_price: float, atr: float, multiple: float, direction: str) -> Optional[float]:
    if atr <= 0:
        return None
    if direction == "long":
        return entry_price - atr * multiple
    if direction == "short":
        return entry_price + atr * multiple
    return None


__all__ = [
    "RiskParameters",
    "apply_position_limits",
    "position_size_vol_target",
    "stop_from_atr",
]
