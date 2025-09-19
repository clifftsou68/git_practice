from app.signals.rules import RuleOutcome, evaluate_rules


def test_rule_between_expression() -> None:
    rules = {
        "entry": "(sma > ema) and (rsi between 40 and 60)",
        "exit": ["close < sma"],
    }
    latest = {"close": 10}
    features = {"sma": 12, "ema": 8, "rsi": 50}
    outcome: RuleOutcome = evaluate_rules(rules, latest, features)
    assert outcome.entry is True
    assert outcome.exit_reasons == ["close < sma"]
