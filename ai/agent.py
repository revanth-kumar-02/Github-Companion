"""Main AI agent loop for GitHub Companion."""
from __future__ import annotations
import json

from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from ai.provider import OpenAIProvider
from ai.tools import TOOL_SCHEMAS, execute_tool
from ai.memory import ConversationMemory
from ai.context import get_project_context
from ai.prompts import SYSTEM_PROMPT, build_context_message
from ai.planner import is_complex_task, get_plan_for, format_plan
from services.config_service import get_openai_api_key, get_ai_model

console = Console()

# Safety cap: prevent infinite tool-call loops
MAX_TOOL_ITERATIONS = 10


class Agent:
    """
    GitHub Companion AI agent powered by OpenAI function calling.

    Lifecycle:
      1. Collect project context (cwd, git, file tree).
      2. Show plan for known complex tasks.
      3. Build messages: system + context + history + user input.
      4. Call OpenAI — get back either tool_calls or a text response.
      5. If tool_calls: execute each tool → append results → loop back to 4.
      6. When the model returns plain text: display in a Rich panel and save to memory.
    """

    def __init__(self):
        api_key = get_openai_api_key()
        model   = get_ai_model()
        self.provider = OpenAIProvider(api_key=api_key, model=model)
        self.memory   = ConversationMemory()
        rprint(f"[dim]  Model: {model}[/dim]")

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(self, user_input: str) -> None:
        """Process a user prompt through the full agent loop."""

        # Show pre-execution plan for known complex tasks
        plan = get_plan_for(user_input)
        if plan and is_complex_task(user_input):
            rprint("\n[bold blue]  📋 Execution Plan:[/bold blue]")
            rprint(format_plan(plan))
            rprint()

        # Build the initial message list for this turn
        context  = get_project_context()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": build_context_message(context)},
            *self.memory.get_history(),
            {"role": "user", "content": user_input},
        ]
        self.memory.add_user(user_input)

        # ── Agent loop ─────────────────────────────────────────────────────────
        iterations = 0

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1

            # Call the LLM
            with console.status("[bold yellow]  Thinking...[/bold yellow]", spinner="dots"):
                response = self.provider.chat(messages, TOOL_SCHEMAS)

            # ── Tool calls ─────────────────────────────────────────────────────
            if response.tool_calls:
                # Append the assistant message (with tool_calls) to the conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id":   tc.id,
                            "type": "function",
                            "function": {
                                "name":      tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in response.tool_calls
                    ],
                })

                # Execute each tool and collect results
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    # Show what tool is being called
                    arg_preview = _format_args(tool_args)
                    rprint(
                        f"[dim]  ⚙  Running[/dim] [bold cyan]{tool_name}[/bold cyan]"
                        + (f"[dim]({arg_preview})[/dim]" if arg_preview else "")
                    )

                    with console.status(
                        f"[bold yellow]  Executing {tool_name}...[/bold yellow]",
                        spinner="dots",
                    ):
                        result = execute_tool(tool_name, tool_args)

                    rprint(f"[dim]  ✔  {tool_name} done[/dim]")

                    # Append tool result to messages
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      result,
                    })

                continue  # Send results back to the LLM for the next step

            # ── Final text response ────────────────────────────────────────────
            final_text = (response.content or "").strip()
            if final_text:
                rprint()
                console.print(Panel(
                    final_text,
                    title="[bold purple]🤖 GitHub Companion AI[/bold purple]",
                    border_style="purple",
                    padding=(1, 2),
                ))
                self.memory.add_assistant(final_text)
            break

        else:
            rprint("[bold red]  ⚠  Agent reached the maximum tool call limit.[/bold red]")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_args(args: dict) -> str:
    """Format tool args as a compact inline string for display."""
    if not args:
        return ""
    parts = []
    for k, v in args.items():
        val = str(v)
        if len(val) > 35:
            val = val[:32] + "..."
        parts.append(f"{k}={val!r}")
    return ", ".join(parts)
