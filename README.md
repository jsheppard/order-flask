# Order Flask API

A RESTful JSON API for managing orders, built with Flask.

This project is a port of a Spring Boot application. The `/api/v2` resources and the
domain models in `app/order_models.py` are ported from the Java `order-models` library
(`com.sbsolutions.order.models`), and the data lives in the same MongoDB database and
collections the Spring `order-data` application uses, so the two can run side by side.
See [Domain models](#domain-models-apporder_modelspy) and
[Domain resources](#domain-resources-apiv2) for how the Java types map to Python.
To set up the project and run all tests, see [Quick start](#quick-start-set-up-and-run-every-test).

## Requirements

- Python 3.10 or newer (the Docker image uses 3.14).
- For the MongoDB tests, one of: a MongoDB server (`mongod`), Docker, or Podman. The
  scripts below can install MongoDB or Podman for you.

## Quick start: set up and run every test

```bash
scripts/test_all.sh
```

`scripts/test_all.sh` prepares the project and runs both the unit tests and the MongoDB
tests, then prints a summary. It can be run again at any time; steps that are already done
are reused. See [Test](#test) for what it does and its options.

## Project layout

```
order-flask/
├── app/
│   ├── __init__.py        # create_app() application factory
│   ├── api.py             # /api blueprint: health check
│   ├── config.py          # Config classes (development / testing / production)
│   ├── errors.py          # ApiError and consistent JSON error responses
│   ├── order_models.py    # Domain models ported from the order-models Java library
│   ├── spring_mapping.py  # Spring Boot (MongoDB) document <-> model conversion
│   ├── domain_api.py      # /api/v2 blueprint: REST resources for the domain models
│   ├── domain_codec.py    # JSON <-> dataclass conversion, driven by type hints
│   └── domain_store.py    # MongoDB storage for /api/v2 (in-memory for tests)
├── java/                  # The Java order-models sources the Python models are ported from
├── scripts/
│   ├── test_all.sh        # Set up the project and run all tests (unit and MongoDB)
│   ├── task00.sh          # Run test_all.sh with the uploaded MongoDB; print PASSED or FAILED
│   ├── test_mongo.py      # Run the MongoDB tests against a real MongoDB
│   ├── install_mongodb.sh # Install and start MongoDB without containers
│   ├── install_podman.sh  # Install Podman and podman-compose
│   └── seed_test_data.py  # Load test fixtures into the compose MongoDB
├── tests/                 # unittest suite (test_domain_mongo.py needs a real MongoDB)
├── run.py                 # Entry point
├── requirements.txt
├── Dockerfile             # Production image for the API (gunicorn)
├── docker-compose.yml     # Test stack: MongoDB plus the API (see Containers)
└── fly.toml               # Fly.io deployment settings
```

## Setup

`scripts/test_all.sh` does this for you. To do it by hand:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Debian and Ubuntu, `python3 -m venv` needs the `python3-venv` package.

## Configuration

| Variable              | Used for                                                                 |
|-----------------------|--------------------------------------------------------------------------|
| `MONGODB_URI`         | MongoDB connection string for the `/api/v2` resources. Required unless `APP_CONFIG` is `testing`, which uses an in-memory store. |
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

There are two kinds of tests, both in `tests/`:

- **Unit tests** use the in-memory store and need no MongoDB.
- **MongoDB tests** (`tests/test_domain_mongo.py`, six tests) round-trip data through a real
  MongoDB. They run only when `MONGODB_TEST_URI` is set and are reported as skipped
  otherwise. They use the `order_flask_test` database, empty it before each test and drop
  it at the end, so no other database (such as `order-data`) is modified.

### Everything at once: `scripts/test_all.sh`

```bash
scripts/test_all.sh                            # set up, then run all tests
scripts/test_all.sh --mongodb-from PATH        # first install MongoDB from a .tgz, .deb or folder
scripts/test_all.sh --uri mongodb://HOST:PORT  # run the MongoDB tests against this server
scripts/test_all.sh --no-mongo                 # unit tests only
scripts/test_all.sh -q                         # less test output
```

It runs these steps and stops with a clear message if one cannot be completed:

1. **Python**: `python3` (or `$PYTHON`) must be 3.10 or newer.
2. **Virtual environment**: creates `.venv` if it is missing or broken and installs
   `requirements.txt` into it. The virtual environment does not need to be activated.
3. **Unit tests**: `python -m unittest discover -s tests`. The six MongoDB tests are
   skipped in this step.
4. **MongoDB**: uses the first of these that is available:
   1. `--uri`, or the `MONGODB_TEST_URI` environment variable;
   2. a `mongod` program (on `PATH`, in `/opt/mongodb` or `~/.local/opt/mongodb`, or installed
      by `--mongodb-from`). The script starts a temporary server with its own empty data
      folder on the first free port from 27019, and stops it and deletes the folder when it
      finishes, also after a failure or Ctrl-C;
   3. a MongoDB already answering on `localhost:27017`;
   4. Docker or Podman, through `scripts/test_mongo.py` and `docker-compose.yml`.
5. **MongoDB tests**: `scripts/test_mongo.py`, which fails if any MongoDB test is skipped.

It ends with a summary, for example:

```
[test_all] setup          OK       Python 3.12.3 in .venv, requirements.txt installed
[test_all] unit tests     PASSED   Ran 69 tests in 0.968s: OK (skipped=6) (the skipped ones are the MongoDB tests)
[test_all] MongoDB        OK       MongoDB 8.3.13, temporary mongod on localhost:27019 (deleted afterwards)
[test_all] MongoDB tests  PASSED   MongoDB tests: 6 of 6 ran; suite: 6 run, 0 failures, 0 errors, 0 skipped
[test_all] result: PASSED
```

Exit codes: `0` all tests passed, `1` tests failed, `2` setup failed (Python, `.venv`,
requirements, or no MongoDB available; the message lists ways to get one).

### Pass/fail only: `scripts/task00.sh`

```bash
scripts/task00.sh
```

Runs `scripts/test_all.sh --mongodb-from ../mongodb-linux-x86_64-ubuntu2404-8.3.13/` from the
project folder (so the MongoDB folder must be next to the project folder), then checks the
summary for `result: PASSED`. It prints only `PASSED` or `FAILED` and exits with `0` or `1`.
The full output of `test_all.sh` goes to `/tmp/task00.log` (or `$TASK00_LOG`).

### Unit tests only

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

### MongoDB tests: `scripts/test_mongo.py`

`scripts/test_mongo.py` runs the MongoDB tests against a real MongoDB. The scripts in
`scripts/` are executable and use the first `python3` on `PATH`, so activate the virtual
environment first (`source .venv/bin/activate`). `scripts/test_all.sh` calls it for you.

```bash
scripts/test_mongo.py                                  # MongoDB tests against the compose MongoDB
scripts/test_mongo.py --all                            # whole suite, MongoDB tests included (0 skipped)
scripts/test_mongo.py --keep-running                   # leave the compose MongoDB running afterwards
scripts/test_mongo.py --uri mongodb://localhost:27017  # use another MongoDB
scripts/test_mongo.py --engine podman                  # use Podman even if Docker is available
```

- Without `--uri` (or `MONGODB_TEST_URI`), it uses the `mongo` service from
  `docker-compose.yml` on port 27018. It runs the service with Docker (`docker compose`)
  when Docker is installed and its daemon is running, and otherwise with Podman
  (`podman compose`, then `podman-compose`). `--engine docker` or `--engine podman` picks
  one.
- If MongoDB is not already answering on port 27018, the script starts the service, waits
  until MongoDB answers and stops the service afterwards (the `mongo-data` volume is kept).
  A MongoDB that was already running is left running.
- If the service cannot start, the script says why instead of waiting: podman-compose 1.0.6
  reports success even when the container was not created (for example when the image
  cannot be pulled), so the script checks that the container exists. If MongoDB starts but
  never answers, it prints the container's state and last log lines.
- A skipped MongoDB test counts as a failure, so a passing run means all six ran.
- Exit codes: `0` passed with nothing skipped, `1` tests failed or were skipped,
  `2` MongoDB could not be reached or started (for example, neither Docker nor Podman is installed).

### Getting a MongoDB for the tests

Any one of these is enough. `scripts/test_all.sh` finds the first two on its own.

**Install MongoDB on the machine** with `scripts/install_mongodb.sh`. It installs MongoDB
Community, starts it on `localhost:27017` and checks that it is listening:

```bash
scripts/install_mongodb.sh                    # from MongoDB's official repository (root or sudo)
scripts/install_mongodb.sh --from FILE.tgz    # from a downloaded tarball (no root needed)
scripts/install_mongodb.sh --from DIR         # from the folder the tarball unpacks to
scripts/install_mongodb.sh --from FILE.deb    # from a mongodb-org-server .deb (Debian/Ubuntu)
scripts/install_mongodb.sh --dry-run          # print the commands only
scripts/install_mongodb.sh --no-start         # install without starting
```

- The repository install uses the 8.0 series and supports Ubuntu 20.04/22.04/24.04,
  Debian 12, RHEL-compatible 8 and 9, and macOS (Homebrew). It needs access to
  `repo.mongodb.org` and `pgp.mongodb.com`, and stops with a clear message if their names
  do not resolve.
- If those servers are blocked (for example on a network that only allows package
  registries), download MongoDB on another machine from
  <https://www.mongodb.com/try/download/community> (your Linux platform, package `tgz`),
  copy the file or the folder it unpacks to onto the machine, and use `--from`, or
  `scripts/test_all.sh --mongodb-from PATH`. It is installed into `/opt/mongodb` as root
  (with `mongod` linked into `/usr/local/bin`), or `~/.local/opt/mongodb` otherwise, with
  its database in `data/` there. Missing system libraries (`libcurl`, `libssl`) are
  installed with the package manager.
- Without systemd (for example in a container or a minimal VM), `mongod` runs in the
  background and the script prints the command that stops it.
- Exit codes: `0` installed (and listening), `1` installation or start failed, `2`
  unsupported platform or bad arguments, `3` root or sudo needed but not available.

**Use containers**: install Docker, or Podman with `scripts/install_podman.sh` (see
[Podman](#podman)). `scripts/test_mongo.py` then runs the `mongo` service from
`docker-compose.yml`. This needs access to Docker Hub to pull the `mongo` image.

**Use an existing server**: `scripts/test_all.sh --uri mongodb://HOST:PORT`.

## Containers

`docker-compose.yml` runs MongoDB 8 and the API together for testing. The commands below
use Docker Compose v2. With Podman, use `podman compose` in their place; podman-compose
1.0.6 (the version in Ubuntu 24.04) supports fewer options than Docker Compose.

```bash
docker compose up -d --build          # build the API image and start both services
curl http://localhost:8080/api/health # API on http://localhost:8080
docker compose logs -f app            # follow API logs
docker compose down                   # stop; keeps the mongo-data volume
docker compose down -v                # stop and delete the database volume
```

- The API container uses the production config (`APP_CONFIG=production`) and connects to
  `mongodb://mongo:27017/order-data`. Both are set in `docker-compose.yml`.
- MongoDB is published on host port 27018 (`mongodb://localhost:27018/order-data`), so it does
  not clash with a MongoDB already on `localhost:27017`. To use a shell against it, run
  `docker compose exec mongo mongosh order-data`.
- The `mongo-data` volume starts empty. Load data into it with the restore steps below, or
  load the test fixtures with `scripts/seed_test_data.py` (see the script for usage).
  `docker compose down -v` deletes the volume, so the data must be restored again after that.
- Image names are written in full (`docker.io/library/mongo:8` in `docker-compose.yml`,
  `docker.io/library/python:3.14-slim` in the `Dockerfile`) so that Podman can pull them
  too. Docker pulls the same images.

To restore an archive into the compose MongoDB, mount its folder read-only and run
`mongorestore` in a one-off container on the compose network:

```bash
docker compose run --rm --no-deps \
  -v /path/to/archive-folder:/restore:ro \
  --entrypoint mongorestore mongo \
  --uri="mongodb://mongo:27017" \
  --archive=/restore/order-data-YYYYMMDD-HHMMSS.archive.gz --gzip
```

Check that the API serves the data, for example `curl http://localhost:8080/api/v2/donuts`.

### Podman

`scripts/install_podman.sh` installs Podman and podman-compose with the system package
manager. It supports Ubuntu/Debian, Fedora/RHEL, openSUSE, Arch, Alpine and macOS
(Homebrew, where it also creates and starts a Podman machine). On Linux it needs root or
sudo. Anything already installed is left alone, and the script checks the result with
`podman info`:

```bash
scripts/install_podman.sh --dry-run      # show the commands without running them
scripts/install_podman.sh                # install podman and podman-compose
scripts/install_podman.sh --no-compose   # install podman only
scripts/install_podman.sh --short-names  # also pull short image names from Docker Hub
```

Exit codes: `0` installed and verified, `1` installation or verification failed, `2`
unsupported platform, `3` root or sudo needed but not available.

Podman does not accept short image names such as `mongo:8` unless a search registry is
configured, and Ubuntu and Debian configure none. That is why the project's image names
are written in full. To make Podman accept short names in your own commands too (for
example `podman run mongo:8`), run the script with `--short-names`. It writes
`/etc/containers/registries.conf.d/50-docker-hub.conf`, which makes Docker Hub the search
registry for every user on the machine. Delete that file to undo it. If you have your own
`~/.config/containers/registries.conf`, Podman ignores that system file for you, and the
script tells you what to add to yours.

## Backup and restore

The `order-data` database can be exported to a single compressed archive with
`mongodump` and loaded into another MongoDB with `mongorestore` (both come with the
MongoDB Database Tools). The archive includes the indexes.

Export (read-only against the source):

```bash
mkdir -p ~/order-data-exports
mongodump --uri="mongodb://localhost:27017/order-data" \
  --archive="$HOME/order-data-exports/order-data-$(date +%Y%m%d-%H%M%S).archive.gz" --gzip
```

Restore into the target MongoDB (this writes to the target, so check the URI first):

```bash
mongorestore --uri="mongodb://TARGET_HOST:27017" \
  --archive=/path/to/order-data-YYYYMMDD-HHMMSS.archive.gz --gzip
```

To load the data into a database with a different name, add
`--nsFrom='order-data.*' --nsTo='NEW_NAME.*'`. To restore into a non-empty database,
add `--drop` only if you intend to replace the existing collections.

To check an archive, restore it into a scratch database and compare document counts
with the source. Drop the scratch database afterward:

```bash
mongorestore --uri="mongodb://localhost:27017" --archive=/path/to/archive.gz --gzip \
  --nsFrom='order-data.*' --nsTo='order-data-verify.*'
```

To restore into the compose test stack instead, see [Containers](#containers).

The archive holds the full database, including the `user`, `gmail_config` and
`gmail_messages` collections, which may contain credentials and personal data. Store
it outside the repository and restrict who can read it.

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

Requests and responses use the snake_case field names from the model. Ids are strings:
with MongoDB they are the document's `_id`, a 24-character ObjectId hex string for new
items (the few Spring collections that use string ids keep them as they are). The
in-memory store the unit tests use numbers them `"1"`, `"2"`, ... within each resource. Enums are sent and returned by member name
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
