"""Code command — autonomous AI coding agent mode with project planning."""
from __future__ import annotations
import json
import sys
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from ai.agent import Agent
from ai.providers.base_provider import BaseProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from services.config_service import (
    get_custom_models,
    get_ollama_host,
    get_openrouter_api_key,
)
from utils.ui import error, success, info

console = Console()


def _get_selected_provider() -> BaseProvider | None:
    """Show model selection menu and return the corresponding provider."""
    rprint()
    rprint("[bold bright_white]Choose Coding Model[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    rprint("  [bold cyan]1[/bold cyan]. Qwen 2.5 Coder ⭐ [dim]Recommended[/dim]")
    rprint("  [bold cyan]2[/bold cyan]. DeepSeek V3")
    rprint("  [bold cyan]3[/bold cyan]. DeepSeek R1")
    rprint("  [bold cyan]4[/bold cyan]. Llama 3.3")

    customs = get_custom_models()
    for idx, c in enumerate(customs, start=5):
        rprint(f"  [bold cyan]{idx}[/bold cyan]. {c.get('provider_name')} - {c.get('model_name')} ⭐")

    rprint()

    choice = console.input("[bold yellow]Select model number : [/bold yellow]").strip()

    if choice == "1":
        # Qwen 2.5 Coder (Ollama fallback OpenRouter)
        ollama = OllamaProvider("qwen2.5-coder", host=get_ollama_host())
        if ollama.health_check():
            return ollama
        try:
            key = get_openrouter_api_key()
            return OpenRouterProvider("qwen2.5-coder", api_key=key)
        except Exception:
            raise RuntimeError(
                "Ollama is offline and OpenRouter key is not configured.\n"
                "  Please run Ollama locally or add openrouter_api_key to settings.json"
            )

    elif choice == "2":
        # DeepSeek V3 via OpenRouter
        key = get_openrouter_api_key()
        return OpenRouterProvider("deepseek-v3", api_key=key)

    elif choice == "3":
        # DeepSeek R1 (Ollama fallback OpenRouter)
        ollama = OllamaProvider("deepseek-r1", host=get_ollama_host())
        if ollama.health_check():
            return ollama
        key = get_openrouter_api_key()
        return OpenRouterProvider("deepseek-r1", api_key=key)

    elif choice == "4":
        # Llama 3.3 (Ollama fallback OpenRouter)
        ollama = OllamaProvider("llama3.3", host=get_ollama_host())
        if ollama.health_check():
            return ollama
        key = get_openrouter_api_key()
        return OpenRouterProvider("llama3.3", api_key=key)

    else:
        try:
            val = int(choice)
            idx = val - 5
            if 0 <= idx < len(customs):
                from ai.providers.custom_provider import CustomProvider
                return CustomProvider(customs[idx])
        except ValueError:
            pass

    return None


def start_code_mode() -> None:
    """Main AI Coding Agent flow (Planning -> Approval -> Generation)."""
    try:
        provider = _get_selected_provider()
    except Exception as exc:
        rprint(f"[bold red]❌ Config error:[/bold red] {exc}")
        return

    if not provider:
        error("Invalid selection.")
        return

    rprint(f"[dim]  Selected: {provider.name} ({provider.model})[/dim]\n")

    project_idea = console.input("[bold cyan]What project would you like to build? : [/bold cyan]").strip()
    if not project_idea:
        error("Project idea cannot be empty.")
        return

    # ── Planning Stage ────────────────────────────────────────────────────────
    plan = _generate_plan(provider, project_idea)
    if not plan:
        error("Failed to generate implementation plan.")
        return

    # User review loop
    while True:
        _display_plan(plan)

        rprint("\n[bold yellow]Options:[/bold yellow]")
        rprint("  [bold green]Y[/bold green]. Approve and Start Coding")
        rprint("  [bold cyan]E[/bold cyan]. Edit Plan")
        rprint("  [bold red]N[/bold red]. Cancel")
        rprint()

        action = console.input("[bold yellow]Select option (Y/E/N) : [/bold yellow]").strip().upper()

        if action == "Y":
            break
        elif action == "N":
            rprint("[dim]  Cancelled by user.[/dim]")
            return
        elif action == "E":
            feedback = console.input("\n[bold cyan]What would you like to edit? : [/bold cyan]").strip()
            if feedback:
                with console.status("[bold yellow]  Re-planning project...[/bold yellow]", spinner="dots"):
                    plan = _regenerate_plan(provider, project_idea, plan, feedback)
                if not plan:
                    error("Failed to update implementation plan.")
                    return
        else:
            error("Invalid option.")

    # ── Coding Stage ──────────────────────────────────────────────────────────
    rprint()
    rprint("[bold purple]Creating project...[/bold purple]")
    rprint()

    # Instantiate the agent with the selected provider
    agent = Agent(provider=provider)

    prompt = f"""\
You are an autonomous AI Coding Agent. The user approved this project plan:
{json.dumps(plan, indent=2)}

Please build the project now in the current directory.
1. Create directories and files one by one using the 'write_file' tool.
2. For each file you write successfully, output a message on a new line: '✓ [file path]'. E.g. '✓ app.py'.
3. Do not output placeholders or comments like '// implement here'. Write full, high-quality, production-ready code.
4. Once all files have been created and the project is fully set up, summarize what you built and output 'Project Complete.'.
"""

    agent.run(prompt)


# ── Plan generation helpers ──────────────────────────────────────────────────

def _generate_plan(provider: BaseProvider, project_idea: str) -> dict | None:
    """Request the AI to generate a structured implementation plan in JSON."""
    system_prompt = """\
You are a Software Architect. You analyze user requests and produce a structured JSON implementation plan.
You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain these exact keys:
- project_name: string (short, clean project name)
- files_count: integer (estimated total files to create)
- architecture: string (e.g. MVC, Modular, Single-file)
- dependencies: list of strings
- estimated_time: string (e.g. '30 sec', '1 min')
- folder_structure: string (ascii diagram showing folders and files)
- files: list of strings (paths to the files to create)
- features: list of strings (key features of the app)
- complexity: string (Simple, Medium, Complex)
- strategy: string (short description of the implementation strategy)
"""
    prompt = f"Analyze and plan: {project_idea}"

    with console.status("[bold yellow]  Planning project...[/bold yellow]", spinner="dots"):
        try:
            # We run with tools disabled during planning to get pure text JSON
            msg = provider.generate(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
            )
            content = msg.content or ""
            return _parse_json_block(content)
        except Exception as exc:
            error(f"Error during planning: {exc}")
            return None


def _regenerate_plan(provider: BaseProvider, project_idea: str, old_plan: dict, feedback: str) -> dict | None:
    """Update implementation plan based on user feedback."""
    system_prompt = """\
You are a Software Architect. Update the implementation plan based on user feedback.
You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Keep the exact same keys as the original JSON.
"""
    prompt = f"""\
Original Idea: {project_idea}
Original Plan: {json.dumps(old_plan, indent=2)}
User request/feedback: {feedback}

Generate the updated JSON plan.
"""
    try:
        msg = provider.generate(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        content = msg.content or ""
        return _parse_json_block(content)
    except Exception as exc:
        error(f"Error updating plan: {exc}")
        return None


def _parse_json_block(content: str) -> dict | None:
    """Parse JSON from markdown code block."""
    try:
        # Extract content between ```json and ```
        if "```json" in content:
            parts = content.split("```json")
            json_str = parts[1].split("```")[0].strip()
        elif "```" in content:
            parts = content.split("```")
            json_str = parts[1].strip()
        else:
            json_str = content.strip()

        return json.loads(json_str)
    except Exception:
        # Try direct parsing as fallback
        try:
            return json.loads(content.strip())
        except Exception:
            return None


def _display_plan(plan: dict) -> None:
    """Beautifully format the implementation plan using Rich."""
    rprint()
    plan_info = (
        f"[bold white]Project :[/bold white] {plan.get('project_name', 'Unnamed')}\n"
        f"[bold white]Files   :[/bold white] {plan.get('files_count', 0)}\n"
        f"[bold white]Arch    :[/bold white] {plan.get('architecture', 'Standard')}\n"
        f"[bold white]Deps    :[/bold white] {', '.join(plan.get('dependencies', [])) or 'None'}\n"
        f"[bold white]Time    :[/bold white] {plan.get('estimated_time', 'N/A')}\n"
        f"[bold white]Level   :[/bold white] {plan.get('complexity', 'Medium')}"
    )

    console.print(Panel(
        plan_info,
        title="[bold green]📋 Implementation Plan[/bold green]",
        border_style="green",
        expand=False,
    ))

    # Features and Folder structure
    rprint("\n[bold cyan]✨ Key Features:[/bold cyan]")
    for feat in plan.get("features", []):
        rprint(f"  • {feat}")

    rprint("\n[bold cyan]📁 Target Folder Structure:[/bold cyan]")
    rprint(plan.get("folder_structure", ""))

    rprint("\n[bold cyan]🛠️ Implementation Strategy:[/bold cyan]")
    rprint(plan.get("strategy", ""))
