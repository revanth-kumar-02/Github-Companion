"""Render GitHub contribution heatmap."""

from rich.console import Console

console = Console()

LEVEL_STYLE = {
    "NONE": "on grey15",
    "FIRST_QUARTILE": "on green4",
    "SECOND_QUARTILE": "on green3",
    "THIRD_QUARTILE": "on green",
    "FOURTH_QUARTILE": "on bright_green",
}


def render_heatmap(weeks):
    """Render GitHub contribution calendar."""

    console.print()
    console.print("[bold cyan]GitHub Contribution Heatmap[/bold cyan]")
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