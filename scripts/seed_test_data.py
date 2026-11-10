#!/usr/bin/env python3
"""Load the fake test fixtures into the MongoDB used by the Docker test stack.

The records below are the same fake payloads the tests use (tests/test_domain_api.py,
tests/test_sorting.py and tests/test_domain_mongo.py). They are written through the
/api/v2 resources, so they go through the same validation and land in the Spring
collections (donut, location, frosting, ...).

Resources that already hold any document are skipped, so running this twice does not
duplicate data. Use the compose stack's database, not a real order-data database:

    docker compose up -d mongo                # or: podman compose up -d mongo
    MONGODB_URI="mongodb://localhost:27018/order-data" scripts/seed_test_data.py

Run it with the project's virtual environment active (`source .venv/bin/activate`).
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402

# (slug, payload) in the order they should be created. Payloads are copied from the tests.
FIXTURES = [
    # tests/test_domain_api.py::test_create_fetch_update_delete_donut
    ("donuts", {"description": "Glazed", "price": 2.5, "item_type": "glazed_donut", "frosting": True}),
    # tests/test_domain_api.py::test_ids_are_per_resource
    ("rolls", {"description": "Cinnamon", "price": 1.75, "allow_dozen": True}),
    # tests/test_domain_mongo.py::test_update_and_delete
    ("frostings", {"description": "Maple"}),
    ("frostings", {"description": "Chocolate"}),
    # tests/test_domain_api.py::test_dates_round_trip_as_iso_strings
    ("announcements", {"title": "Holiday", "start_date": "2026-12-24", "end_date": "2026-12-26"}),
    # tests/test_domain_api.py::test_list_is_in_creation_order / test_stores_are_isolated_between_apps
    ("toppings", {"description": "Sprinkles"}),
    ("toppings", {"description": "Peanuts"}),
    # tests/test_sorting.py::setUp (locations)
    ("locations", {"name": "Cherry", "city": "Omaha", "address1": "1 St", "state": "NE", "zip": "68508"}),
    ("locations", {"name": "apple", "city": "Omaha", "address1": "1 St", "state": "NE", "zip": "68508"}),
    ("locations", {"name": "Banana", "city": "Lincoln", "address1": "1 St", "state": "NE", "zip": "68508"}),
    ("locations", {"name": "Date", "city": "Lincoln", "address1": "1 St", "state": "NE", "zip": "68508"}),
    # tests/test_domain_api.py::test_order_with_nested_items_and_enum_status
    (
        "scheduled-orders",
        {
            "name": "Ada",
            "status": "approved",
            "items": [{"product_name": "Glazed", "qty": 2, "unit_price": 1.25, "item_type": "ROLL"}],
        },
    ),
    # tests/test_domain_api.py::test_scheduled_order_includes_order_fields
    ("scheduled-orders", {"name": "Weekly", "weekday": 0, "recurrence_type": "monthly"}),
]


def main() -> int:
    if not os.environ.get("MONGODB_URI") and not os.environ.get("SPRING_MONGODB_URI"):
        print("Set MONGODB_URI (for example mongodb://localhost:27018/order-data).", file=sys.stderr)
        return 2

    app = create_app(Config)
    app.config["TESTING"] = True
    client = app.test_client()

    skipped = set()
    created = 0
    for slug, payload in FIXTURES:
        if slug in skipped:
            continue
        if client.get(f"/api/v2/{slug}").get_json()["count"]:
            print(f"{slug}: already has data, skipping")
            skipped.add(slug)
            continue
        res = client.post(f"/api/v2/{slug}", json=payload)
        if res.status_code != 201:
            print(f"{slug}: failed with {res.status_code}: {res.get_json()}", file=sys.stderr)
            return 1
        created += 1
        print(f"{slug}: created id {res.get_json()['data']['id']}")

    print(f"Done. {created} record(s) created.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
