"""Render GitHub contribution heatmap."""

from rich.console import Console
from services.theme_service import get_active_theme_obj
from config.themes import FixedComponentTheme

console = Console()

LEVEL_STYLE = FixedComponentTheme.GITHUB_HEATMAP


def render_heatmap(weeks):
    """Render GitHub contribution calendar."""
    theme = get_active_theme_obj()

    console.print()
    console.print(f"[{theme.header}]GitHub Contribution Heatmap[/{theme.header}]")
    console.print()

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

    # Print the heatmap
    for row in range(7):

        console.print(f"[bold]{day_names[row]:<4}[/bold] ", end="")

        for level in grid[row]:

            style = LEVEL_STYLE.get(level, "on grey15")

            console.print("  ", style=style, end="")

        console.print()

    console.print()

    # Legend
    console.print(
        "\nLess ",
        end=""
    )

    for level in [
        "NONE",
        "FIRST_QUARTILE",
        "SECOND_QUARTILE",
        "THIRD_QUARTILE",
        "FOURTH_QUARTILE",
    ]:

        console.print("  ", style=LEVEL_STYLE[level], end=" ")

    console.print(" More")