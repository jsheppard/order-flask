#!/usr/bin/env bash
# Set up the project and run every test: the unit tests (in-memory store) and the MongoDB
# integration tests (against a real MongoDB). Run it from anywhere; it works in the project.
#
#   scripts/test_all.sh                            # set up, then run all tests
#   scripts/test_all.sh --mongodb-from PATH        # first install MongoDB from a .tgz, .deb or folder
#   scripts/test_all.sh --uri mongodb://HOST:PORT  # run the MongoDB tests against this server
#   scripts/test_all.sh --no-mongo                 # unit tests only
#   scripts/test_all.sh -q                         # less test output
#
# Steps:
#   1. Python: $PYTHON, or python3, must be 3.10 or newer.
#   2. Virtual environment: creates .venv if it is missing or broken, then installs
#      requirements.txt into it.
#   3. Unit tests: `python -m unittest discover -s tests` with the in-memory store. The six
#      MongoDB tests are skipped in this step; step 5 runs them.
#   4. MongoDB: uses the first of these that is available:
#        a. --uri, or the MONGODB_TEST_URI environment variable;
#        b. a mongod program (on PATH, in /opt/mongodb or ~/.local/opt/mongodb, or installed
#           by --mongodb-from): a temporary server with its own empty data folder, on the first
#           free port from 27019. It is stopped and its folder deleted when the script ends;
#        c. a MongoDB already answering on localhost:27017;
#        d. Docker or Podman: the `mongo` service from docker-compose.yml, which
#           scripts/test_mongo.py starts and stops.
#      The tests only use the `order_flask_test` database and drop it when they finish.
#   5. MongoDB tests: scripts/test_mongo.py, which fails if any MongoDB test is skipped.
#
# Exit codes: 0 all tests passed, 1 tests failed, 2 setup failed (Python, .venv,
# requirements, or no MongoDB available).

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
VENV_PY="$VENV/bin/python"
MIN_PYTHON="3.10"

URI="${MONGODB_TEST_URI:-}"
MONGODB_FROM=""
NO_MONGO=0
QUIET=0

log() { printf '[test_all] %s\n' "$*" >&2; }
usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --uri)
            [ $# -ge 2 ] || { log "--uri needs a connection string"; exit 2; }
            URI="$2"; shift ;;
        --mongodb-from)
            [ $# -ge 2 ] || { log "--mongodb-from needs a file or folder"; exit 2; }
            MONGODB_FROM="$2"; shift ;;
        --no-mongo) NO_MONGO=1 ;;
        -q | --quiet) QUIET=1 ;;
        -h | --help) usage; exit 0 ;;
        *) log "unknown option: $1"; usage >&2; exit 2 ;;
    esac
    shift
done

cd "$ROOT" || exit 2

# Summary rows, printed at the end: "step|status|details".
SUMMARY=()
record() { SUMMARY+=("$1|$2|$3"); }

print_summary() {
    local row step status details
    log "------------------------------- summary -------------------------------"
    for row in ${SUMMARY[@]+"${SUMMARY[@]}"}; do
        IFS='|' read -r step status details <<< "$row"
        log "$(printf '%-14s %-8s %s' "$step" "$status" "$details")"
    done
}

finish() {
    local code=$1
    print_summary
    case "$code" in
        0) log "result: PASSED" ;;
        1) log "result: FAILED (see the test output above)" ;;
        *) log "result: SETUP FAILED (see the errors above)" ;;
    esac
    exit "$code"
}

redact() { printf '%s' "$1" | sed -E 's#(mongodb(\+srv)?://[^:/@]+):[^@]*@#\1:***@#'; }

# Is something accepting connections on localhost:$1?
listening() { (exec 3<> "/dev/tcp/127.0.0.1/$1") 2> /dev/null; }

# ---- 1. Python ------------------------------------------------------------------------------

PYTHON="${PYTHON:-python3}"
log "step 1/5: Python"
if ! command -v "$PYTHON" > /dev/null 2>&1; then
    log "ERROR: $PYTHON is not installed. Install Python $MIN_PYTHON or newer (or set PYTHON=/path/to/python)."
    record "setup" "FAILED" "$PYTHON not found"
    finish 2
fi
PY_VERSION="$("$PYTHON" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
if ! "$PYTHON" -c "import sys; sys.exit(sys.version_info < (3, 10))"; then
    log "ERROR: $PYTHON is Python $PY_VERSION; the project needs $MIN_PYTHON or newer (dataclass kw_only)."
    record "setup" "FAILED" "Python $PY_VERSION is older than $MIN_PYTHON"
    finish 2
fi
log "using $PYTHON (Python $PY_VERSION)"

# ---- 2. Virtual environment -------------------------------------------------------------------

log "step 2/5: virtual environment and requirements"
if [ -x "$VENV_PY" ] && "$VENV_PY" -c "import sys; sys.exit(sys.version_info < (3, 10))" 2> /dev/null; then
    log "reusing $VENV ($("$VENV_PY" --version 2>&1))"
