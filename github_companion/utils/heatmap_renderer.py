"""Render GitHub contribution heatmap."""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import box
from github_companion.services.theme_service import get_active_theme_obj
from github_companion.config.themes import FixedComponentTheme

console = Console()

LEVEL_STYLE = FixedComponentTheme.GITHUB_HEATMAP


def render_heatmap(weeks):
    """Render GitHub contribution calendar."""
    theme = get_active_theme_obj()

    # Create 7 rows (Sun -> Sat)
    grid = [[] for _ in range(7)]

    # Fill the grid week by week
    for week in weeks:
        days = week["contributionDays"]
        # Every week should have 7 positions
        for row in range(7):
            if row < len(days):
                grid[row].append(days[row]["contributionLevel"])
            else:
                grid[row].append("NONE")

    day_names = [
        "Sun",
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
    ]

    lines = []
    # Print the heatmap
    for row in range(7):
        row_text = Text()
        row_text.append(f"{day_names[row]:<4} ", style="bold")
        for level in grid[row]:
            style = LEVEL_STYLE.get(level, "on grey15")
            row_text.append("  ", style=style)
            row_text.append(" ")  # spacer
        lines.append(row_text)

    # Legend
    legend_text = Text()
    legend_text.append("\nLess ")
    for level in [
        "NONE",
        "FIRST_QUARTILE",
        "SECOND_QUARTILE",
        "THIRD_QUARTILE",
        "FOURTH_QUARTILE",
    ]:
        legend_text.append("  ", style=LEVEL_STYLE[level])
        legend_text.append(" ")
    legend_text.append(" More")
    lines.append(legend_text)

    from rich.console import Group
    group = Group(*lines)

    console.print()
    console.print(f"[bold {theme.header}]GitHub Contribution Heatmap[/bold {theme.header}]")
    console.print("─" * 40, style=theme.border)
    console.print()
    console.print(group)
    console.print()