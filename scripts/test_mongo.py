#!/usr/bin/env python3
"""Run the MongoDB integration tests (tests/test_domain_mongo.py) against a real MongoDB.

Those tests are skipped by the normal test run because they need MONGODB_TEST_URI. This
script provides a MongoDB, sets the variable, runs the tests and fails if any of them
were skipped, so a green result always means the MongoDB code was exercised.

Where the MongoDB comes from:

- By default, the `mongo` service from docker-compose.yml (host port 27018), run with
  Docker when it is available and otherwise with Podman: `docker compose`, then
  `podman compose`, then `podman-compose` (--engine picks one). If MongoDB is not already
  answering on port 27018, the script starts the service, waits until MongoDB answers and
  stops the service afterwards (`stop`, which keeps the mongo-data volume). A MongoDB that
  was already running is left running.
- With --uri, or when MONGODB_TEST_URI is already set, that server is used and no
  container engine is needed.

The tests only use the `order_flask_test` database, which they empty before each test and
drop at the end. Any database named in the URI is ignored, so `order-data` is not modified.

    scripts/test_mongo.py                 # compose MongoDB, MongoDB tests only
    scripts/test_mongo.py --all           # whole suite, MongoDB tests included
    scripts/test_mongo.py --keep-running  # leave the compose MongoDB running
    scripts/test_mongo.py --uri mongodb://localhost:27017
    scripts/test_mongo.py --engine podman  # use Podman even if Docker is available

Run it with the project's virtual environment (`source .venv/bin/activate`), or let
scripts/test_all.sh set everything up and call it.

Exit codes: 0 all tests passed and none were skipped, 1 tests failed or were skipped,
2 MongoDB could not be reached or started.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(ROOT, "tests")
MONGO_TEST_MODULE = "test_domain_mongo"
COMPOSE_SERVICE = "mongo"
COMPOSE_URI = "mongodb://localhost:27018"  # docker-compose.yml publishes 27018 -> 27017


def log(message: str) -> None:
    print(f"[test_mongo] {message}", file=sys.stderr, flush=True)


def redact(uri: str) -> str:
    """Hide the password in a connection string before printing it."""
    return re.sub(r"(mongodb(?:\+srv)?://[^:/@]+):[^@]*@", r"\1:***@", uri)


# --- container engine (Docker or Podman) -------------------------------------------------
#
# Only `up -d SERVICE` and `stop SERVICE` are used: docker compose, podman compose and
# podman-compose (1.0.6 on Ubuntu 24.04, which has no `up --wait` or `ps --status`) all
# support them. Whether MongoDB is running, and when it is ready, is checked by pinging it.


class Compose:
    def __init__(self, command: list[str], label: str, engine: str):
        self.command = command  # for example ["docker", "compose"] or ["podman-compose"]
        self.label = label
        self.engine = engine  # "docker" or "podman"

    def run(self, *args: str) -> int:
        log(f"running: {' '.join(self.command + list(args))}")
        return subprocess.run([*self.command, *args], cwd=ROOT, check=False).returncode

    def podman_container(self) -> dict | None:
        """The podman container of this project's compose service, or None if there is none.

        Compose tools label containers with the service name and the project directory.
        """
        result = probe(
            "podman", "ps", "--all", "--format", "json",
            "--filter", f"label=com.docker.compose.service={COMPOSE_SERVICE}",
        )
        if result is None or result.returncode != 0:
            return None
        try:
            containers = json.loads(result.stdout or "[]")
        except ValueError:
            return None
        root = os.path.realpath(ROOT)
        for container in containers:
            workdir = (container.get("Labels") or {}).get("com.docker.compose.project.working_dir", "")
            if workdir and os.path.realpath(workdir) == root:
                return container
        return None

    def explain_not_ready(self) -> None:
        """Print the service's state and recent log lines, to show why MongoDB is not answering."""
        if self.engine == "podman":
            container = self.podman_container()
            if container is None:
                log(f"no '{COMPOSE_SERVICE}' container exists")
                return
            name = (container.get("Names") or [container.get("Id", "?")])[0]
            log(f"container {name}: {container.get('State', '?')} ({container.get('Status', '')})")
            log("its last 20 log lines:")
            subprocess.run(["podman", "logs", "--tail", "20", container.get("Id", name)], check=False)
        else:
            subprocess.run([*self.command, "ps", "--all", COMPOSE_SERVICE], cwd=ROOT, check=False)
            log("its last 20 log lines:")
            subprocess.run([*self.command, "logs", "--tail", "20", COMPOSE_SERVICE], cwd=ROOT, check=False)


