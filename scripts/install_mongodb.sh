#!/usr/bin/env bash
# Install MongoDB Community and start it on localhost:27017, for running the MongoDB tests
# without containers. The repository install uses the 8.0 series (docker-compose.yml uses the
# mongo:8 image); --from installs whichever version the file contains.
#
#   scripts/install_mongodb.sh                   # from MongoDB's official package repository
#   scripts/install_mongodb.sh --from FILE.tgz   # from a downloaded MongoDB tarball (no root needed)
#   scripts/install_mongodb.sh --from DIR        # from an unpacked tarball folder (no root needed)
#   scripts/install_mongodb.sh --from FILE.deb   # from a downloaded mongodb-org-server .deb
#   scripts/install_mongodb.sh --dry-run         # print the commands without running them
#   scripts/install_mongodb.sh --no-start        # install only, do not start mongod
#
#   scripts/test_mongo.py --all --uri mongodb://localhost:27017
#   scripts/test_all.sh            # or let it find the installed mongod and run every test
#
# Repository installs support Ubuntu 20.04/22.04/24.04, Debian 12, RHEL-compatible 8/9
# (RHEL, Rocky, Alma, CentOS Stream, Oracle Linux) and macOS (Homebrew). They need root or
# sudo, and access to repo.mongodb.org and pgp.mongodb.com.
#
# Use --from when those servers are blocked. Download the file on another machine from
# https://www.mongodb.com/try/download/community (version 8.0, your Linux platform, package
# "tgz", or "server" .deb for Debian/Ubuntu) and copy it here. A .tgz, or the folder it
# unpacks to, is installed into /opt/mongodb (root) or ~/.local/opt/mongodb (other users),
# and its database and log live in the data/ folder there.
#
# Without systemd (for example in a container or a minimal VM), mongod is started in the
# background with --fork. Stop it with the command the script prints.
#
# Exit codes: 0 installed (and listening, unless --no-start), 1 installation or start
# failed, 2 unsupported platform or bad arguments, 3 root or sudo is required but not available.

set -euo pipefail

SERIES="8.0"
PORT=27017
DRY_RUN=0
START=1
FROM=""
# For testing only: read the OS description from another file.
OS_RELEASE="${OS_RELEASE:-/etc/os-release}"

log() { printf '[install_mongodb] %s\n' "$*" >&2; }
die() { local code=$1; shift; log "ERROR: $*"; exit "$code"; }
usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --no-start) START=0 ;;
        --from)
            [ $# -ge 2 ] || { log "--from needs a file"; exit 2; }
            FROM="$2"
            shift
            ;;
        -h | --help) usage; exit 0 ;;
        *) log "unknown option: $1"; usage >&2; exit 2 ;;
    esac
    shift
done

# Print a command, then run it unless this is a dry run.
run() {
    printf '+ %s\n' "$*" >&2
    [ "$DRY_RUN" = 1 ] || "$@"
}

have() { command -v "$1" > /dev/null 2>&1; }
is_root() { [ "$(id -u)" -eq 0 ]; }

SUDO=()
need_root() {
    if is_root; then
        SUDO=()
    elif have sudo; then
        SUDO=(sudo)
    elif [ "$DRY_RUN" = 1 ]; then
        [ ${#SUDO[@]} -gt 0 ] || log "not root and sudo is not installed; a real run would stop here (exit 3)"
        SUDO=(sudo)
    else
        die 3 "this step needs root, and sudo is not installed. Re-run as root."
    fi
}

# Is something accepting connections on localhost:PORT?
listening() { (exec 3<> "/dev/tcp/127.0.0.1/$PORT") 2> /dev/null; }

wait_listening() {
    local tries=30
    while [ "$tries" -gt 0 ]; do
        listening && return 0
        sleep 1
        tries=$((tries - 1))
    done
    return 1
}

# --- platform -----------------------------------------------------------------------------

ID="" ID_LIKE="" VERSION_ID="" VERSION_CODENAME=""
detect_platform() {
    if [ "$(uname -s)" = "Darwin" ]; then
        PLATFORM=macos
        return
    fi
    [ -r "$OS_RELEASE" ] || die 2 "cannot read $OS_RELEASE, so the Linux distribution is unknown"
    # shellcheck disable=SC1090
    . "$OS_RELEASE"
    case " ${ID:-} ${ID_LIKE:-} " in
        *" ubuntu "*) PLATFORM=ubuntu ;;
        *" debian "*) PLATFORM=debian ;;
        *" rhel "* | *" centos "*) PLATFORM=rhel ;;
        *" fedora "*) die 2 "MongoDB publishes no Fedora packages. Use --from with a RHEL 9 .tgz instead." ;;
        *) die 2 "unsupported distribution (ID=${ID:-?}). Use --from with a MongoDB .tgz instead." ;;
    esac
}

