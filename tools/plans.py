"""
Tools for reading and editing Brandon's Obsidian Plans.

Structure:
  Plans/_Today.md          — tasks due/scheduled today (live query view)
  Plans/Task Dashboard.md  — all tasks across all weeks
  Plans/Week N - <date>.md — weekly task files
"""
import re
from pathlib import Path
from datetime import date, timedelta
from config.settings import OBSIDIAN_VAULT_PATH

PLANS_DIR = OBSIDIAN_VAULT_PATH / "Plans"


def _week_files() -> list[Path]:
    return sorted(PLANS_DIR.glob("Week *.md"))


def _current_week_file() -> Path | None:
    """Return the week file whose Monday is closest to (and not after) today."""
    today = date.today()
    best = None
    best_date = None
    for f in _week_files():
        # filename: "Week N - May 25.md"
        match = re.search(r"- (.+)\.md$", f.name)
        if not match:
            continue
        try:
            week_date = date(today.year, *_parse_month_day(match.group(1)))
        except Exception:
            continue
        if week_date <= today:
            if best_date is None or week_date > best_date:
                best_date = week_date
                best = f
    return best


def _parse_month_day(s: str) -> tuple[int, int]:
    months = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    parts = s.strip().split()
    return months[parts[0]], int(parts[1])


def get_todays_tasks() -> str:
    """Return tasks scheduled or due today across all week plans."""
    today_str = date.today().isoformat()
    results = []
    for f in _week_files():
        text = f.read_text(encoding="utf-8")
        for line in text.splitlines():
            if f"📅 {today_str}" in line or f"⏳ {today_str}" in line:
                results.append(line.strip())
    if not results:
        return "No tasks scheduled for today."
    return "\n".join(results)


def get_current_week_plan() -> str:
    """Return the full contents of the current week's plan."""
    f = _current_week_file()
    if not f:
        return "No current week plan found."
    return f"# {f.stem}\n\n" + f.read_text(encoding="utf-8")


def get_week_plan(week_name: str) -> str:
    """Return a specific week plan by partial name match, e.g. 'Week 1' or 'Jun 1'."""
    for f in _week_files():
        if week_name.lower() in f.stem.lower():
            return f"# {f.stem}\n\n" + f.read_text(encoding="utf-8")
    available = ", ".join(f.stem for f in _week_files())
    return f"Week plan '{week_name}' not found. Available: {available}"


def add_task(task_description: str, section: str = "", week: str = "current",
             due_date: str = "", priority: str = "normal", tag: str = "craft") -> str:
    """
    Add a task to a week plan under the given section.

    Args:
        task_description: The task text
        section: Section heading to add under (e.g. 'JARVIS', 'Peterson Automations'). Empty = end of file.
        week: 'current' or partial week name like 'Week 2'
        due_date: ISO date string YYYY-MM-DD, or empty
        priority: 'highest', 'high', 'medium', 'normal', 'low'
        tag: task tag, e.g. 'craft', 'career'
    """
    if week == "current":
        f = _current_week_file()
        if not f:
            return "No current week plan found."
    else:
        matches = [fp for fp in _week_files() if week.lower() in fp.stem.lower()]
        if not matches:
            return f"Week '{week}' not found."
        f = matches[0]

    priority_emoji = {"highest": "⏫", "high": "🔺", "medium": "🔼", "normal": "", "low": "🔽"}.get(priority, "")
    date_str = f" 📅 {due_date} ⏳ {due_date}" if due_date else ""
    tag_str = f" #{tag}" if tag else ""
    task_line = f"- [ ] {task_description} {priority_emoji}{date_str}{tag_str}".strip()

    content = f.read_text(encoding="utf-8")
    lines = content.splitlines()

    if section:
        # Find the section heading and insert after it (before the next heading or EOF)
        insert_idx = None
        for i, line in enumerate(lines):
            if section.lower() in line.lower() and line.startswith("#"):
                # Find the blank line or first task after this heading
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("#"):
                        insert_idx = j
                        break
                if insert_idx is None:
                    insert_idx = len(lines)
                break
        if insert_idx is not None:
            lines.insert(insert_idx, task_line)
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return f"Task added to '{section}' in {f.stem}."

    # Fallback: append to end of file
    content = content.rstrip() + "\n" + task_line + "\n"
    f.write_text(content, encoding="utf-8")
    return f"Task added to {f.stem}."


def mark_task_done(task_partial: str) -> str:
    """Mark a task as complete by matching partial text against all week plans."""
    for f in _week_files():
        content = f.read_text(encoding="utf-8")
        if task_partial.lower() in content.lower():
            # Replace first matching incomplete task
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "- [ ]" in line and task_partial.lower() in line.lower():
                    lines[i] = line.replace("- [ ]", "- [x]", 1)
                    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    return f"Marked done: {line.strip()}"
    return f"No incomplete task matching '{task_partial}' found."


def list_week_plans() -> str:
    """List all available week plan files."""
    files = _week_files()
    if not files:
        return "No week plans found."
    return "\n".join(f.stem for f in files)
