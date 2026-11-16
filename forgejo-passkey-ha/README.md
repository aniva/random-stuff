# forgejo-passkey-ha

Lightweight, VPN-only self-hosted Git forge (**Forgejo**) with **Passkey-only OIDC login** (**Pocket ID**), **PostgreSQL**, **Caddy** TLS (Route 53 DNS-01), Telegram onboarding alerts (`/request-access`), server-side push guardrails, `restic` 12-hour dual-target backups, and **Active/Standby** replication over VPN.

Designed for small private teams (≤20 devs) where:
- The Git server is purely source-of-truth (all builds/CI/deployments run locally by developers or local AI agents).
- Web logins use **Passkeys only** (FaceID/TouchID, Windows Hello, or hardware key) via Pocket ID—no passwords, no TOTP.
- New users can submit `POST https://<AUTH_DOMAIN>/request-access` over VPN to notify the admin via Telegram.
- Git transport uses **SSH keys**; AI agents use the [`forgejo-client` skill](./skills/forgejo-client/SKILL.md), REST API + scoped PATs, or **`fj`** (`forgejo-cli`).
- Dual-target `restic` backups + optional Standby replication protect against single-drive failure or accidental deletion.

---

## Quick Start (Primary Host)

1. **Clone & prepare permissions:**
   ```bash
   git clone <this-repo-url> forgejo-passkey-ha
   cd forgejo-passkey-ha
   chmod +x hooks/pre-receive scripts/*.sh
   cp .env.example .env
   ```

2. **Edit `.env`:**
   - Set `GIT_DOMAIN` and `AUTH_DOMAIN` (your internal VPN DNS names).
   - Set `DATA_DIR` to a dedicated directory/disk (e.g., `/srv/my_git/sas_data`) so the stack has zero access to the rest of the host.
   - Generate strong values for `POSTGRES_PASSWORD` and `POCKET_ID_ENCRYPTION_KEY`.

3. **Prepare data dir & start the stack:**
   ```bash
   mkdir -p data/forgejo/git/hooks/pre-receive.d
   docker compose up -d
   ```

4. **Configure Passkey-Only OIDC (One-Time):**
   - Open `https://<AUTH_DOMAIN>/setup` to create your admin passkey in **Pocket ID**.
   - In Pocket ID, create an OIDC Client named `Forgejo` with callback URL:
     `https://<GIT_DOMAIN>/user/oauth2/pocketid/callback`
   - Temporarily enable registration/login or use `forgejo-cli` inside the container to add the OIDC Authentication Source (`pocketid`) in Forgejo **Site Administration → Identity & Access → Authentication Sources**.
   - Once verified, native password sign-in is disabled (`ENABLE_PASSWORD_SIGNIN_FORM=false`).

---

## Standby Host Setup (Friend's Machine)

1. **Clone the repo & copy `.env.example` to `.env`** (matching `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `GIT_DOMAIN`, `AUTH_DOMAIN`).
2. **Do not start the stack yet**—the standby stays cold until failover.
3. **Create a restricted sync user** on the standby host and add the Primary's replication public key to `~/.ssh/authorized_keys` (the Primary pushes `pg_dump` + `rsync` hourly).
4. **On Primary**, configure `STANDBY_*` in `.env` and add an hourly cron job:
   ```cron
   0 * * * * /path/to/forgejo-passkey-ha/scripts/sync-to-standby.sh >> /var/log/mygit-sync.log 2>&1
   ```
5. **Failover:** If Primary goes down, run `./scripts/promote-standby.sh` on Standby and flip your VPN DNS A-records for `GIT_DOMAIN` / `AUTH_DOMAIN` to Standby's VPN IP.

---

## Agentic CLI Usage (`fj` & Agent Skill)

See [skills/forgejo-client/SKILL.md](./skills/forgejo-client/SKILL.md) for a ready-to-use agent skill covering onboarding (`POST /request-access`), SSH/PAT verification, listing shared repos, creating/sharing repos, and opening/merging PRs.

Local AI agents can also use [`fj` (`forgejo-cli`)](https://crates.io/crates/forgejo-cli):
```bash
fj auth login --host https://git.home.internal --token <PAT>
fj pr create --title "feat: ..."
fj pr merge <id>
fj api repos/<owner>/<repo>/pulls
```

---

## Host Security & Onboarding Checklist

See [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md) for the mandatory hardening checklist, [NEW_USER_ONBOARDING_GUIDE.md](./NEW_USER_ONBOARDING_GUIDE.md) for the step-by-step clean remote VM onboarding walkthrough, and [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md) for point-in-time `restic` backups and full recovery procedures. Key points:
- Run Docker/Podman **rootless** under an unprivileged service user.
- Bind-mount **only** `DATA_DIR` into containers.
- Restrict VPN firewall rules so dev peers can **only** reach `HTTPS_PORT` (`443`) and `SSH_PORT` (`2222`), never the host OS `sshd` or internal services.
