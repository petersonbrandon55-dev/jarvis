"""
JARVIS HTTP server — exposes JARVIS over a local API so you can reach it
from your phone via Tailscale without needing a mic on the server machine.

Usage:
    python server.py

Then from your phone (connected to Tailscale), hit:
    POST http://<mac-tailscale-ip>:8888/ask
    Body: {"message": "Hey JARVIS, what's the weather?"}

    GET  http://<mac-tailscale-ip>:8888/status
"""
from flask import Flask, request, jsonify
from core.brain import Brain

def build_tool_handlers():
    from tools.search import web_search
    from tools.mac_control import open_application, run_shell_command
    from tools.obsidian import read_obsidian_note, write_obsidian_note, list_obsidian_notes
    from tools.home_assistant import smart_home_control
    from tools.plans import (
        get_todays_tasks, get_current_week_plan, get_week_plan,
        add_task, mark_task_done, list_week_plans,
    )
    return {
        "web_search": web_search,
        "open_application": open_application,
        "run_shell_command": run_shell_command,
        "read_obsidian_note": read_obsidian_note,
        "write_obsidian_note": write_obsidian_note,
        "list_obsidian_notes": list_obsidian_notes,
        "smart_home_control": smart_home_control,
        "get_todays_tasks": get_todays_tasks,
        "get_current_week_plan": get_current_week_plan,
        "get_week_plan": get_week_plan,
        "add_task": add_task,
        "mark_task_done": mark_task_done,
        "list_week_plans": list_week_plans,
    }


app = Flask(__name__)
brain = Brain(build_tool_handlers())


@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "online", "name": "JARVIS"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400
    response = brain.think(message)
    return jsonify({"response": response})


@app.route("/reset", methods=["POST"])
def reset():
    brain.history.clear()
    return jsonify({"status": "conversation reset"})


if __name__ == "__main__":
    print("[JARVIS] Server starting on port 8888")
    print("[JARVIS] From your phone (via Tailscale): POST http://<mac-ip>:8888/ask")
    app.run(host="0.0.0.0", port=8888)
