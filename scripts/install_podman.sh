#!/usr/bin/env bash
# Install Podman and podman-compose with the system package manager.
#
#   scripts/install_podman.sh                # install podman and podman-compose
#   scripts/install_podman.sh --dry-run      # print the commands without running them
#   scripts/install_podman.sh --no-compose   # install podman only
#   scripts/install_podman.sh --short-names  # also resolve short image names on Docker Hub
#
# Supported: Ubuntu/Debian (apt), Fedora/RHEL/CentOS/Rocky/Alma (dnf or yum), openSUSE/SLES
# (zypper), Arch (pacman), Alpine (apk) and macOS (Homebrew, plus a Podman machine).
# On Linux this needs root or sudo. Tools that are already installed are not reinstalled.
#
# --short-names (Linux only) writes /etc/containers/registries.conf.d/50-docker-hub.conf so that
# short image names such as mongo:8 are pulled from Docker Hub, as Docker does. Without it,
# Podman on Ubuntu and Debian rejects them. It applies to every user on the machine; delete
# the file to undo it.
#
# If the distribution has no podman-compose package (for example RHEL without EPEL), podman
# is still installed and the script prints how to add podman-compose with pipx.
#
# Exit codes: 0 installed and verified, 1 installation or verification failed,
# 2 unsupported platform or bad arguments, 3 root or sudo is required but not available.

set -euo pipefail

DRY_RUN=0
WITH_COMPOSE=1
SHORT_NAMES=0
# For testing only: read the OS description from another file, write the registries drop-in elsewhere.
OS_RELEASE="${OS_RELEASE:-/etc/os-release}"
REGISTRIES_CONF_D="${REGISTRIES_CONF_D:-/etc/containers/registries.conf.d}"
SHORT_NAMES_FILE="$REGISTRIES_CONF_D/50-docker-hub.conf"

log() { printf '[install_podman] %s\n' "$*" >&2; }
die() { local code=$1; shift; log "ERROR: $*"; exit "$code"; }

usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --no-compose) WITH_COMPOSE=0 ;;
        --short-names) SHORT_NAMES=1 ;;
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

# --- privileges ---------------------------------------------------------------------------

SUDO=()
need_root() {
    if [ "$(id -u)" -eq 0 ]; then
        SUDO=()
    elif have sudo; then
        SUDO=(sudo)
    elif [ "$DRY_RUN" = 1 ]; then
        [ ${#SUDO[@]} -gt 0 ] || log "not root and sudo is not installed; a real run would stop here (exit 3)"
        SUDO=(sudo)
    else
        die 3 "installing packages needs root, and sudo is not installed. Re-run as root."
    fi
}

# --- platform detection -------------------------------------------------------------------

detect_platform() {
    if [ "$(uname -s)" = "Darwin" ]; then
        echo macos
        return
    fi
    [ -r "$OS_RELEASE" ] || die 2 "cannot read $OS_RELEASE, so the Linux distribution is unknown"
    local ID="" ID_LIKE=""
    # shellcheck disable=SC1090
    . "$OS_RELEASE"
    local ids=" ${ID:-} ${ID_LIKE:-} "
    case "$ids" in
        *" ubuntu "* | *" debian "*) echo apt ;;
        *" fedora "* | *" rhel "* | *" centos "*) echo dnf ;;
        *" opensuse"* | *" suse "* | *" sles "*) echo zypper ;;
        *" arch "*) echo pacman ;;
        *" alpine "*) echo apk ;;
        *) die 2 "unsupported distribution (ID=${ID:-?}, ID_LIKE=${ID_LIKE:-none}). See https://podman.io/docs/installation" ;;
    esac
}

# --- installers ---------------------------------------------------------------------------

# Packages to install: podman unless it is already present, and the compose provider if wanted.
PODMAN_PKGS=()
COMPOSE_PKGS=()
plan_packages() {
    if have podman; then
        log "podman is already installed: $(podman --version)"
    else
        PODMAN_PKGS=(podman "$@")
    fi
    if [ "$WITH_COMPOSE" = 1 ]; then
        if have podman-compose; then
            log "podman-compose is already installed"
        else
            COMPOSE_PKGS=(podman-compose)
        fi
    fi
}

