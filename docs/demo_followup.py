"""
Peterson Automations — Live Follow-Up Demo
Run this during a client meeting to show exactly what happens after a job.

Usage:
    python demo_followup.py

It will ask for a customer name and job type, then walk through
the full automation sequence in real-time so the client can see
exactly what their customers would receive.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
import textwrap
from datetime import datetime, timedelta
from config.settings import ANTHROPIC_API_KEY
import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Colors for terminal output ────────────────────────────────────────────────
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
W  = "\033[97m"   # white
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"

def wrap(text, width=60, indent="   "):
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)

def divider(char="─", n=64):
    print(DIM + char * n + RESET)

def header(text):
    print()
    divider()
    print(f"{BOLD}{W}  {text}{RESET}")
    divider()

def step(label, color=G):
    print(f"\n{color}{BOLD}  ▸ {label}{RESET}")

def phone_bubble(text, sender="Business", color=G):
    print(f"\n{DIM}  ┌─ {sender}'s automated text ─────────────────────{RESET}")
    for line in textwrap.wrap(text, width=52):
        print(f"{color}  │  {line}{RESET}")
    print(f"{DIM}  └───────────────────────────────────────────────{RESET}")

def email_block(subject, body):
    print(f"\n{DIM}  ┌─ Automated Email ──────────────────────────────{RESET}")
    print(f"{Y}  │  Subject: {subject}{RESET}")
    print(f"{DIM}  │{RESET}")
    for line in textwrap.wrap(body, width=52):
        print(f"  │  {line}")
    print(f"{DIM}  └───────────────────────────────────────────────{RESET}")


def generate_followup(business_name: str, owner_name: str, job_type: str, customer_name: str) -> dict:
    """Use Claude to generate real, personalized follow-up messages."""
    prompt = f"""You are writing automated follow-up messages for a local service business.

Business: {business_name} (owner: {owner_name})
Job completed: {job_type}
Customer: {customer_name}

Write:
1. A follow-up text message (2-3 sentences, casual, friendly, sent 2 hours after job)
2. A Google review request text (sent 1 day after job, includes placeholder [REVIEW_LINK])
3. An email subject line + body (sent 2 days after job, under 80 words)

Keep everything natural — like a real person wrote it, just automatically.
No corporate language. No "I hope this message finds you well."

Format your response exactly like this:
FOLLOW_UP_TEXT: [text here]
REVIEW_TEXT: [text here]
EMAIL_SUBJECT: [subject here]
EMAIL_BODY: [body here]"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text
    result = {}
    for line in text.split("\n"):
        if line.startswith("FOLLOW_UP_TEXT:"):
            result["follow_up"] = line.split("FOLLOW_UP_TEXT:", 1)[1].strip()
        elif line.startswith("REVIEW_TEXT:"):
            result["review"] = line.split("REVIEW_TEXT:", 1)[1].strip()
        elif line.startswith("EMAIL_SUBJECT:"):
            result["email_subject"] = line.split("EMAIL_SUBJECT:", 1)[1].strip()
        elif line.startswith("EMAIL_BODY:"):
            result["email_body"] = line.split("EMAIL_BODY:", 1)[1].strip()
    return result


def run_demo():
    os.system("cls" if os.name == "nt" else "clear")

    print(f"""
{G}{BOLD}
  ██████╗ ███████╗████████╗███████╗██████╗ ███████╗ ██████╗ ███╗   ██╗
  ██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔════╝██╔═══██╗████╗  ██║
  ██████╔╝█████╗     ██║   █████╗  ██████╔╝███████╗██║   ██║██╔██╗ ██║
  ██╔═══╝ ██╔══╝     ██║   ██╔══╝  ██╔══██╗╚════██║██║   ██║██║╚██╗██║
  ██║     ███████╗   ██║   ███████╗██║  ██║███████║╚██████╔╝██║ ╚████║
  ╚═╝     ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
{RESET}{DIM}  AUTOMATIONS — Follow-Up Demo · Hampton Roads, VA{RESET}
""")

    print(f"  {W}This demo shows exactly what happens after you complete a job.{RESET}")
    print(f"  {DIM}Your customers get followed up with automatically. Every time. No effort.{RESET}\n")

    divider()

    # Collect info
    print(f"\n{Y}  Let's set up your demo:{RESET}\n")
    business_name = input(f"  Your business name: ").strip() or "Coastal Lawn Care"
    owner_name    = input(f"  Your name:          ").strip() or "Mike"
    job_type      = input(f"  Job type completed: ").strip() or "lawn mowing and edging"
    customer_name = input(f"  Customer first name: ").strip() or "Sarah"

    header(f"DEMO: Automation sequence for {business_name}")

    print(f"""
  {DIM}Here's what happens automatically after you complete a job.
  You don't touch anything — it all fires on its own.{RESET}
""")

    # Step 1: Job complete
    now = datetime.now()
    step("Job marked complete in your system")
    print(f"  {DIM}Time: {now.strftime('%I:%M %p')}{RESET}")
    time.sleep(1.2)

    # Generate messages
    step("Generating personalized messages...", color=Y)
    print(f"  {DIM}Using your business info + customer name...{RESET}", end="", flush=True)
    messages = generate_followup(business_name, owner_name, job_type, customer_name)
    print(f"  {G}done{RESET}")
    time.sleep(0.5)

    # Step 2: 2-hour follow-up
    two_hours = (now + timedelta(hours=2)).strftime("%I:%M %p")
    step(f"2 hours later ({two_hours}) — Follow-up text fires automatically")
    if "follow_up" in messages:
        phone_bubble(messages["follow_up"], sender=business_name)
    time.sleep(1.0)

    # Step 3: Review request next day
    tomorrow = (now + timedelta(days=1)).strftime("%a %I:%M %p")
    step(f"Next day ({tomorrow}) — Google review request")
    if "review" in messages:
        review_text = messages["review"].replace("[REVIEW_LINK]", "g.page/coastallawnva")
        phone_bubble(review_text, sender=business_name)
    time.sleep(1.0)

    # Step 4: Email follow-up
    two_days = (now + timedelta(days=2)).strftime("%a %I:%M %p")
    step(f"Two days later ({two_days}) — Email follow-up")
    if "email_subject" in messages and "email_body" in messages:
        email_block(messages["email_subject"], messages["email_body"])
    time.sleep(0.8)

    # Summary
    header("WHAT THIS DOES FOR YOUR BUSINESS")
    print(f"""
  {G}✓{RESET}  Every customer gets followed up with — even on your busiest days
  {G}✓{RESET}  Review requests go out automatically when the job is fresh
  {G}✓{RESET}  More Google reviews = more calls from people searching your area
  {G}✓{RESET}  You do nothing after marking the job complete

  {DIM}Once this is set up, it runs every single job, every single day.{RESET}
""")

    divider()
    print(f"""
  {W}{BOLD}Ready to set this up for {business_name}?{RESET}

  {Y}Brandon Peterson{RESET} — Peterson Automations
  {DIM}Text or call: (757) 867-5309
  Email: brandon@petersonauto.co
  Hampton Roads, VA{RESET}

""")


if __name__ == "__main__":
    run_demo()
