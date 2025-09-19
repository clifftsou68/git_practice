"""Rule parsing and evaluation."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


ALLOWED_FUNCS = {"max": max, "min": min, "abs": abs, "round": round}


class SafeEval(ast.NodeVisitor):
    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id not in self.context:
            msg = f"Unknown identifier in rule: {node.id}"
            raise NameError(msg)
        return self.context[node.id]

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        values = [self.visit(v) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        msg = "Unsupported boolean operator"
        raise ValueError(msg)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        msg = "Unsupported unary operator"
        raise ValueError(msg)

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        msg = "Unsupported binary operator"
        raise ValueError(msg)

    def visit_Compare(self, node: ast.Compare) -> Any:
        left = self.visit(node.left)
        result = True
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(op, ast.Gt):
                result = result and (left > right)
            elif isinstance(op, ast.GtE):
                result = result and (left >= right)
            elif isinstance(op, ast.Lt):
                result = result and (left < right)
            elif isinstance(op, ast.LtE):
                result = result and (left <= right)
            elif isinstance(op, ast.Eq):
                result = result and (left == right)
            elif isinstance(op, ast.NotEq):
                result = result and (left != right)
            else:
                msg = "Unsupported comparison operator"
                raise ValueError(msg)
            left = right
        return result

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            msg = "Only simple function calls are allowed"
            raise ValueError(msg)
        func_name = node.func.id
        if func_name not in ALLOWED_FUNCS:
            msg = f"Function {func_name} is not allowed in rules"
            raise ValueError(msg)
        func = ALLOWED_FUNCS[func_name]
        args = [self.visit(arg) for arg in node.args]
        kwargs = {kw.arg: self.visit(kw.value) for kw in node.keywords}
        return func(*args, **kwargs)


@dataclass
class RuleOutcome:
    entry: bool
    exit_reasons: List[str]
    trailing_stop: Optional[float]


_BETWEEN_PATTERN = re.compile(
    r"(?P<lhs>[A-Za-z_][A-Za-z0-9_]*)\s+between\s+(?P<low>[^\s]+)\s+and\s+(?P<high>[^\s]+)"
)


def _preprocess_expression(expression: str) -> str:
    def repl(match: re.Match[str]) -> str:
        lhs = match.group("lhs")
        low = match.group("low")
        high = match.group("high")
        return f"(({lhs} >= {low}) and ({lhs} <= {high}))"

    return _BETWEEN_PATTERN.sub(repl, expression)


def evaluate_expression(expression: str, context: Dict[str, Any]) -> Any:
    processed = _preprocess_expression(expression)
    tree = ast.parse(processed, mode="eval")
    evaluator = SafeEval(context)
    return evaluator.visit(tree)


def evaluate_rules(
    rules: Dict[str, Any],
    latest: Dict[str, float],
    features: Dict[str, float],
) -> RuleOutcome:
    context = {**features, **latest}
    entry_rule = rules.get("entry", "True")
    entry_result = bool(evaluate_expression(entry_rule, context))

    trailing_stop_value: Optional[float] = None
    exit_reasons: List[str] = []
    for rule in rules.get("exit", []):
        rule = rule.strip()
        if rule.startswith("trailing_stop"):
            inner = rule[len("trailing_stop") :].strip("() ")
            trailing_stop_value = float(evaluate_expression(inner, context))
            continue
        if bool(evaluate_expression(rule, context)):
            exit_reasons.append(rule)
    return RuleOutcome(entry=entry_result, exit_reasons=exit_reasons, trailing_stop=trailing_stop_value)


__all__ = ["RuleOutcome", "evaluate_rules"]
