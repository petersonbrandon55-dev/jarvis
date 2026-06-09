"""
Peterson Automations — Mission Control
Run: python agents/peterson_automations/mission_control.py
Opens at http://localhost:8891
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import threading
import webbrowser
from pathlib import Path
from flask import Flask, Response, render_template, request, stream_with_context, jsonify, send_file

from agents.peterson_automations.agents import hawk, cipher, oracle
from agents.peterson_automations import session_log

app = Flask(__name__, template_folder="templates")
app.config["TEMPLATES_AUTO_RELOAD"] = True

PORT = 8891

AGENT_MAP = {
    "hawk": hawk,
    "cipher": cipher,
    "oracle": oracle,
}


@app.route("/")
def index():
    return render_template("mission_control.html")


@app.route("/landing")
def landing():
    return send_file(Path(__file__).parent.parent.parent / "website" / "index.html")


@app.route("/stream")
def stream():
    agent_name = request.args.get("agent", "")
    user_input = request.args.get("input", "").strip()

    if agent_name not in AGENT_MAP:
        def err():
            yield f"data: {json.dumps({'token': f'Unknown agent: {agent_name}'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        return Response(stream_with_context(err()), mimetype="text/event-stream")

    if not user_input:
        def empty():
            yield f"data: {json.dumps({'token': 'No input provided.'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        return Response(stream_with_context(empty()), mimetype="text/event-stream")

    def generate():
        try:
            for token in AGENT_MAP[agent_name](user_input):
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'\\n\\n[ERROR] {e}'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/session")
def session():
    return jsonify(session_log.get_log())


@app.route("/session/clear", methods=["POST"])
def clear_session():
    session_log.clear()
    return jsonify({"status": "cleared"})


def open_browser():
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()


if __name__ == "__main__":
    print(f"\n  PETERSON AUTOMATIONS // MISSION CONTROL")
    print(f"  http://localhost:{PORT}\n")
    open_browser()
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
