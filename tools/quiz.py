import random
import re
from pathlib import Path
from config.settings import OBSIDIAN_VAULT_PATH

SECURITY_PLUS_NOTE = OBSIDIAN_VAULT_PATH / "wiki" / "security" / "security-plus.md"

# Fallback question bank if the note can't be parsed
FALLBACK_QUESTIONS = [
    ("What is the difference between authentication and authorization?",
     "Authentication verifies identity; authorization determines what that identity is allowed to do."),
    ("Name three types of social engineering attacks.",
     "Phishing, vishing, tailgating, shoulder surfing, watering hole — any three count."),
    ("What does MITRE ATT&CK map?",
     "Adversary tactics, techniques, and procedures (TTPs) used in real-world attacks."),
    ("What is a rainbow table attack?",
     "A precomputed table of hash values used to crack hashed passwords without brute-forcing each one."),
    ("What is the difference between a virus and a worm?",
     "A virus requires a host file and user action to spread; a worm self-replicates across networks without user interaction."),
    ("What does SHA-256 do?",
     "Produces a 256-bit cryptographic hash — used to verify data integrity."),
    ("What is an evil twin attack?",
     "A rogue wireless access point that mimics a legitimate one to intercept traffic."),
    ("What is a zero-day vulnerability?",
     "A flaw unknown to the vendor with no patch available, making it immediately exploitable."),
    ("What is the principle of least privilege?",
     "Users and systems should have only the minimum permissions needed to perform their function."),
    ("What is a buffer overflow?",
     "Writing more data to a buffer than it can hold, potentially overwriting adjacent memory and allowing code execution."),
]


def _extract_qa_pairs(text: str) -> list[tuple[str, str]]:
    """Pull bold terms and their surrounding context as Q&A pairs."""
    pairs = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        bold_terms = re.findall(r"\*\*(.+?)\*\*", line)
        for term in bold_terms:
            context = line.replace(f"**{term}**", term).strip("- ").strip()
            if len(context) > 20:
                pairs.append((
                    f"Define or explain: {term}",
                    context
                ))
    return pairs


def security_plus_quiz() -> str:
    """Return a single spoken Security+ quiz question with its answer."""
    pairs = []
    if SECURITY_PLUS_NOTE.exists():
        try:
            text = SECURITY_PLUS_NOTE.read_text(encoding="utf-8")
            pairs = _extract_qa_pairs(text)
        except Exception:
            pass

    pool = pairs if len(pairs) >= 5 else FALLBACK_QUESTIONS
    question, answer = random.choice(pool)
    return (
        f"Security plus quiz. Here is your question: {question} "
        f"... Take a moment ... The answer is: {answer}"
    )
