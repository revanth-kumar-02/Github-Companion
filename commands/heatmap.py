"""Heatmap command."""

from services.heatmap_service import get_contribution_calendar
from utils.heatmap_renderer import render_heatmap
from utils.ui import error


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