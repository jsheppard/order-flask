#!/usr/bin/env bash
# task00: run the full test setup and report only the overall result.
#
#   scripts/task00.sh
#
# Runs, from the project folder:
#
#   scripts/test_all.sh --mongodb-from ../mongodb-linux-x86_64-ubuntu2404-8.3.13/
#
# and checks the summary that test_all.sh prints at the end for the text "result: PASSED".
# Prints PASSED to the console if it is there, otherwise FAILED. Nothing else is printed; the
# full output of test_all.sh is written to a log file (default /tmp/task00.log, or $TASK00_LOG).
#
# Exit codes: 0 PASSED, 1 FAILED.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="${TASK00_LOG:-${TMPDIR:-/tmp}/task00.log}"

# Run from the project folder so that the relative paths in the command resolve as intended.
cd "$ROOT" || { echo FAILED; exit 1; }
scripts/test_all.sh --mongodb-from ../mongodb-linux-x86_64-ubuntu2404-8.3.13/ > "$LOG" 2>&1

# The summary is everything from test_all.sh's "---- summary ----" line to the end.
if sed -n '/-\{5\} summary -\{5\}/,$p' "$LOG" | grep -qF "result: PASSED"; then
    echo PASSED
    exit 0
fi
echo FAILED
exit 1
