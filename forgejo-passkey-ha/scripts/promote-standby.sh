#!/usr/bin/env bash
# Promote the Standby node to Active after Primary failure.
# Restores the latest synced PostgreSQL dump and starts the full stack.
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
DB_DUMP="${DATA_DIR}/backups/forgejo-db.sql.gz"

if [[ ! -f "$DB_DUMP" ]]; then
    echo "ERROR: Synced database dump not found at $DB_DUMP" >&2
    exit 1
fi

echo "Starting PostgreSQL..."
docker compose up -d postgres
until docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-forgejo}" -d "${POSTGRES_DB:-forgejo}" >/dev/null 2>&1; do
    sleep 2
done

echo "Restoring latest database snapshot..."
gunzip -c "$DB_DUMP" | docker compose exec -T postgres psql -U "${POSTGRES_USER:-forgejo}" -d "${POSTGRES_DB:-forgejo}"

echo "Starting Forgejo, Pocket ID, and Caddy..."
docker compose up -d

echo "Standby promoted. Update internal VPN DNS to point ${GIT_DOMAIN} and ${AUTH_DOMAIN} to this host."
