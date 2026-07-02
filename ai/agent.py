"""Main AI agent loop for GitHub Companion."""
from __future__ import annotations
import json

from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from ai.provider import get_provider
from ai.model_selector import select_model_type, describe_model_type
from ai.tools import TOOL_SCHEMAS, execute_tool
from ai.memory import ConversationMemory
from ai.context import get_project_context
from ai.prompts import SYSTEM_PROMPT, build_context_message
from ai.planner import is_complex_task, get_plan_for, format_plan
from ai.providers.base_provider import BaseProvider

console = Console()

# Safety cap: prevent infinite tool-call loops
MAX_TOOL_ITERATIONS = 10


class Agent:
    """
    GitHub Companion AI agent with automatic model selection.

    On every user turn:
      1. Classify the request → model type (coding / reasoning / assistant).
      2. Fetch the right provider via the factory (with automatic fallback).
      3. Show which provider + model is being used.
      4. Build messages: system prompt + project context + history + user input.
      5. Call provider.generate() — with tools only if provider.supports_tools().
      6. If tool_calls returned → execute each → append results → loop.
      7. When plain text returned → display in Rich panel → save to memory.

    Provider instances are cached by model type so we don't reconnect on
    every turn (e.g., repeated coding questions reuse the same Ollama connection).
    """

    def __init__(self, provider: BaseProvider | None = None) -> None:
        self.memory: ConversationMemory = ConversationMemory()
        self._provider_cache: dict[str, BaseProvider] = {}
        self.provider = provider

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(self, user_input: str, system_prompt: str | None = None, enable_tools: bool = True) -> None:
        """Process a user prompt through the full agent loop."""

        # ── 1. Pick model ─────────────────────────────────────────────────────
        if self.provider:
            provider = self.provider
        else:
            model_type = select_model_type(user_input)
            try:
                provider = self._get_provider(model_type)
            except RuntimeError as exc:
                rprint(f"\n[bold red]❌ {exc}[/bold red]")
                return

            type_label = describe_model_type(model_type)
            rprint(
                f"[dim]  {type_label} | "
                f"{provider.name} / {provider.model} | "
                f"tools={'yes' if (provider.supports_tools() and enable_tools) else 'no'}[/dim]"
            )

        # ── 2. Show pre-execution plan for known complex tasks ─────────────────
        plan = get_plan_for(user_input)
        if plan and is_complex_task(user_input):
            rprint("\n[bold blue]  📋 Execution Plan:[/bold blue]")
            rprint(format_plan(plan))
            rprint()

        # ── 3. Build messages ──────────────────────────────────────────────────
        context = get_project_context()
        sys_prompt = system_prompt or SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "system", "content": build_context_message(context)},
            *self.memory.get_history(),
            {"role": "user", "content": user_input},
        ]
        self.memory.add_user(user_input)

        # Tools are passed only when the model supports function calling and tools are enabled
        active_tools = TOOL_SCHEMAS if (provider.supports_tools() and enable_tools) else None


        # ── 4. Agent loop ──────────────────────────────────────────────────────
        iterations = 0

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1

            with console.status("[bold yellow]  Thinking...[/bold yellow]", spinner="dots"):
                response = provider.generate(messages, tools=active_tools)

            # ── Tool calls ─────────────────────────────────────────────────────
            if active_tools and response.tool_calls:
                messages.append({
                    "role":    "assistant",
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

                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

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

                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      result,
                    })

                continue  # Feed results back to the LLM

            # ── Final text response ────────────────────────────────────────────
            final_text = (response.content or "").strip()
            if final_text:
                rprint()
                console.print(Panel(
                    final_text,
                    title=f"[bold purple]🤖 {provider.name.capitalize()} / {provider.model}[/bold purple]",
                    border_style="purple",
                    padding=(1, 2),
                ))
                self.memory.add_assistant(final_text)
            break

        else:
            rprint("[bold red]  ⚠  Agent reached the maximum tool call limit.[/bold red]")

    # ── Private ────────────────────────────────────────────────────────────────

    def _get_provider(self, model_type: str) -> BaseProvider:
        """Return a cached provider for the given model type, creating if needed."""
        if model_type not in self._provider_cache:
            self._provider_cache[model_type] = get_provider(model_type)
        return self._provider_cache[model_type]


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
