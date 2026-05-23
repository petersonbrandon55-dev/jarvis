"""
ui/web_hud.py — Iron Man HUD web interface for JARVIS.

Runs a lightweight Flask server in a background thread.
The front-end at /ui/static/hud.html connects via Server-Sent Events.

Usage (standalone test):
    python -m ui.web_hud

Integration (from main.py or wherever):
    from ui.web_hud import WebHUD
    hud = WebHUD()
    hud.start()
    hud.open_browser()

    hud.set_status("listening")          # idle | listening | thinking | speaking
    hud.add_message("user",   "Hello!")
    hud.add_message("jarvis", "Good evening, Boss.")
    hud.stop()
"""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

# Flask is already in requirements.txt (flask>=3.0.0)
from flask import Flask, Response, jsonify, request, send_from_directory

# ─── Configuration ────────────────────────────────────────────────────────────

PORT        = 8889
HOST        = "127.0.0.1"
STATIC_DIR  = Path(__file__).parent / "static"
HUD_FILE    = "hud.html"

# Keep the Flask logger quiet unless debugging
log = logging.getLogger("web_hud")
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# ─── Flask app ────────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=str(STATIC_DIR))

# Global registry of active SSE subscriber queues
_subscribers: list[queue.Queue] = []
_subscribers_lock = threading.Lock()


def _broadcast(payload: dict) -> None:
    """Push a JSON payload to every connected SSE client."""
    data = json.dumps(payload)
    with _subscribers_lock:
        dead: list[queue.Queue] = []
        for q in _subscribers:
            try:
                q.put_nowait(data)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _subscribers.remove(q)


def _subscribe() -> queue.Queue:
    q: queue.Queue = queue.Queue(maxsize=64)
    with _subscribers_lock:
        _subscribers.append(q)
    return q


def _unsubscribe(q: queue.Queue) -> None:
    with _subscribers_lock:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the HUD HTML page."""
    return send_from_directory(str(STATIC_DIR), HUD_FILE)


@app.route("/events")
def events():
    """Server-Sent Events stream — one connection per browser tab."""
    q = _subscribe()

    def stream():
        # Send an initial ping so the client knows we're alive
        yield "data: {\"type\": \"ping\"}\n\n"
        try:
            while True:
                try:
                    data = q.get(timeout=20)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    # Heartbeat to keep connection alive through proxies / browsers
                    yield "data: {\"type\": \"ping\"}\n\n"
        except GeneratorExit:
            pass
        finally:
            _unsubscribe(q)

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":  "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":     "keep-alive",
        },
    )


@app.route("/update", methods=["POST"])
def update():
    """
    Accept JSON:  {"status": "...", "role": "...", "text": "..."}
    Any combination is valid:
      - status alone  → status update only
      - role + text   → new message only
      - all three     → status update + new message
    """
    body = request.get_json(silent=True) or {}

    status: Optional[str] = body.get("status")
    role:   Optional[str] = body.get("role")
    text:   Optional[str] = body.get("text")

    if status:
        _broadcast({"type": "status", "status": status})

    if role and text:
        _broadcast({"type": "message", "role": role, "text": text})

    return jsonify({"ok": True})


# ─── WebHUD class ─────────────────────────────────────────────────────────────

class WebHUD:
    """
    Thin wrapper around the Flask app that manages the background thread.

    Example
    -------
    hud = WebHUD()
    hud.start()
    hud.open_browser()

    hud.set_status("listening")
    hud.add_message("user", "Turn on the lights.")
    hud.add_message("jarvis", "Turning on the living room lights, Boss.")
    hud.set_status("idle")

    hud.stop()
    """

    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self._thread: Optional[threading.Thread] = None
        self._running = False

    # ── Lifecycle ─────────────────────────────────────────────────

    def start(self) -> None:
        """Start the Flask server in a daemon background thread."""
        if self._running:
            log.warning("WebHUD is already running.")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._serve,
            name="WebHUD-Flask",
            daemon=True,           # exits when main program exits
        )
        self._thread.start()
        log.info("WebHUD started at http://%s:%s", self.host, self.port)

    def stop(self) -> None:
        """Signal shutdown (Flask will stop on next request or when daemon dies)."""
        self._running = False
        # Broadcast a shutdown event so clients can show a reconnect state
        try:
            _broadcast({"type": "status", "status": "idle"})
        except Exception:
            pass
        log.info("WebHUD stop requested.")

    def _serve(self) -> None:
        import werkzeug.serving
        # Use Werkzeug's make_server for clean shutdown support
        server = werkzeug.serving.make_server(
            self.host, self.port, app, threaded=True
        )
        server.serve_forever()

    # ── Public API ────────────────────────────────────────────────

    def set_status(self, status: str) -> None:
        """
        Update the HUD status indicator.
        Accepted values: 'idle', 'listening', 'thinking', 'speaking'
        """
        _broadcast({"type": "status", "status": status})

    def add_message(self, role: str, text: str) -> None:
        """
        Append a message to the HUD conversation log.
        role: 'user' | 'jarvis' (or 'assistant')
        """
        _broadcast({"type": "message", "role": role, "text": text})

    def open_browser(self) -> None:
        """Open the HUD in the default web browser."""
        url = f"http://{self.host}:{self.port}"
        # Give the server a moment to be ready if called immediately after start()
        time.sleep(0.3)
        webbrowser.open(url)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


# ─── Standalone demo ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time

    hud = WebHUD()
    hud.start()
    hud.open_browser()

    print(f"JARVIS HUD running at {hud.url}")
    print("Press Ctrl+C to stop.\n")

    # Demo sequence
    demo_messages = [
        ("idle",      None,     None,                                  1.5),
        ("listening", None,     None,                                  0.5),
        ("listening", "user",   "JARVIS, what's the weather like?",    1.5),
        ("thinking",  None,     None,                                  2.0),
        ("speaking",  "jarvis", "The weather in San Francisco is currently 68°F and partly cloudy, Boss.", 2.5),
        ("idle",      None,     None,                                  1.0),
        ("listening", None,     None,                                  0.5),
        ("listening", "user",   "Turn on the living room lights.",     1.2),
        ("thinking",  None,     None,                                  1.5),
        ("speaking",  "jarvis", "Done. Living room lights are now on.", 2.0),
        ("idle",      None,     None,                                  0),
    ]

    try:
        for status, role, text, delay in demo_messages:
            hud.set_status(status)
            if role and text:
                hud.add_message(role, text)
            if delay:
                time.sleep(delay)

        # Keep server alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down.")
        hud.stop()
