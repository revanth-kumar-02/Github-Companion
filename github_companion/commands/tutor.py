"""Tutor command — interactive walkthrough tutorial for GitHub Companion."""
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from github_companion.utils.ui import success, info, warning, error

console = Console()
GC_DIR = Path.home() / ".gc"
PROGRESS_PATH = GC_DIR / "tutor_progress.json"

CHAPTERS = [
    {
        "id": 1,
        "title": "Welcome to GitHub Companion",
        "desc": "Overview of GC features, modes, and command layout."
    },
    {
        "id": 2,
        "title": "System Diagnostics",
        "desc": "Check your local system requirements using the doctor command."
    },
    {
        "id": 3,
        "title": "Workspace & Projects Configuration",
        "desc": "Learn how GC automates project generation and paths."
    },
    {
        "id": 4,
        "title": "Personalizing Visual Appearance",
        "desc": "Customize terminal themes with custom presets."
    },
    {
        "id": 5,
        "title": "Autonomous AI Coding Agents",
        "desc": "Understanding Ask, AI, and Autonomous Code execution."
    }
]


def load_progress() -> dict:
    """Load tutor progress tracking file."""
    if not PROGRESS_PATH.exists():
        return {"completed_chapters": []}
    try:
        with open(PROGRESS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"completed_chapters": []}


def save_progress(progress: dict) -> None:
    """Save tutor progress tracking file."""
    GC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(PROGRESS_PATH, "w") as f:
            json.dump(progress, f, indent=4)
    except Exception:
        pass


def mark_chapter_completed(chapter_id: int) -> None:
    """Mark a specific chapter as completed in progress config."""
    progress = load_progress()
    if chapter_id not in progress["completed_chapters"]:
        progress["completed_chapters"].append(chapter_id)
        save_progress(progress)


def run_chapter_1() -> None:
    rprint()
    rprint(Panel(
        "[bold bright_white]Chapter 1: Introducing GitHub Companion (GC)[/bold bright_white]\n\n"
        "GitHub Companion is an advanced autonomous CLI developer tool built to supercharge your "
        "workflows with GitHub integrations and AI capabilities.\n\n"
        "It provides standard wrapper helpers for managing profile credentials, workspace git status, "
        "and repositories, as well as powerful AI agents to write code directly.",
        border_style="bright_blue",
        title="GC Tutor"
    ))
    rprint("\n[dim]Press Enter to continue...[/dim]")
    input()
    
    rprint("[bold yellow]Key CLI modes:[/bold yellow]")
    rprint("  • [cyan]Interactive Shell[/cyan]: Simply run `gc` to get a persistent terminal session.")
    rprint("  • [cyan]Direct CLI Invocation[/cyan]: Run `python app.py <command>` to run commands quickly.")
    
    rprint("\n[dim]Press Enter to finish Chapter 1...[/dim]")
    input()
    mark_chapter_completed(1)
    success("Chapter 1 Completed!")


def run_chapter_2() -> None:
    rprint()
    rprint(Panel(
        "[bold bright_white]Chapter 2: Diagnosing setup with doctor[/bold bright_white]\n\n"
        "GC comes with a diagnostic tool named `doctor` to ensure everything needed is fully installed "
        "and authenticated (such as Git, active internet connection, credentials, and configured LLMs).",
        border_style="bright_blue",
        title="GC Tutor"
    ))
    
    rprint("\nLet's check if you remember the command check for LLMs:")
    rprint("To check diagnostic status of AI models registry specifically, which option do you add?")
    rprint("  [bold cyan]1[/bold cyan]. doctor --llm")
    rprint("  [bold cyan]2[/bold cyan]. doctor ai")
    rprint("  [bold cyan]3[/bold cyan]. doctor test")
    rprint()
    
    while True:
        try:
            choice = console.input("[bold yellow]Choose 1, 2, or 3 : [/bold yellow]").strip()
        except (KeyboardInterrupt, EOFError):
            return
        if choice == "2":
            success("Correct! Running `doctor ai` diagnoses model availability and response metrics.")
            break
        else:
            warning("Incorrect, try again! Hint: It is 'doctor ai'.")

    rprint("\n[dim]Press Enter to finish Chapter 2...[/dim]")
    input()
    mark_chapter_completed(2)
    success("Chapter 2 Completed!")


def run_chapter_3() -> None:
    rprint()
    rprint(Panel(
        "[bold bright_white]Chapter 3: Workspaces & Projects[/bold bright_white]\n\n"
        "GC tracks a default directory location to generate codebases, inspect packages, or execute git sync commands.\n\n"
        "  • [cyan]workspace[/cyan]: Displays or configures the absolute file path to the default workspace directory.\n"
        "  • [cyan]projects[/cyan]: Lists existing folders inside the workspace and lets you run commands inside them.",
        border_style="bright_blue",
        title="GC Tutor"
    ))
    rprint("\n[dim]Press Enter to continue...[/dim]")
    input()

    rprint("[bold yellow]Configuration Tip:[/bold yellow]")
    rprint("You can easily view or edit settings in detail using `gc config` at any time.")

    rprint("\n[dim]Press Enter to finish Chapter 3...[/dim]")
    input()
    mark_chapter_completed(3)
    success("Chapter 3 Completed!")


