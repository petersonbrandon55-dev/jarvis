import json
import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL

SYSTEM_PROMPT = """You are JARVIS — an advanced AI personal assistant for Brandon Peterson.

Personality: Intelligent, concise, occasionally witty. Like Tony Stark's JARVIS — competent, direct, slightly dry humor. Call Brandon "Boss" occasionally. You know his full situation and speak to it directly.

Key rules for voice responses:
- Keep responses SHORT — you're speaking aloud, not writing an essay
- No bullet points or markdown in voice responses — speak naturally
- For complex info, summarize the key points conversationally

--- WHO BRANDON IS ---
- College athlete: played football all 4 years + ran track. Discipline is baked in.
- Now a tech builder and entrepreneur. Has a following on TikTok (day-in-the-life content, wants to restart).
- Friends say they see him getting famous — he sees it as business ownership and building a brand.

--- WHAT'S LIVE RIGHT NOW ---
- **Security+ exam: July 10–11, 2026** — studying hard, use get_key_dates for the live countdown
- **Booz Allen Hamilton start: July 13, 2026** — first real job out of college, government security work
- **Peterson Automations** — AI automation business targeting local service businesses (lawn care, pool maintenance, HVAC) in Hampton Roads VA. Dad has warm intros to these owners. Stack: n8n. Core offer: automated follow-up texts, Google review requests, lead capture, appointment scheduling.
- **JARVIS** — this assistant, which Brandon built himself from scratch
- **Trading app idea** — Duolingo-style app for teaching trading; medium-term project post-Booz Allen

--- HOMELAB / SECURITY OPS CENTER ---
Brandon runs a real home SOC in his bedroom:
- Dell Optiplex 3050 (VM host): Wazuh SIEM + Splunk Enterprise
- Raspberry Pi 5: Pi-hole DNS filtering (77k+ domains blocked), monitoring agent
- Dell Inspiron 15R: Kali Linux native (dedicated attack machine)
- Mac: command center + Kali VM
- Surface Pro 8: school + Kali WSL2
- PS5: monitored network endpoint
- Wazuh → Universal Forwarder → Splunk pipeline is live
- Tailscale VPN for remote access
- Pending: OPNsense firewall, VLANs, Security Onion, Docker on Pi, Ansible

--- CAPSTONE PROJECT (completed) ---
Built a full penetration test proof-of-concept: 5 Python scripts simulating attacks on a live sports data feed, SHA-256 integrity detection, MITRE ATT&CK mapping, Flask live dashboard, deployed on Raspberry Pi with Tailscale. Presented at capstone fair. Pitchable to DraftKings/FanDuel.

--- OBSIDIAN SECOND BRAIN ---
Vault: BP's Second Brain. Key locations:
- Plans/_Today.md — tasks due/scheduled today
- Plans/Week N - <date>.md — weekly task files
- wiki/security/homelab.md — homelab docs
- wiki/security/security-plus.md — Security+ study notes
- wiki/security/capstone-sports-data-pentest.md — capstone project
- wiki/business/peterson-automations.md — business notes
- wiki/self/personal-brand.md — personal brand strategy

--- TOOL GUIDANCE ---
- get_key_dates → always use when Brandon asks how long until the exam or Booz Allen
- security_plus_quiz → use when Brandon asks to be quizzed, drilled, or tested
- get_homelab_status → use when Brandon asks about the lab, Pi-hole, or network
- get_todays_tasks / get_current_week_plan → use for anything task/schedule related
- web_search → always use for current info, never guess"""

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information, news, AI tools, business strategies, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "open_application",
        "description": "Open a Mac application by name",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Application name, e.g. 'Safari', 'Spotify', 'Terminal'"},
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "run_shell_command",
        "description": "Run a shell command on the Mac. Use for file operations, system info, launching things, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_obsidian_note",
        "description": "Read the contents of an Obsidian note by filename",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Note filename (with or without .md), e.g. 'weekly plan' or 'business ideas.md'"},
                "folder": {"type": "string", "description": "Optional subfolder within vault", "default": ""},
            },
            "required": ["filename"],
        },
    },
    {
        "name": "write_obsidian_note",
        "description": "Create or update an Obsidian note",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Note filename"},
                "content": {"type": "string", "description": "Full note content in Markdown"},
                "folder": {"type": "string", "description": "Optional subfolder within vault", "default": ""},
                "append": {"type": "boolean", "description": "If true, append to existing note instead of overwriting", "default": False},
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "list_obsidian_notes",
        "description": "List notes in the Obsidian vault, optionally filtered by folder",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "Optional subfolder to list", "default": ""},
            },
        },
    },
    {
        "name": "get_todays_tasks",
        "description": "Get all tasks scheduled or due today from Brandon's weekly plans",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_current_week_plan",
        "description": "Get the full contents of the current week's plan",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_week_plan",
        "description": "Get a specific week plan by name, e.g. 'Week 1' or 'Week 2'",
        "input_schema": {
            "type": "object",
            "properties": {
                "week_name": {"type": "string", "description": "Partial week name, e.g. 'Week 1', 'Jun 1'"},
            },
            "required": ["week_name"],
        },
    },
    {
        "name": "add_task",
        "description": "Add a new task to a week plan. Use this when Brandon asks to add something to his plans.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "The task text"},
                "section": {"type": "string", "description": "Section to add under, e.g. 'JARVIS', 'Peterson Automations', 'Day Trading'", "default": ""},
                "week": {"type": "string", "description": "'current' or partial week name like 'Week 2'", "default": "current"},
                "due_date": {"type": "string", "description": "ISO date YYYY-MM-DD, or empty string", "default": ""},
                "priority": {"type": "string", "description": "highest, high, medium, normal, low", "default": "normal"},
                "tag": {"type": "string", "description": "Task tag: 'craft' or 'career'", "default": "craft"},
            },
            "required": ["task_description"],
        },
    },
    {
        "name": "mark_task_done",
        "description": "Mark a task as complete by matching partial text",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_partial": {"type": "string", "description": "Partial text of the task to mark done"},
            },
            "required": ["task_partial"],
        },
    },
    {
        "name": "list_week_plans",
        "description": "List all available week plan files",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_key_dates",
        "description": "Get countdown in days to Brandon's key upcoming dates: Security+ exam (July 10) and Booz Allen Hamilton start (July 13)",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "security_plus_quiz",
        "description": "Generate a spoken Security+ quiz question from Brandon's study notes. Use when he asks to be quizzed, tested, or drilled on Security+.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_homelab_status",
        "description": "Get live status of Brandon's home SOC: Pi-hole stats (queries blocked, percentage), Pi uptime, Wazuh alert count",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "smart_home_control",
        "description": "Control smart home devices via Home Assistant (lights, switches, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Action: 'turn_on', 'turn_off', 'toggle', 'set_brightness', 'list_devices'"},
                "entity_id": {"type": "string", "description": "Home Assistant entity ID, e.g. 'light.living_room'"},
                "brightness": {"type": "integer", "description": "Brightness 0-255 (for set_brightness action)"},
            },
            "required": ["action"],
        },
    },
]


class Brain:
    def __init__(self, tool_handlers: dict):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.tool_handlers = tool_handlers
        self.history = []

    def think(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=self.history,
        )

        # Agentic tool-use loop
        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[JARVIS] Using tool: {block.name}({json.dumps(block.input)})")
                    result = self._dispatch(block.name, block.input)
                    print(f"[JARVIS] Tool result: {str(result)[:200]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })

            self.history.append({"role": "assistant", "content": response.content})
            self.history.append({"role": "user", "content": tool_results})

            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history,
            )

        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        self.history.append({"role": "assistant", "content": text})

        # Keep history from growing unbounded — keep last 20 turns
        if len(self.history) > 40:
            self.history = self.history[-40:]

        return text

    def _dispatch(self, name: str, inputs: dict):
        handler = self.tool_handlers.get(name)
        if not handler:
            return f"Tool '{name}' is not registered."
        try:
            return handler(**inputs)
        except Exception as e:
            return f"Tool error: {e}"
