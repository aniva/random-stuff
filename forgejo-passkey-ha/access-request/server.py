"""Minimal VPN-only access-request relay that notifies the admin on Telegram."""
import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
GIT_DOMAIN = os.environ.get("GIT_DOMAIN", "git.example.com")
MAX_BODY = 8192


def send_telegram(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Telegram credentials not configured")
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Telegram returned HTTP {resp.status}")


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/request-access":
            self._reply(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            self._reply(400, {"error": "invalid content length"})
            return
        try:
            data = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._reply(400, {"error": "invalid json"})
            return

        username = str(data.get("username", "")).strip()
        email = str(data.get("email", "")).strip()
        ssh_pubkey = str(data.get("ssh_pubkey", "")).strip()
        note = str(data.get("note", "")).strip()
        if not username or not email:
            self._reply(400, {"error": "username and email are required"})
            return

        msg = (
            f"🔐 New {GIT_DOMAIN} Access Request\n"
            f"User: {username}\n"
            f"Email: {email}\n"
            f"Note: {note or '-'}\n"
            f"SSH Key: {ssh_pubkey[:120] or '(none)'}"
        )
        try:
            send_telegram(msg)
        except Exception as exc:
            self._reply(502, {"error": f"notification failed: {exc}"})
            return

        self._reply(202, {"status": "submitted", "message": "Admin notified via Telegram."})

    def log_message(self, fmt: str, *args) -> None:
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
