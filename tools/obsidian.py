from pathlib import Path
from config.settings import OBSIDIAN_VAULT_PATH


def _resolve(filename: str, folder: str = "") -> Path:
    if not filename.endswith(".md"):
        filename += ".md"
    base = OBSIDIAN_VAULT_PATH / folder if folder else OBSIDIAN_VAULT_PATH
    return base / filename


def read_obsidian_note(filename: str, folder: str = "") -> str:
    path = _resolve(filename, folder)
    if not path.exists():
        return f"Note not found: {path}"
    return path.read_text(encoding="utf-8")


def write_obsidian_note(filename: str, content: str, folder: str = "", append: bool = False) -> str:
    path = _resolve(filename, folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    if append and path.exists():
        existing = path.read_text(encoding="utf-8")
        content = existing.rstrip() + "\n\n" + content
    path.write_text(content, encoding="utf-8")
    action = "Appended to" if append else "Wrote"
    return f"{action} note: {path}"


def list_obsidian_notes(folder: str = "") -> str:
    base = OBSIDIAN_VAULT_PATH / folder if folder else OBSIDIAN_VAULT_PATH
    if not base.exists():
        return f"Folder not found: {base}"
    notes = sorted(base.rglob("*.md"))
    if not notes:
        return "No notes found."
    return "\n".join(str(n.relative_to(OBSIDIAN_VAULT_PATH)) for n in notes[:100])
