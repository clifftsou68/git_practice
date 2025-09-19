"""Lightweight backtest engine using pure Python data structures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import isnan
from typing import Any, Dict, Iterable, List

from app.config.models import BacktestConfig, IndicatorConfig, PortfolioLimits, RulesConfig, SizingConfig
from app.core.portfolio import Order, Portfolio
from app.core.risk import (
    RiskParameters,
    apply_position_limits,
    position_size_vol_target,
    stop_from_atr,
)
from app.data.providers import DataProvider
from app.signals.pipeline import compute_indicator_frame, generate_signals

from .metrics import BacktestMetrics, TradeRecord, compute_metrics


@dataclass
class BacktestResult:
    strategy_name: str
    metrics: BacktestMetrics
    trades: List[TradeRecord]
    orders: List[Order]


@dataclass
class EngineConfig:
    initial_equity: float = 100_000.0


@dataclass
class BacktestEngine:
    data_provider: DataProvider
    engine_config: EngineConfig = field(default_factory=EngineConfig)

    def run(
        self,
        strategy_name: str,
        symbols: Iterable[str],
        indicator_configs: List[IndicatorConfig],
        rules: RulesConfig,
        sizing: SizingConfig,
        portfolio_limits: PortfolioLimits,
        backtest_config: BacktestConfig,
    ) -> BacktestResult:
        start_dt = datetime.combine(backtest_config.start, datetime.min.time())
        end_dt = datetime.combine(backtest_config.end, datetime.min.time())
        price_history = self.data_provider.get_price_history(
            symbols,
            start=start_dt,
            end=end_dt,
        )
        portfolio = Portfolio(cash=self.engine_config.initial_equity)
        risk_params = RiskParameters(
            max_positions=portfolio_limits.max_positions,
            max_gross_exposure=portfolio_limits.max_gross_exposure,
            max_position_pct=portfolio_limits.max_position_pct,
        )
        trades: List[TradeRecord] = []
        orders: List[Order] = []

        indicator_maps: Dict[str, Dict[Any, Dict[str, float]]] = {}
        signal_maps: Dict[str, Dict[Any, Dict[str, Any]]] = {}
        for symbol, series in price_history.items():
            indicator_rows = compute_indicator_frame(series, indicator_configs)
            signal_rows = generate_signals(series, indicator_rows, rules)
            indicator_maps[symbol] = {
                bar.timestamp: indicator_rows[idx] for idx, bar in enumerate(series)
            }
            signal_maps[symbol] = {
                bar.timestamp: signal_rows[idx] for idx, bar in enumerate(series)
            }

        all_dates = sorted({bar.timestamp for series in price_history.values() for bar in series})
        open_positions: Dict[str, Dict[str, Any]] = {}

        for timestamp in all_dates:
            price_snapshot: Dict[str, float] = {}
            for symbol, series in price_history.items():
                bar = next((b for b in series if b.timestamp == timestamp), None)
                if bar:
                    price_snapshot[symbol] = bar.close
            equity = portfolio.market_value(price_snapshot)
            portfolio.update_equity(timestamp, equity)

            for symbol, series in price_history.items():
                bar = next((b for b in series if b.timestamp == timestamp), None)
                if not bar:
                    continue
                indicator_row = indicator_maps[symbol][timestamp]
                signal_row = signal_maps[symbol][timestamp]

                if any(isinstance(value, float) and isnan(value) for value in indicator_row.values()):
                    continue

                position = portfolio.position(symbol)
                if position:
                    stop_price = position.stop_price
                    qty_held = position.quantity
                    if stop_price is not None and bar.low <= stop_price:
                        order = Order(
                            symbol=symbol,
                            quantity=qty_held,
                            price=stop_price,
                            side="sell",
                            reason="stop",
                        )
                        portfolio.remove_position(order)
                        orders.append(order)
                        entry_info = open_positions[symbol]
                        trades.append(
                            TradeRecord(
                                symbol=symbol,
                                entry_date=entry_info["entry_date"],
                                exit_date=timestamp,
                                entry_price=entry_info["entry_price"],
                                exit_price=stop_price,
                                quantity=qty_held,
                                pnl=(stop_price - entry_info["entry_price"]) * qty_held,
                                return_pct=(stop_price / entry_info["entry_price"]) - 1,
                                holding_period=(timestamp - entry_info["entry_date"]).days,
                            )
                        )
                        del open_positions[symbol]
                        continue

                    trailing_stop = signal_row.get("trailing_stop")
                    if isinstance(trailing_stop, float) and not isnan(trailing_stop):
                        position.update_stop(trailing_stop)

                    exit_reasons = signal_row.get("exit_reasons", [])
                    if exit_reasons:
                        price = bar.close
                        order = Order(
                            symbol=symbol,
                            quantity=qty_held,
                            price=price,
                            side="sell",
                            reason=",".join(exit_reasons),
                        )
                        portfolio.remove_position(order)
                        orders.append(order)
                        entry_info = open_positions[symbol]
                        trades.append(
                            TradeRecord(
                                symbol=symbol,
                                entry_date=entry_info["entry_date"],
                                exit_date=timestamp,
                                entry_price=entry_info["entry_price"],
                                exit_price=price,
                                quantity=qty_held,
                                pnl=(price - entry_info["entry_price"]) * qty_held,
                                return_pct=(price / entry_info["entry_price"]) - 1,
                                holding_period=(timestamp - entry_info["entry_date"]).days,
                            )
                        )
                        del open_positions[symbol]
                        continue

                if not signal_row.get("entry") or position:
                    continue

                price = bar.close
                atr_value = None
                for key in ("atr14", "atr", "atr_14"):
                    candidate = indicator_row.get(key)
                    if isinstance(candidate, float) and not isnan(candidate):
                        atr_value = candidate
                        break
                if atr_value is None or atr_value <= 0:
                    continue

                if sizing.type == "vol_target":
                    qty = position_size_vol_target(
                        equity=equity,
                        price=price,
                        atr=float(atr_value),
                        risk_per_trade=float(sizing.params.get("risk_per_trade", 0.01)),
                        atr_multiple=float(sizing.params.get("atr_multiple", 2.0)),
                    )
                elif sizing.type == "fixed":
                    qty = float(sizing.params.get("shares", 0))
                else:
                    qty = 0.0

                if equity > 0:
                    gross_exposure = sum(
                        abs(pos.quantity * price_snapshot.get(sym, price))
                        for sym, pos in portfolio.positions.items()
                    ) / equity
                else:
                    gross_exposure = 0.0

                qty = apply_position_limits(
                    desired_qty=qty,
                    price=price,
                    equity=equity,
                    params=risk_params,
                    current_positions=len(portfolio.positions),
                    gross_exposure=gross_exposure,
                )
                if qty <= 0:
                    continue

                order = Order(symbol=symbol, quantity=qty, price=price, side="buy", reason="entry")
                portfolio.add_position(order)
                orders.append(order)
                stop_multiple = float(sizing.params.get("atr_multiple", 2.0))
                stop_price = stop_from_atr(price, float(atr_value), stop_multiple, direction="long")
                open_positions[symbol] = {
                    "entry_date": timestamp,
                    "entry_price": price,
                }
                position = portfolio.position(symbol)
                if position and stop_price:
                    position.stop_price = stop_price

        equity_curve = portfolio.equity_history
        metrics = compute_metrics(equity_curve, trades, backtest_config.frequency)
        return BacktestResult(
            strategy_name=strategy_name,
            metrics=metrics,
            trades=trades,
            orders=orders,
        )


__all__ = ["BacktestEngine", "BacktestResult", "EngineConfig"]
