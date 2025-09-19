"""Utilities for loading YAML configuration files."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .models import AppSettings, StrategyConfig
from .parser import parse_yaml


class ConfigError(RuntimeError):
    """Raised when configuration files cannot be parsed."""


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        msg = f"Configuration file not found: {path}"
        raise ConfigError(msg) from exc
    try:
        data = parse_yaml(raw_text)
    except Exception as exc:  # pragma: no cover - parser errors
        msg = f"Failed to parse YAML file: {path}"
        raise ConfigError(msg) from exc
    if not isinstance(data, dict):
        msg = f"YAML file does not contain a mapping: {path}"
        raise ConfigError(msg)
    return data


def load_settings(path: Path) -> AppSettings:
    payload = load_yaml(path)
    return AppSettings.from_dict(payload)


def load_strategy(path: Path) -> StrategyConfig:
    payload = load_yaml(path)
    return StrategyConfig.from_dict(payload)


__all__ = ["ConfigError", "load_settings", "load_strategy"]
