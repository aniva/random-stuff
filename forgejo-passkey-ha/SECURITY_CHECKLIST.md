# Security Hardening & User Onboarding Checklist (Must-Have)

Follow this checklist for **every** fresh deployment and **every** new developer/friend added to the stack.

---

## 1. Initial From-Scratch Setup Hardening

### Network & Host Isolation
- [ ] **Bind to isolated VPN/LAN IP only:** Set `BIND_IP` in `.env` so Caddy (`443`) and Forgejo SSH (`2222`) never listen on the primary LAN or public interfaces.
- [ ] **No public internet exposure:** Internal domains (`GIT_DOMAIN`, `AUTH_DOMAIN`) resolve only via internal/VPN DNS. Public DNS (Route 53) is used solely for temporary `_acme-challenge` TXT records.
- [ ] **Strict container volume scope:** Bind-mount **only** `DATA_DIR` into containers. Never mount host `/`, `/home`, or sensitive host paths.
- [ ] **Firewall VPN peers:** Allow dev VPN peers to reach **only** `BIND_IP:443` (HTTPS) and `BIND_IP:2222` (Git SSH)—block host `sshd` and all other host ports.
- [ ] **Built-in Go SSH only:** Keep `FORGEJO__server__START_SSH_SERVER=true` on port `2222`. Developers never receive OS shell accounts on the host.

### Pocket ID (`AUTH_DOMAIN`) Hardening
- [ ] **Disable self-signup:** In **Administration → Application Configuration**, verify `allowUserSignups` is **`disabled`**.
- [ ] **Disable unauthenticated email one-time links:** Verify `emailOneTimeAccessAsUnauthenticatedEnabled` is **`false`**.
- [ ] **Single admin only:** Keep Admin privileges strictly to the owner account. All other users must be standard non-admin users.
- [ ] **Per-client Access lists:** On every OIDC Client (**Administration → OIDC Clients → `<Client>` → Access**), explicitly allow only the intended users/groups.
- [ ] **Set display name:** Set `appName` (e.g., `Home Git`) so passkey prompts clearly identify the service.

### Forgejo (`GIT_DOMAIN`) Hardening
- [ ] **Disable password login:** `FORGEJO__service__ENABLE_INTERNAL_SIGNIN=false` (and `ENABLE_PASSWORD_SIGNIN_FORM=false`)
- [ ] **External OIDC registration only:** `FORGEJO__service__ALLOW_ONLY_EXTERNAL_REGISTRATION=true` and `FORGEJO__oauth2_client__ENABLE_AUTO_REGISTRATION=true`
- [ ] **Require sign-in to view anything:** `FORGEJO__service__REQUIRE_SIGNIN_VIEW=true`
- [ ] **Force private repos by default:** `FORGEJO__repository__FORCE_PRIVATE=true`
- [ ] **Push guardrails active:** `FORGEJO__security__DISABLE_GIT_HOOKS=false` with server-admin-managed `hooks/pre-receive` enforcing `MAX_FILE_SIZE_MB` and disallowed binary/archive MIME types.
- [ ] **Separate personal vs. shared (optional):** If maximum blast-radius isolation is needed between personal and friend projects, run a second Forgejo container (separate Postgres DB, separate `DATA_DIR`, separate SSH port) with its own Pocket ID OIDC client restricted to the owner only.

---

## 2. Adding a New User / Friend (Onboarding Checklist)

1. **VPN Access:** Provision the friend's WireGuard/VPN peer with access **only** to `BIND_IP:443` and `BIND_IP:2222` + internal DNS for `GIT_DOMAIN` and `AUTH_DOMAIN`.
2. **Create User in Pocket ID (Admin-Only):**
   - In Pocket ID **Administration → Users → Add User**, create their account as a **non-admin** user.
   - Generate a **one-time access link** (`docker exec mygit-pocket-id /app/pocket-id one-time-access-token <username>`) and send it securely.
3. **Passkey Enrollment:**
   - Friend opens the one-time link and registers their **Passkey** (via their favorite secrets manager, device biometrics, or hardware key).
4. **Grant OIDC Client Access:**
   - Add the user (or their group) under **OIDC Clients → Forgejo → Access** in Pocket ID.
5. **First Sign-In & Role Check in Forgejo:**
   - Friend opens `https://<GIT_DOMAIN>` → **Sign In → Sign in with pocketid**.
   - Confirm in Forgejo **Site Administration → User Accounts** that the new user has `IsAdmin = false` (regular user only).
6. **Client SSH Setup (New User):**
   - **Generate or export an Ed25519 keypair:**
     - *Option A (Secrets Manager):* Create an SSH Key item in your favorite secrets manager, copy the private key to `~/.ssh/id_ed25519_mygit`, and run `chmod 600 ~/.ssh/id_ed25519_mygit`.
     - *Option B (Terminal):*
       ```bash
       ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_mygit -C "yourname@mygit"
       ```
   - **Configure `~/.ssh/config`** (Windows: `C:\Users\<YOU>\.ssh\config`):
     ```sshconfig
     Host <GIT_DOMAIN>
         User git
         Port 2222
         IdentityFile ~/.ssh/id_ed25519_mygit
         IdentitiesOnly yes
     ```
   - **Upload Public Key:** Sign in to `https://<GIT_DOMAIN>` → **Settings → SSH / GPG Keys → Add Key**, paste `~/.ssh/id_ed25519_mygit.pub`, name it `forgejo`, and save.
   - **Verify:**
     ```bash
     ssh -T git@<GIT_DOMAIN>
     ```
     Expected: `"Hi there, <username>! You've successfully authenticated with the key named forgejo, but Forgejo does not provide shell access."`
