import unittest

from app import create_app
from app.config import TestingConfig
from app.domain_api import RESOURCES


def details(res) -> list[str]:
    return res.get_json()["error"].get("details", [])


class DomainApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)  # fresh store per test
        self.client = self.app.test_client()

    def post(self, slug, payload):
        return self.client.post(f"/api/v2/{slug}", json=payload)

    def test_every_resource_lists_empty(self):
        for res in RESOURCES:
            with self.subTest(resource=res.slug):
                body = self.client.get(f"/api/v2/{res.slug}").get_json()
                self.assertEqual(body, {"data": [], "count": 0})

    def test_create_fetch_update_delete_donut(self):
        res = self.post("donuts", {"description": "Glazed", "price": 2.5, "item_type": "glazed_donut"})
        self.assertEqual(res.status_code, 201)
        created = res.get_json()["data"]
        self.assertEqual(created["id"], "1")
        self.assertEqual(created["price"], "2.5")
        self.assertEqual(created["item_type"], "GLAZED_DONUT")
        self.assertEqual(created["location_allowed"], "ANY")
        self.assertEqual(res.headers["Location"], "/api/v2/donuts/1")

        got = self.client.get("/api/v2/donuts/1")
        self.assertEqual(got.get_json()["data"]["description"], "Glazed")

        patched = self.client.patch("/api/v2/donuts/1", json={"frosting": True, "price": "3.00"})
        self.assertEqual(patched.status_code, 200)
        self.assertTrue(patched.get_json()["data"]["frosting"])
        self.assertEqual(patched.get_json()["data"]["price"], "3.00")

        deleted = self.client.delete("/api/v2/donuts/1")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get("/api/v2/donuts/1").status_code, 404)

    def test_ids_are_per_resource(self):
        self.post("donuts", {"description": "A", "price": 1})
        roll = self.post("rolls", {"description": "B", "price": 1})
        self.assertEqual(roll.get_json()["data"]["id"], "1")

    def test_order_with_nested_items_and_enum_status(self):
        res = self.post(
            "scheduled-orders",
            {
                "name": "Ada",
                "status": "approved",
                "items": [{"product_name": "Glazed", "qty": 2, "unit_price": 1.25, "item_type": "ROLL"}],
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        self.assertEqual(data["status"], "APPROVED")
        self.assertEqual(data["type"], "DELIVERY")  # default
        self.assertEqual(data["items"][0]["qty"], 2)
        self.assertEqual(data["items"][0]["item_type"], "ROLL")
        self.assertIsNone(data["items"][0]["frosting_id"])

    def test_scheduled_order_includes_order_fields(self):
        res = self.post("scheduled-orders", {"name": "Weekly", "weekday": 0, "recurrence_type": "monthly"})
        data = res.get_json()["data"]
        self.assertEqual(data["name"], "Weekly")
        self.assertEqual(data["recurrence_type"], "MONTHLY")
        self.assertEqual(data["status"], "PENDING")

    def test_dates_round_trip_as_iso_strings(self):
        res = self.post("announcements", {"title": "Holiday", "start_date": "2026-12-24", "end_date": "2026-12-26"})
        data = res.get_json()["data"]
        self.assertEqual(data["start_date"], "2026-12-24")
        self.assertEqual(data["end_date"], "2026-12-26")
        self.assertTrue(data["active"])

    def test_required_fields_are_enforced_on_create(self):
        res = self.post("locations", {"name": "  "})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            details(res),
            ["name is required", "address1 is required", "city is required", "state is required", "zip is required"],
        )

    def test_required_fields_cannot_be_cleared_on_update(self):
        self.post("donuts", {"description": "A", "price": 1})
        res = self.client.patch("/api/v2/donuts/1", json={"description": None})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(details(res), ["description is required"])

    def test_type_errors_report_the_path(self):
        res = self.post("scheduled-orders", {"items": [{"qty": "two", "unit_price": "cheap"}]})
        self.assertEqual(res.status_code, 400)
        self.assertIn("items[0].qty must be an integer", details(res))
        self.assertIn("items[0].unit_price must be a number", details(res))

    def test_money_must_be_non_negative_decimal(self):
        res = self.post("donuts", {"description": "A", "price": -1})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(details(res), ["price must be a non-negative number"])

    def test_bad_enum_lists_choices(self):
        res = self.post("scheduled-orders", {"status": "shipped"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            details(res),
            ["status must be one of: PENDING, APPROVED, COMPLETED, DENIED, DECLINED, DELETED"],
        )

    def test_unknown_and_server_fields_are_rejected(self):
        res = self.post("frostings", {"description": "Ada", "nickname": "x", "id": "99", "created_at": "2026-01-01"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(details(res), ["unknown fields: created_at, id, nickname"])

    def test_pastry_dozen_flags_cannot_both_be_true(self):
        res = self.post("donuts", {"description": "A", "price": 1, "allow_dozen": True, "product_dozen": True})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(details(res), ["allow_dozen and product_dozen cannot both be true"])

        self.post("rolls", {"description": "B", "price": 1, "allow_dozen": True})
        res = self.client.patch("/api/v2/rolls/1", json={"product_dozen": True})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(details(res), ["allow_dozen and product_dozen cannot both be true"])
        self.assertFalse(self.client.get("/api/v2/rolls/1").get_json()["data"]["product_dozen"])

    def test_patch_rejects_empty_body_and_unknown_fields(self):
        self.post("frostings", {"description": "Maple"})
        self.assertEqual(self.client.patch("/api/v2/frostings/1", json={}).status_code, 400)
        res = self.client.patch("/api/v2/frostings/1", json={"flavour": "x"})
        self.assertEqual(details(res), ["unknown fields: flavour"])

    def test_missing_items_return_404_and_bad_bodies_return_400(self):
        self.assertEqual(self.client.get("/api/v2/icings/42").status_code, 404)
        self.assertEqual(self.client.patch("/api/v2/icings/42", json={"description": "x"}).status_code, 404)
        self.assertEqual(self.client.delete("/api/v2/icings/42").status_code, 404)
        res = self.client.post("/api/v2/icings", data="not json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

    def test_orders_resource_is_read_only(self):
        res = self.post("orders", {"name": "Ada"})
        self.assertEqual(res.status_code, 405)
        self.assertEqual(set(res.headers["Allow"].split(", ")), {"GET", "HEAD", "OPTIONS"})
        self.assertEqual(res.get_json()["error"]["code"], 405)
        self.assertEqual(self.client.patch("/api/v2/orders/1", json={"name": "x"}).status_code, 405)
        self.assertEqual(self.client.delete("/api/v2/orders/1").status_code, 405)

    def test_stores_are_isolated_between_apps(self):
        self.post("toppings", {"description": "Sprinkles"})
        other = create_app(TestingConfig).test_client()
        self.assertEqual(other.get("/api/v2/toppings").get_json()["count"], 0)


if __name__ == "__main__":
    unittest.main()
