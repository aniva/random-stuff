#!/usr/bin/env bash
# Hourly one-way replication from Primary -> Standby over VPN.
# Run via cron or systemd timer on the Primary host.
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
mkdir -p "$BACKUP_DIR"

echo "[$(date -Iseconds)] Dumping PostgreSQL database..."
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-forgejo}" "${POSTGRES_DB:-forgejo}" \
    | gzip > "${BACKUP_DIR}/forgejo-db.sql.gz.tmp"
mv "${BACKUP_DIR}/forgejo-db.sql.gz.tmp" "${BACKUP_DIR}/forgejo-db.sql.gz"

echo "[$(date -Iseconds)] Syncing Forgejo, Pocket ID, Caddy certs, and DB dump to Standby..."
rsync -az --delete \
    -e "ssh -i ${STANDBY_SSH_KEY} -o StrictHostKeyChecking=accept-new" \
    --exclude 'postgres/' \
    "${DATA_DIR}/" \
    "${STANDBY_SSH_TARGET}:${STANDBY_REMOTE_DIR}/"

echo "[$(date -Iseconds)] Standby sync completed."
