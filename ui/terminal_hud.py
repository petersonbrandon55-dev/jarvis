"""
JARVIS Terminal HUD
Provides a full-screen rich terminal display for the JARVIS voice assistant.
"""
import threading
import time
import random
from collections import deque
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


# ── Constants ──────────────────────────────────────────────────────────────────

WAVEFORM_CHARS = "▁▂▃▄▅▆▇█"
WAVEFORM_WIDTH = 40          # number of bars
MAX_MESSAGES   = 8           # conversation log depth
REFRESH_HZ     = 10          # Live refresh rate

STATUS_CONFIG = {
    "idle":      ("dim",     "●", "IDLE"),
    "listening": ("green",   "●", "LISTENING"),
    "thinking":  ("yellow",  "●", "THINKING"),
    "speaking":  ("cyan",    "●", "SPEAKING"),
}


# ── HUD ────────────────────────────────────────────────────────────────────────

class HUD:
    """
    Full-screen terminal HUD for JARVIS.

    Usage
    -----
        hud = HUD()
        hud.start()
        hud.set_status("listening")
        hud.add_message("user", "Hello JARVIS")
        hud.add_message("jarvis", "Hello, Boss.")
        hud.stop()
    """

    def __init__(self):
        self._status: str = "idle"
        self._messages: deque = deque(maxlen=MAX_MESSAGES)
        self._waveform: list[int] = [0] * WAVEFORM_WIDTH

        self._lock    = threading.Lock()
        self._thread  = None
        self._running = False
        self._live    = None
        self._console = Console()

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_status(self, status: str) -> None:
        """Set the current assistant status.  Values: idle | listening | thinking | speaking."""
        status = status.lower().strip()
        if status not in STATUS_CONFIG:
            raise ValueError(f"Unknown status '{status}'. Choose from: {list(STATUS_CONFIG)}")
        with self._lock:
            self._status = status

    def add_message(self, role: str, text: str) -> None:
        """Append a message to the conversation log.  role: 'user' | 'jarvis'."""
        role = role.lower().strip()
        with self._lock:
            self._messages.append((role, text))

    def start(self) -> None:
        """Start the HUD in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the HUD and restore the terminal."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass

    # ── Internal rendering ─────────────────────────────────────────────────────

    def _run(self) -> None:
        """Background thread: drives the Live display."""
        with Live(
            self._build_layout(),
            console=self._console,
            refresh_per_second=REFRESH_HZ,
            screen=True,
        ) as live:
            self._live = live
            while self._running:
                self._tick_waveform()
                live.update(self._build_layout())
                time.sleep(1 / REFRESH_HZ)

    def _tick_waveform(self) -> None:
        """Advance the waveform animation one frame."""
        with self._lock:
            status = self._status

        if status == "listening":
            new_wave = [random.randint(0, len(WAVEFORM_CHARS) - 1) for _ in range(WAVEFORM_WIDTH)]
        else:
            # Flat line at the lowest bar
            new_wave = [0] * WAVEFORM_WIDTH

        with self._lock:
            self._waveform = new_wave

    # ── Panel builders ─────────────────────────────────────────────────────────

    def _build_layout(self) -> Layout:
        with self._lock:
            status   = self._status
            waveform = list(self._waveform)
            messages = list(self._messages)

        layout = Layout()
        layout.split_column(
            Layout(name="header",       size=3),
            Layout(name="middle",       ratio=1),
            Layout(name="footer",       size=3),
        )
        layout["middle"].split_row(
            Layout(name="left",  ratio=1),
            Layout(name="right", ratio=2),
        )
        layout["left"].split_column(
            Layout(name="status",   size=5),
            Layout(name="waveform", ratio=1),
        )

        layout["header"].update(self._header_panel())
        layout["status"].update(self._status_panel(status))
        layout["waveform"].update(self._waveform_panel(waveform))
        layout["right"].update(self._conversation_panel(messages))
        layout["footer"].update(self._footer_panel())

        return layout

    def _header_panel(self) -> Panel:
        title = Text("J . A . R . V . I . S", style="bold cyan", justify="center")
        return Panel(title, style="cyan", box=box.DOUBLE)

    def _status_panel(self, status: str) -> Panel:
        color, dot, label = STATUS_CONFIG.get(status, ("dim", "●", "UNKNOWN"))
        line = Text()
        line.append(f"  {dot}  ", style=color)
        line.append(label, style=f"bold {color}")
        return Panel(line, title="[bold]Status[/bold]", style="bright_black")

    def _waveform_panel(self, waveform: list[int]) -> Panel:
        bars = Text()
        for idx in waveform:
            bars.append(WAVEFORM_CHARS[idx], style="bold green")
        # Center the bar string
        centered = Text(justify="center")
        centered.append_text(bars)
        return Panel(
            centered,
            title="[bold]Audio[/bold]",
            style="bright_black",
        )

    def _conversation_panel(self, messages: list) -> Panel:
        if not messages:
            placeholder = Text("  No messages yet…", style="dim italic")
            return Panel(placeholder, title="[bold]Conversation[/bold]", style="bright_black")

        table = Table.grid(padding=(0, 1))
        table.add_column(width=8,  no_wrap=True)
        table.add_column(ratio=1)

        for role, text in messages:
            if role == "user":
                label = Text("You:", style="bold white")
                body  = Text(text, style="white")
            else:
                label = Text("JARVIS:", style="bold cyan")
                body  = Text(text, style="cyan")
            table.add_row(label, body)

        return Panel(table, title="[bold]Conversation[/bold]", style="bright_black")

    def _footer_panel(self) -> Panel:
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %B %-d %Y")
        line = Text(f"{time_str}   {date_str}", justify="right", style="dim")
        return Panel(line, style="bright_black")
