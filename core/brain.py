import json
import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL

SYSTEM_PROMPT = """You are JARVIS — an advanced AI personal assistant for Brandon Peterson, entrepreneur and founder of Peterson Automations.

Personality: Intelligent, concise, occasionally witty. Like Tony Stark's JARVIS — competent, direct, slightly dry humor. Call Brandon "Boss" occasionally.

Key rules for voice responses:
- Keep responses SHORT — you're speaking aloud, not writing an essay
- No bullet points or markdown in voice responses — speak naturally
- For complex info (news, strategies), summarize the key points conversationally

Brandon's context:
- Runs an AI automation business (Peterson Automations) — early stage, always looking for growth strategies
- Wants proactive AI news and business strategy insights
- Uses Obsidian for his second brain / personal wiki
- On Mac primarily, also has a Dell

You have tools to: search the web, control the Mac, read/write Obsidian notes, manage Brandon's plans/tasks, and control smart home devices.
Always use tools when you need current info rather than guessing.

Brandon's Obsidian Plans structure:
- Plans/_Today.md — tasks due/scheduled today
- Plans/Week N - <date>.md — weekly task files (Week 1, Week 2, etc.)
- Sections inside each week: CAREER (Security+, Peterson Automations) and CRAFT (JARVIS, Day Trading)
When Brandon asks what's on his plate, what's due, or to add/check off a task — use the plan tools."""

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
