---
name: forgejo-client
description: Operate the private Forgejo git forge with Passkey/OIDC onboarding. Use when requesting a new account and admin approval, verifying SSH/PAT auth, listing shared repos, creating or sharing repos, opening pull requests, or merging PRs.
---

# Forgejo Client Operations

Use `curl` + `git` (or `fj` if installed) against the private Forgejo instance. Never hardcode tokens; read `GIT_HOST`, `AUTH_HOST`, `FORGEJO_PAT`, and `SSH_PORT` (default `2222`) from the environment or a gitignored `.env`.

```bash
# Required environment variables
export GIT_HOST="${GIT_HOST:?set git host, e.g. git.example.com}"
export AUTH_HOST="${AUTH_HOST:?set auth host, e.g. auth.example.com}"
export SSH_PORT="${SSH_PORT:-2222}"
# Set after onboarding:
# export FORGEJO_PAT="..."
```

## 0. VPN Setup & Requesting VPN Access (Start Here)

Both `AUTH_HOST` and `GIT_HOST` (HTTPS `443` and SSH `2222`) are **VPN/private-LAN only**—none of the onboarding or Git endpoints are reachable from the public internet.

1. **Install WireGuard** (or the team VPN client) on your machine.
2. **Request VPN access from the admin** (out-of-band):
   - Either ask the admin for a pre-built WireGuard `.conf` profile, **or** generate a local keypair and send only your **public** key:
     ```bash
     umask 077
     wg genkey | tee ~/.ssh/wg_private.key | wg pubkey > ~/.ssh/wg_public.key
     cat ~/.ssh/wg_public.key
     ```
3. **Activate the VPN tunnel** and verify internal DNS + HTTPS reachability before requesting a Forgejo account:
   ```bash
   curl -fsSI "https://${AUTH_HOST}" | head -n 5
   ```
   If resolution or connection times out, confirm the VPN tunnel is up and its DNS/AllowedIPs cover the private forge host.

## 1. Request Account & Get Approval (New User)

1. Ensure an `ed25519` SSH key exists (create one if missing: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""`).
2. Submit an access request to trigger an admin Telegram notification (`202` = delivered):

```bash
PUBKEY="$(cat ~/.ssh/id_ed25519.pub)"
curl -fsS -X POST "https://${AUTH_HOST}/request-access" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"<desired-username>\",\"email\":\"<email>\",\"ssh_pubkey\":\"${PUBKEY}\",\"note\":\"<reason>\"}"
```

3. **Wait for admin approval:**
   - Admin sends a Pocket ID **One-Time Access Link** (valid briefly). Open it over VPN in a browser to register your Passkey.
   - Sign in once at `https://${GIT_HOST}` via **Sign in with Pocket ID** to auto-create your Forgejo user.
   - Confirm SSH key is attached (by admin or in **Settings → SSH / GPG Keys**).
   - Create a scoped token in **Settings → Applications → Access Tokens** and save it to your gitignored `.env` as `FORGEJO_PAT`.

## 2. Verify Auth (SSH + API)

```bash
ssh -T -p "${SSH_PORT}" "git@${GIT_HOST}"
curl -fsS -H "Authorization: token ${FORGEJO_PAT}" "https://${GIT_HOST}/api/v1/user" | jq '{login, email}'
```

## 3. List Accessible / Shared Repos

`FORCE_PRIVATE=true` is enabled, so this lists only repos you own or were added to as a collaborator:

```bash
curl -fsS -H "Authorization: token ${FORGEJO_PAT}" \
  "https://${GIT_HOST}/api/v1/user/repos?limit=50" \
  | jq '.[] | {full_name, private, ssh_url, permissions}'
```

## 4. Create & Clone a Repo

```bash
curl -fsS -X POST "https://${GIT_HOST}/api/v1/user/repos" \
  -H "Authorization: token ${FORGEJO_PAT}" \
  -H "Content-Type: application/json" \
  -d '{"name":"<repo-name>","private":true,"auto_init":true}' \
  | jq '{full_name, ssh_url}'

git clone "ssh://git@${GIT_HOST}:${SSH_PORT}/<owner>/<repo-name>.git"
```

## 5. Share a Repo (Collaborators)

Grant `read`, `write`, or `admin` access to another user:

```bash
curl -fsS -X PUT "https://${GIT_HOST}/api/v1/repos/<owner>/<repo>/collaborators/<username>" \
  -H "Authorization: token ${FORGEJO_PAT}" \
  -H "Content-Type: application/json" \
  -d '{"permission":"write"}'

# List current collaborators
curl -fsS -H "Authorization: token ${FORGEJO_PAT}" \
  "https://${GIT_HOST}/api/v1/repos/<owner>/<repo>/collaborators" \
  | jq '.[] | {login, permissions}'
```

## 6. Push Branch, Open PR, List PRs, and Merge

```bash
# Push feature branch over SSH
git checkout -b "<branch>"
git push -u origin "<branch>"

# Open PR
curl -fsS -X POST "https://${GIT_HOST}/api/v1/repos/<owner>/<repo>/pulls" \
  -H "Authorization: token ${FORGEJO_PAT}" \
  -H "Content-Type: application/json" \
  -d '{"title":"<title>","body":"<body>","head":"<branch>","base":"main"}' \
  | jq '{number, state, html_url}'

# List open PRs
curl -fsS -H "Authorization: token ${FORGEJO_PAT}" \
  "https://${GIT_HOST}/api/v1/repos/<owner>/<repo>/pulls?state=open" \
  | jq '.[] | {number, title, head: .head.ref, base: .base.ref}'

# Merge PR #<number> (Do: merge | squash | rebase)
curl -fsS -X POST "https://${GIT_HOST}/api/v1/repos/<owner>/<repo>/pulls/<number>/merge" \
  -H "Authorization: token ${FORGEJO_PAT}" \
  -H "Content-Type: application/json" \
  -d '{"Do":"merge","delete_branch_after_merge":true}'
```

## Optional: `fj` (`forgejo-cli`) Equivalents

If `fj` is installed (`fj auth login --host "https://${GIT_HOST}" --token "${FORGEJO_PAT}"`):
- `fj repo create <name> --private`
- `fj pr create --title "..." --base main`
- `fj pr list`
- `fj pr merge <number>`
