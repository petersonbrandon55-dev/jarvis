import requests
from config.settings import HOME_ASSISTANT_URL, HOME_ASSISTANT_TOKEN


def _headers():
    return {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}", "Content-Type": "application/json"}


def smart_home_control(action: str, entity_id: str = "", brightness: int = None) -> str:
    if not HOME_ASSISTANT_TOKEN:
        return "Home Assistant token not set. Add HOME_ASSISTANT_TOKEN to .env."

    base = HOME_ASSISTANT_URL.rstrip("/")

    if action == "list_devices":
        r = requests.get(f"{base}/api/states", headers=_headers(), timeout=5)
        if r.status_code != 200:
            return f"HA error: {r.status_code}"
        states = r.json()
        devices = [f"{s['entity_id']} ({s['state']})" for s in states[:50]]
        return "\n".join(devices)

    if not entity_id:
        return "entity_id is required for this action."

    domain = entity_id.split(".")[0]

    if action in ("turn_on", "turn_off", "toggle"):
        service = action
        payload = {"entity_id": entity_id}
        if action == "turn_on" and brightness is not None:
            payload["brightness"] = brightness
        r = requests.post(f"{base}/api/services/{domain}/{service}", json=payload, headers=_headers(), timeout=5)
        return f"{action} on {entity_id}: {'OK' if r.status_code == 200 else r.text}"

    if action == "set_brightness":
        payload = {"entity_id": entity_id, "brightness": brightness}
        r = requests.post(f"{base}/api/services/{domain}/turn_on", json=payload, headers=_headers(), timeout=5)
        return f"Brightness set on {entity_id}: {'OK' if r.status_code == 200 else r.text}"

    return f"Unknown action: {action}"
