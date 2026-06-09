"""
Peterson Automations — Live Follow-Up Demo
Run this during a client meeting to show exactly what happens after a job.

Usage:
    python website/demo_followup.py
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

G   = "\033[92m"
Y   = "\033[93m"
B   = "\033[94m"
W   = "\033[97m"
DIM = "\033[2m"
RST = "\033[0m"
BLD = "\033[1m"

def divider(n=64): print(DIM + "─" * n + RST)

def header(text):
    print(); divider()
    print(f"{BLD}{W}  {text}{RST}"); divider()

def step(label, color=G):
    print(f"\n{color}{BLD}  ▸ {label}{RST}")

def phone_bubble(text, sender="Business"):
    print(f"\n{DIM}  ┌─ {sender}'s automated text ─────────────────────{RST}")
    for line in textwrap.wrap(text, width=52):
        print(f"{G}  │  {line}{RST}")
    print(f"{DIM}  └───────────────────────────────────────────────{RST}")

def email_block(subject, body):
    print(f"\n{DIM}  ┌─ Automated Email ──────────────────────────────{RST}")
    print(f"{Y}  │  Subject: {subject}{RST}")
    print(f"{DIM}  │{RST}")
    for line in textwrap.wrap(body, width=52):
        print(f"  │  {line}")
    print(f"{DIM}  └───────────────────────────────────────────────{RST}")


def generate_messages(business_name, owner_name, job_type, customer_name):
    prompt = f"""Write automated follow-up messages for a local service business.

Business: {business_name} (owner: {owner_name})
Job completed: {job_type}
Customer: {customer_name}

Write:
1. A follow-up text (2-3 sentences, casual, sent 2 hours after job)
2. A Google review request text (sent next day, include placeholder [REVIEW_LINK])
3. An email subject + body (sent 2 days after job, under 80 words)

Natural tone — like a real person wrote it, just automatically sent.
No corporate language.

Format exactly:
FOLLOW_UP_TEXT: [text]
REVIEW_TEXT: [text]
EMAIL_SUBJECT: [subject]
EMAIL_BODY: [body]"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    result = {}
    for line in text.split("\n"):
        for key, prefix in [("follow_up","FOLLOW_UP_TEXT:"),("review","REVIEW_TEXT:"),
                             ("email_subject","EMAIL_SUBJECT:"),("email_body","EMAIL_BODY:")]:
            if line.startswith(prefix):
                result[key] = line.split(prefix, 1)[1].strip()
    return result


def run_demo():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"\n{G}{BLD}  PETERSON AUTOMATIONS — Follow-Up Demo{RST}")
    print(f"  {DIM}Shows exactly what your customers receive after a job.{RST}\n")
    divider()

    print(f"\n{Y}  Enter your info:{RST}\n")
    business_name = input("  Your business name:   ").strip() or "Coastal Lawn Care"
    owner_name    = input("  Your name:            ").strip() or "Mike"
    job_type      = input("  Job type completed:   ").strip() or "lawn mowing and edging"
    customer_name = input("  Customer first name:  ").strip() or "Sarah"

    header(f"Automation sequence for {business_name}")

    now = datetime.now()
    step("Job marked complete")
    print(f"  {DIM}{now.strftime('%I:%M %p')}{RST}")
    time.sleep(1.0)

    step("Generating personalized messages...", color=Y)
    print("  ", end="", flush=True)
    messages = generate_messages(business_name, owner_name, job_type, customer_name)
    print(f"{G}done{RST}")
    time.sleep(0.4)

    step(f"2 hours later ({(now + timedelta(hours=2)).strftime('%I:%M %p')}) — Follow-up text")
    if "follow_up" in messages:
        phone_bubble(messages["follow_up"], sender=business_name)
    time.sleep(0.8)

    step(f"Next day ({(now + timedelta(days=1)).strftime('%a %I:%M %p')}) — Review request")
    if "review" in messages:
        phone_bubble(messages["review"].replace("[REVIEW_LINK]", "g.page/yourbusiness"), sender=business_name)
    time.sleep(0.8)

    step(f"Two days later ({(now + timedelta(days=2)).strftime('%a %I:%M %p')}) — Email")
    if "email_subject" in messages and "email_body" in messages:
        email_block(messages["email_subject"], messages["email_body"])

    header("WHAT THIS DOES FOR YOUR BUSINESS")
    print(f"""
  {G}✓{RST}  Every customer gets followed up — even on your busiest days
  {G}✓{RST}  Review requests fire automatically when the job is fresh
  {G}✓{RST}  More Google reviews = more calls from people searching nearby
  {G}✓{RST}  You do nothing after marking the job complete

  {DIM}Runs every job, every day, forever.{RST}
""")
    divider()
    print(f"""
  {W}{BLD}Interested in setting this up for {business_name}?{RST}

  {Y}Brandon Peterson{RST} — Peterson Automations
  {DIM}petersonbrandon55@gmail.com · Hampton Roads, VA{RST}

""")


if __name__ == "__main__":
    run_demo()
