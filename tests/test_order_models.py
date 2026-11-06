import unittest
from datetime import date
from decimal import Decimal

from app.order_models import (
    Announcement,
    Donut,
    ItemType,
    ItemTypeLimit,
    Merchandise,
    MonthlyDayPattern,
    Order,
    OrderStatus,
    OrderType,
    Permission,
    Product,
    ProductLocationAllowed,
    Role,
    Roll,
    ScheduledOrder,
    User,
)


class OrderStatusTests(unittest.TestCase):
    def test_str_returns_label(self):
        self.assertEqual(str(OrderStatus.APPROVED), "Approved")

    def test_from_label_matches_label_or_name_case_insensitively(self):
        self.assertIs(OrderStatus.from_label("approved"), OrderStatus.APPROVED)
        self.assertIs(OrderStatus.from_label("DENIED"), OrderStatus.DENIED)
        self.assertIs(OrderStatus.from_label("Completed"), OrderStatus.COMPLETED)

    def test_from_label_defaults_to_pending(self):
        self.assertIs(OrderStatus.from_label(None), OrderStatus.PENDING)
        self.assertIs(OrderStatus.from_label("nonsense"), OrderStatus.PENDING)


class EntityDefaultsTests(unittest.TestCase):
    def test_order_defaults(self):
        order = Order(id="1")
        self.assertIs(order.type, OrderType.DELIVERY)
        self.assertIs(order.status, OrderStatus.PENDING)
        self.assertFalse(order.approved)
        self.assertEqual(order.items, [])

    def test_order_items_are_not_shared_between_instances(self):
        a, b = Order(), Order()
        a.items.append("x")
        self.assertEqual(b.items, [])

    def test_scheduled_order_is_an_order(self):
        scheduled = ScheduledOrder(weekday=0)
        self.assertIsInstance(scheduled, Order)
        self.assertIs(scheduled.status, OrderStatus.PENDING)

    def test_announcement_effective_end_date(self):
        single = Announcement(start_date=date(2026, 12, 25))
        self.assertEqual(single.effective_end_date, date(2026, 12, 25))
        self.assertFalse(single.is_multi_day)
        self.assertEqual(single.color, "#2962FF")
        self.assertTrue(single.active)

        multi = Announcement(start_date=date(2026, 12, 24), end_date=date(2026, 12, 26))
        self.assertEqual(multi.effective_end_date, date(2026, 12, 26))
        self.assertTrue(multi.is_multi_day)

    def test_user_defaults_and_helpers(self):
        user = User(first_name="Ada", last_name="Lovelace")
        self.assertTrue(user.allow_notifications)
        self.assertEqual(user.theme, "light")
        self.assertEqual(user.full_name, "Ada Lovelace")
        self.assertEqual(user.last_login_location, "Unknown location")
        self.assertFalse(user.has_geolocation_data())

        user.last_login_city, user.last_login_country = "London", "United Kingdom"
        self.assertEqual(user.last_login_location, "London, United Kingdom")


class EqualityTests(unittest.TestCase):
    def test_entities_compare_by_id(self):
        self.assertEqual(Order(id="1", name="A"), Order(id="1", name="B"))
        self.assertNotEqual(Order(id="1"), Order(id="2"))

    def test_different_classes_with_same_id_are_not_equal(self):
        self.assertNotEqual(Donut(id="1"), Roll(id="1"))
        self.assertNotEqual(Product(id="1"), Donut(id="1"))

    def test_entities_are_hashable_by_id(self):
        self.assertEqual(len({Order(id="1"), Order(id="1", name="B")}), 1)

    def test_user_compares_by_all_fields(self):
        self.assertNotEqual(User(id="1", email="a@x"), User(id="1", email="b@x"))


class DozenRuleTests(unittest.TestCase):
    def test_setting_allow_dozen_clears_product_dozen(self):
        donut = Donut(id="d", product_dozen=True)
        donut.set_allow_dozen(True)
        self.assertTrue(donut.allow_dozen)
        self.assertFalse(donut.product_dozen)

    def test_setting_product_dozen_clears_allow_dozen(self):
        roll = Roll(id="r", allow_dozen=True)
        roll.set_product_dozen(True)
        self.assertTrue(roll.product_dozen)
        self.assertFalse(roll.allow_dozen)

    def test_setting_false_does_not_touch_the_other_flag(self):
        donut = Donut(id="d", allow_dozen=True)
        donut.set_product_dozen(False)
        self.assertTrue(donut.allow_dozen)


class ProductTests(unittest.TestCase):
    def test_product_defaults(self):
        product = Product(id="p", description="Glazed", price=Decimal("1.25"))
        self.assertEqual(product.order, 0)
        self.assertIs(product.location_allowed, ProductLocationAllowed.ANY)

    def test_merchandise_defaults(self):
        shirt = Merchandise(id="m", item_type=ItemType.SHIRT, size="M")
        self.assertFalse(shirt.has_size_options)
        self.assertFalse(shirt.has_color_options)
        self.assertIsInstance(shirt, Product)


class ItemTypeLimitTests(unittest.TestCase):
    def test_create_defaults_covers_every_item_type_unconstrained(self):
        limits = ItemTypeLimit.create_defaults()
        self.assertEqual([limit.item_type for limit in limits], list(ItemType))
        self.assertTrue(all(limit.capacity == -1 for limit in limits))


class PermissionTests(unittest.TestCase):
    def test_display_name_includes_roles(self):
        self.assertEqual(Permission.MANAGE_USERS.display_name, "Manage Users (ADMIN)")
        self.assertEqual(Permission.VIEW_BOARD.display_name, "View Pickup/Deliver (ADMIN, STAFF)")

    def test_default_roles_are_staff_and_admin(self):
        self.assertEqual(Permission.REVIEW_ORDERS.allowed_roles, frozenset({Role.STAFF, Role.ADMIN}))


class MonthlyDayPatternTests(unittest.TestCase):
    def test_occurrence_numbers(self):
        self.assertEqual(MonthlyDayPattern.LAST_OCCURRENCE.occurrence_number, 5)
        self.assertEqual(MonthlyDayPattern.LAST_BUSINESS_DAY.display_name, "Last Business Day")


if __name__ == "__main__":
    unittest.main()
