"""Performance metrics for backtests using built-in Python types."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple


ANNUALIZATION = {"1D": 252, "1H": 252 * 6.5}


@dataclass
class TradeRecord:
    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    holding_period: int


@dataclass
class BacktestMetrics:
    cagr: float
    volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    hit_rate: float
    profit_factor: float
    expectancy: float
    avg_win: float
    avg_loss: float
    avg_hold_days: float
    turnover: float
    exposure: float
    num_trades: int
    best_month: Optional[float]
    worst_month: Optional[float]
    monthly_returns: Dict[str, float]
    equity_curve: List[Tuple[datetime, float]]
    drawdown: List[Tuple[datetime, float]]


def _annual_factor(frequency: str) -> float:
    return ANNUALIZATION.get(frequency, 252)


def _pct_changes(values: Sequence[float]) -> List[float]:
    returns: List[float] = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if prev == 0:
            returns.append(0.0)
        else:
            returns.append((curr - prev) / prev)
    return returns


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance**0.5


def compute_metrics(
    equity_curve: List[Tuple[datetime, float]],
    trades: List[TradeRecord],
    frequency: str,
) -> BacktestMetrics:
    if len(equity_curve) < 2:
        raise ValueError("Equity curve must contain at least two observations")

    timestamps = [ts for ts, _ in equity_curve]
    values = [value for _, value in equity_curve]
    returns = _pct_changes(values)
    downside = [r for r in returns if r < 0]
    ann_factor = _annual_factor(frequency)

    total_return = values[-1] / values[0] - 1
    years = len(values) / ann_factor
    years = max(years, 1e-9)
    cagr = (1 + total_return) ** (1 / years) - 1
    volatility = _std(returns) * (ann_factor**0.5)
    sharpe = (_mean(returns) * ann_factor) / volatility if volatility else 0.0
    downside_std = _std(downside) * (ann_factor**0.5) if downside else 0.0
    sortino = (_mean(returns) * ann_factor) / downside_std if downside_std else 0.0

    equity_roll_max = []
    running_max = values[0]
    for value in values:
        running_max = max(running_max, value)
        equity_roll_max.append(running_max)
    drawdown = []
    max_drawdown = 0.0
    for ts, value, peak in zip(timestamps, values, equity_roll_max):
        dd = value / peak - 1 if peak else 0.0
        drawdown.append((ts, dd))
        max_drawdown = min(max_drawdown, dd)
    calmar = (_mean(returns) * ann_factor) / abs(max_drawdown) if max_drawdown != 0 else 0.0

    pnl_array = [trade.pnl for trade in trades]
    wins = [p for p in pnl_array if p > 0]
    losses = [p for p in pnl_array if p < 0]
    hit_rate = len(wins) / len(trades) if trades else 0.0
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else float("inf")
    expectancy = _mean(pnl_array) if pnl_array else 0.0
    avg_win = _mean(wins) if wins else 0.0
    avg_loss = _mean(losses) if losses else 0.0
    avg_hold_days = _mean([trade.holding_period for trade in trades]) if trades else 0.0

    turnover = sum(abs(trade.quantity) * trade.entry_price for trade in trades)
    exposure = (
        sum(abs(trade.quantity) * trade.entry_price for trade in trades) / values[0]
        if trades and values[0]
        else 0.0
    )

    monthly_returns: Dict[str, float] = {}
    month_groups: Dict[str, List[float]] = {}
    for i in range(1, len(values)):
        month_key = timestamps[i].strftime("%Y-%m")
        month_groups.setdefault(month_key, []).append(returns[i - 1])
    for month, month_rets in month_groups.items():
        compounded = 1.0
        for ret in month_rets:
            compounded *= 1 + ret
        monthly_returns[month] = compounded - 1
    best_month = max(monthly_returns.values()) if monthly_returns else None
    worst_month = min(monthly_returns.values()) if monthly_returns else None

    return BacktestMetrics(
        cagr=cagr,
        volatility=volatility,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_drawdown,
        calmar=calmar,
        hit_rate=hit_rate,
        profit_factor=profit_factor,
        expectancy=expectancy,
        avg_win=avg_win,
        avg_loss=avg_loss,
        avg_hold_days=avg_hold_days,
        turnover=turnover,
        exposure=exposure,
        num_trades=len(trades),
        best_month=best_month,
        worst_month=worst_month,
        monthly_returns=monthly_returns,
        equity_curve=equity_curve,
        drawdown=drawdown,
    )


__all__ = ["BacktestMetrics", "TradeRecord", "compute_metrics"]