else
    [ -e "$VENV" ] && log "$VENV is missing its Python or uses one older than $MIN_PYTHON; recreating it"
    if ! "$PYTHON" -m venv --clear "$VENV"; then
        log "ERROR: could not create $VENV."
        log "  On Debian and Ubuntu, install the venv module first: apt install python3-venv"
        record "setup" "FAILED" "python -m venv failed"
        finish 2
    fi
    log "created $VENV"
fi
if ! "$VENV_PY" -m pip install --quiet --disable-pip-version-check -r requirements.txt; then
    log "ERROR: installing requirements.txt into $VENV failed (see pip's message above)."
    record "setup" "FAILED" "pip install -r requirements.txt failed"
    finish 2
fi
log "requirements installed: $("$VENV_PY" -m pip freeze --disable-pip-version-check 2> /dev/null | grep -iE '^(flask|pymongo|gunicorn)==' | tr '\n' ' ')"
record "setup" "OK" "Python $("$VENV_PY" -c 'import platform; print(platform.python_version())') in .venv, requirements.txt installed"

VERBOSITY=(-v)
[ "$QUIET" = 1 ] && VERBOSITY=()
TMP_OUT="$(mktemp)"
MONGO_TMP=""
# shellcheck disable=SC2329  # invoked by the EXIT trap
cleanup() {
    rm -f "$TMP_OUT"
    if [ -n "$MONGO_TMP" ]; then
        # The pid file can be missing if the run was interrupted while mongod was starting, so
        # also look for the process by its data folder, which is unique to this run.
        local pids tries=30
        pids="$(cat "$MONGO_TMP/mongod.pid" 2> /dev/null; pgrep -f -- "--dbpath $MONGO_TMP/db" 2> /dev/null)"
        pids="$(printf '%s\n' "$pids" | sort -u | tr '\n' ' ')"
        if [ -n "${pids// /}" ]; then
            log "stopping the temporary mongod (pid ${pids% }) and deleting $MONGO_TMP"
            # shellcheck disable=SC2086  # one word per pid
            kill $pids 2> /dev/null
            # shellcheck disable=SC2086
            while kill -0 $pids 2> /dev/null && [ "$tries" -gt 0 ]; do sleep 1; tries=$((tries - 1)); done
        else
            log "deleting $MONGO_TMP"
        fi
        rm -rf "$MONGO_TMP"
    fi
}
trap cleanup EXIT
trap 'log "interrupted; cleaning up"; exit 130' INT TERM

# ---- 3. Unit tests ------------------------------------------------------------------------------

log "step 3/5: unit tests (in-memory store)"
# Unset MONGODB_TEST_URI so that this step is always the in-memory run.
env -u MONGODB_TEST_URI "$VENV_PY" -m unittest discover -s tests ${VERBOSITY[@]+"${VERBOSITY[@]}"} 2>&1 | tee "$TMP_OUT"
UNIT_STATUS=${PIPESTATUS[0]}
UNIT_RESULT="$(grep -E '^Ran [0-9]+ test' "$TMP_OUT" | tail -1): $(grep -E '^(OK|FAILED)' "$TMP_OUT" | tail -1)"
if [ "$UNIT_STATUS" -eq 0 ]; then
    record "unit tests" "PASSED" "$UNIT_RESULT (the skipped ones are the MongoDB tests)"
else
    record "unit tests" "FAILED" "$UNIT_RESULT"
fi

if [ "$NO_MONGO" = 1 ]; then
    record "MongoDB tests" "SKIPPED" "--no-mongo"
    [ "$UNIT_STATUS" -eq 0 ] && finish 0
    finish 1
fi

# ---- 4. MongoDB ---------------------------------------------------------------------------------

log "step 4/5: MongoDB"

if [ -n "$MONGODB_FROM" ]; then
    log "installing MongoDB from $MONGODB_FROM"
    if ! "$ROOT/scripts/install_mongodb.sh" --from "$MONGODB_FROM" --no-start; then
        log "ERROR: scripts/install_mongodb.sh --from $MONGODB_FROM failed (see above)."
        record "MongoDB" "FAILED" "install from $MONGODB_FROM failed"
        finish 2
    fi
fi

