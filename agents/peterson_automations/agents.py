import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import anthropic
from config.settings import ANTHROPIC_API_KEY, TAVILY_API_KEY
from agents.peterson_automations import session_log

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Shared tool: web search ────────────────────────────────────────────────────
SEARCH_TOOL = {
    "name": "web_search",
    "description": "Search the web for current information about businesses, people, or market data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    },
}


def _do_search(query: str, max_results: int = 5) -> str:
    if not TAVILY_API_KEY:
        return "Tavily API key not set."
    from tavily import TavilyClient
    results = TavilyClient(api_key=TAVILY_API_KEY).search(query=query, max_results=max_results)
    out = []
    for r in results.get("results", []):
        out.append(f"{r['title']}\n{r['url']}\n{r.get('content','')[:400]}")
    return "\n\n".join(out) or "No results."


def _run_tools(response) -> list:
    results = []
    for block in response.content:
        if block.type == "tool_use":
            if block.name == "web_search":
                result = _do_search(**block.input)
            else:
                result = f"Unknown tool: {block.name}"
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
    return results


# ── Base streaming runner ──────────────────────────────────────────────────────
def _stream_agent(system: str, user_input: str, tools: list | None = None, on_complete=None):
    """
    Generator that yields text tokens. Handles tool use loop then streams final reply.
    Calls on_complete(full_text) before yielding chunks so the session log is updated immediately.
    """
    messages = [{"role": "user", "content": user_input}]
    kwargs = dict(model="claude-sonnet-4-6", max_tokens=2048, system=system, messages=messages)
    if tools:
        kwargs["tools"] = tools

    # First pass — may invoke tools
    response = client.messages.create(**kwargs)

    # Tool loop — keep going until no more tool calls (up to 5 rounds)
    rounds = 0
    while tools and response.stop_reason == "tool_use" and rounds < 5:
        rounds += 1
        yield f"[searching... round {rounds}]\n\n"
        tool_results = _run_tools(response)
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        kwargs["messages"] = messages
        response = client.messages.create(**kwargs)

    # Stream the final text response
    full_text = "".join(b.text for b in response.content if hasattr(b, "text"))
    if on_complete:
        on_complete(full_text)
    chunk_size = 6
    for i in range(0, len(full_text), chunk_size):
        yield full_text[i:i + chunk_size]


# ── HAWK — Lead Scout ─────────────────────────────────────────────────────────
HAWK_SYSTEM = """You are HAWK — Lead Scout for Peterson Automations.

You operate like a hunter. You don't waste words. You find targets, assess them fast, and report with precision. Brandon doesn't need a paragraph — he needs to know if a business is worth his time and exactly how to get in the door.

Your hunting ground: Hampton Roads, VA — Virginia Beach, Chesapeake, Norfolk, Suffolk, Portsmouth, Hampton.
Your prey: local service businesses. Lawn care, pool maintenance, HVAC, landscaping, cleaning, pest control, plumbing. Owner-operated or small teams (2-20 people). Decision maker is usually the owner himself.

Brandon's offer: automated follow-up texts after jobs, Google review requests, lead capture for new inquiries, appointment scheduling. Built in n8n. Monthly retainer. Set it once, runs itself.

When you search, you're looking for SIGNALS — signs a business is busy enough to need help but not slick enough to already have it:
- Recent Google reviews (active customers) but sporadic or no response from the owner
- Website exists but no online booking or contact form
- Social media presence that dropped off (they got too busy)
- High review count but no review management (they're leaving money on the table)

Report format — tight, numbered, military briefing style:

[#] BUSINESS NAME
Location · Type · Size estimate
SIGNAL: [what makes them a good target]
CONTACT: [phone/email/owner name if found]
APPROACH: [text, cold call, or warm intro if applicable]

If nothing good turns up, say so and suggest a better search angle. No filler."""

