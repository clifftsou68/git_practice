# QuantDesk

QuantDesk is an educational desktop application for market analysis, trade signal generation,
and paper-trading alerts. It provides a configurable strategy DSL powered by YAML/JSON files and
an offline-friendly backtesting engine for discretionary review. The project is designed for
research only—**not** financial advice.

## Features

- Pluggable data providers with caching (Yahoo Finance demo provider included)
- Configurable universe filters and indicator pipeline
- Declarative signal rules with portfolio risk management
- Lightweight backtesting with rich performance metrics
- Paper-trading loop with alert fan-out (desktop toasts, email, webhooks)
- PyQt6 desktop shell with Dashboard, Screener, Strategy, Backtest, Paper Trade, Logs, and
  Settings tabs (optional)
- YAML (JSON-compatible) strategy files with hot reload
- SQLite storage for results and application state
- Packaging via Poetry and PyInstaller (one-file Windows EXE)

## Project Layout

```
app/
  __init__.py
  __main__.py          # Entry point for desktop launcher
  config/              # Dataclass models and YAML loaders
  core/                # Portfolio, position, order, and risk models
  data/                # Data provider abstractions and cache management
  signals/             # Indicator registry and rule evaluation
  backtest/            # Backtest engine, reports, statistics
  paper/               # Paper trading scheduler and alert fan-out
  notify/              # Desktop toast, email, and webhook clients
  ui/                  # PyQt6 views and controllers
  utils/               # Shared utilities
assets/
  sample_data/         # Example OHLCV data for offline demo
  strategies/          # Sample strategy YAML files
  watchlists/          # Example universe definitions
tests/
  ...
```

## Getting Started

### Prerequisites

- Python 3.11+
- (Optional) Poetry 1.6+

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
PYTHONPATH=. python -m app --help
```

To launch the desktop UI:

```bash
PYTHONPATH=. python -m app gui
```

To run a sample backtest:

```bash
PYTHONPATH=. python -m app backtest assets/strategies/momentum_pullback.yaml
```

To execute the paper trading loop in simulation mode:

```bash
PYTHONPATH=. python -m app paper assets/strategies/momentum_pullback.yaml
```

### Testing & Quality

```bash
PYTHONPATH=. pytest -q
```

### Packaging

```bash
poetry run pyinstaller --noconfirm --onefile app/__main__.py --name QuantDesk
```

## Configuration

- `.env` for API keys (Alpha Vantage, Finnhub, etc.)
- `config/settings.yaml` controls data cache path, polling cadence, and trading calendars
- Strategy YAML (JSON-compatible) files define universes, indicators, rules, sizing, and alert routing

## Disclaimer

```
QuantDesk is for educational use only. It does not provide financial advice. Markets carry risk.
```

Always review signals before taking action. No broker integration is enabled by default.
