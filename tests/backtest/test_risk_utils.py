from app.core.risk import RiskParameters, apply_position_limits, position_size_vol_target


def test_position_size_vol_target() -> None:
    shares = position_size_vol_target(equity=100_000, price=100, atr=2, risk_per_trade=0.01, atr_multiple=2)
    assert round(shares, 2) == 250.0


def test_apply_position_limits() -> None:
    params = RiskParameters(max_positions=5, max_gross_exposure=1.0, max_position_pct=0.2)
    qty = apply_position_limits(
        desired_qty=1000,
        price=100,
        equity=100_000,
        params=params,
        current_positions=2,
        gross_exposure=0.4,
    )
    assert qty <= 200
