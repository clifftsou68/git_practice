"""Indicator computation and signal generation pipeline."""
from __future__ import annotations

from typing import Dict, List

from app.config.models import IndicatorConfig, RulesConfig
from app.data.providers import PriceBar

from .indicators import compute_indicator
from .rules import RuleOutcome, evaluate_rules


def compute_indicator_frame(
    bars: List[PriceBar], indicator_configs: List[IndicatorConfig]
) -> List[Dict[str, float]]:
    features: List[Dict[str, float]] = [dict() for _ in bars]
    for indicator in indicator_configs:
        values = compute_indicator(indicator.kind, bars, indicator.params)
        for idx, value in enumerate(values):
            features[idx][indicator.name] = value
    return features


def generate_signals(
    price_data: List[PriceBar],
    indicator_frame: List[Dict[str, float]],
    rules: RulesConfig,
) -> List[Dict[str, object]]:
    signals: List[Dict[str, object]] = []
    rule_dict = {"entry": rules.entry, "exit": rules.exit}
    for bar, feature_row in zip(price_data, indicator_frame):
        latest = {
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
        }
        outcome: RuleOutcome = evaluate_rules(rule_dict, latest, feature_row)
        signals.append(
            {
                "timestamp": bar.timestamp,
                "entry": outcome.entry,
                "exit_reasons": outcome.exit_reasons,
                "trailing_stop": outcome.trailing_stop,
                "features": feature_row,
            }
        )
    return signals


__all__ = ["compute_indicator_frame", "generate_signals"]
