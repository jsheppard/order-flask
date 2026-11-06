"""Round-trip tests against a real MongoDB. Skipped unless MONGODB_TEST_URI is set.

The database is ``order_flask_test`` and is dropped at the end of the class. The
tests use the Spring collection names inside it, so the Spring application's own
database (``order-data``) is never touched.
"""

import os
import unittest

from bson import ObjectId

from app import create_app
from app.config import Config

TEST_URI = os.environ.get("MONGODB_TEST_URI")
TEST_DATABASE = "order_flask_test"


@unittest.skipUnless(TEST_URI, "set MONGODB_TEST_URI to run MongoDB integration tests")
class MongoDomainStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class MongoTestConfig(Config):
            TESTING = True
            DOMAIN_STORE = "mongo"
            MONGODB_URI = TEST_URI
            MONGODB_DATABASE = TEST_DATABASE

        cls.app = create_app(MongoTestConfig)
        cls.client = cls.app.test_client()
        cls.store = cls.app.extensions["domain_store"]
        cls.db = cls.store._db

    @classmethod
    def tearDownClass(cls):
        cls.store._client.drop_database(TEST_DATABASE)
        cls.store._client.close()

    def setUp(self):
        for name in self.db.list_collection_names():
            self.db.drop_collection(name)

    def create(self, slug, payload):
        res = self.client.post(f"/api/v2/{slug}", json=payload)
        self.assertEqual(res.status_code, 201, res.get_json())
        return res.get_json()["data"]["id"]

    def test_donut_round_trip_uses_spring_collection(self):
        donut_id = self.create("donuts", {"description": "Glazed", "price": "2.50"})
        self.assertTrue(ObjectId.is_valid(donut_id))

        self.assertIn("donut", self.db.list_collection_names())
        self.assertFalse([n for n in self.db.list_collection_names() if n.startswith("flask_")])

        stored = self.db["donut"].find_one({"_id": ObjectId(donut_id)})
        self.assertEqual(stored["description"], "Glazed")
        self.assertEqual(str(stored["price"]), "2.50")
        self.assertIn("_id", stored)

        fetched = self.client.get(f"/api/v2/donuts/{donut_id}").get_json()["data"]
        self.assertEqual(fetched["price"], "2.50")
        self.assertEqual(fetched["location_allowed"], "ANY")

    def test_update_and_delete(self):
        frosting_id = self.create("frostings", {"description": "Maple"})
        patched = self.client.patch(f"/api/v2/frostings/{frosting_id}", json={"description": "Chocolate"})
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(self.db["frosting"].find_one({"_id": ObjectId(frosting_id)})["description"], "Chocolate")

        self.assertEqual(self.client.delete(f"/api/v2/frostings/{frosting_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/v2/frostings/{frosting_id}").status_code, 404)
        self.assertEqual(self.db["frosting"].count_documents({}), 0)

    def test_partial_update_keeps_spring_only_fields(self):
        self.db["location"].insert_one({"name": "Old", "createdAt": "keep-me", "visible": True})
        loc = self.db["location"].find_one({"name": "Old"})
        res = self.client.patch(f"/api/v2/locations/{loc['_id']}", json={"city": "Lincoln"})
        self.assertEqual(res.status_code, 200)
        stored = self.db["location"].find_one({"_id": loc["_id"]})
        self.assertEqual(stored["city"], "Lincoln")
        self.assertEqual(stored["createdAt"], "keep-me")
        self.assertTrue(stored["visible"])

    def test_order_with_nested_items_and_enums(self):
        order_id = self.create(
            "scheduled-orders",
            {"name": "Ada", "status": "approved", "items": [{"qty": 2, "item_type": "roll"}]},
        )
        data = self.client.get(f"/api/v2/scheduled-orders/{order_id}").get_json()["data"]
        self.assertEqual(data["status"], "APPROVED")
        self.assertEqual(data["items"][0]["item_type"], "ROLL")
        self.assertEqual(data["items"][0]["qty"], 2)

        stored = self.db["scheduledOrder"].find_one({"_id": ObjectId(order_id)})
        self.assertEqual(stored["status"], "Approved")  # Spring stores the label
        self.assertEqual(stored["items"][0]["itemType"], "ROLL")

    def test_list_is_in_creation_order(self):
        ids = [self.create("toppings", {"description": d}) for d in ("A", "B", "C")]
        listed = self.client.get("/api/v2/toppings").get_json()
        self.assertEqual([item["id"] for item in listed["data"]], ids)

    def test_dozen_rule_is_enforced_before_storing(self):
        res = self.client.post(
            "/api/v2/rolls",
            json={"description": "R", "price": 1, "allow_dozen": True, "product_dozen": True},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(self.db["roll"].count_documents({}), 0)


if __name__ == "__main__":
    unittest.main()
