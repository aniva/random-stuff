# Clean Remote VM & New User Onboarding Guide

Step-by-step manual playbook for onboarding a completely new user (e.g. `newdev`) from a fresh, isolated remote machine (such as an AWS EC2 instance) to the private, VPN-only Forgejo git forge.

---

## 1. Cloud VM Pricing & Options (AWS EC2)

| Instance Type | Architecture | Specs | Cost | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`t3.micro`** | x86_64 | 2 vCPU, 1 GB RAM | **Free** or **$0.0104/hr** | 750 hrs/month under 12-month AWS Free Tier. Zero binary compatibility issues. |
| **`t3.nano`** | x86_64 | 2 vCPU, 0.5 GB RAM | **$0.0052/hr** | ~$0.12 for 24 hours. |
| **`t4g.nano`** | ARM64 | 2 vCPU, 0.5 GB RAM | **$0.0042/hr** | Absolute cheapest on-demand instance in AWS (~$0.10 for 24 hours). |
| **`t3.micro` (Spot)**| x86_64 | 2 vCPU, 1 GB RAM | **~$0.0031/hr** | Ephemeral testing; cost is fractions of a cent for a test run. |

> **Recommended Target**: Ubuntu 24.04 LTS `t3.micro` with an 8 GB gp3 root volume.

---

## 2. Onboarding Workflow Overview

```text
+-----------------------------------------------------------------------------------------+
|                                    ONBOARDING PHASES                                    |
|                                                                                         |
|  [Phase 1] Remote VM: Install OpenVPN -> Connect to Home VPN -> Verify DNS              |
|                                     │                                                   |
|                                     ▼                                                   |
|  [Phase 2] Remote VM: Generate SSH Key -> POST /request-access                          |
|                                     │                                                   |
|                                     ▼                                                   |
|  [Phase 3] Admin: Telegram Alert -> Pocket ID One-Time Link -> Passkey Register         |
|                                     │                                                   |
|                                     ▼                                                   |
|  [Phase 4] Remote VM: First Sign-In -> Set PAT -> Verify SSH & fj CLI                   |
+-----------------------------------------------------------------------------------------+
```

---

## Phase 1: Connect Clean Remote VM to the VPN

SSH into the clean AWS instance as `ubuntu`:

```bash
# 1. Update packages and install dependencies
sudo apt-get update && sudo apt-get install -y openvpn resolvconf curl jq git dnsutils

# 2. Transfer your OpenVPN client profile (e.g. client.ovpn) to the remote VM
# (From your local admin machine: scp -i <ec2-key.pem> mylocal.ovpn ubuntu@<EC2_PUBLIC_IP>:~/client.ovpn)

# 3. Start OpenVPN in background
sudo openvpn --config ~/client.ovpn --daemon

# 4. Confirm tunnel interface is up and has an IP in 10.0.9.0/24
ip -br a show tun0
# Expected output: tun0 UP 10.0.9.x

# 5. Verify internal DNS resolution to Netgate pfSense (10.44.55.254)
dig @10.44.55.254 git.home.jumtxt.com +short
# Expected output: 10.44.66.11
```

> **DNS Note**: If `/etc/resolv.conf` on the VM does not automatically query `10.44.55.254`, add `nameserver 10.44.55.254` to `/etc/resolv.conf` or configure NetworkManager / systemd-resolved to use Netgate as the primary DNS resolver.

---

## Phase 2: Generate Key & Request Access (New User)

Run on the clean VM as the unprivileged user:

```bash
# 1. Generate a dedicated Ed25519 SSH keypair
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "newdev@example.com"
PUBKEY=$(cat ~/.ssh/id_ed25519.pub)

# 2. Submit onboarding request to Telegram alert service
curl -fsS -X POST "https://auth.home.jumtxt.com/request-access" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"newdev\",
    \"email\": \"newdev@example.com\",
    \"ssh_pubkey\": \"${PUBKEY}\",
    \"note\": \"Clean AWS VM onboarding test\"
  }"
```

