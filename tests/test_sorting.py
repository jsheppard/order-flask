import unittest

from app import create_app
from app.config import TestingConfig


class ListSortingTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(TestingConfig).test_client()
        for name, city in [("Cherry", "Omaha"), ("apple", "Omaha"), ("Banana", "Lincoln"), ("Date", "Lincoln")]:
            res = self.client.post(
                "/api/v2/locations",
                json={"name": name, "city": city, "address1": "1 St", "state": "NE", "zip": "68508"},
            )
            self.assertEqual(res.status_code, 201, res.get_json())

    def names(self, query=""):
        res = self.client.get(f"/api/v2/locations{query}")
        self.assertEqual(res.status_code, 200, res.get_json())
        return [x["name"] for x in res.get_json()["data"]]

    def test_no_sort_keeps_creation_order(self):
        self.assertEqual(self.names(), ["Cherry", "apple", "Banana", "Date"])

    def test_ascending_is_case_insensitive(self):
        self.assertEqual(self.names("?sort=name"), ["apple", "Banana", "Cherry", "Date"])

    def test_descending_with_minus(self):
        self.assertEqual(self.names("?sort=-name"), ["Date", "Cherry", "Banana", "apple"])

    def test_multiple_keys(self):
        self.assertEqual(self.names("?sort=city,-name"), ["Date", "Banana", "Cherry", "apple"])

    def test_missing_values_sort_last_in_both_directions(self):
        # Only Banana has an address2; the other three are null.
        rid = next(x["id"] for x in self.client.get("/api/v2/locations").get_json()["data"] if x["name"] == "Banana")
        self.assertEqual(self.client.patch(f"/api/v2/locations/{rid}", json={"address2": "Suite 2"}).status_code, 200)
        others = {"Cherry", "apple", "Date"}
        for query in ("?sort=address2", "?sort=-address2"):
            with self.subTest(query=query):
                names = self.names(query)
                self.assertEqual(names[0], "Banana")
                self.assertEqual(set(names[1:]), others)

    def test_empty_sort_is_ignored(self):
        self.assertEqual(self.names("?sort="), self.names())

    def test_unknown_field_is_rejected_with_choices(self):
        res = self.client.get("/api/v2/locations?sort=bogus")
        self.assertEqual(res.status_code, 400)
        details = res.get_json()["error"]["details"]
        self.assertIn("unknown sort field: bogus", details)
        self.assertTrue(any(d.startswith("sortable fields: ") and "name" in d for d in details))

    def test_list_fields_cannot_be_sorted(self):
        res = self.client.get("/api/v2/orders?sort=items")
        self.assertEqual(res.status_code, 400)

    def test_sort_applies_to_every_list_endpoint(self):
        for slug in ("donuts", "toppings", "scheduled-orders", "announcements", "pricing-sheets"):
            with self.subTest(resource=slug):
                self.assertEqual(self.client.get(f"/api/v2/{slug}?sort=bogus").status_code, 400)
                self.assertEqual(self.client.get(f"/api/v2/{slug}?sort=-id").status_code, 200)


if __name__ == "__main__":
    unittest.main()