COMPOSE_FAILED=0
# Install podman (failure is fatal), then the compose provider (failure is reported at the end).
install_with() {
    if [ ${#PODMAN_PKGS[@]} -gt 0 ]; then
        run "$@" "${PODMAN_PKGS[@]}" || die 1 "installing ${PODMAN_PKGS[*]} failed"
    fi
    if [ ${#COMPOSE_PKGS[@]} -gt 0 ]; then
        run "$@" "${COMPOSE_PKGS[@]}" || COMPOSE_FAILED=1
    fi
}

nothing_to_do() { [ ${#PODMAN_PKGS[@]} -eq 0 ] && [ ${#COMPOSE_PKGS[@]} -eq 0 ]; }

install_apt() {
    plan_packages uidmap  # uidmap provides newuidmap/newgidmap for rootless containers
    nothing_to_do && return
    need_root
    run ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get update
    install_with ${SUDO[@]+"${SUDO[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y
}

install_dnf() {
    plan_packages
    nothing_to_do && return
    need_root
    local pm
    if have dnf || [ "$DRY_RUN" = 1 ]; then
        pm=dnf
    elif have yum; then
        pm=yum
    else
        die 2 "neither dnf nor yum is installed"
    fi
    install_with ${SUDO[@]+"${SUDO[@]}"} "$pm" install -y
}

install_zypper() {
    plan_packages
    nothing_to_do && return
    need_root
    install_with ${SUDO[@]+"${SUDO[@]}"} zypper --non-interactive install
}

install_pacman() {
    plan_packages
    nothing_to_do && return
    need_root
    # -Syu, not -Sy: refreshing the databases without upgrading is an unsupported partial upgrade.
    install_with ${SUDO[@]+"${SUDO[@]}"} pacman -Syu --needed --noconfirm
}

install_apk() {
    plan_packages
    nothing_to_do && return
    need_root
    run ${SUDO[@]+"${SUDO[@]}"} apk update
    install_with ${SUDO[@]+"${SUDO[@]}"} apk add
}

install_macos() {
    have brew || [ "$DRY_RUN" = 1 ] || die 2 "Homebrew is required on macOS. Install it from https://brew.sh"
    plan_packages
    nothing_to_do || install_with brew install
    # On macOS, containers run in a Linux VM (a "Podman machine"). Create and start one.
    if [ "$DRY_RUN" = 1 ]; then
        run podman machine init
        run podman machine start
        return
    fi
    if ! podman machine inspect > /dev/null 2>&1; then
        run podman machine init
    fi
    if ! podman machine inspect --format '{{.State}}' 2> /dev/null | grep -q running; then
        run podman machine start
    fi
}

# --- short image names --------------------------------------------------------------------

SHORT_NAMES_CONF='# Written by scripts/install_podman.sh --short-names (order-flask).
# Pull short image names such as mongo:8 from Docker Hub, as Docker does.
# With a single search registry Podman never prompts. Delete this file to undo.
unqualified-search-registries = ["docker.io"]'

# Home directory of the user who ran the script, also under sudo.
invoking_home() {
    if [ -n "${SUDO_USER:-}" ] && have getent; then
        getent passwd "$SUDO_USER" | cut -d: -f6
    else
        printf '%s\n' "$HOME"
    fi
}

configure_short_names() {
    if [ "$(uname -s)" = "Darwin" ]; then
        log "--short-names: skipped on macOS; image names are resolved inside the Podman machine"
        return
    fi
    if [ -f "$SHORT_NAMES_FILE" ] && [ "$(cat "$SHORT_NAMES_FILE")" = "$SHORT_NAMES_CONF" ]; then
        log "short image names: already configured in $SHORT_NAMES_FILE"
    else
        need_root
        log "short image names: writing $SHORT_NAMES_FILE"
        run ${SUDO[@]+"${SUDO[@]}"} mkdir -p "$REGISTRIES_CONF_D"
        printf '%s\n' "$SHORT_NAMES_CONF" | run ${SUDO[@]+"${SUDO[@]}"} tee "$SHORT_NAMES_FILE" > /dev/null
    fi
    # A per-user registries.conf makes Podman skip the system drop-in directory for that user.
    local user_conf
    user_conf="$(invoking_home)/.config/containers/registries.conf"
    if [ -f "$user_conf" ]; then
        log "WARNING: $user_conf exists, so Podman ignores $REGISTRIES_CONF_D for this user."
        log "  Add this line to it instead: unqualified-search-registries = [\"docker.io\"]"
    fi
}

# --- verification -------------------------------------------------------------------------

verify() {
    if [ "$DRY_RUN" = 1 ]; then
        log "dry run: nothing was installed, skipping verification"
        return 0
    fi
    local failed=0

    if have podman; then
        log "podman: $(podman --version)"
    else
        log "ERROR: podman is not on PATH after installation"
        return 1
    fi

    # Runs the container engine end to end (storage, runtime, user namespaces) without pulling an image.
    if podman info > /dev/null 2>&1; then
        log "podman info: OK (rootless: $(podman info --format '{{.Host.Security.Rootless}}' 2> /dev/null || echo unknown))"
    else
        log "ERROR: 'podman info' failed. Its output:"
        podman info >&2 || true
        failed=1
    fi

    if [ "$SHORT_NAMES" = 1 ] && [ "$(uname -s)" = "Linux" ]; then
        local search
        search="$(podman info --format '{{index .Registries "search"}}' 2> /dev/null || true)"
        if [[ "$search" == *docker.io* ]]; then
            log "short image names: OK (search registries: $search)"
        else
            log "ERROR: short image names are not enabled; podman search registries: ${search:-none}"
            failed=1
        fi
    fi

    # Rootless Podman needs subordinate uid/gid ranges for the user.
    if [ "$(uname -s)" = "Linux" ] && [ "$(id -u)" -ne 0 ]; then
        local user
        user="$(id -un)"
        if ! grep -q "^${user}:" /etc/subuid 2> /dev/null || ! grep -q "^${user}:" /etc/subgid 2> /dev/null; then
            log "WARNING: $user has no entry in /etc/subuid or /etc/subgid, which rootless containers need:"
            log "  sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 $user && podman system migrate"
        fi
    fi

    if [ "$WITH_COMPOSE" = 1 ]; then
        if have podman-compose; then
            log "podman-compose: $(podman-compose version 2> /dev/null | grep -i 'podman-compose' | head -1 || echo installed)"
        else
            log "ERROR: podman-compose is not installed (the distribution may not package it)."
            log "  Install it with pipx instead: pipx install podman-compose"
            failed=1
        fi
    fi
    return "$failed"
}

# --- main ---------------------------------------------------------------------------------

main() {
    local platform
    platform="$(detect_platform)"
    if [ "$DRY_RUN" = 1 ]; then
        log "platform: $platform (dry run: commands are printed, not run)"
    else
        log "platform: $platform"
    fi

    "install_$platform"

    if [ "$SHORT_NAMES" = 1 ]; then
        configure_short_names
    fi

    if [ "$COMPOSE_FAILED" = 1 ]; then
        log "WARNING: installing podman-compose with $platform failed; podman itself was installed"
    fi

    if verify; then
        log "done"
    else
        log "FAILED: see the errors above"
        exit 1
    fi
}

main
