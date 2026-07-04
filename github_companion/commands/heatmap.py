"""Heatmap command."""

from github_companion.services.heatmap_service import get_contribution_calendar
from github_companion.utils.heatmap_renderer import render_heatmap
from github_companion.utils.ui import error


def show_gc_heatmap():
    """Display GitHub contribution heatmap."""

    try:
        data = get_contribution_calendar()

        weeks = (
            data["data"]["user"]
            ["contributionsCollection"]
            ["contributionCalendar"]
            ["weeks"]
        )

        render_heatmap(weeks)

    except Exception as e:
        error(str(e))