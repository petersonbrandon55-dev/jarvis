"""
Shared session memory for Peterson Automations agents.
HAWK and CIPHER write here automatically. ORACLE reads it before every response.
"""
import threading
from datetime import datetime

_lock = threading.Lock()

_log = {
    "hawk":   [],   # [{query, summary, timestamp}]
    "cipher": [],   # [{lead, summary, timestamp}]
}


def _now():
    return datetime.now().strftime("%I:%M %p")


def log_hawk(query: str, full_output: str):
    # Pull the first business name line from HAWK's output as a summary
    lines = [l.strip() for l in full_output.splitlines() if l.strip()]
    business_lines = [l for l in lines if l.startswith("[") and "]" in l]
    summary = ", ".join(b.split("]")[1].strip() for b in business_lines[:6]) or full_output[:120]
    with _lock:
        _log["hawk"].append({"query": query, "summary": summary, "timestamp": _now()})
        _log["hawk"] = _log["hawk"][-5:]  # keep last 5


def log_cipher(lead: str, full_output: str):
    summary = full_output[:300].replace("\n", " ").strip()
    with _lock:
        _log["cipher"].append({"lead": lead, "summary": summary, "timestamp": _now()})
        _log["cipher"] = _log["cipher"][-5:]


def get_context_for_oracle() -> str:
    with _lock:
        hawk_entries  = list(_log["hawk"])
        cipher_entries = list(_log["cipher"])

    if not hawk_entries and not cipher_entries:
        return ""

    lines = ["// SESSION MEMORY — what your agents have done this session:"]

    for e in hawk_entries:
        lines.append(f"// HAWK searched \"{e['query']}\" at {e['timestamp']}")
        lines.append(f"//   Targets found: {e['summary']}")

    for e in cipher_entries:
        lines.append(f"// CIPHER drafted outreach for: \"{e['lead']}\" at {e['timestamp']}")
        lines.append(f"//   Draft preview: {e['summary'][:200]}")

    lines.append("//")
    return "\n".join(lines) + "\n\n"


def get_log() -> dict:
    with _lock:
        return {
            "hawk":   list(_log["hawk"]),
            "cipher": list(_log["cipher"]),
        }


def clear():
    with _lock:
        _log["hawk"].clear()
        _log["cipher"].clear()
