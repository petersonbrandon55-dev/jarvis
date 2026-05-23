#!/usr/bin/env python3
"""
JARVIS — Brandon's personal AI assistant.
Usage:
    python main.py              # Voice mode with terminal HUD
    python main.py --web        # Voice mode with web HUD (opens in browser)
    python main.py --both       # Voice mode with BOTH HUDs running simultaneously
    python main.py --text       # Text-only mode (no mic/speakers needed)
"""
import argparse


def build_tool_handlers() -> dict:
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


def _make_hud(use_terminal: bool, use_web: bool):
    """Return a unified HUD proxy that forwards calls to whichever HUDs are active."""

    huds = []
    if use_terminal:
        from ui.terminal_hud import HUD
        huds.append(HUD())
    if use_web:
        from ui.web_hud import WebHUD
        huds.append(WebHUD())

    class MultiHUD:
        def start(self):
            for h in huds:
                h.start()
            if use_web:
                huds[-1].open_browser()

        def stop(self):
            for h in huds:
                h.stop()

        def set_status(self, status):
            for h in huds:
                h.set_status(status)

        def add_message(self, role, text):
            for h in huds:
                h.add_message(role, text)

    return MultiHUD()


def run_voice_mode(use_terminal=True, use_web=False):
    from core.listener import Listener
    from core.transcriber import Transcriber
    from core.speaker import Speaker
    from core.brain import Brain

    tool_handlers = build_tool_handlers()
    brain = Brain(tool_handlers)
    listener = Listener()
    transcriber = Transcriber()
    speaker = Speaker()

    hud = _make_hud(use_terminal, use_web)
    hud.start()

    # Startup briefing — time, date, weather, today's tasks
    hud.set_status("thinking")
    from datetime import datetime
    now = datetime.now()
    briefing_prompt = (
        f"JARVIS is just coming online. The current time is {now.strftime('%I:%M %p')} "
        f"on {now.strftime('%A, %B %d')}. "
        "Give Brandon a natural spoken startup greeting that includes: "
        "1) a greeting with the time and day, "
        "2) current weather for the DMV area (use web_search), "
        "3) his tasks for today (use get_todays_tasks). "
        "Keep it conversational and concise — you're speaking aloud, not writing a report."
    )
    briefing = brain.think(briefing_prompt)
    hud.set_status("speaking")
    hud.add_message("jarvis", briefing)
    listener.muted = True
    speaker.speak(briefing)
    listener.muted = False
    hud.set_status("idle")

    while True:
        try:
            hud.set_status("idle")
            pre_roll = listener.wait_for_wake()

            hud.set_status("listening")
            user_input = transcriber.listen_and_transcribe(pre_roll=pre_roll)
            if not user_input.strip():
                continue

            hud.add_message("user", user_input)

            if user_input.lower() in ("goodbye", "bye jarvis", "shut down", "exit"):
                hud.set_status("speaking")
                listener.muted = True
                speaker.speak("Understood. Going offline. Goodbye, Boss.")
                listener.muted = False
                hud.add_message("jarvis", "Understood. Going offline. Goodbye, Boss.")
                break

            hud.set_status("thinking")
            response = brain.think(user_input)

            hud.set_status("speaking")
            hud.add_message("jarvis", response)
            listener.muted = True
            speaker.speak(response)
            listener.muted = False

        except KeyboardInterrupt:
            print("\n[JARVIS] Shutting down.")
            break

    hud.stop()


def run_text_mode():
    from core.brain import Brain

    tool_handlers = build_tool_handlers()
    brain = Brain(tool_handlers)

    print("\nJARVIS online (text mode). Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "bye"):
                print("JARVIS: Goodbye, Boss.")
                break
            response = brain.think(user_input)
            print(f"\nJARVIS: {response}\n")
        except KeyboardInterrupt:
            print("\n[JARVIS] Shutting down.")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument("--text", action="store_true", help="Text-only mode")
    parser.add_argument("--web",  action="store_true", help="Web HUD (opens in browser)")
    parser.add_argument("--both", action="store_true", help="Terminal + web HUD simultaneously")
    args = parser.parse_args()

    if args.text:
        run_text_mode()
    elif args.web:
        run_voice_mode(use_terminal=False, use_web=True)
    elif args.both:
        run_voice_mode(use_terminal=True, use_web=True)
    else:
        run_voice_mode(use_terminal=True, use_web=False)