def run_chapter_4() -> None:
    rprint()
    rprint(Panel(
        "[bold bright_white]Chapter 4: Visual Theme Personalization[/bold bright_white]\n\n"
        "You can customize GC CLI aesthetics in a flash using the new `theme` command.\n\n"
        "The theme configuration supports preset choices such as:\n"
        "  • [bold #bd93f9]Dracula[/bold #bd93f9]: Classic purple-themed layout.\n"
        "  • [bold #81a1c1]Nord[/bold #81a1c1]: Arctic polar night blue colors.\n"
        "  • [bold #ff007f]Synthwave[/bold #ff007f]: Bright neon aesthetic styling.\n"
        "  • [bold #f92672]Monokai[/bold #f92672]: Classic high-contrast syntax colors.",
        border_style="bright_blue",
        title="GC Tutor"
    ))
    rprint("\nTo see the available themes and configure them interactively, run [bold cyan]gc theme[/bold cyan] from the main console.")
    rprint("\n[dim]Press Enter to finish Chapter 4...[/dim]")
    input()
    mark_chapter_completed(4)
    success("Chapter 4 Completed!")


def run_chapter_5() -> None:
    rprint()
    rprint(Panel(
        "[bold bright_white]Chapter 5: AI Coding Agents[/bold bright_white]\n\n"
        "GitHub Companion features 3 distinct AI modes tailored for different development tasks:\n\n"
        "  1. [cyan]gc ask[/cyan] : General Q&A conversational helper (no write permissions to files).\n"
        "  2. [cyan]gc ai[/cyan] : Natural language assistant capable of executing shell commands and searching logs.\n"
        "  3. [cyan]gc code[/cyan]: Autonomous agent that builds implementation plans, generates code, and edits local files.",
        border_style="bright_blue",
        title="GC Tutor"
    ))
    rprint("\n[dim]Press Enter to continue...[/dim]")
    input()

    rprint("[bold green]All chapters completed! You are now a GC Expert Developer. 🚀[/bold green]")
    rprint("\n[dim]Press Enter to finish Chapter 5...[/dim]")
    input()
    mark_chapter_completed(5)
    success("Chapter 5 Completed!")


def tutor_cmd(args: list[str] = None) -> None:
    """Run interactive CLI guide step-by-step."""
    progress = load_progress()
    completed = progress.get("completed_chapters", [])

    if args and len(args) > 0:
        chapter_sel = args[0].strip()
        if chapter_sel.isdigit():
            ch_id = int(chapter_sel)
            if ch_id == 1:
                run_chapter_1()
            elif ch_id == 2:
                run_chapter_2()
            elif ch_id == 3:
                run_chapter_3()
            elif ch_id == 4:
                run_chapter_4()
            elif ch_id == 5:
                run_chapter_5()
            else:
                error(f"Invalid chapter ID: {ch_id}. Chapters go from 1 to 5.")
        else:
            error(f"Invalid argument: '{chapter_sel}'. Enter a number from 1 to 5.")
        return

    # Interactive Chapter selector
    while True:
        rprint()
        rprint("[bold bright_white]GitHub Companion Interactive Tutor[/bold bright_white]")
        rprint(f"[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n")
        
        for ch in CHAPTERS:
            status_icon = "[bold green]✓[/bold green]" if ch["id"] in completed else "[dim] [/dim]"
            rprint(f"  {status_icon} [bold cyan]{ch['id']}[/bold cyan]. [bold]{ch['title']}[/bold]")
            rprint(f"     [dim]{ch['desc']}[/dim]")
        rprint()
        rprint("  [bold cyan]R[/bold cyan]. Reset progress")
        rprint("  [bold cyan]Q[/bold cyan]. Quit tutor")
        rprint()

        try:
            choice = console.input("[bold yellow]Select a chapter (1-5), R to reset, or Q to quit : [/bold yellow]").strip().lower()
        except (KeyboardInterrupt, EOFError):
            rprint("\n[dim]  Goodbye![/dim]")
            break

        if choice == 'q':
            rprint("[dim]  Goodbye![/dim]")
            break
        elif choice == 'r':
            save_progress({"completed_chapters": []})
            completed = []
            success("Progress reset successfully.")
            continue
        elif choice == '1':
            run_chapter_1()
        elif choice == '2':
            run_chapter_2()
        elif choice == '3':
            run_chapter_3()
        elif choice == '4':
            run_chapter_4()
        elif choice == '5':
            run_chapter_5()
        else:
            error("Invalid input. Choose a chapter between 1 and 5, R, or Q.")
        
        # Refresh progress
        progress = load_progress()
        completed = progress.get("completed_chapters", [])
