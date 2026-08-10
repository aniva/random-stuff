#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/remote/qidi"
SERVICE_NAME="qidi-streamer.service"

echo "=== Deploying QIDI Multi-Layer Log Streamer to ai-box ==="

# 1. Create target log directory
echo "[1/4] Ensuring log directory exists: ${LOG_DIR}"
sudo mkdir -p "${LOG_DIR}"
sudo chown -R me:me "${LOG_DIR}"
sudo chmod 755 "${LOG_DIR}"

# 2. Install systemd service
echo "[2/4] Installing systemd service unit..."
sudo cp "${SCRIPT_DIR}/${SERVICE_NAME}" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"

# 3. Install rsyslog config
if [ -f "${SCRIPT_DIR}/20-qidi-rsyslog.conf" ]; then
    echo "[3/4] Installing rsyslog configuration..."
    sudo cp "${SCRIPT_DIR}/20-qidi-rsyslog.conf" /etc/rsyslog.d/
    sudo systemctl restart rsyslog || true
fi

# 4. Restart service
echo "[4/4] Starting ${SERVICE_NAME}..."
sudo systemctl restart "${SERVICE_NAME}"

echo ""
echo "=== Deployment Complete ==="
echo "Check daemon status: sudo systemctl status ${SERVICE_NAME}"
echo "View live logs:      tail -f ${LOG_DIR}/qidi.log"
echo "View raw JSONL:      tail -f ${LOG_DIR}/qidi_raw.jsonl"
