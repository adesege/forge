#!/usr/bin/env bash
# cleanup-worktrees.sh — Interactively clean up git worktrees and their branches.
#
# For each worktree (excluding the main worktree):
#   - If branch is merged and worktree is clean → auto-delete
#   - Otherwise → prompt the user
#
# Usage: scripts/cleanup-worktrees.sh [--dry-run]

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || git worktree list --porcelain | head -1 | sed 's/^worktree //')"
MAIN_BRANCH="$(git -C "$REPO_ROOT" symbolic-ref --short HEAD 2>/dev/null || echo master)"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN — no changes will be made ==="
    echo
fi

bold()  { printf '\033[1m%s\033[0m' "$*"; }
green() { printf '\033[32m%s\033[0m' "$*"; }
red()   { printf '\033[31m%s\033[0m' "$*"; }
yellow(){ printf '\033[33m%s\033[0m' "$*"; }

confirm() {
    local prompt="$1"
    local reply
    # Read from /dev/tty to work even when stdin is piped
    while true; do
        read -rp "$prompt [y/n/q] " reply </dev/tty
        case "$reply" in
            [Yy]) return 0 ;;
            [Nn]) return 1 ;;
            [Qq]) echo "Aborted."; exit 0 ;;
            *)    echo "Please answer y, n, or q (quit)." ;;
        esac
    done
}

remove_worktree() {
    local wt_path="$1"
    local branch="$2"
    local force="${3:-false}"

    if $DRY_RUN; then
        echo "  Would remove worktree: $wt_path"
        echo "  Would delete branch:   $branch"
        return
    fi

    if [[ "$force" == "true" ]]; then
        git worktree remove --force "$wt_path"
    else
        git worktree remove "$wt_path"
    fi

    if git show-ref --verify --quiet "refs/heads/$branch"; then
        git branch -D "$branch"
        echo "  $(green "Deleted branch: $branch")"
    fi
}

# Parse porcelain output into arrays of paths and branches
declare -a wt_paths=()
declare -a wt_branches=()

current_path=""
current_branch=""
while IFS= read -r line; do
    case "$line" in
        worktree\ *)
            # If we have a pending entry, save it
            if [[ -n "$current_path" ]]; then
                wt_paths+=("$current_path")
                wt_branches+=("$current_branch")
            fi
            current_path="${line#worktree }"
            current_branch=""
            ;;
        branch\ *)
            current_branch="${line#branch refs/heads/}"
            ;;
        "")
            ;;
    esac
done < <(git -C "$REPO_ROOT" worktree list --porcelain)
# Save the last entry
if [[ -n "$current_path" ]]; then
    wt_paths+=("$current_path")
    wt_branches+=("$current_branch")
fi

worktree_count=0
skipped=0
auto_cleaned=0
manual_cleaned=0

for i in "${!wt_paths[@]}"; do
    wt_path="${wt_paths[$i]}"
    wt_branch="${wt_branches[$i]}"

    # Skip the main worktree
    [[ "$wt_path" == "$REPO_ROOT" ]] && continue

    worktree_count=$((worktree_count + 1))

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$(bold "Worktree:") $wt_path"
    echo "$(bold "Branch: ") ${wt_branch:-detached HEAD}"
    echo

    # Check if worktree directory exists
    if [[ ! -d "$wt_path" ]]; then
        echo "  $(yellow "Worktree directory missing — pruning reference.")"
        if ! $DRY_RUN; then
            git worktree prune
        else
            echo "  Would prune worktree references."
        fi
        if [[ -n "$wt_branch" ]] && git show-ref --verify --quiet "refs/heads/$wt_branch"; then
            if confirm "  Delete orphaned branch $(bold "$wt_branch")?"; then
                if ! $DRY_RUN; then
                    git branch -D "$wt_branch"
                    echo "  $(green "Deleted branch: $wt_branch")"
                else
                    echo "  Would delete branch: $wt_branch"
                fi
                manual_cleaned=$((manual_cleaned + 1))
            else
                skipped=$((skipped + 1))
            fi
        fi
        continue
    fi

    # Check for uncommitted changes in the worktree
    has_changes=false
    wt_status="$(git -C "$wt_path" status --porcelain 2>/dev/null)"
    if [[ -n "$wt_status" ]]; then
        has_changes=true
    fi

    # Check for unpushed commits (commits on branch not in main)
    has_unpushed=false
    unpushed_count=0
    if [[ -n "$wt_branch" ]]; then
        unpushed_count="$(git -C "$REPO_ROOT" log --oneline "$MAIN_BRANCH..$wt_branch" 2>/dev/null | wc -l)"
        if [[ "$unpushed_count" -gt 0 ]]; then
            has_unpushed=true
        fi
    fi

    # Check if branch is merged into main
    is_merged=false
    if [[ -n "$wt_branch" ]]; then
        if git -C "$REPO_ROOT" merge-base --is-ancestor "$wt_branch" "$MAIN_BRANCH" 2>/dev/null; then
            is_merged=true
        fi
    fi

    # Display status
    if $is_merged; then
        echo "  Merged into $MAIN_BRANCH: $(green "yes")"
    else
        echo "  Merged into $MAIN_BRANCH: $(red "no")"
    fi

    if $has_changes; then
        echo "  Uncommitted changes:    $(red "yes")"
        git -C "$wt_path" status --short | sed 's/^/    /'
    else
        echo "  Uncommitted changes:    $(green "none")"
    fi

    if $has_unpushed; then
        echo "  Unmerged commits:       $(yellow "$unpushed_count")"
        git -C "$REPO_ROOT" log --oneline "$MAIN_BRANCH..$wt_branch" 2>/dev/null | sed 's/^/    /'
    else
        echo "  Unmerged commits:       $(green "none")"
    fi
    echo

    # Decide action
    if $is_merged && ! $has_changes; then
        # Safe to auto-remove
        echo "  $(green "→ Auto-cleaning (merged, no changes)")"
        remove_worktree "$wt_path" "$wt_branch"
        auto_cleaned=$((auto_cleaned + 1))
    elif $is_merged && $has_changes; then
        echo "  $(yellow "Branch is merged but worktree has uncommitted changes.")"
        if confirm "  Force-remove worktree and delete branch?"; then
            remove_worktree "$wt_path" "$wt_branch" true
            manual_cleaned=$((manual_cleaned + 1))
        else
            skipped=$((skipped + 1))
        fi
    elif ! $is_merged && ! $has_changes && ! $has_unpushed; then
        echo "  $(yellow "Branch is not merged but has no changes or unique commits.")"
        if confirm "  Remove worktree and delete branch?"; then
            remove_worktree "$wt_path" "$wt_branch"
            manual_cleaned=$((manual_cleaned + 1))
        else
            skipped=$((skipped + 1))
        fi
    else
        echo "  $(red "Branch has unmerged work.")"
        if confirm "  Force-remove worktree and delete branch anyway?"; then
            remove_worktree "$wt_path" "$wt_branch" true
            manual_cleaned=$((manual_cleaned + 1))
        else
            skipped=$((skipped + 1))
        fi
    fi

done

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ "$worktree_count" -eq 0 ]]; then
    echo "No worktrees to clean up."
else
    echo "$(bold "Summary:")"
    echo "  Worktrees found:    $worktree_count"
    echo "  Auto-cleaned:       $auto_cleaned"
    echo "  Manually cleaned:   $manual_cleaned"
    echo "  Skipped:            $skipped"
fi

# Final prune to clean up any stale references
if ! $DRY_RUN; then
    git -C "$REPO_ROOT" worktree prune 2>/dev/null
fi
