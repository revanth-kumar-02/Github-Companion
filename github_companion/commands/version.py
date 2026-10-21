"""Version command — display GitHub Companion and installed Git versions."""
from github_companion import __version__
from github_companion.services.git_service import get_git_version
from github_companion.utils.ui import info
from rich import print as rprint


def show_gc_version() -> None:
    """Display GitHub Companion version and underlying Git CLI version."""
    rprint()
    rprint("[white]" + "─" * 47 + "[/white]")
    info(f" GitHub Companion CLI : v{__version__}")
    rprint()
    git_ver = get_git_version() or "Not found in system PATH"
    info(f" System Git Version   : {git_ver}")
    rprint("[white]" + "─" * 47 + "[/white]")