**Expected HTTP Response**:
```json
{"status":"accepted","message":"Access request submitted to admin"}
```

---

## Phase 3: Admin Approval Workflow (Admin Action)

1. **Telegram Alert Received**:
   The admin receives a real-time Telegram notification via the `access-request` service:
   > 🚀 **New Forgejo Access Request**
   > **User**: `newdev`
   > **Email**: `newdev@example.com`
   > **Note**: Clean AWS VM onboarding test
   > **SSH Key**: `ssh-ed25519 AAAAC3... newdev@example.com`

2. **Pocket ID User Invitation**:
   - Admin navigates to `https://auth.home.jumtxt.com` (Pocket ID).
   - Creates a user record:
     - Username: `newdev`
     - Email: `newdev@example.com`
   - Clicks **Create One-Time Access Link** (single-use URL).
   - Sends the access link securely to the new user.

3. **Passkey Enrollment**:
   - The user opens the One-Time Access Link in their browser over the VPN.
   - Enrolls their hardware security key, TouchID, FaceID, or Windows Hello passkey.

---

## Phase 4: First Sign-In, SSH Key Linking & PAT Generation

1. **First Sign-In (Auto-Provisions Forgejo Account)**:
   - User opens `https://git.home.jumtxt.com` in their browser.
   - Clicks **Sign in with Pocket ID**.
   - Authenticates using their newly enrolled Passkey.
   - Forgejo automatically provisions the `newdev` user profile via OIDC.

2. **Add SSH Key in Forgejo Web UI**:
   - User goes to **Settings → SSH / GPG Keys → Add Key**.
   - Pastes the public key generated in Phase 2 (`~/.ssh/id_ed25519.pub`).

3. **Generate Personal Access Token (PAT)**:
   - User goes to **Settings → Applications → Generate New Token**.
   - Token Name: `cli-token`.
   - Scopes: Select `repo` and `user`.
   - Copy the generated token string.

---

## Phase 5: Client Tooling Setup & Verification (Remote VM)

On the clean VM:

```bash
# 1. Configure SSH Host stanza
cat <<'EOF' >> ~/.ssh/config
Host git.home.jumtxt.com
    User git
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
EOF
chmod 600 ~/.ssh/config

# 2. Verify SSH Authentication
ssh -T git.home.jumtxt.com
# Expected output:
# Hi there, newdev! You've successfully authenticated with the key named ..., but Forgejo does not provide shell access.

# 3. Install `fj` (forgejo-cli)
mkdir -p ~/.local/bin
curl -fsSL https://codeberg.org/forgejo-contrib/forgejo-cli/releases/download/v0.7.0/forgejo-cli-x86_64-linux.tar.gz | tar -xz -C ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"

# 4. Authenticate `fj` CLI
export FORGEJO_PAT="<NEW_USER_PAT>"
fj auth add-token -H https://git.home.jumtxt.com "${FORGEJO_PAT}"
fj auth use-ssh -H https://git.home.jumtxt.com true

# Verify whoami
fj whoami -H https://git.home.jumtxt.com
# Expected output:
# currently signed into newdev@git.home.jumtxt.com

# 5. End-to-End Git Test (Create Repo, Branch, PR, Merge)
fj repo create test-newdev-repo --private
cd test-newdev-repo

git checkout -b feat/initial-commit
echo "Hello from isolated AWS VM" > proof.txt
git add proof.txt && git commit -m "feat: initial commit from clean VM"
git push -u origin feat/initial-commit

fj pr create "feat: initial PR from newdev"
fj pr merge 1

git checkout main && git pull
cat proof.txt
```

---

## Phase 6: Teardown & Cleanup

Once testing is complete:

1. **Delete Test Repository**:
   ```bash
   cd ..
   rm -rf test-newdev-repo
   curl -fsS -X DELETE "https://git.home.jumtxt.com/api/v1/repos/newdev/test-newdev-repo" \
     -H "Authorization: token ${FORGEJO_PAT}"
   ```
2. **Terminate EC2 Instance**:
   Stop and terminate the AWS EC2 instance to incur zero recurring charges.
