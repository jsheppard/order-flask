"""Domain models ported from the Java ``order-models`` library.

Source: ``com.sbsolutions.order.models`` in the order-models project. Names are
snake_case versions of the Java field names. Java ``@Id`` fields become ``id``
(``None`` until assigned), and entities whose Java classes compare by ``id``
keep that behaviour via ``_IdEquality``.

These models are standalone. They are not wired into the API, and they do not
replace ``app.models.Order``/``OrderItem``, which use a different status
vocabulary (see README).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OrderStatus(Enum):
    """Order statuses. ``str()`` returns the human label, as in Java."""

    PENDING = "Pending"
    APPROVED = "Approved"
    COMPLETED = "Completed"
    DENIED = "Denied"
    DECLINED = "Declined"
    DELETED = "Deleted"

    @property
    def label(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_label(cls, label: str | None) -> OrderStatus:
        """Match by label or constant name, case-insensitively. Defaults to PENDING."""
        if label is None:
            return cls.PENDING
        for status in cls:
            if status.value.lower() == label.lower() or status.name.lower() == label.lower():
                return status
        return cls.PENDING


class OrderType(Enum):
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"
    STANDARD = "STANDARD"


class ItemType(Enum):
    GLAZED_DONUT = "GLAZED_DONUT"
    GLAZED_DONUT_HOLES = "GLAZED_DONUT_HOLES"
    CAKE_DONUT = "CAKE_DONUT"
    CAKE_DONUT_HOLES = "CAKE_DONUT_HOLES"
    RAISED_DONUT = "RAISED_DONUT"
    RAISED_DONUT_HOLES = "RAISED_DONUT_HOLES"
    ROLL = "ROLL"
    BIG_DONUT = "BIG_DONUT"
    MUFFIN = "MUFFIN"
    PASTRY = "PASTRY"
    COOKIE = "COOKIE"
    CROISSANT = "CROISSANT"
    BAGEL = "BAGEL"
    BEVERAGE = "BEVERAGE"
    GLUTEN_FREE = "GLUTEN_FREE"
    VEGAN = "VEGAN"
    HALAL = "HALAL"
    CUP = "CUP"
    SHIRT = "SHIRT"
    MISC = "MISC"
    MIX = "MIX"


class ProductType(Enum):
    DONUT = "DONUT"
    DONUT_HOLE = "DONUT_HOLE"
    ROLL = "ROLL"
    MIX = "MIX"
    BIG_DONUT = "BIG_DONUT"
    BEVERAGE = "BEVERAGE"
    OTHER = "OTHER"


class ProductLocationAllowed(Enum):
    """Where a product can be fulfilled."""

    ANY = "ANY"
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"


class OrderPlacementStatus(Enum):
    OFF = "OFF"
    SCHEDULED = "SCHEDULED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class RecurrenceType(Enum):
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class MonthlyDayPattern(Enum):
    """Which occurrence of a weekday in a month a scheduled order repeats on."""

    FIRST_OCCURRENCE = (1, "First")
    SECOND_OCCURRENCE = (2, "Second")
    THIRD_OCCURRENCE = (3, "Third")
    FOURTH_OCCURRENCE = (4, "Fourth")
    LAST_OCCURRENCE = (5, "Last")
    LAST_BUSINESS_DAY = (6, "Last Business Day")

    def __init__(self, occurrence_number: int, display_name: str) -> None:
        self.occurrence_number = occurrence_number
        self.display_name = display_name


class Role(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    STAFF = "STAFF"


class Permission(Enum):
    """Granular permissions. ``ADMIN`` implicitly holds all of them.

    Each member is ``(display_name, description, allowed_roles)``. The Java
    constructor appended the roles to the display name, which is what
    ``display_name`` does here. Roles are listed in ``Role`` declaration order,
    because Java's ``Set.of`` order is not stable.
    """

    MANAGE_PRODUCTS = ("Manage Products", "Edit donuts, rolls, frostings, icings, and toppings", {Role.ADMIN})
    MANAGE_USERS = ("Manage Users", "Access user management and edit user accounts", {Role.ADMIN})
    MANAGE_MESSAGES = ("Manage Messages", "Access and manage contact inquiries", {Role.ADMIN})
    MANAGE_SWEEPSTAKES = (
        "Manage Sweepstakes",
        "Create, edit, and manage promotional sweepstakes contests",
        {Role.ADMIN},
    )
    MANAGE_LOCATIONS = ("Manage Locations", "Add, edit, and remove store locations", {Role.ADMIN})
    MANAGE_PRODUCT_ORDERING = ("Manage Product Display Order", "Control display order of menu products", {Role.ADMIN})
    MANAGE_PRICING = ("Manage Pricing", "View and edit the pricing sheet", {Role.ADMIN})
    MANAGE_SCHEDULE = ("Manage Schedule", "Access and modify scheduling configuration", {Role.ADMIN})
    MANAGE_SYSTEM_MESSAGES = (
        "Manage System Messages",
        "Access and configure system messages for order statuses",
        {Role.ADMIN},
    )
    MANAGE_LIMITS = ("Manage Limits", "Configure item-type production capacity limits", {Role.STAFF, Role.ADMIN})
    REVIEW_ORDERS = ("Review Orders", "Access all orders review and management", {Role.STAFF, Role.ADMIN})
    MANAGE_DAILY_SPECIAL = ("Manage Daily Special", "Set and manage daily specials", {Role.STAFF, Role.ADMIN})
    VIEW_PRODUCTION = ("View Production Day", "Access production day planning", {Role.STAFF, Role.ADMIN})
    VIEW_BOARD = ("View Pickup/Deliver", "Access the pickup/delivery order board", {Role.STAFF, Role.ADMIN})
    VIEW_STATS = ("View Statistics", "Access application statistics and metrics", {Role.STAFF, Role.ADMIN})
    VIEW_DASHBOARD = ("View Dashboard", "Access administrative dashboard with KPI charts", {Role.ADMIN})
    VIEW_REPORTS = ("View Reports", "Access system reports and data exports", {Role.ADMIN})
    VIEW_ANNOUNCEMENTS = (
        "View Announcements",
        "Access announcements and events calendar",
        {Role.STAFF, Role.ADMIN},
    )

    def __init__(self, display_name: str, description: str, allowed_roles: set[Role]) -> None:
        self.description = description
        self.allowed_roles = frozenset(allowed_roles)
        roles = ", ".join(role.name for role in Role if role in self.allowed_roles)
        self.display_name = f"{display_name} ({roles})" if roles else display_name


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


class _IdEquality:
    """Equality and hashing by ``id`` and exact class, like Java's ``@EqualsAndHashCode(of = "id")``."""

    id: str | None

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))


