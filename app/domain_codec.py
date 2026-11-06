"""Convert ``app.order_models`` dataclasses to and from JSON-compatible values.

Decoding uses the dataclass type hints, so every model field is checked against
its declared type. Problems are appended to an ``errors`` list (with a dotted
path such as ``items[0].qty``), so a request reports all of them at once.
"""

from __future__ import annotations

import types
import typing
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from enum import Enum

_BAD = object()  # sentinel: this value failed to decode; an error was recorded


def encode(value):
    """Turn a model value into plain JSON types. Enums use their member name."""
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: encode(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (set, frozenset)):
        return sorted(encode(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def decode_fields(cls: type, data: dict, errors: list[str], prefix: str = "", exclude=frozenset()) -> dict:
    """Decode the keys of ``data`` that name fields of dataclass ``cls``.

    Returns keyword arguments for the fields that decoded cleanly. Unknown keys
    and keys in ``exclude`` are reported as errors.
    """
    names = {f.name for f in fields(cls)} - set(exclude)
    unknown = sorted(set(data) - names)
    if unknown:
        errors.append(f"{prefix}unknown fields: {', '.join(unknown)}")

    hints = typing.get_type_hints(cls)
    kwargs = {}
    for name in sorted(set(data) & names):
        value = _decode(hints[name], data[name], f"{prefix}{name}", errors)
        if value is not _BAD:
            kwargs[name] = value
    return kwargs


def _decode(hint, value, path: str, errors: list[str]):
    origin = typing.get_origin(hint)
    args = typing.get_args(hint)

    if origin in (typing.Union, types.UnionType):
        if value is None:
            if type(None) in args:
                return None
            errors.append(f"{path} must not be null")
            return _BAD
        # Every optional field in order_models is "single type | None".
        (inner,) = [a for a in args if a is not type(None)]
        return _decode(inner, value, path, errors)

    if origin in (list, set, frozenset):
        if not isinstance(value, list):
            errors.append(f"{path} must be a list")
            return _BAD
        items = [_decode(args[0], v, f"{path}[{i}]", errors) for i, v in enumerate(value)]
        if any(item is _BAD for item in items):
            return _BAD
        return origin(items)

    if value is None:
        errors.append(f"{path} must not be null")
        return _BAD

    if is_dataclass(hint):
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object")
            return _BAD
        return hint(**decode_fields(hint, value, errors, prefix=f"{path}."))

    if isinstance(hint, type) and issubclass(hint, Enum):
        wanted = value.lower() if isinstance(value, str) else None
        for member in hint:
            if wanted is not None and (
                member.name.lower() == wanted
                or (isinstance(member.value, str) and member.value.lower() == wanted)
            ):
                return member
        choices = ", ".join(m.name for m in hint)
        errors.append(f"{path} must be one of: {choices}")
        return _BAD

    if hint is bool:
        if isinstance(value, bool):
            return value
        errors.append(f"{path} must be true or false")
        return _BAD

    if hint is int:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        errors.append(f"{path} must be an integer")
        return _BAD

    if hint is float:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        errors.append(f"{path} must be a number")
        return _BAD

    if hint is str:
        if isinstance(value, str):
            return value
        errors.append(f"{path} must be a string")
        return _BAD

    if hint is Decimal:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            errors.append(f"{path} must be a non-negative number")
            return _BAD
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            amount = None
        if amount is None or not amount.is_finite() or amount < 0:
            errors.append(f"{path} must be a non-negative number")
            return _BAD
        return amount

    if hint in (datetime, date, time):
        if isinstance(value, str):
            try:
                return hint.fromisoformat(value)
            except ValueError:
                pass
        errors.append(f"{path} must be an ISO 8601 {hint.__name__} string")
        return _BAD

    raise TypeError(f"Unsupported type for {path}: {hint!r}")  # programming error, not client error
