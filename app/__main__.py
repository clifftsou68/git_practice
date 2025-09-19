"""CLI entry point for QuantDesk."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.backtest.engine import BacktestEngine, EngineConfig
from app.config.loader import load_strategy
from app.data.providers import CSVPriceProvider
from app.notify.channels import ConsoleChannel, NotificationManager
from app.paper.trader import PaperTrader


def run_backtest(strategy_path: Path, output_dir: Path) -> None:
    strategy = load_strategy(strategy_path)
    provider = CSVPriceProvider(root=Path("assets/sample_data"))
    engine = BacktestEngine(provider, EngineConfig(initial_equity=100_000))
    result = engine.run(
        strategy_name=strategy.name,
        symbols=strategy.universe.symbols,
        indicator_configs=strategy.indicators,
        rules=strategy.rules,
        sizing=strategy.sizing,
        portfolio_limits=strategy.portfolio,
        backtest_config=strategy.backtest,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = strategy.name.replace(" ", "_").lower()
    equity_path = output_dir / f"{base_name}_equity.csv"
    trades_path = output_dir / f"{base_name}_trades.csv"
    metrics_path = output_dir / f"{base_name}_metrics.json"

    with equity_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "equity"])
        for ts, value in result.metrics.equity_curve:
            writer.writerow([ts.isoformat(), value])

    with trades_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "symbol",
            "entry_date",
            "exit_date",
            "entry_price",
            "exit_price",
            "quantity",
            "pnl",
            "return_pct",
            "holding_period",
        ])
        for trade in result.trades:
            writer.writerow(
                [
                    trade.symbol,
                    trade.entry_date.isoformat(),
                    trade.exit_date.isoformat(),
                    trade.entry_price,
                    trade.exit_price,
                    trade.quantity,
                    trade.pnl,
                    trade.return_pct,
                    trade.holding_period,
                ]
            )

    metrics_payload = {
        "cagr": result.metrics.cagr,
        "volatility": result.metrics.volatility,
        "sharpe": result.metrics.sharpe,
        "sortino": result.metrics.sortino,
        "max_drawdown": result.metrics.max_drawdown,
        "calmar": result.metrics.calmar,
        "hit_rate": result.metrics.hit_rate,
        "profit_factor": result.metrics.profit_factor,
        "expectancy": result.metrics.expectancy,
        "avg_win": result.metrics.avg_win,
        "avg_loss": result.metrics.avg_loss,
        "avg_hold_days": result.metrics.avg_hold_days,
        "turnover": result.metrics.turnover,
        "exposure": result.metrics.exposure,
        "num_trades": result.metrics.num_trades,
        "best_month": result.metrics.best_month,
        "worst_month": result.metrics.worst_month,
        "monthly_returns": result.metrics.monthly_returns,
    }
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    print(f"Backtest complete. Equity curve saved to {equity_path}")
    print(f"Trades saved to {trades_path}")
    print(f"Metrics saved to {metrics_path}")


def run_paper(strategy_path: Path) -> None:
    strategy = load_strategy(strategy_path)
    provider = CSVPriceProvider(root=Path("assets/sample_data"))
    notifier = NotificationManager()
    notifier.register(ConsoleChannel())
    trader = PaperTrader(provider, notifier)
    events = trader.evaluate_strategy(strategy)
    for event in events:
        print(f"{event.timestamp} {event.symbol} {event.action} @ {event.price:.2f} ({event.reason})")
    if not events:
        print("No actionable signals at this time.")


def main() -> None:
    parser = argparse.ArgumentParser(description="QuantDesk CLI")
    parser.add_argument("command", choices=["gui", "backtest", "paper"], help="Action to perform")
    parser.add_argument("strategy", nargs="?", type=Path, help="Path to strategy YAML file")
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports"),
        help="Directory to write backtest reports",
    )
    args = parser.parse_args()

    if args.command == "gui":
        from app.ui.main_window import launch_main_window

        launch_main_window()
        return

    if not args.strategy:
        raise SystemExit("A strategy file must be provided for backtest and paper commands")

    if args.command == "backtest":
        run_backtest(args.strategy, args.report_dir)
    elif args.command == "paper":
        run_paper(args.strategy)


if __name__ == "__main__":
    main()