# Repository installs download from MongoDB's servers; fail early and clearly when DNS blocks them.
check_reachable() {
    local host
    for host in "$@"; do
        if have getent && ! getent hosts "$host" > /dev/null; then
            if [ "$DRY_RUN" = 1 ]; then
                log "WARNING: $host does not resolve here; a real run would stop (exit 1)"
            else
                die 1 "$host does not resolve (DNS lookup failed), so MongoDB's package servers are unreachable from this machine. Download MongoDB elsewhere and use --from (see --help)."
            fi
        fi
    done
}

# Download URL and pipe it into a command (run as root if needed). Dry runs only print it.
fetch_into() {
    local url=$1
    shift
    printf '+ curl -fsSL %s | %s\n' "$url" "$*" >&2
    [ "$DRY_RUN" = 1 ] || curl -fsSL "$url" | "$@"
}

# --- install from MongoDB's repository ----------------------------------------------------

KEYRING="/usr/share/keyrings/mongodb-server-$SERIES.gpg"

install_apt_repo() {
    local distro=$1 codename=${VERSION_CODENAME:-} component
    if [ "$distro" = ubuntu ]; then
        # Ubuntu derivatives (Mint, Pop!_OS) name their base release in UBUNTU_CODENAME.
        codename="${UBUNTU_CODENAME:-$codename}"
        case "$codename" in focal | jammy | noble) ;; *) die 2 "MongoDB $SERIES has no packages for Ubuntu '$codename' (supported: focal, jammy, noble)" ;; esac
        component=multiverse
    else
        case "$codename" in bookworm) ;; *) die 2 "MongoDB $SERIES has no packages for Debian '$codename' (supported: bookworm)" ;; esac
        component=main
    fi
    check_reachable pgp.mongodb.com repo.mongodb.org
    need_root
    run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get update
    run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y curl gnupg ca-certificates
    log "adding MongoDB's signing key and repository"
    fetch_into "https://pgp.mongodb.com/server-$SERIES.asc" ${SUDO[@]+"${SUDO[@]}"} gpg --batch --yes --dearmor -o "$KEYRING"
    local line="deb [ signed-by=$KEYRING ] https://repo.mongodb.org/apt/$distro $codename/mongodb-org/$SERIES $component"
    log "repository: $line"
    echo "$line" |
        run ${SUDO[@]+"${SUDO[@]}"} tee "/etc/apt/sources.list.d/mongodb-org-$SERIES.list" > /dev/null
    run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get update
    run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y mongodb-org
}

install_rhel_repo() {
    local major=${VERSION_ID%%.*}
    case "$major" in 8 | 9) ;; *) die 2 "MongoDB $SERIES has no packages for RHEL-compatible version '$VERSION_ID' (supported: 8, 9)" ;; esac
    check_reachable pgp.mongodb.com repo.mongodb.org
    need_root
    local pm=dnf
    if ! have dnf && have yum; then
        pm=yum
    fi
    log "repository: https://repo.mongodb.org/yum/redhat/$major/mongodb-org/$SERIES/\$basearch/"
    printf '%s\n' "[mongodb-org-$SERIES]" "name=MongoDB Repository" \
        "baseurl=https://repo.mongodb.org/yum/redhat/$major/mongodb-org/$SERIES/\$basearch/" \
        "gpgcheck=1" "enabled=1" "gpgkey=https://pgp.mongodb.com/server-$SERIES.asc" |
        run ${SUDO[@]+"${SUDO[@]}"} tee "/etc/yum.repos.d/mongodb-org-$SERIES.repo" > /dev/null
    run ${SUDO[@]+"${SUDO[@]}"} "$pm" install -y mongodb-org
}