find_mongod() {
    local candidate
    for candidate in "$(command -v mongod 2> /dev/null)" /opt/mongodb/bin/mongod "$HOME/.local/opt/mongodb/bin/mongod"; do
        if [ -n "$candidate" ] && [ -x "$candidate" ]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

# Start a throwaway mongod with its own data folder on a free port, and set PORT. Runs in this
# shell (not in $(...)) so that MONGO_TMP reaches the cleanup trap.
PORT=""
start_temporary_mongod() {
    local mongod=$1 port=27019 tries=30 out
    while listening "$port"; do
        port=$((port + 1))
        [ "$port" -le 27099 ] || { log "ERROR: no free port between 27019 and 27099"; return 1; }
    done
    MONGO_TMP="$(mktemp -d "${TMPDIR:-/tmp}/order-flask-mongod.XXXXXX")"
    mkdir -p "$MONGO_TMP/db"
    log "starting a temporary mongod on localhost:$port (data in $MONGO_TMP)"
    # Output goes to a file so that the forked server cannot hold our stdout open.
    out="$MONGO_TMP/start.out"
    if ! "$mongod" --dbpath "$MONGO_TMP/db" --logpath "$MONGO_TMP/mongod.log" --pidfilepath "$MONGO_TMP/mongod.pid" \
        --bind_ip 127.0.0.1 --port "$port" --fork < /dev/null > "$out" 2>&1; then
        cat "$out" >&2
        log "ERROR: mongod did not start. Last lines of its log:"
        tail -n 20 "$MONGO_TMP/mongod.log" >&2 2> /dev/null
        return 1
    fi
    while ! listening "$port"; do
        tries=$((tries - 1))
        if [ "$tries" -le 0 ]; then
            log "ERROR: mongod is not listening on port $port after 30 seconds. Last lines of its log:"
            tail -n 20 "$MONGO_TMP/mongod.log" >&2 2> /dev/null
            return 1
        fi
        sleep 1
    done
    PORT="$port"
}

MONGO_ARGS=()
if [ -n "$URI" ]; then
    log "using the MongoDB from --uri / MONGODB_TEST_URI: $(redact "$URI")"
    MONGO_ARGS=(--uri "$URI")
    MONGO_SOURCE="given MongoDB $(redact "$URI")"
elif MONGOD="$(find_mongod)"; then
    log "found $MONGOD ($("$MONGOD" --version 2> /dev/null | sed -n 1p))"
    if ! start_temporary_mongod "$MONGOD"; then
        record "MongoDB" "FAILED" "temporary mongod did not start"
        finish 2
    fi
    MONGO_ARGS=(--uri "mongodb://localhost:$PORT")
    MONGO_SOURCE="temporary mongod on localhost:$PORT (deleted afterwards)"
elif listening 27017; then
    log "a MongoDB is already answering on localhost:27017; using it (only the order_flask_test database is touched)"
    MONGO_ARGS=(--uri "mongodb://localhost:27017")
    MONGO_SOURCE="MongoDB already running on localhost:27017"
elif command -v docker > /dev/null 2>&1 || command -v podman > /dev/null 2>&1; then
    log "no mongod program found; using the docker-compose.yml mongo service (Docker or Podman)"
    MONGO_SOURCE="docker-compose.yml mongo service"
else
    log "ERROR: no MongoDB is available for the MongoDB tests. Any one of these fixes it:"
    log "  - install MongoDB from a downloaded .tgz, .deb or folder: scripts/test_all.sh --mongodb-from PATH"
    log "  - install MongoDB from its official repository:           scripts/install_mongodb.sh"
    log "  - install Podman to use the docker-compose.yml service:    scripts/install_podman.sh"
    log "  - use an existing server:                                  scripts/test_all.sh --uri mongodb://HOST:PORT"
    log "  - skip the MongoDB tests:                                   scripts/test_all.sh --no-mongo"
    record "MongoDB" "FAILED" "no MongoDB available"
    finish 2
fi

# ---- 5. MongoDB tests ---------------------------------------------------------------------------

log "step 5/5: MongoDB tests"
QUIET_ARG=()
[ "$QUIET" = 1 ] && QUIET_ARG=(-q)
"$VENV_PY" scripts/test_mongo.py ${MONGO_ARGS[@]+"${MONGO_ARGS[@]}"} ${QUIET_ARG[@]+"${QUIET_ARG[@]}"} 2>&1 | tee "$TMP_OUT"
MONGO_STATUS=${PIPESTATUS[0]}
MONGO_VERSION="$(sed -nE 's/.*connected to MongoDB ([^ ]+) at.*/\1/p' "$TMP_OUT" | tail -1)"
record "MongoDB" "$([ -n "$MONGO_VERSION" ] && echo OK || echo FAILED)" "${MONGO_VERSION:+MongoDB $MONGO_VERSION, }$MONGO_SOURCE"
MONGO_RESULT="$(sed -nE 's/^\[test_mongo\] (MongoDB tests: .*)/\1/p' "$TMP_OUT" | tail -1)"
case "$MONGO_STATUS" in
    0) record "MongoDB tests" "PASSED" "$MONGO_RESULT" ;;
    1) record "MongoDB tests" "FAILED" "${MONGO_RESULT:-see the output above}" ;;
    *) record "MongoDB tests" "FAILED" "MongoDB could not be reached or started (see above)" ;;
esac

if [ "$MONGO_STATUS" -ge 2 ]; then
    finish 2
elif [ "$UNIT_STATUS" -ne 0 ] || [ "$MONGO_STATUS" -ne 0 ]; then
    finish 1
fi
finish 0
