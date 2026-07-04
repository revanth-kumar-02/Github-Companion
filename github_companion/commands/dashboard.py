"""Dashboard command — displays detailed environment and system diagnostic dashboard."""
from github_companion.utils.ui import show_dashboard

def show_gc_dashboard() -> None:
    """Displays environment, authentication, workspace, active model/theme, and system status."""
    show_dashboard()
