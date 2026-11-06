import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from bson import Decimal128, ObjectId

from app.domain_codec import decode_fields
from app.order_models import Donut, Item, Order, OrderStatus, ScheduledOrder
from app.spring_mapping import COLLECTIONS, document_fields, spring_document, spring_values

ORDER_DOC = {
    "_id": ObjectId("69b6ba4b6afd4426f89d351f"),
    "createdBy": "someone@example.com",
    "customerId": 1.0,
    "name": "Sandhills Event Center",
    "orderDate": datetime(2026, 3, 15, 13, 55, 23, 777000),
    "type": "DELIVERY",
    "deliverDate": datetime(2026, 3, 21),
    "approved": True,
    "status": "Approved",
    "items": [
        {
            "_id": "item-1",
            "orderId": "69b6ba4b6afd4426f89d351f",
            "itemId": "abc",
            "itemType": "GLAZED_DONUT",
            "qty": 42.0,
            "unitPrice": 1.95,
            "lineTotal": 81.9,
            "dozenProductId": "p-2",
        }
    ],
    "updatedAt": datetime(2026, 3, 16, 9, 0),
    "_class": "com.sbsolutions.order.models.Order",
    "someSpringOnlyField": "ignored",
}


def decode(model, doc):
    errors: list[str] = []
    kwargs = decode_fields(model, document_fields(model, doc), errors)
    if errors:
        raise AssertionError(errors)
    return model(**kwargs)


class ReadMappingTests(unittest.TestCase):
    def test_order_fields_and_ids(self):
        order = decode(Order, ORDER_DOC)
        self.assertEqual(order.id, "69b6ba4b6afd4426f89d351f")
        self.assertEqual(order.created_by, "someone@example.com")
        self.assertEqual(order.customer_id, 1)
        self.assertEqual(order.status, OrderStatus.APPROVED)
        self.assertEqual(order.updated_at, datetime(2026, 3, 16, 9, 0, tzinfo=timezone.utc))

    def test_nested_items(self):
        item = decode(Order, ORDER_DOC).items[0]
        self.assertEqual(item.id, "item-1")
        self.assertEqual(item.order_id, "69b6ba4b6afd4426f89d351f")
        self.assertEqual(item.qty, 42)
        self.assertEqual(item.dozen_product_id, "p-2")

    def test_deliver_date_is_a_date(self):
        self.assertEqual(decode(Order, ORDER_DOC).deliver_date, date(2026, 3, 21))

    def test_decimal128_money_is_decoded(self):
        donut = decode(Donut, {"_id": ObjectId(), "description": "A", "price": Decimal128("2.50")})
        self.assertEqual(donut.price, Decimal("2.50"))

    def test_scheduled_order_weekday_alias(self):
        order = decode(ScheduledOrder, {"_id": ObjectId(), "weekDay": 3.0, "recurrenceType": "MONTHLY"})
        self.assertEqual(order.weekday, 3)

    def test_nulls_and_missing_values_use_defaults(self):
        order = decode(Order, {"_id": "x", "status": None, "items": None, "customerId": None})
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.items, [])
        self.assertIsNone(order.customer_id)

    def test_string_ids_are_kept(self):
        self.assertEqual(decode(Order, {"_id": "1"}).id, "1")


class WriteMappingTests(unittest.TestCase):
    def test_document_uses_spring_names_and_omits_none(self):
        donut = Donut(description="Glazed", price=Decimal("2.5"), frosting=True, item_type=None)
        doc = spring_document(donut)
        self.assertEqual(doc["description"], "Glazed")
        self.assertEqual(doc["price"], Decimal128("2.5"))
        self.assertTrue(doc["frosting"])
        self.assertNotIn("itemType", doc)
        self.assertNotIn("id", doc)
        self.assertNotIn("specialPrice", doc)

    def test_enum_is_written_as_spring_stores_it(self):
        order = Order(status=OrderStatus.APPROVED)
        self.assertEqual(spring_document(order)["status"], "Approved")

    def test_nested_item_id_becomes_underscore_id(self):
        order = Order(items=[Item(id="i-1", order_id="o-1", qty=2)])
        self.assertEqual(spring_document(order)["items"][0], {"_id": "i-1", "orderId": "o-1", "qty": 2, "mix": False})

    def test_dates_are_written_as_bson_dates(self):
        order = Order(deliver_date=date(2026, 3, 21), created_at=datetime(2026, 3, 1, tzinfo=timezone.utc))
        doc = spring_document(order)
        self.assertEqual(doc["deliverDate"], datetime(2026, 3, 21, tzinfo=timezone.utc))
        self.assertEqual(doc["createdAt"], datetime(2026, 3, 1, tzinfo=timezone.utc))

    def test_partial_update_keeps_explicit_nulls_only_in_changes(self):
        values = spring_values(Donut, {"description": "New", "special_price": None, "allow_dozen": True})
        self.assertEqual(values, {"description": "New", "specialPrice": None, "allowDozen": True})

    def test_weekday_alias_on_write(self):
        self.assertEqual(spring_document(ScheduledOrder(weekday=2))["weekDay"], 2)


class SpecialFieldTests(unittest.TestCase):
    def test_day_name_becomes_monday_zero_int(self):
        order = decode(ScheduledOrder, {"_id": ObjectId(), "recurrenceType": "MONTHLY", "monthlyDayOfWeek": "THURSDAY"})
        self.assertEqual(order.monthly_day_of_week, 3)
        self.assertEqual(spring_document(order)["monthlyDayOfWeek"], "THURSDAY")

    def test_status_times_are_time_of_day(self):
        from datetime import time as dtime
        from app.order_models import Status

        status = decode(Status, {"_id": "s", "startTime": datetime(2026, 11, 3, 10, 0), "endTime": datetime(2026, 11, 3, 18, 30)})
        self.assertEqual(status.start_time, dtime(10, 0))
        self.assertEqual(status.end_time, dtime(18, 30))
        self.assertEqual(spring_document(status)["startTime"], datetime(1970, 1, 1, 10, 0, tzinfo=timezone.utc))


class CollectionMapTests(unittest.TestCase):
    def test_every_resource_has_a_spring_collection(self):
        from app.domain_api import RESOURCES

        self.assertEqual({r.slug for r in RESOURCES}, set(COLLECTIONS))
        self.assertEqual(COLLECTIONS["orders"], "order")
        self.assertEqual(COLLECTIONS["scheduled-orders"], "scheduledOrder")


if __name__ == "__main__":
    unittest.main()
