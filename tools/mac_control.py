import subprocess
import shlex


_BLOCKED = ["rm -rf", "sudo rm", "mkfs", "dd if=", ":(){:|:&};:"]


def open_application(app_name: str) -> str:
    result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
    if result.returncode == 0:
        return f"Opened {app_name}."
    return f"Could not open {app_name}: {result.stderr.strip()}"


def run_shell_command(command: str) -> str:
    for blocked in _BLOCKED:
        if blocked in command:
            return f"Blocked: '{command}' contains a potentially destructive pattern."

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout.strip() or result.stderr.strip() or "(no output)"
    return output[:2000]  # cap at 2000 chars
