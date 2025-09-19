"""Dataclass configuration models for QuantDesk."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class PathsSettings:
    cache_dir: Path = Path(".cache")
    db_path: Path = Path("quantdesk.sqlite")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PathsSettings":
        return cls(
            cache_dir=Path(data.get("cache_dir", cls.cache_dir)),
            db_path=Path(data.get("db_path", cls.db_path)),
        )


@dataclass
class MarketSettings:
    calendar: str = "XNYS"
    timezone: str = "America/New_York"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketSettings":
        return cls(
            calendar=data.get("calendar", cls.calendar),
            timezone=data.get("timezone", cls.timezone),
        )


@dataclass
class AlertSettings:
    desktop_enabled: bool = True
    email_enabled: bool = False
    webhook_enabled: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertSettings":
        return cls(
            desktop_enabled=bool(data.get("desktop_enabled", cls.desktop_enabled)),
            email_enabled=bool(data.get("email_enabled", cls.email_enabled)),
            webhook_enabled=bool(data.get("webhook_enabled", cls.webhook_enabled)),
        )


@dataclass
class LoggingSettings:
    level: str = "INFO"
    file: Path = Path("quantdesk.log")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoggingSettings":
        return cls(level=data.get("level", cls.level), file=Path(data.get("file", cls.file)))


@dataclass
class AppSettings:
    paths: PathsSettings = field(default_factory=PathsSettings)
    market: MarketSettings = field(default_factory=MarketSettings)
    alerts: AlertSettings = field(default_factory=AlertSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        return cls(
            paths=PathsSettings.from_dict(data.get("paths", {})),
            market=MarketSettings.from_dict(data.get("market", {})),
            alerts=AlertSettings.from_dict(data.get("alerts", {})),
            logging=LoggingSettings.from_dict(data.get("logging", {})),
        )


@dataclass
class UniverseFilters:
    min_avg_dollar_volume: Optional[float] = None
    price_between: Optional[Sequence[float]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniverseFilters":
        price_between = data.get("price_between")
        if price_between is not None and len(price_between) == 2:
            low, high = float(price_between[0]), float(price_between[1])
            if low >= high:
                raise ValueError("price_between lower bound must be less than upper bound")
            price_between = [low, high]
        else:
            price_between = None if price_between is None else list(price_between)
        return cls(
            min_avg_dollar_volume=(
                float(data["min_avg_dollar_volume"]) if "min_avg_dollar_volume" in data else None
            ),
            price_between=price_between,
        )


@dataclass
class UniverseConfig:
    region: str = "US"
    symbols: List[str] = field(default_factory=list)
    filters: UniverseFilters = field(default_factory=UniverseFilters)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniverseConfig":
        return cls(
            region=data.get("region", "US"),
            symbols=list(data.get("symbols", [])),
            filters=UniverseFilters.from_dict(data.get("filters", {})),
        )


@dataclass
class IndicatorConfig:
    name: str
    kind: str
    inputs: List[str]
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndicatorConfig":
        return cls(
            name=data["name"],
            kind=data["kind"],
            inputs=list(data.get("inputs", [])),
            params=dict(data.get("params", {})),
        )


@dataclass
class RulesConfig:
    entry: str
    exit: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RulesConfig":
        exit_rules = data.get("exit", [])
        if isinstance(exit_rules, list):
            exit_list = [str(rule) for rule in exit_rules]
        else:
            exit_list = [str(exit_rules)]
        return cls(entry=str(data.get("entry", "True")), exit=exit_list)


@dataclass
class SizingConfig:
    type: str = "fixed"
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SizingConfig":
        return cls(type=data.get("type", "fixed"), params=dict(data.get("params", {})))


@dataclass
class PortfolioLimits:
    max_positions: int = 10
    max_gross_exposure: float = 1.0
    max_position_pct: float = 0.2

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortfolioLimits":
        return cls(
            max_positions=int(data.get("max_positions", cls.max_positions)),
            max_gross_exposure=float(data.get("max_gross_exposure", cls.max_gross_exposure)),
            max_position_pct=float(data.get("max_position_pct", cls.max_position_pct)),
        )


@dataclass
class BacktestConfig:
    frequency: str
    start: date
    end: date
    slippage_bps: float = 0.0
    commission_per_share: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BacktestConfig":
        return cls(
            frequency=data.get("frequency", "1D"),
            start=date.fromisoformat(str(data["start"])),
            end=date.fromisoformat(str(data["end"])),
            slippage_bps=float(data.get("slippage_bps", 0.0)),
            commission_per_share=float(data.get("commission_per_share", 0.0)),
        )


@dataclass
class AlertChannelConfig:
    desktop: bool = True
    email: Dict[str, Any] = field(default_factory=dict)
    telegram: Dict[str, Any] = field(default_factory=dict)
    webhook: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertChannelConfig":
        return cls(
            desktop=bool(data.get("desktop", True)),
            email=dict(data.get("email", {})),
            telegram=dict(data.get("telegram", {})),
            webhook=dict(data.get("webhook", {})),
        )


@dataclass
class AlertConfig:
    check_interval_minutes: int = 15
    channels: AlertChannelConfig = field(default_factory=AlertChannelConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertConfig":
        return cls(
            check_interval_minutes=int(data.get("check_interval_minutes", 15)),
            channels=AlertChannelConfig.from_dict(data.get("channels", {})),
        )


@dataclass
class StrategyConfig:
    name: str
    universe: UniverseConfig
    indicators: List[IndicatorConfig]
    rules: RulesConfig
    sizing: SizingConfig
    portfolio: PortfolioLimits
    backtest: BacktestConfig
    alerts: AlertConfig

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyConfig":
        return cls(
            name=data.get("name", "Unnamed Strategy"),
            universe=UniverseConfig.from_dict(data.get("universe", {})),
            indicators=[IndicatorConfig.from_dict(item) for item in data.get("indicators", [])],
            rules=RulesConfig.from_dict(data.get("rules", {})),
            sizing=SizingConfig.from_dict(data.get("sizing", {})),
            portfolio=PortfolioLimits.from_dict(data.get("portfolio", {})),
            backtest=BacktestConfig.from_dict(data.get("backtest", {})),
            alerts=AlertConfig.from_dict(data.get("alerts", {})),
        )


__all__ = [
    "AlertConfig",
    "AlertChannelConfig",
    "AlertSettings",
    "AppSettings",
    "BacktestConfig",
    "IndicatorConfig",
    "LoggingSettings",
    "MarketSettings",
    "PathsSettings",
    "PortfolioLimits",
    "RulesConfig",
    "SizingConfig",
    "StrategyConfig",
    "UniverseConfig",
    "UniverseFilters",
]