def probe(*command: str, timeout: int = 30) -> subprocess.CompletedProcess | None:
    """Run a detection command quietly. None if it is missing or hangs."""
    try:
        return subprocess.run(
            command, cwd=ROOT, check=False, text=True, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def find_docker() -> tuple[Compose | None, str]:
    if shutil.which("docker") is None:
        return None, "docker: not installed"
    version = probe("docker", "--version")
    if version is not None and "podman" in (version.stdout + version.stderr).lower():
        # The podman-docker package installs a `docker` command that runs podman.
        return None, "docker: the `docker` command is Podman's Docker emulation; using Podman directly"
    result = probe("docker", "compose", "version")
    if result is None or result.returncode != 0:
        return None, "docker: `docker compose` (Compose v2) is not available"
    result = probe("docker", "info")
    if result is None or result.returncode != 0:
        return None, "docker: the Docker daemon is not reachable (is Docker running?)"
    return Compose(["docker", "compose"], "docker compose", "docker"), ""


def find_podman() -> tuple[Compose | None, str]:
    if shutil.which("podman") is None:
        return None, "podman: not installed (scripts/install_podman.sh installs it)"
    result = probe("podman", "compose", "version")
    if result is not None and result.returncode == 0:
        return Compose(["podman", "compose"], "podman compose", "podman"), ""
    if shutil.which("podman-compose") is not None:
        result = probe("podman-compose", "version")
        if result is not None and result.returncode == 0:
            return Compose(["podman-compose"], "podman-compose", "podman"), ""
    return None, "podman: installed, but neither `podman compose` nor `podman-compose` works (scripts/install_podman.sh installs podman-compose)"


def find_compose(engine: str) -> Compose | None:
    finders = {"docker": [find_docker], "podman": [find_podman], "auto": [find_docker, find_podman]}[engine]
    reasons = []
    for finder in finders:
        compose, reason = finder()
        if compose is not None:
            return compose
        reasons.append(reason)
    log("no usable container engine found:")
    for reason in reasons:
        log(f"  {reason}")
    return None


# --- MongoDB -----------------------------------------------------------------------------


def wait_for_mongo(uri: str, timeout: int, quiet: bool = False) -> str | None:
    """Ping the server until it answers. Return its version, or None on timeout."""
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    deadline = time.monotonic() + timeout
    last_error = None
    while True:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        try:
            client.admin.command("ping")
            return client.server_info().get("version", "unknown")
        except PyMongoError as exc:
            last_error = exc
        finally:
            client.close()
        if time.monotonic() >= deadline:
            if not quiet:
                log(f"MongoDB did not answer within {timeout}s: {last_error}")
            return None
        time.sleep(1)


# --- tests -------------------------------------------------------------------------------


def iter_tests(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from iter_tests(test)
        else:
            yield test


def run_tests(run_all: bool, verbosity: int) -> int:
    # MONGODB_TEST_URI is read when the test module is imported, so it is set before this.
    sys.path.insert(0, ROOT)
    loader = unittest.TestLoader()
    pattern = "test*.py" if run_all else f"{MONGO_TEST_MODULE}.py"
    suite = loader.discover(TESTS_DIR, pattern=pattern, top_level_dir=TESTS_DIR)

    mongo_ids = {t.id() for t in iter_tests(suite) if t.id().startswith(MONGO_TEST_MODULE + ".")}
    if not mongo_ids:
        log(f"no tests found in tests/{MONGO_TEST_MODULE}.py")
        return 1

    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)

    # A skipped MongoDB test means the integration code was not exercised: treat it as a failure.
    skipped_mongo = [(t.id(), reason) for t, reason in result.skipped if t.id() in mongo_ids]
    for test_id, reason in skipped_mongo:
        log(f"SKIPPED (counted as failure): {test_id}: {reason}")

    ran_mongo = len(mongo_ids) - len(skipped_mongo)
    log(
        f"MongoDB tests: {ran_mongo} of {len(mongo_ids)} ran; "
        f"suite: {result.testsRun} run, {len(result.failures)} failures, "
        f"{len(result.errors)} errors, {len(result.skipped)} skipped"
    )
    if result.wasSuccessful() and not skipped_mongo:
        log("PASSED")
        return 0
    log("FAILED")
    return 1


# --- main --------------------------------------------------------------------------------


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run tests/test_domain_mongo.py against a real MongoDB.",
    )
    parser.add_argument(
        "--uri",
        default=os.environ.get("MONGODB_TEST_URI"),
        help="Use this MongoDB instead of the compose service (default: $MONGODB_TEST_URI).",
    )
    parser.add_argument(
        "--engine",
        choices=("auto", "docker", "podman"),
        default="auto",
        help="Container engine for the compose MongoDB (default: auto, Docker first, then Podman).",
    )
    parser.add_argument("--all", action="store_true", help="Run the whole suite, not just the MongoDB tests.")
    parser.add_argument(
        "--keep-running",
        action="store_true",
        help="Leave the compose MongoDB running afterwards, even if this script started it.",
    )
    parser.add_argument(
        "--timeout", type=int, default=60,
        help="Seconds to wait for MongoDB to answer after starting it (default: 60).",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Less test output.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        import pymongo  # noqa: F401
    except ImportError:
        log("pymongo is not installed. Run: pip install -r requirements.txt")
        return 2

    compose = None
    started_here = False
    if args.uri:
        uri = args.uri
        log(f"using the MongoDB given by --uri / MONGODB_TEST_URI: {redact(uri)}")
    else:
        uri = COMPOSE_URI
        compose = find_compose(args.engine)
        if compose is None:
            log("Install Docker or Podman, or start a MongoDB yourself and pass --uri.")
            return 2
        log(f"container engine: {compose.label}")
        if wait_for_mongo(uri, 0, quiet=True):
            log(f"MongoDB is already answering at {uri}; using it and leaving it running")
        else:
            if compose.run("up", "-d", COMPOSE_SERVICE) != 0:
                log(f"starting the '{COMPOSE_SERVICE}' service failed; the error is in the output above")
                return 2
            # podman-compose 1.0.6 exits 0 from `up -d` even when `podman run` failed (for example
            # because the image could not be pulled), so check that the container exists.
            if compose.engine == "podman" and compose.podman_container() is None:
                log(f"`{compose.label} up` reported success, but no '{COMPOSE_SERVICE}' container was created.")
                log("podman-compose does not report a failed `podman run`; the error is in the output")
                log("above, usually the image pull.")
                return 2
            started_here = True

    try:
        version = wait_for_mongo(uri, args.timeout)
        if version is None:
            if compose is not None:
                compose.explain_not_ready()
            return 2
        log(f"connected to MongoDB {version} at {redact(uri)}; tests use the 'order_flask_test' database")
        os.environ["MONGODB_TEST_URI"] = uri
        return run_tests(args.all, verbosity=1 if args.quiet else 2)
    finally:
        if started_here and not args.keep_running:
            log(f"stopping the '{COMPOSE_SERVICE}' service (the mongo-data volume is kept)")
            compose.run("stop", COMPOSE_SERVICE)


if __name__ == "__main__":
    sys.exit(main())
