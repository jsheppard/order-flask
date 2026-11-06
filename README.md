# Order Flask API

A RESTful JSON API for managing orders, built with Flask.

This project is a port of a Spring Boot application. The `/api/v2` resources and the
domain models in `app/order_models.py` are ported from the Java `order-models` library
(`com.sbsolutions.order.models`), and the data lives in the same MongoDB database and
collections the Spring `order-data` application uses, so the two can run side by side.
See [Domain models](#domain-models-apporder_modelspy) and
[Domain resources](#domain-resources-apiv2) for how the Java types map to Python.

## Project layout

```
order-flask/
├── app/
│   ├── __init__.py    # create_app() application factory
│   ├── api.py         # /api blueprint: health check
│   ├── config.py      # Config classes (development / testing / production)
│   ├── errors.py      # ApiError and consistent JSON error responses
│   ├── order_models.py # Domain models ported from the order-models Java library
│   ├── spring_mapping.py # Spring Boot (MongoDB) document <-> model conversion
│   ├── domain_api.py  # /api/v2 blueprint: REST resources for the domain models
│   ├── domain_codec.py # JSON <-> dataclass conversion, driven by type hints
│   ├── domain_store.py # MongoDB storage for /api/v2 (in-memory for tests)
├── tests/
├── run.py             # Entry point
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

| Variable              | Used for                                                                 |
|-----------------------|--------------------------------------------------------------------------|
| `MONGODB_URI`         | MongoDB connection string for the `/api/v2` resources. Required unless `DOMAIN_STORE` is `memory`. |
| `SPRING_MONGODB_URI`  | Fallback for `MONGODB_URI`; the variable the Spring `order-data` app uses. |
| `MONGODB_DATABASE`    | Optional. Database name, overriding the database named in the URI path.  |
| `APP_CONFIG`          | `development` (default), `testing` or `production`.                      |
| `PORT`                | Port for `python run.py` (default `5000`).                               |

The `/api/v2` resources use the collections the Spring order-data application uses (`donut`,
`roll`, `order`, and so on; see `app/spring_mapping.py` for the full list). Documents
are converted between the Spring shape (camelCase keys, ObjectId `_id`, BSON dates and
Decimal128 money) and the models. Spring-only fields are kept when a document is updated.
`/api/v2/orders` is read-only: its POST, PATCH and DELETE return 405.

The app will not start in `development` or `production` without `MONGODB_URI`
(or with a URI that has no database name and no `MONGODB_DATABASE`).

## Run

```bash
export MONGODB_URI="mongodb://localhost:27017/order-data"  # see Configuration
python run.py                       # development server on http://localhost:5000
APP_CONFIG=production python run.py # or serve with gunicorn: gunicorn "run:app"
```

## Test

```bash
python -m unittest discover -s tests -v
```

The unit tests use the in-memory store and do not need MongoDB. The MongoDB round-trip
tests in `tests/test_domain_mongo.py` run only when `MONGODB_TEST_URI` is set. They
use the `order_flask_test` database and drop it when they finish:

```bash
MONGODB_TEST_URI="$MONGODB_URI" python -m unittest tests.test_domain_mongo -v
```

## Endpoints

| Method | Path          | Description  |
|--------|---------------|--------------|
| GET    | `/api/health` | Health check |

The domain resources are under `/api/v2`, described below.

## Examples

Create a donut:

```bash
curl -X POST http://localhost:5000/api/v2/donuts \
  -H "Content-Type: application/json" \
  -d '{"description": "Glazed", "price": "2.50", "frosting": true}'
```

List locations from Z to A:

```bash
curl "http://localhost:5000/api/v2/locations?sort=-name"
```

## Error format

All errors share one shape:

```json
{
  "error": {
    "code": 400,
    "message": "Validation failed",
    "details": ["price must be a non-negative number"]
  }
}
```

## Domain resources (`/api/v2`)

Each model in `app/order_models.py` is exposed as a REST resource under `/api/v2`.
Every resource has the same five routes. Slugs and the `id` format are shown below.

| Method | Path                          | Description                                  |
|--------|-------------------------------|----------------------------------------------|
| GET    | `/api/v2/<slug>`              | List items; returns `{"data": [...], "count": n}` |
| POST   | `/api/v2/<slug>`              | Create an item (returns `201` and `Location`) |
| GET    | `/api/v2/<slug>/<id>`         | Get one item                                 |
| PATCH  | `/api/v2/<slug>/<id>`         | Partially update an item                     |
| DELETE | `/api/v2/<slug>/<id>`         | Delete an item (returns `204`)               |

List routes accept `?sort=`: a comma-separated list of scalar fields, with `-` for
descending, for example `?sort=city,-name`. Missing values sort last in both directions.
Unknown or list-valued fields return 400 with the sortable fields listed. Without `sort`,
records come back in creation order.

Resources:

| Slug              | Model                  | Required on create                          |
|-------------------|------------------------|---------------------------------------------|
| `orders`          | `Order`                |                                             |
| `scheduled-orders`| `ScheduledOrder`       |                                             |
| `frostings`       | `Frosting`             |                                             |
| `icings`          | `Icing`                |                                             |
| `toppings`        | `Topping`              |                                             |
| `donuts`          | `Donut`                | `description`, `price`                      |
| `rolls`           | `Roll`                 | `description`, `price`                      |
| `merchandise`     | `Merchandise`          | `description`, `price`                      |
| `locations`       | `Location`             | `name`, `address1`, `city`, `state`, `zip`  |
| `statuses`        | `Status`               |                                             |
| `pricing-sheets`  | `PricingSheet`         |                                             |
| `item-type-limits`| `ItemTypeLimit`        |                                             |
| `sweepstakes`     | `Sweepstakes`          | `title`, `description`, `begin_date`, `end_date` |
| `announcements`   | `Announcement`         | `title`, `start_date`                       |

Requests and responses use the snake_case field names from the model. Ids are strings,
numbered from `"1"` within each resource. Enums are sent and returned by member name
(`"GLAZED_DONUT"`, `"PENDING"`), and the name is matched case-insensitively. Decimal money
fields (`price`, `special_price`) are returned as strings. `items[].unit_price` is a float
because the Java field is a `Double`. Dates are ISO 8601 strings.

Request bodies are checked against the model's field types. A bad body returns `400`
with every problem listed in `error.details`, using paths such as `items[0].qty`. Unknown
fields are rejected. `id`, `created_at` and `updated_at` are set by the server.
`donuts` and `rolls` cannot have both `allow_dozen` and `product_dozen` set to `true`.

Not exposed: `Item` (only meaningful inside an order), `Product` (abstract base),
`User` and `ContactMessage`. `User` holds login IPs, locations and contact details, and
`ContactMessage` holds customer inquiries. This API has no authentication, so those
two are left out until auth exists.

The `/api/v2/orders` resource uses the `order_models.Order` shape and Java status
names. Its data is in MongoDB (see Configuration).

## Domain models (`app/order_models.py`)

`app/order_models.py` is a port of the domain model classes from the Java
`order-models` library (`com.sbsolutions.order.models`). It contains dataclasses and
enums for orders and their line items, the catalog (products, donuts, rolls,
merchandise, frostings, icings, toppings), locations, placement windows, pricing,
production limits, contact messages, sweepstakes, announcements, users and permissions.

Conventions:

- Field names are snake_case versions of the Java names (`unitPrice` → `unit_price`).
- Java `@Id` fields are `id: str | None`, `None` until assigned. Entities compare and
  hash by `id` (and class), as the Java `@EqualsAndHashCode(of = "id")` does. `User`
  compares by all fields, as in Java.
- Money is `Decimal` (`float` where the Java field was `Double`). Java `Date` and
  `Instant` map to `datetime`, `LocalDate` to `date`, `LocalTime` to `time`.
- `DayOfWeek` is an `int` with Monday = 0, matching `datetime.weekday()`.
- `Donut` and `Roll` share `PastryProduct`. Use `set_allow_dozen()` and
  `set_product_dozen()` so that the two dozen flags are never both true.
- `Permission` members carry their allowed roles. The `display_name` property appends
  those roles. The Java source gave every permission a role list (`ADMIN` is in all of
  them), and the Java `ADMIN` implicit-access rule is not implemented here.

These models are exposed through the `/api/v2` resources (see above). Order statuses use
the Java names `PENDING`, `APPROVED`, `COMPLETED`, `DENIED`, `DECLINED` and `DELETED`.
Tests are in `tests/test_order_models.py` and run with the rest of the suite.

## Notes

- The `/api/v2` data is in MongoDB. Each PATCH reads the document and writes it back, so
  two simultaneous PATCHes to the same item can overwrite each other (last write wins).
- Money is handled with `Decimal` and returned as strings such as `"24.98"`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.
