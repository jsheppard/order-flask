"""REST endpoints for the order-models resources. Mounted under /api/v2.

Every resource gets the same five routes:

    GET    /api/v2/<slug>             list (``{"data": [...], "count": n}``), ``?sort=name,-city``
    POST   /api/v2/<slug>             create (201, with a Location header)
    GET    /api/v2/<slug>/<id>        fetch one
    PATCH  /api/v2/<slug>/<id>        partial update
    DELETE /api/v2/<slug>/<id>        delete (204)

Read-only resources (``read_only=True``) register only the two GET routes.

Resources are declared in ``RESOURCES`` below. Request bodies are decoded from the
model's type hints (see ``domain_codec``).
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from typing import Callable

from flask import Blueprint, current_app, jsonify, request, url_for

from .domain_codec import decode_fields, encode
from .errors import ApiError
from .order_models import (
    Announcement,
    Donut,
    Frosting,
    Icing,
    ItemTypeLimit,
    Location,
    Merchandise,
    Order,
    PricingSheet,
    Roll,
    ScheduledOrder,
    Status,
    Sweepstakes,
    Topping,
)

domain_bp = Blueprint("domain", __name__)

# Set by the server, never by the client.
SERVER_FIELDS = frozenset({"id", "created_at", "updated_at"})


@dataclass(frozen=True)
class Resource:
    slug: str
    model: type
    required: tuple[str, ...] = ()
    check: Callable[[object], list[str]] | None = None  # cross-field rules, returns error messages
    read_only: bool = False  # only the GET routes are registered


def _check_pastry(obj) -> list[str]:
    if obj.allow_dozen and obj.product_dozen:
        return ["allow_dozen and product_dozen cannot both be true"]
    return []


RESOURCES: tuple[Resource, ...] = (
    Resource("orders", Order, read_only=True),  # read from the Spring order-data collection
    Resource("scheduled-orders", ScheduledOrder),
    Resource("frostings", Frosting),
    Resource("icings", Icing),
    Resource("toppings", Topping),
    Resource("donuts", Donut, required=("description", "price"), check=_check_pastry),
    Resource("rolls", Roll, required=("description", "price"), check=_check_pastry),
    Resource("merchandise", Merchandise, required=("description", "price")),
    Resource("locations", Location, required=("name", "address1", "city", "state", "zip")),
    Resource("statuses", Status),
    Resource("pricing-sheets", PricingSheet),
    Resource("item-type-limits", ItemTypeLimit),
    Resource("sweepstakes", Sweepstakes, required=("title", "description", "begin_date", "end_date")),
    Resource("announcements", Announcement, required=("title", "start_date")),
)

# Not exposed as REST resources:
#   Item          - a line item, only meaningful inside an Order
#   Product       - abstract base; the concrete types are donuts, rolls and merchandise
#   User          - holds login IPs, locations and contact details, and this API has no auth
#   ContactMessage - customer inquiries, same concern as User

MODELS: dict[str, type] = {res.slug: res.model for res in RESOURCES}


def _store():
    return current_app.extensions["domain_store"]


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "Request body must be a JSON object")
    return data


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _scalar_fields(model: type) -> set[str]:
    """Fields a list can be sorted by: everything except lists and nested objects."""
    hints = typing.get_type_hints(model)
    names: set[str] = set()
    for field in fields(model):
        hint = hints[field.name]
        if typing.get_origin(hint) in (typing.Union, types.UnionType):
            args = [a for a in typing.get_args(hint) if a is not type(None)]
            hint = args[0] if len(args) == 1 else hint
        if typing.get_origin(hint) in (list, set, frozenset) or is_dataclass(hint):
            continue
        names.add(field.name)
    return names


def _parse_sort(model: type, raw: str) -> list[tuple[str, bool]]:
    """Parse ``sort=name,-city`` into (field, descending) pairs. ``-`` means descending."""
    allowed = _scalar_fields(model)
    terms: list[tuple[str, bool]] = []
    errors: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        descending = part.startswith("-")
        name = part[1:] if descending else part
        if name in allowed:
            terms.append((name, descending))
        else:
            errors.append(f"unknown sort field: {name}")
    if errors:
        errors.append(f"sortable fields: {', '.join(sorted(allowed))}")
        raise ApiError(400, "Invalid sort", errors)
    return terms


def _sort_value(value):
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, str):
        return value.lower()
    return value


def _apply_sort(objects: list, terms: list[tuple[str, bool]]) -> list:
    """Stable multi-key sort. Missing (null) values go last whatever the direction."""
    for name, descending in reversed(terms):
        present = [o for o in objects if getattr(o, name) is not None]
        missing = [o for o in objects if getattr(o, name) is None]
        present.sort(key=lambda o: _sort_value(getattr(o, name)), reverse=descending)
        objects = present + missing
    return objects


def _raise_if(errors: list[str]) -> None:
    if errors:
        raise ApiError(400, "Validation failed", errors)


def _get_or_404(res: Resource, item_id: str):
    obj = _store().get(res.slug, item_id)
    if obj is None:
        raise ApiError(404, f"{res.slug} item {item_id} not found")
    return obj


def _run_check(res: Resource, obj) -> None:
    if res.check is not None:
        _raise_if(res.check(obj))


def _make_views(res: Resource) -> tuple[Callable, Callable, Callable, Callable, Callable]:
    """Return (list, create, get, update, delete) view functions bound to ``res``."""

    def list_items():
        items = _store().list(res.slug)
        terms = _parse_sort(res.model, request.args.get("sort", ""))
        items = _apply_sort(items, terms)
        return jsonify({"data": [encode(obj) for obj in items], "count": len(items)})

    def create_item():
        data = _json_body()
        errors: list[str] = []
        kwargs = decode_fields(res.model, data, errors, exclude=SERVER_FIELDS)
        for name in res.required:
            if name not in data:
                errors.append(f"{name} is required")
            elif name in kwargs and _is_blank(kwargs[name]):
                errors.append(f"{name} is required")
        _raise_if(errors)

        obj = res.model(**kwargs)
        _run_check(res, obj)
        obj = _store().create(res.slug, obj)

        response = jsonify({"data": encode(obj)})
        response.status_code = 201
        response.headers["Location"] = url_for(f"domain.{res.slug}_item", item_id=obj.id)
        return response

    def get_item(item_id: str):
        return jsonify({"data": encode(_get_or_404(res, item_id))})

    def update_item(item_id: str):
        existing = _get_or_404(res, item_id)
        data = _json_body()
        errors: list[str] = []
        changes = decode_fields(res.model, data, errors, exclude=SERVER_FIELDS)
        for name in res.required:
            if name in changes and _is_blank(changes[name]):
                errors.append(f"{name} is required")
        _raise_if(errors)
        if not changes:
            raise ApiError(400, "No changes supplied")

        # Check the merged result before storing it, so a bad combination is rejected whole.
        _run_check(res, replace(existing, **changes))
        return jsonify({"data": encode(_store().apply(res.slug, item_id, changes))})

    def delete_item(item_id: str):
        _get_or_404(res, item_id)
        _store().delete(res.slug, item_id)
        return "", 204

    return list_items, create_item, get_item, update_item, delete_item


def _register_resources() -> None:
    for res in RESOURCES:
        list_items, create_item, get_item, update_item, delete_item = _make_views(res)
        base = f"/{res.slug}"
        item = f"{base}/<string:item_id>"
        domain_bp.add_url_rule(base, endpoint=f"{res.slug}_list", view_func=list_items, methods=["GET"])
        domain_bp.add_url_rule(item, endpoint=f"{res.slug}_item", view_func=get_item, methods=["GET"])
        if res.read_only:
            continue
        domain_bp.add_url_rule(base, endpoint=f"{res.slug}_create", view_func=create_item, methods=["POST"])
        domain_bp.add_url_rule(item, endpoint=f"{res.slug}_update", view_func=update_item, methods=["PATCH"])
        domain_bp.add_url_rule(item, endpoint=f"{res.slug}_delete", view_func=delete_item, methods=["DELETE"])


_register_resources()
