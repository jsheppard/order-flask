"""Storage for the order-models resources.

Two implementations share one interface:

* ``MongoResourceStore`` (the default) reads and writes the collections the Spring
  order-data application uses, at the URI in ``MONGODB_URI`` (or ``SPRING_MONGODB_URI``).
  Documents are converted with ``spring_mapping``.
* ``InMemoryResourceStore`` is used by the test configuration.

Both return the same model objects, so the API output does not depend on the store.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from threading import Lock
from typing import Mapping

from .domain_codec import decode_fields
from .spring_mapping import COLLECTIONS, document_fields, spring_document, spring_values


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp_create(obj) -> None:
    if hasattr(obj, "created_at"):
        obj.created_at = _now()
    if hasattr(obj, "updated_at"):
        obj.updated_at = obj.created_at if hasattr(obj, "created_at") else _now()


def _stamp_update(obj) -> None:
    if hasattr(obj, "updated_at"):
        obj.updated_at = _now()


def _id_sort_key(obj):
    # Numeric ids sort numerically; ObjectId strings sort after them, in creation order.
    return (0, int(obj.id), "") if obj.id.isdigit() else (1, 0, obj.id)


def _sort_by_id(objects: list) -> list:
    return sorted(objects, key=_id_sort_key)


class InMemoryResourceStore:
    def __init__(self, models: Mapping[str, type]) -> None:
        self._items: dict[str, dict[str, object]] = {}
        self._next_ids: dict[str, int] = {}
        self._lock = Lock()

    def create(self, slug: str, obj):
        with self._lock:
            number = self._next_ids.get(slug, 1)
            obj.id = str(number)
            self._next_ids[slug] = number + 1
            _stamp_create(obj)
            self._items.setdefault(slug, {})[obj.id] = obj
            return obj

    def get(self, slug: str, item_id: str):
        with self._lock:
            return self._items.get(slug, {}).get(item_id)

    def list(self, slug: str) -> list:
        with self._lock:
            items = list(self._items.get(slug, {}).values())
        return _sort_by_id(items)

    def apply(self, slug: str, item_id: str, changes: dict):
        with self._lock:
            current = self._items.get(slug, {}).get(item_id)
            if current is None:
                return None
            updated = replace(current, **changes)
            _stamp_update(updated)
            self._items[slug][item_id] = updated
            return updated

    def delete(self, slug: str, item_id: str) -> bool:
        with self._lock:
            return self._items.get(slug, {}).pop(item_id, None) is not None


class MongoResourceStore:
    def __init__(self, uri: str, database: str | None, models: Mapping[str, type]) -> None:
        from pymongo import MongoClient

        self._client = MongoClient(uri)
        if database:
            self._db = self._client[database]
        else:
            # The database named in the URI path, as the Spring application uses.
            self._db = self._client.get_default_database()
        self._models = dict(models)
        self._class_names: dict[str, str | None] = {}

    def _collection(self, slug: str):
        return self._db[COLLECTIONS[slug]]

    @staticmethod
    def _lookup(item_id: str) -> dict:
        # Spring ids are ObjectIds for most collections and strings for a few.
        from bson import ObjectId

        ids: list = [item_id]
        if ObjectId.is_valid(item_id):
            ids.append(ObjectId(item_id))
        return {"_id": {"$in": ids}}

    def _spring_class(self, slug: str) -> str | None:
        """The Java class name Spring writes into ``_class`` for this collection, if any."""
        if slug not in self._class_names:
            sample = self._collection(slug).find_one({"_class": {"$exists": True}}, {"_class": 1})
            self._class_names[slug] = sample["_class"] if sample else None
        return self._class_names[slug]

    def _decode(self, slug: str, doc: dict):
        model = self._models[slug]
        errors: list[str] = []
        kwargs = decode_fields(model, document_fields(model, doc), errors)
        if errors:
            raise RuntimeError(f"Stored {slug} document {doc['_id']} does not match its model: {errors}")
        return model(**kwargs)

    def create(self, slug: str, obj):
        from bson import ObjectId

        oid = ObjectId()
        obj.id = str(oid)
        _stamp_create(obj)
        doc = spring_document(obj)
        doc["_id"] = oid
        class_name = self._spring_class(slug)
        if class_name:
            doc["_class"] = class_name
        self._collection(slug).insert_one(doc)
        return obj

    def get(self, slug: str, item_id: str):
        doc = self._collection(slug).find_one(self._lookup(item_id))
        return None if doc is None else self._decode(slug, doc)

    def list(self, slug: str) -> list:
        return _sort_by_id([self._decode(slug, doc) for doc in self._collection(slug).find()])

    def apply(self, slug: str, item_id: str, changes: dict):
        current = self.get(slug, item_id)
        if current is None:
            return None
        updated = replace(current, **changes)
        _stamp_update(updated)
        # Only the changed fields (plus updated_at) are written, so Spring-only keys survive.
        write = dict(changes)
        if hasattr(updated, "updated_at"):
            write["updated_at"] = updated.updated_at
        self._collection(slug).update_one(self._lookup(item_id), {"$set": spring_values(self._models[slug], write)})
        return updated

    def delete(self, slug: str, item_id: str) -> bool:
        return self._collection(slug).delete_one(self._lookup(item_id)).deleted_count > 0


def create_domain_store(config: Mapping, models: Mapping[str, type]):
    """Build the store named by ``config["DOMAIN_STORE"]``.

    ``"mongo"`` needs ``MONGODB_URI`` (or ``SPRING_MONGODB_URI``). ``MONGODB_DATABASE``
    overrides the database named in the URI.
    """
    if config.get("DOMAIN_STORE") == "memory":
        return InMemoryResourceStore(models)

    uri = config.get("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI must be set to store the order-models data in MongoDB")
    from pymongo.uri_parser import parse_uri

    database = config.get("MONGODB_DATABASE") or parse_uri(uri).get("database")
    if not database:
        raise RuntimeError(
            "MONGODB_URI has no database name. Add one (for example /order-data), "
            "or set MONGODB_DATABASE."
        )
    return MongoResourceStore(uri, database, models)
