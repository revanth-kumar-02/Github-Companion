"""Theme command — customize visual appearance of GitHub Companion."""
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from github_companion.services.theme_service import get_available_themes, get_active_theme, set_active_theme, get_active_theme_obj
from github_companion.utils.ui import success, error, info

console = Console()


def show_theme_preview(theme_name: str) -> None:
    """Print a small mockup table previewing the colors of a theme."""
    from github_companion.services.theme_service import get_active_theme_obj
    theme = get_active_theme_obj()
    header_style = theme.table_header
    border_style = theme.border
    category_styles = theme.category_colors

    rprint(f"\n[{theme.header}]Theme Preview: {theme_name.capitalize()}[/{theme.header}]")
    rprint(f"[{theme.border}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{theme.border}]")

    table = Table(
        show_header=True,
        header_style=header_style,
        border_style=border_style,
        padding=(0, 1),
        expand=False,
    )

    table.add_column("Command", no_wrap=True, width=12)
    table.add_column("Category", no_wrap=True, width=14)
    table.add_column("Description", style=theme.description, no_wrap=False, width=30)

    # Preview elements
    preview_rows = [
        ("profile", "GitHub", "Show profile details"),
        ("create", "Repository", "Create new repository"),
        ("readme", "Utility", "Generate README file"),
    ]

    for cmd, category, desc in preview_rows:
        style = category_styles.get(category, "white")
        styled_cmd = f"[{style}]{cmd}[/{style}]"
        styled_category = f"[{style}]{category}[/{style}]"
        table.add_row(styled_cmd, styled_category, desc)

    console.print(table)
    rprint()


def theme_cmd(args: list[str] = None) -> None:
    """Select and preview visual themes."""
    available = get_available_themes()
    current = get_active_theme()
    theme = get_active_theme_obj()

    if args and len(args) > 0:
        target_theme = args[0].lower().strip()
        if target_theme in available:
            if set_active_theme(target_theme):
                # Reload theme object after setting it
                theme = get_active_theme_obj()
                success(f"Visual theme updated to: {target_theme}")
                show_theme_preview(target_theme)
            else:
                error("Failed to update theme configuration.")
        else:
            error(f"Unknown theme: '{target_theme}'")
            info(f"Available themes: {', '.join(available)}")
        return

    # Interactive menu mode
    rprint()
    rprint(f"[{theme.header}]Visual Themes Configuration[/{theme.header}]")
    rprint(f"[{theme.border}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{theme.border}]")
    rprint(f"Current theme: [{theme.success}]{current}[/{theme.success}]\n")

    rprint("Available Themes:")
    for idx, t in enumerate(available, start=1):
        is_active = " (active)" if t == current else ""
        rprint(f"  [{theme.highlight}]{idx}[/{theme.highlight}]. [bold]{t}[/bold]{is_active}")
    rprint()

    try:
        choice = console.input(f"[{theme.prompt}]Select a theme (enter name or number) : [/{theme.prompt}]").strip().lower()
    except (KeyboardInterrupt, EOFError):
        rprint("\n[dim]  Cancelled.[/dim]")
        return

    if not choice:
        rprint("[dim]  No selection made. Keeping current theme.[/dim]")
        return

    # Check if choice is numeric index
    selected_theme = None
    if choice.isdigit():
        val = int(choice)
        if 1 <= val <= len(available):
            selected_theme = available[val - 1]
    elif choice in available:
        selected_theme = choice

    if selected_theme:
        if set_active_theme(selected_theme):
            success(f"Visual theme updated to: {selected_theme}")
            show_theme_preview(selected_theme)
        else:
            error("Failed to update theme configuration.")
    else:
        error(f"Invalid selection: '{choice}'")
