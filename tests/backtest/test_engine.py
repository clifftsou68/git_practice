from pathlib import Path

from app.backtest.engine import BacktestEngine, EngineConfig
from app.config.loader import load_strategy
from app.data.providers import CSVPriceProvider


def test_backtest_runs(tmp_path) -> None:
    strategy = load_strategy(Path("assets/strategies/momentum_pullback.yaml"))
    provider = CSVPriceProvider(root=Path("assets/sample_data"))
    engine = BacktestEngine(provider, EngineConfig(initial_equity=50_000))
    result = engine.run(
        strategy_name=strategy.name,
        symbols=strategy.universe.symbols,
        indicator_configs=strategy.indicators,
        rules=strategy.rules,
        sizing=strategy.sizing,
        portfolio_limits=strategy.portfolio,
        backtest_config=strategy.backtest,
    )
    assert result.metrics.cagr is not None
    assert result.metrics.equity_curve[0][1] == 50_000
    assert result.metrics.num_trades >= 0
