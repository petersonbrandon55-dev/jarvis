from datetime import date

KEY_DATES = {
    "Security+ Exam": date(2026, 7, 10),
    "Booz Allen Hamilton Start": date(2026, 7, 13),
}


def get_key_dates() -> str:
    today = date.today()
    lines = []
    for label, target in KEY_DATES.items():
        delta = (target - today).days
        if delta < 0:
            lines.append(f"{label}: {abs(delta)} days ago ({target})")
        elif delta == 0:
            lines.append(f"{label}: TODAY ({target})")
        else:
            lines.append(f"{label}: {delta} days away ({target})")
    return "\n".join(lines)