install_macos() {
    have brew || [ "$DRY_RUN" = 1 ] || die 2 "Homebrew is required on macOS. Install it from https://brew.sh"
    run brew tap mongodb/brew
    run brew install "mongodb-community@$SERIES"
}

# --- install from a downloaded file -------------------------------------------------------

PREFIX=""
# Install a MongoDB tarball (.tgz) or the folder it unpacks to.
install_tarball() {
    local src=$1
    [ "$(uname -s)" = "Linux" ] || die 2 "--from FILE.tgz or DIR is for Linux; on macOS run the script without --from"
    if is_root; then PREFIX=/opt/mongodb; BIN_LINK_DIR=/usr/local/bin; else PREFIX="$HOME/.local/opt/mongodb"; BIN_LINK_DIR="$HOME/.local/bin"; fi

    if [ -d "$src" ]; then
        [ -f "$src/bin/mongod" ] || die 2 "$src is not an unpacked MongoDB server tarball (it has no bin/mongod)"
        # Copying a folder onto itself after removing bin/ would delete the only copy.
        [ "$(cd "$src" && pwd -P)" != "$(mkdir -p "$PREFIX" && cd "$PREFIX" && pwd -P)" ] ||
            die 2 "$src is the install location itself; nothing to install"
        log "folder: $src"
    else
        local top
        top="$(tar -tzf "$src" 2> /dev/null | grep -m1 -E '^[^/]+/bin/mongod$' || true)"
        [ -n "$top" ] || die 2 "$src is not a MongoDB server tarball (it has no */bin/mongod)"
        log "tarball: ${top%%/*}"
    fi

    run mkdir -p "$PREFIX" "$PREFIX/data/db" "$BIN_LINK_DIR"
    run rm -rf "$PREFIX/bin"   # replace an older install; data/ is kept
    if [ -d "$src" ]; then
        run cp -R "$src/." "$PREFIX/"
    else
        run tar -xzf "$src" -C "$PREFIX" --strip-components=1
    fi
    for b in mongod mongos; do
        if [ "$DRY_RUN" = 1 ] || [ -e "$PREFIX/bin/$b" ]; then
            run ln -sf "$PREFIX/bin/$b" "$BIN_LINK_DIR/$b"
        fi
    done
    case ":$PATH:" in *":$BIN_LINK_DIR:"*) ;; *) log "NOTE: $BIN_LINK_DIR is not on PATH; run mongod as $PREFIX/bin/mongod" ;; esac
    [ "$DRY_RUN" = 1 ] || install_missing_libs "$PREFIX/bin/mongod"
}

# The Linux builds link against the system's libcurl and OpenSSL. Install them if missing.
install_missing_libs() {
    local binary=$1 missing
    have ldd || return 0
    # ldd exits non-zero for files that are not dynamic executables; that is not an error here.
    missing="$({ ldd "$binary" 2> /dev/null || true; } | awk '/not found/{print $1}' | tr '\n' ' ')"
    [ -n "$missing" ] || return 0
    log "mongod needs libraries that are not installed: $missing"
    if have apt-get; then
        need_root
        run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get update
        run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y libcurl4 libssl3 liblzma5
    elif have dnf; then
        need_root
        run ${SUDO[@]+"${SUDO[@]}"} dnf install -y libcurl openssl-libs xz-libs
    fi
    # ldd exits non-zero for files that are not dynamic executables; that is not an error here.
    missing="$({ ldd "$binary" 2> /dev/null || true; } | awk '/not found/{print $1}' | tr '\n' ' ')"
    [ -z "$missing" ] || die 1 "still missing: $missing. Was the tarball built for this distribution and version?"
}