@dataclass(kw_only=True, eq=False)
class Item(_IdEquality):
    """A line item in an order. Product details are copied in at order time."""

    id: str | None = None
    order_id: str | None = None
    item_id: str | None = None
    item_type: ItemType | None = None
    qty: int | None = None
    # Snapshot of product info at order time
    product_name: str | None = None
    product_image_url: str | None = None
    product_unit: str | None = None
    unit_price: float | None = None
    line_total: float | None = None
    # Customization
    frosting_id: str | None = None
    frosting_name: str | None = None
    icing_id: str | None = None
    icing_name: str | None = None
    topping_id: str | None = None
    topping_name: str | None = None
    notes: str | None = None
    mix: bool = False
    # Dozen grouping
    dozen_id: str | None = None
    dozen_name: str | None = None
    dozen_product_id: str | None = None
    dozen_product_name: str | None = None
    # Merchandise
    brand: str | None = None
    size: str | None = None
    color: str | None = None
    material: str | None = None


@dataclass(kw_only=True, eq=False)
class Order(_IdEquality):
    id: str | None = None
    created_by: str | None = None
    customer_id: int | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    order_date: datetime | None = None
    type: OrderType = OrderType.DELIVERY
    deliver_date: date | None = None
    approved: bool = False
    approved_date: date | None = None
    location_id: str | None = None
    status: OrderStatus = OrderStatus.PENDING
    calendar_event_id: str | None = None
    items: list[Item] = field(default_factory=list)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    slack_channel_id: str | None = None
    slack_message_ts: str | None = None


@dataclass(kw_only=True, eq=False)
class ScheduledOrder(Order):
    """A template order that repeats weekly or monthly."""

    # Java DayOfWeek is not used here; the weekday is an int with Monday=0,
    # matching datetime.weekday().
    weekday: int | None = None
    recurrence_type: RecurrenceType = RecurrenceType.WEEKLY
    monthly_pattern: MonthlyDayPattern | None = None
    monthly_day_of_week: int | None = None  # 0=Monday .. 6=Sunday


@dataclass(kw_only=True, eq=False)
class Frosting(_IdEquality):
    id: str | None = None
    description: str | None = None
    url: str | None = None
    image_original: str | None = None
    image_medium: str | None = None
    image_small: str | None = None
    image_icon: str | None = None


@dataclass(kw_only=True, eq=False)
class Icing(_IdEquality):
    id: str | None = None
    description: str | None = None
    url: str | None = None


@dataclass(kw_only=True, eq=False)
class Topping(_IdEquality):
    id: str | None = None
    description: str | None = None
    url: str | None = None


@dataclass(kw_only=True, eq=False)
class Product(_IdEquality):
    """Base catalog product. Subclasses: ``Donut``, ``Roll``, ``Merchandise``."""

    id: str | None = None
    order: int = 0
    description: str | None = None
    price: Decimal | None = None
    special_price: Decimal | None = None
    special_price_date: datetime | None = None
    item_type: ItemType | None = None
    location_allowed: ProductLocationAllowed = ProductLocationAllowed.ANY
    unit: str | None = None
    url: str | None = None
    available_days: str | None = None
    image_original: str | None = None
    image_medium: str | None = None
    image_small: str | None = None
    image_icon: str | None = None
    image_thumbnail: str | None = None


