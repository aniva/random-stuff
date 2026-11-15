#!/usr/bin/env bash
# Point-in-time, encrypted, deduplicated backup of the full stack using restic.
# Protects against single-drive failure, host loss, and accidental/malicious deletion.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

if [[ ! -f .env ]]; then
    echo "ERROR: .env not found in $REPO_DIR" >&2
    exit 1
fi

# shellcheck disable=SC1091
source .env

DATA_DIR="${DATA_DIR:-./data}"
BACKUP_DIR="${DATA_DIR}/backups"
PASS_FILE="${RESTIC_PASSWORD_FILE:-${REPO_DIR}/.restic-pass}"

if [[ ! -f "$PASS_FILE" ]]; then
    echo "ERROR: Restic password file not found at $PASS_FILE" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "[$(date -Iseconds)] Dumping PostgreSQL..."
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-forgejo}" --clean --if-exists "${POSTGRES_DB:-forgejo}" \
    | gzip > "${BACKUP_DIR}/forgejo-db.sql.gz.tmp"
mv "${BACKUP_DIR}/forgejo-db.sql.gz.tmp" "${BACKUP_DIR}/forgejo-db.sql.gz"

backup_target() {
    local repo="$1"
    echo "[$(date -Iseconds)] Backing up to $repo..."
    RESTIC_PASSWORD_FILE="$PASS_FILE" restic -r "$repo" backup \
        --exclude "${DATA_DIR}/postgres" \
        "$REPO_DIR" "$DATA_DIR"
    RESTIC_PASSWORD_FILE="$PASS_FILE" restic -r "$repo" forget \
        --keep-hourly 24 --keep-daily 14 --keep-weekly 8 --keep-monthly 6 --prune
}

if [[ -n "${RESTIC_REPO_LOCAL:-}" ]]; then
    backup_target "$RESTIC_REPO_LOCAL"
fi

if [[ -n "${RESTIC_REPO_REMOTE:-}" ]]; then
    if [[ "$RESTIC_REPO_REMOTE" == sftp:* ]]; then
        remote_target="${RESTIC_REPO_REMOTE#sftp:}"
        remote_host="${remote_target%%:*}"
        if ssh -n -o BatchMode=yes -o ConnectTimeout=5 "$remote_host" true 2>/dev/null; then
            backup_target "$RESTIC_REPO_REMOTE"
        else
            echo "[$(date -Iseconds)] WARNING: Remote target '$remote_host' is offline; skipping off-box backup."
        fi
    else
        backup_target "$RESTIC_REPO_REMOTE"
    fi
fi

echo "[$(date -Iseconds)] Snapshot backup completed."
