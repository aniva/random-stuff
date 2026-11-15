# Aniva's Personal Monorepo (`random-stuff`)

A collection of self-hosted infrastructure stacks, VPN setup guides, 3D printing automation, and custom hardware projects.

---

## Repository Index

### 1. 🔐 [forgejo-passkey-ha](forgejo-passkey-ha/)
Lightweight, VPN-only self-hosted Git forge (**Forgejo**) with **Passkey-only OIDC login** (**Pocket ID**), **Caddy** TLS (Route 53 DNS-01), **PostgreSQL**, Telegram access-request alerts, `restic` point-in-time backups, Active/Standby replication, and an agent skill.
* **Passkey-Only Web Auth:** Passwordless OIDC via Pocket ID; native Forgejo password login disabled.
* **Telegram Onboarding:** `POST /request-access` notifies the admin via Telegram when new users request access.
* **Agentic Workflow:** Includes [forgejo-client skill](forgejo-passkey-ha/skills/forgejo-client/SKILL.md) and `fj` CLI support.
* **Resilience & Security:** 12-hour dual-target `restic` backups ([DISASTER_RECOVERY.md](forgejo-passkey-ha/DISASTER_RECOVERY.md)), 512 MB push guardrails, and [SECURITY_CHECKLIST.md](forgejo-passkey-ha/SECURITY_CHECKLIST.md).

---

### 2. 📱 [vpn-guides](vpn-guides/)
Step-by-step client setup guides with screenshots for connecting mobile devices to the private VPN.
* **Apple iOS:** [vpn-guides/apple/](vpn-guides/apple/README.md) (Streisand setup guide + `.docx`)
* **Samsung / Android:** [vpn-guides/samsung/](vpn-guides/samsung/README.md) (v2rayNG setup guide + HTML + `.docx`)

---

### 3. 🖨️ [qidi-studio](qidi-studio/)
Version-controlling and AI-driven automation for [QIDI Studio](https://github.com/QIDITECH/QIDIStudio) (Orca Slicer-based) printer, filament, and process profiles.
* **AppData Linker:** Symlinks `%AppData%\QIDIStudio\user\default` to this repo via `prepare_windows.cmd`.
* **Calibrated Material Profiles:** Structural filament settings and printer upgrade/fix notes.
* **Documentation:** [qidi-studio/README.md](qidi-studio/README.md).

---

### 4. 📐 [sff_case_9L_01](sff_case_9L_01/)
Open-source **Aniva SFF01** ~9L Small Form Factor PC chassis — CAD fabrication files and an integrated ESP32-C6 hardware telemetry display.
* **CAD Fabrication Files ([cad_files/](sff_case_9L_01/cad_files/)):** STEP/STL panels tuned for Polymaker PC-PBT and M3 hardware.
* **Microcontroller Telemetry ([telemetry_display/](sff_case_9L_01/telemetry_display/)):** Waveshare ESP32-C6 1.47" LCD firmware (LovyanGFX + dual AHT20 sensors + solar dimming) paired with a Windows LibreHardwareMonitor Python daemon.
* **Documentation:** [sff_case_9L_01/README.md](sff_case_9L_01/README.md).
