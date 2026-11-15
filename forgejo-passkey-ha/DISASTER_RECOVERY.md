# Disaster Recovery & Point-in-Time Restore Guide

This stack uses **encrypted, deduplicated `restic` snapshots** stored on **two independent locations** (a second physical drive + an off-box host) to protect against:
- **Single-drive failure** (snapshot on secondary physical drive)
- **Full host loss** (snapshot on off-box host via SFTP)
- **Accidental or malicious repo/DB deletion** (point-in-time retention: 24 hourly, 14 daily, 8 weekly, 6 monthly)

> **CRITICAL:** Save a copy of `.restic-pass` (your restic encryption key) in your secrets manager. Without it, encrypted snapshots cannot be decrypted if the primary host is lost.

---

## 1. Verify Available Snapshots

```bash
RESTIC_PASSWORD_FILE=.restic-pass restic -r <RESTIC_REPO> snapshots
```

## 2. Recover a Single Deleted Repository (Point-in-Time)

If a repository was accidentally or maliciously deleted, you do **not** need to roll back the whole server:

1. List snapshots and pick one from before the deletion (`<SNAPSHOT_ID>`).
2. Restore only that repository folder from the snapshot:
   ```bash
   RESTIC_PASSWORD_FILE=.restic-pass restic -r <RESTIC_REPO> restore <SNAPSHOT_ID> \
     --target /tmp/repo-recover \
     --include "*/forgejo/git/repositories/<owner>/<repo>.git"
   ```
3. Create a fresh empty repo in Forgejo (or push the recovered bare repo / bundle):
   ```bash
   git clone /tmp/repo-recover/.../<repo>.git /tmp/repo-work
   cd /tmp/repo-work
   git push --mirror git@<GIT_DOMAIN>:<owner>/<repo>.git
   ```

## 3. Full Host / Drive Recovery (From Scratch)

1. Install Docker Engine + Compose and `restic` on the replacement host.
2. Put your `.restic-pass` file in place.
3. Extract the latest (or chosen) snapshot:
   ```bash
   restic -r <RESTIC_REPO> restore latest --target /tmp/mygit-restore
   ```
4. Copy the restored app directory (`compose.yaml`, `.env`, `caddy/`, `hooks/`, `scripts/`) and `DATA_DIR` (`forgejo/`, `pocket-id/`, `caddy/`, `backups/forgejo-db.sql.gz`) into place.
5. Start PostgreSQL and restore the database dump:
   ```bash
   docker compose up -d postgres
   # Wait until healthy, then:
   gunzip -c <DATA_DIR>/backups/forgejo-db.sql.gz | docker compose exec -T postgres psql -U forgejo -d forgejo
   ```
6. Start the full stack:
   ```bash
   docker compose up -d
   ```
7. Update internal DNS (`GIT_DOMAIN`, `AUTH_DOMAIN`) if the replacement host has a new IP.
