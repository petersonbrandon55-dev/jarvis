import os
import subprocess
import urllib.request
import json

PIHOLE_API_URL = os.getenv("PIHOLE_API_URL", "http://192.168.1.2/admin/api.php")
PIHOLE_API_KEY = os.getenv("PIHOLE_API_KEY", "")

HOMELAB_SSH_HOST = os.getenv("HOMELAB_SSH_HOST", "")  # e.g. pi@100.x.x.x (Tailscale IP)


def _pihole_stats() -> dict | None:
    try:
        url = PIHOLE_API_URL
        if PIHOLE_API_KEY:
            url += f"?auth={PIHOLE_API_KEY}"
        with urllib.request.urlopen(url, timeout=4) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _ssh_command(cmd: str) -> str | None:
    if not HOMELAB_SSH_HOST:
        return None
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=4", "-o", "StrictHostKeyChecking=no",
             HOMELAB_SSH_HOST, cmd],
            capture_output=True, text=True, timeout=8
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_homelab_status() -> str:
    lines = []

    # Pi-hole stats
    stats = _pihole_stats()
    if stats:
        blocked = stats.get("ads_blocked_today", "?")
        total = stats.get("dns_queries_today", "?")
        pct = stats.get("ads_percentage_today", "?")
        status = "enabled" if stats.get("status") == "enabled" else "DISABLED"
        lines.append(f"Pi-hole: {status} — {blocked} domains blocked today out of {total} queries ({pct:.1f}% blocked)" if isinstance(pct, float) else f"Pi-hole: {status} — {blocked} blocked / {total} queries")
    else:
        lines.append("Pi-hole: unreachable (check PIHOLE_API_URL in .env)")

    # Wazuh / Pi system info via SSH
    if HOMELAB_SSH_HOST:
        uptime = _ssh_command("uptime -p")
        if uptime:
            lines.append(f"Pi uptime: {uptime}")

        wazuh_alerts = _ssh_command(
            "grep -c 'Alert' /var/ossec/logs/alerts/alerts.log 2>/dev/null || echo 0"
        )
        if wazuh_alerts:
            lines.append(f"Wazuh alert log entries today: {wazuh_alerts}")

        disk = _ssh_command("df -h / | tail -1 | awk '{print $3\"/\"$2\" used (\"$5\" full)\"}'")
        if disk:
            lines.append(f"Pi disk: {disk}")
    else:
        lines.append("SSH homelab access: not configured (set HOMELAB_SSH_HOST in .env)")

    return "\n".join(lines) if lines else "Homelab status unavailable."