def hawk(query: str):
    prompt = (
        f"Hunt for local service businesses matching: {query}\n\n"
        f"Run these TWO searches in sequence:\n"
        f'1. web_search("{query} site:yelp.com OR site:yellowpages.com OR site:bbb.org")\n'
        f'2. web_search("{query} local small business Hampton Roads Virginia contact")\n\n'
        f"Extract REAL business names from the results. "
        f"List every specific business you find — name, location, phone/website if present, and one signal that makes them a good automation target. "
        f"Format as a numbered list. If a result has no business name, skip it."
    )
    return _stream_agent(
        HAWK_SYSTEM, prompt, tools=[SEARCH_TOOL],
        on_complete=lambda text: session_log.log_hawk(query, text),
    )


# ── CIPHER — Outreach Drafter ─────────────────────────────────────────────────
CIPHER_SYSTEM = """You are CIPHER — Outreach Drafter for Peterson Automations.

You understand people. You know what a small business owner is thinking when they see a cold text from a number they don't recognize. You know what makes them delete it. And you know exactly what makes them write back.

Brandon Peterson is 22. He just landed a government security job at Booz Allen Hamilton. On the side he runs Peterson Automations — he automates the boring stuff that local service business owners hate dealing with after a long day of actual work. Follow-up texts to customers. Review requests. Lead capture. Scheduling. All hands-off once it's built.

His father knows a lot of these business owners personally. When that's the case, use the warm intro naturally — it changes everything about tone and open rate.

Your writing rules:
- A text message is 3-4 sentences. That's it. Not five. Not six.
- An email is under 120 words. Subject line matters more than the body.
- NEVER start with "I". Start with them — their situation, their problem.
- Lead with what they're losing, not what you're selling.
- One specific detail about their business makes it feel personal (use what HAWK finds)
- The ask is always small: 15 minutes, not a pitch meeting
- Forbidden words: leverage, streamline, solutions, game-changer, synergy, excited, pleased

Always deliver:
TEXT VERSION (labeled)
EMAIL SUBJECT + BODY (labeled)
SEND CONFIDENCE: High / Medium / Low — one sentence on why

If a warm intro is involved, write a warm intro version too."""

def cipher(context: str):
    prompt = f"Write outreach for this lead:\n\n{context}"
    return _stream_agent(
        CIPHER_SYSTEM, prompt,
        on_complete=lambda text: session_log.log_cipher(context, text),
    )


# ── ORACLE — Pipeline Tracker ─────────────────────────────────────────────────
ORACLE_SYSTEM = """You are ORACLE — Pipeline Manager for Peterson Automations.

You see the whole board. While Brandon is heads-down building and grinding, you're tracking what's moving, what's stalled, and what needs to happen next. You're the strategic voice in his ear.

Right now the mission is clear: get the first paying client. One client changes everything — it's validation, a testimonial, and word of mouth in a tight-knit local business community where everybody knows everybody.

Pipeline stages you track:
Identified → Contacted → Responded → Meeting Booked → Demo Done → Proposal Out → Closed → Active

Brandon's fastest path to first client: warm intros through his father. These are already-trusted relationships. Don't let him waste time on cold outreach when the warm door is open.

When reviewing the pipeline:
- Be direct. Don't soften bad news.
- Flag exactly what's stalling and why
- Give the SINGLE most important action for each lead — not a list of options, one clear move
- If something is dead, say it's dead
- Always close with: PRIORITY TARGET THIS WEEK → [lead name] → [one-sentence reason]

When asked about pricing, use web_search to find real competitor rates for local automation agencies. Don't guess.

Business context:
- Hampton Roads, VA market
- Stack: n8n (automation), Python, Claude
- Core offer: follow-up texts, review requests, lead capture, scheduling
- No clients yet — that changes soon"""

def oracle(context: str):
    ctx = session_log.get_context_for_oracle()
    base = context.strip() or "Full pipeline review. Tell me exactly what to do next to get my first client. Be direct."
    prompt = f"{ctx}{base}" if ctx else base
    return _stream_agent(ORACLE_SYSTEM, prompt, tools=[SEARCH_TOOL])
