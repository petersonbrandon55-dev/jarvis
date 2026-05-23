#!/usr/bin/env python3
"""
JARVIS — Brandon's personal AI assistant.
Usage:
    python main.py              # Wake word / keyboard mode with voice I/O
    python main.py --text       # Text-only mode (no mic/speakers needed)
"""
import sys
import argparse


def build_tool_handlers() -> dict:
    from tools.search import web_search
    from tools.mac_control import open_application, run_shell_command
    from tools.obsidian import read_obsidian_note, write_obsidian_note, list_obsidian_notes
    from tools.home_assistant import smart_home_control

    return {
        "web_search": web_search,
        "open_application": open_application,
        "run_shell_command": run_shell_command,
        "read_obsidian_note": read_obsidian_note,
        "write_obsidian_note": write_obsidian_note,
        "list_obsidian_notes": list_obsidian_notes,
        "smart_home_control": smart_home_control,
    }


def run_voice_mode():
    from core.listener import Listener
    from core.transcriber import Transcriber
    from core.speaker import Speaker
    from core.brain import Brain

    tool_handlers = build_tool_handlers()
    brain = Brain(tool_handlers)
    listener = Listener()
    transcriber = Transcriber()
    speaker = Speaker()

    speaker.speak("JARVIS online. How can I help you, Boss?")

    while True:
        try:
            listener.wait_for_wake()
            user_input = transcriber.listen_and_transcribe()
            if not user_input.strip():
                continue
            if user_input.lower() in ("goodbye", "bye jarvis", "shut down", "exit"):
                speaker.speak("Understood. Going offline. Goodbye, Boss.")
                break
            response = brain.think(user_input)
            speaker.speak(response)
        except KeyboardInterrupt:
            print("\n[JARVIS] Shutting down.")
            break


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
    parser.add_argument("--text", action="store_true", help="Run in text-only mode")
    args = parser.parse_args()

    if args.text:
        run_text_mode()
    else:
        run_voice_mode()
