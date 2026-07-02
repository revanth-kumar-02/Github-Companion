"""Readme command — interactively generate a professional README.md."""
import os
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from services.readme_service import generate_readme
from utils.ui import success, error, warning, info

console = Console()


def _prompt_list(prompt: str) -> list:
    """Prompt the user to enter items one-by-one until an empty line is entered."""
    rprint(f"[bold cyan]  {prompt}[/bold cyan] [dim](press Enter twice when done)[/dim]")
    items = []
    while True:
        item = console.input("    → ").strip()
        if not item:
            break
        items.append(item)
    return items


def show_gc_readme():
    rprint()
    rprint("[bold bright_white]README Generator[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    rprint("[dim]  Answer the prompts below to generate a professional README.md[/dim]")
    rprint()

    # ── Collect metadata ────────────────────────────────────────────────────
    project_name  = console.input("[bold cyan]  Project Name         : [/bold cyan]").strip()
    description   = console.input("[bold cyan]  Description          : [/bold cyan]").strip()

    rprint()
    features      = _prompt_list("Features")

    rprint()
    installation  = console.input("[bold cyan]  Installation Command : [/bold cyan]").strip()
    usage         = console.input("[bold cyan]  Usage Command        : [/bold cyan]").strip()

    rprint()
    technologies  = _prompt_list("Technologies Used")

    rprint()
    license_type  = console.input("[bold cyan]  License              : [/bold cyan][dim](e.g. MIT)[/dim][bold cyan] : [/bold cyan]").strip()
    author        = console.input("[bold cyan]  Author               : [/bold cyan]").strip()

    rprint()
    output_folder = console.input("[bold cyan]  Output Folder        : [/bold cyan]").strip()

    # ── Validate output folder ──────────────────────────────────────────────
    if not output_folder:
        output_folder = "."

    if not os.path.isdir(output_folder):
        warning(f"Folder '{output_folder}' not found. Creating it...")
        try:
            os.makedirs(output_folder, exist_ok=True)
        except OSError as e:
            error(f"Failed to create folder: {e}")
            return

    # ── Auto-fill missing fields ────────────────────────────────────────────
    if not project_name:
        project_name = os.path.basename(os.path.normpath(output_folder))

    if not license_type:
        license_type = "MIT"

    # ── Generate README ─────────────────────────────────────────────────────
    data = {
        "name":         project_name,
        "description":  description,
        "features":     features,
        "installation": installation,
        "usage":        usage,
        "technologies": technologies,
        "license":      license_type,
        "author":       author,
    }

    with console.status("[bold yellow]  Generating README.md...[/bold yellow]"):
        output_path = generate_readme(data, output_folder)

    rprint()
    console.print(Panel(
        f"[bold green]📄 README.md generated successfully![/bold green]\n\n"
        f"[bold white]File :[/bold white] [underline]{output_path}[/underline]\n"
        f"[bold white]Project :[/bold white] {project_name}\n"
        f"[bold white]Author  :[/bold white] {author or '—'}\n"
        f"[bold white]License :[/bold white] {license_type}",
        title="[bold green]✅ README Created[/bold green]",
        border_style="green",
        padding=(1, 2),
    ))