install_deb() {
    local file=$1
    have apt-get || die 2 "--from FILE.deb needs apt (Debian or Ubuntu)"
    need_root
    # A path with a slash makes apt install the file and fetch its dependencies from the archive.
    case "$file" in /*) ;; *) file="./$file" ;; esac
    run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y "$file"
}

# Run `mongod ... --fork`. Its output goes through a file, not straight to our stdout/stderr, so
# that a background server can never hold this script's output open (which would hang a
# caller that pipes it, for example `scripts/install_mongodb.sh | tee install.log`).
run_fork() {
    printf '+ %s\n' "$*" >&2
    [ "$DRY_RUN" = 1 ] && return 0
    local out status=0
    out="$(mktemp)"
    "$@" < /dev/null > "$out" 2>&1 || status=$?
    cat "$out" >&2
    rm -f "$out"
    return "$status"
}

# --- start --------------------------------------------------------------------------------

STOP_HINT=""
start_mongod() {
    [ -n "$PREFIX" ] && STOP_HINT="$PREFIX/bin/mongod --dbpath $PREFIX/data/db --shutdown"
    if [ "$DRY_RUN" = 0 ] && listening; then
        log "something is already listening on localhost:$PORT; not starting another mongod"
        return
    fi
    if [ -n "$PREFIX" ]; then
        # Tarball install: run from the install folder with its own data folder.
        local conf=(--dbpath "$PREFIX/data/db" --logpath "$PREFIX/data/mongod.log" --logappend
            --bind_ip 127.0.0.1 --port "$PORT")
        run_fork "$PREFIX/bin/mongod" "${conf[@]}" --fork || return 1
    elif [ "$PLATFORM" = macos ]; then
        run brew services start "mongodb-community@$SERIES" || return 1
        STOP_HINT="brew services stop mongodb-community@$SERIES"
    elif [ -d /run/systemd/system ]; then
        need_root
        run ${SUDO[@]+"${SUDO[@]}"} systemctl enable --now mongod || return 1
        STOP_HINT="sudo systemctl stop mongod"
    else
        # Package install without systemd: start it as the package's service user.
        need_root
        local user=mongodb   # the service user the Debian/Ubuntu packages create
        [ "$PLATFORM" = rhel ] && user=mongod
        run_fork ${SUDO[@]+"${SUDO[@]}"} runuser -u "$user" -- mongod --config /etc/mongod.conf --fork || return 1
        STOP_HINT="sudo runuser -u $user -- mongod --config /etc/mongod.conf --shutdown"
    fi
}

# --- main ---------------------------------------------------------------------------------

main() {
    detect_platform
    [ "$DRY_RUN" = 1 ] && log "dry run: commands are printed, not run"

    if [ -n "$FROM" ]; then
        [ -e "$FROM" ] || die 2 "no such file or folder: $FROM"
        if [ -d "$FROM" ]; then
            install_tarball "$FROM"
        else
            case "$FROM" in
                *.tgz | *.tar.gz) install_tarball "$FROM" ;;
                *.deb) install_deb "$FROM" ;;
                *) die 2 "--from expects a .tgz or .deb file, or an unpacked MongoDB folder: $FROM" ;;
            esac
        fi
    else
        log "platform: $PLATFORM, MongoDB $SERIES from the official repository"
        case "$PLATFORM" in
            ubuntu | debian) install_apt_repo "$PLATFORM" ;;
            rhel) install_rhel_repo ;;
            macos) install_macos ;;
        esac
    fi

    if [ "$DRY_RUN" = 1 ]; then
        [ "$START" = 1 ] && start_mongod
        log "dry run: nothing was installed"
        return 0
    fi

    local mongod_bin=mongod
    [ -n "$PREFIX" ] && mongod_bin="$PREFIX/bin/mongod"
    have "$mongod_bin" || [ -x "$mongod_bin" ] || die 1 "mongod is not installed after the install step"
    local version
    version="$("$mongod_bin" --version 2>&1 || true)"
    log "installed: ${version%%$'\n'*}"

    if [ "$START" = 0 ]; then
        log "done (not started: --no-start)"
        return 0
    fi
    if start_mongod && wait_listening; then
        log "mongod is listening on localhost:$PORT"
        [ -n "$STOP_HINT" ] && log "stop it with: $STOP_HINT"
        log "run the tests with: scripts/test_mongo.py --all --uri mongodb://localhost:$PORT"
    else
        log "ERROR: mongod did not start, or is not listening on localhost:$PORT after 30 seconds"
        local logfile=/var/log/mongodb/mongod.log
        [ -n "$PREFIX" ] && logfile="$PREFIX/data/mongod.log"
        if [ -r "$logfile" ]; then
            log "last 20 lines of $logfile:"
            tail -n 20 "$logfile" >&2
        fi
        exit 1
    fi
}

main
