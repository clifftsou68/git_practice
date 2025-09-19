from pathlib import Path

from app.config.loader import load_strategy


def test_load_strategy(tmp_path: Path) -> None:
    src = Path("assets/strategies/momentum_pullback.yaml")
    strategy = load_strategy(src)
    assert strategy.name == "Momentum Pullback with Risk Controls"
    assert strategy.universe.symbols == ["AAPL", "MSFT"]
    assert strategy.rules.entry.startswith("(sma10 > sma20)")
    assert strategy.sizing.type == "vol_target"
