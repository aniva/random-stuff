#!/usr/bin/env bash
# Restore a point-in-time restic snapshot to a target directory.
# Usage: ./scripts/restore-snapshot.sh <restic-repo> [snapshot-id|latest] [restore-dir]
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <restic-repo> [snapshot-id|latest] [restore-dir]" >&2
    exit 1
fi

RESTIC_REPO="$1"
SNAPSHOT_ID="${2:-latest}"
RESTORE_DIR="${3:-/tmp/mygit-restore}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PASS_FILE="${RESTIC_PASSWORD_FILE:-${REPO_DIR}/.restic-pass}"

if [[ ! -f "$PASS_FILE" ]]; then
    echo "ERROR: Restic password file not found at $PASS_FILE" >&2
    exit 1
fi

mkdir -p "$RESTORE_DIR"
echo "Restoring snapshot '$SNAPSHOT_ID' from '$RESTIC_REPO' into '$RESTORE_DIR'..."
RESTIC_PASSWORD_FILE="$PASS_FILE" restic -r "$RESTIC_REPO" restore "$SNAPSHOT_ID" --target "$RESTORE_DIR"
echo "Restore extracted to $RESTORE_DIR. Follow DISASTER_RECOVERY.md to bring the stack online."
