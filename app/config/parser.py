"""Minimal YAML parser for QuantDesk configuration files."""
from __future__ import annotations

import json
from typing import Any, List


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("\"") and value.endswith("\""):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts = [part.strip() for part in inner.split(",")]
        return [_parse_scalar(part) for part in parts]
    cleaned = value.replace("_", "")
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return value


def parse_yaml(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    lines = [line.rstrip() for line in text.splitlines()]
    index = 0

    def parse_block(indent: int) -> Any:
        nonlocal index
        mapping: dict[str, Any] = {}
        sequence: List[Any] | None = None
        while index < len(lines):
            line = lines[index]
            if not line.strip() or line.strip().startswith("#"):
                index += 1
                continue
            current_indent = len(line) - len(line.lstrip(" "))
            if current_indent < indent:
                break
            if line.lstrip().startswith("- "):
                if sequence is None:
                    sequence = []
                if current_indent > indent:
                    raise ValueError("Invalid indentation for list item")
                item_content = line.lstrip()[2:]
                index += 1
                if not item_content:
                    sequence.append(parse_block(indent + 2))
                else:
                    item: Any
                    if ":" in item_content:
                        key, value_part = item_content.split(":", 1)
                        key = key.strip()
                        value_part = value_part.strip()
                        if value_part:
                            item = {key: _parse_scalar(value_part)}
                        else:
                            nested = parse_block(indent + 2)
                            item = {key: nested}
                    else:
                        item = _parse_scalar(item_content)
                    # merge additional mapping lines for this item
                    additional = parse_block(indent + 2)
                    if isinstance(item, dict) and isinstance(additional, dict):
                        item.update(additional)
                        sequence.append(item)
                    else:
                        if additional not in ({}, None):
                            if isinstance(item, dict):
                                item["value"] = additional
                            else:
                                item = [item, additional]
                        sequence.append(item)
            else:
                if sequence is not None:
                    break
                if ":" not in line:
                    raise ValueError(f"Invalid line: {line}")
                key, value_part = line.strip().split(":", 1)
                key = key.strip()
                value_part = value_part.strip()
                index += 1
                if value_part:
                    mapping[key] = _parse_scalar(value_part)
                else:
                    mapping[key] = parse_block(current_indent + 2)
        return sequence if sequence is not None else mapping

    result = parse_block(0)
    return result


__all__ = ["parse_yaml"]