@dataclass(kw_only=True, eq=False)
class PastryProduct(Product):
    """Shared base for ``Donut`` and ``Roll``: frosting/icing/topping options and dozen flags.

    ``allow_dozen`` and ``product_dozen`` are never both true. Use the
    ``set_*`` methods to keep that invariant, as the Java setters do.
    """

    frosting: bool = False
    required_frosting: bool = False
    icing: bool = False
    required_icing: bool = False
    topping: bool = False
    required_topping: bool = False
    allow_mix: bool = False
    allow_dozen: bool = False
    product_dozen: bool = False

    def set_allow_dozen(self, allow_dozen: bool) -> None:
        self.allow_dozen = allow_dozen
        if allow_dozen:
            self.product_dozen = False

    def set_product_dozen(self, product_dozen: bool) -> None:
        self.product_dozen = product_dozen
        if product_dozen:
            self.allow_dozen = False


@dataclass(kw_only=True, eq=False)
class Donut(PastryProduct):
    pass


@dataclass(kw_only=True, eq=False)
class Roll(PastryProduct):
    pass


@dataclass(kw_only=True, eq=False)
class Merchandise(Product):
    size: str | None = None
    color: str | None = None
    material: str | None = None
    brand: str | None = None
    has_size_options: bool = False
    has_color_options: bool = False


@dataclass(kw_only=True, eq=False)
class Location(_IdEquality):
    id: str | None = None
    name: str | None = None
    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    phone: str | None = None
    email: str | None = None
    primary_location: bool = False
    visible: bool = True
    latitude: float | None = None
    longitude: float | None = None

    def has_geolocation(self) -> bool:
        return self.latitude is not None and self.longitude is not None


@dataclass(kw_only=True, eq=False)
class Status(_IdEquality):
    """Order-placement window and the notification messages for each order status."""

    id: str | None = None
    status: OrderPlacementStatus | None = None
    start_time: time | None = None
    end_time: time | None = None
    pending_message: str | None = None
    pending_subject: str = "Order Pending"
    approved_message: str | None = None
    approved_subject: str = "Order Approved"
    declined_message: str | None = None
    declined_subject: str = "Order Declined"
    completed_message: str | None = None
    completed_subject: str = "Order Completed"
    denied_message: str | None = None
    denied_subject: str = "Order Denied"
    deleted_message: str | None = None
    deleted_subject: str = "Order Deleted"
    staff_message: str | None = None


@dataclass(kw_only=True, eq=False)
class PricingSheet(_IdEquality):
    id: str | None = None
    location_id: str | None = None
    order: int | None = None
    product_type: ProductType | None = None
    product_code: str | None = None
    description: str | None = None
    unit: str | None = None
    price: Decimal | None = None


@dataclass(kw_only=True)
class ItemTypeLimit:
    """Production capacity for one item type. ``capacity == -1`` means unconstrained."""

    id: str | None = None
    item_type: ItemType | None = None
    capacity: int | None = None
    sheet_size: int | None = None

    @classmethod
    def create_defaults(cls) -> list[ItemTypeLimit]:
        return [cls(id=None, item_type=t, capacity=-1, sheet_size=None) for t in ItemType]


@dataclass(kw_only=True, eq=False)
class ContactMessage(_IdEquality):
    id: str | None = None
    name: str | None = None
    email: str | None = None
    subject: str | None = None
    message: str | None = None
    created_at: datetime | None = None


@dataclass(kw_only=True, eq=False)
class Sweepstakes(_IdEquality):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    begin_date: date | None = None
    end_date: date | None = None
    image_url: str | None = None
    winner_email: str | None = None
    winner_date: date | None = None
    ticket_number: str | None = None
    entered_users: list[str] | None = None
    calendar_event_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(kw_only=True, eq=False)
class Announcement(_IdEquality):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    color: str = "#2962FF"
    active: bool = True
    created_at: datetime | None = None
    created_by: str | None = None

    @property
    def effective_end_date(self) -> date | None:
        """The end date, or the start date when no end date is set."""
        return self.end_date if self.end_date is not None else self.start_date

    @property
    def is_multi_day(self) -> bool:
        return self.end_date is not None and self.end_date != self.start_date


@dataclass(kw_only=True)
class User:
    """Account created from OAuth2 sign-in. Compares by all fields, as Java ``@Data`` does."""

    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    picture: str | None = None
    role: set[Role] = field(default_factory=set)
    permissions: set[Permission] = field(default_factory=set)
    last_login_ip: str | None = None
    last_login_city: str | None = None
    last_login_country: str | None = None
    last_login_country_code: str | None = None
    last_login_latitude: float | None = None
    last_login_longitude: float | None = None
    last_login_timestamp: datetime | None = None
    last_login_device_type: str | None = None
    last_login_user_agent: str | None = None
    last_location_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled: bool = False
    contact_email: str | None = None
    contact_phone: str | None = None
    allow_notifications: bool = True
    theme: str = "light"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def last_login_location(self) -> str:
        if self.last_login_city is not None and self.last_login_country is not None:
            return f"{self.last_login_city}, {self.last_login_country}"
        if self.last_login_country is not None:
            return self.last_login_country
        return "Unknown location"

    def has_geolocation_data(self) -> bool:
        return self.last_login_ip is not None
