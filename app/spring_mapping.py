"""Map documents between the Spring order-data application's collections and the models.

Spring stores each resource in its own collection with camelCase keys, an ObjectId (or
string) ``_id``, BSON dates, and BSON Decimal128 for money. The models use snake_case
and Python types. This module converts in both directions, guided by each dataclass's
type hints, so the same ``domain_codec`` validation applies to stored and submitted data.

* Reading: unknown Spring keys (and ``_class``) are ignored, and null or missing values
  fall back to model defaults.
* Writing: only the fields the caller supplies are sent, so Spring-only keys on an
  existing document are left as they are.
"""

from __future__ import annotations

import dataclasses
import re
import types
import typing
from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum

from bson import Decimal128, ObjectId

# Model resource slug -> Spring collection name.
COLLECTIONS: dict[str, str] = {
    "orders": "order",
    "scheduled-orders": "scheduledOrder",
    "frostings": "frosting",
    "icings": "icing",
    "toppings": "topping",
    "donuts": "donut",
    "rolls": "roll",
    "merchandise": "merchandise",
    "locations": "location",
    "statuses": "status",
    "pricing-sheets": "pricingSheet",
    "item-type-limits": "itemTypeLimit",
    "sweepstakes": "sweepstakes",
    "announcements": "announcement",
}

# Spring names that do not follow the camelCase rule.
SPRING_NAME_OVERRIDES: dict[str, str] = {"weekday": "weekDay"}
_MODEL_NAME_OVERRIDES: dict[str, str] = {spring: model for model, spring in SPRING_NAME_OVERRIDES.items()}

# Fields Spring stores as a day name (Java DayOfWeek) while the model uses an int, Monday=0.
DAY_NAME_FIELDS = frozenset({"monthly_day_of_week"})
DAY_NAMES = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")

# Spring stores a time of day as a BSON date on this day.
_TIME_ANCHOR = (1970, 1, 1)

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_UTC = timezone.utc


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


def _snake(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def spring_name(field_name: str) -> str:
    """The Spring key for a model field (``id`` is ``_id``)."""
    if field_name == "id":
        return "_id"
    return SPRING_NAME_OVERRIDES.get(field_name) or _camel(field_name)


def _model_name(spring_key: str) -> str:
    if spring_key == "_id":
        return "id"
    return _MODEL_NAME_OVERRIDES.get(spring_key) or _snake(spring_key)


def _unwrap_optional(hint):
    if typing.get_origin(hint) in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return hint


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=_UTC)


# --- reading: Spring value -> value that domain_codec.decode_fields accepts -------------

def _to_model(hint, value, name: str = ""):
    if value is None:
        return None
    hint = _unwrap_optional(hint)
    origin = typing.get_origin(hint)
    if origin in (list, set, frozenset):
        (inner,) = typing.get_args(hint)
        return [_to_model(inner, item) for item in value]
    if dataclasses.is_dataclass(hint) and isinstance(value, dict):
        return _document_to_fields(hint, value)
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Decimal128):
        return str(value.to_decimal())
    if isinstance(value, datetime):
        if hint is date:
            return value.date().isoformat()
        if hint is time:
            return _aware(value).time().isoformat()
        return _aware(value).isoformat()
    if name in DAY_NAME_FIELDS and isinstance(value, str) and value.upper() in DAY_NAMES:
        return DAY_NAMES.index(value.upper())
    if hint is int and isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _document_to_fields(cls: type, doc: dict) -> dict:
    hints = typing.get_type_hints(cls)
    fields: dict = {}
    for key, value in doc.items():
        if key == "_class":
            continue
        name = _model_name(key)
        if name not in hints:
            continue  # Spring-only data; kept in the document, not exposed
        converted = _to_model(hints[name], value, name)
        if converted is not None:
            fields[name] = converted
    return fields


def document_fields(model: type, doc: dict) -> dict:
    """Snake_case field values for one Spring document, ready for ``decode_fields``."""
    return _document_to_fields(model, doc)


# --- writing: model value -> BSON-friendly value ----------------------------------------

def _to_spring(hint, value, name: str = ""):
    if value is None:
        return None
    hint = _unwrap_optional(hint)
    origin = typing.get_origin(hint)
    if origin in (list, set, frozenset):
        (inner,) = typing.get_args(hint)
        return [_to_spring(inner, item) for item in value]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return spring_document(value, nested=True)
    if isinstance(value, Enum):
        return value.value if isinstance(value.value, str) else value.name
    if name in DAY_NAME_FIELDS and isinstance(value, int) and not isinstance(value, bool):
        return DAY_NAMES[value]
    if isinstance(value, Decimal):
        return Decimal128(value)
    if isinstance(value, time):
        return datetime(*_TIME_ANCHOR, value.hour, value.minute, value.second, value.microsecond, tzinfo=_UTC)
    if isinstance(value, datetime):
        return _aware(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=_UTC)
    return value


def spring_document(obj, nested: bool = False) -> dict:
    """The Spring document for a model object. ``None`` fields are omitted.

    The top-level ``id`` is not included (the store sets ``_id``). A nested object's
    ``id`` is written as ``_id`` when present, as Spring does for line items.
    """
    hints = typing.get_type_hints(type(obj))
    doc: dict = {}
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if value is None:
            continue
        if field.name == "id":
            if nested:
                doc["_id"] = value
            continue
        doc[spring_name(field.name)] = _to_spring(hints[field.name], value, field.name)
    return doc


def spring_values(model: type, changes: dict) -> dict:
    """Spring keys and values for a partial update. Explicit ``None`` is kept (it clears the field)."""
    hints = typing.get_type_hints(model)
    return {spring_name(name): _to_spring(hints[name], value, name) for name, value in changes.items()}
