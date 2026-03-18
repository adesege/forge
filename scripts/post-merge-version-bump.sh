#!/usr/bin/env bash
# post-merge-version-bump.sh — Prompt for version bump after merge to release branch.
#
# Called from .git-hooks/post-merge. Reads from /dev/tty so it works
# in the git-hook context where stdin is not a terminal.
#
# Respects RELEASE_BRANCH env var (default: main).

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
RELEASE_BRANCH="${RELEASE_BRANCH:-main}"

# Only trigger on the release branch
if [ "$BRANCH" != "$RELEASE_BRANCH" ]; then
    exit 0
fi

# Only trigger if stdin is connected to a terminal (skip in CI / non-interactive)
if ! [ -t 0 ] && ! [ -e /dev/tty ]; then
    exit 0
fi

CURRENT=$(grep '^version' "$REPO_ROOT/pyproject.toml" | head -1 | sed 's/.*"\(.*\)"/\1/')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

bold()   { printf '\033[1m%s\033[0m' "$*"; }
green()  { printf '\033[32m%s\033[0m' "$*"; }
yellow() { printf '\033[33m%s\033[0m' "$*"; }

PATCH_V="$MAJOR.$MINOR.$((PATCH + 1))"
MINOR_V="$MAJOR.$((MINOR + 1)).0"
MAJOR_V="$((MAJOR + 1)).0.0"

echo
echo "$(bold "Merge to $RELEASE_BRANCH detected.")"
echo "Current version: $(green "$CURRENT")"
echo

read -r -p "Would you like to bump the version? [y/N] " reply < /dev/tty
case "$reply" in
    [yY]|[yY][eE][sS]) ;;
    *) exit 0;;
esac

echo
echo "  $(bold "p")atch  — $(yellow "$CURRENT") → $(green "$PATCH_V")"
echo "  $(bold "m")inor  — $(yellow "$CURRENT") → $(green "$MINOR_V")"
echo "  $(bold "M")ajor  — $(yellow "$CURRENT") → $(green "$MAJOR_V")"
echo

read -r -p "Bump type [p/m/M]: " bump_type < /dev/tty
case "$bump_type" in
    p|patch) BUMP=patch;;
    m|minor) BUMP=minor;;
    M|major) BUMP=major;;
    *)
        echo "Unknown bump type: $bump_type"
        exit 1
        ;;
esac

echo
make -C "$REPO_ROOT" release BUMP="$BUMP"
