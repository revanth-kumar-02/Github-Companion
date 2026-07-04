"""Central visual theme registry for GitHub Companion."""

class FixedComponentTheme:
    """Styles that remain constant regardless of the user's selected CLI theme to preserve platform branding."""
    GITHUB_HEATMAP = {
        "NONE": "on grey15",
        "FIRST_QUARTILE": "on green4",
        "SECOND_QUARTILE": "on green3",
        "THIRD_QUARTILE": "on green",
        "FOURTH_QUARTILE": "on bright_green",
    }


class CompanionTheme:
    """Represents a visual color palette theme for the GitHub Companion CLI."""
    def __init__(
        self,
        name: str,
        banner: str,
        header: str,
        table_header: str,
        command: str,
        category: str,
        description: str,
        success: str,
        warning: str,
        error: str,
        prompt: str,
        border: str,
        highlight: str,
        category_colors: dict
    ):
        self.name = name
        self.banner = banner
        self.header = header
        self.table_header = table_header
        self.command = command
        self.category = category
        self.description = description
        self.success = success
        self.warning = warning
        self.error = error
        self.prompt = prompt
        self.border = border
        self.highlight = highlight
        self.category_colors = category_colors


THEMES = {
    "default": CompanionTheme(
        name="default",
        banner="bold bright_blue",
        header="bold bright_white",
        table_header="bold bright_blue",
        command="bold bright_cyan",
        category="bold gold1",
        description="white",
        success="bold green",
        warning="bold yellow",
        error="bold red",
        prompt="bold blue",
        border="dim cyan",
        highlight="bright_cyan",
        category_colors={
            "GitHub": "bold bright_cyan",
            "Repository": "bold hot_pink",
            "Utility": "bold bright_magenta",
            "AI Agent": "bold bright_red",
            "Workspace": "bold gold1",
            "System": "bold sky_blue1",
        }
    ),
    "dracula": CompanionTheme(
        name="dracula",
        banner="bold purple",
        header="bold bright_purple",
        table_header="bold purple",
        command="bold bright_cyan",
        category="bold bright_purple",
        description="white",
        success="bold green",
        warning="bold yellow",
        error="bold red",
        prompt="bold purple",
        border="purple",
        highlight="bright_purple",
        category_colors={
            "GitHub": "bold bright_cyan",
            "Repository": "bold purple",
            "Utility": "bold bright_purple",
            "AI Agent": "bold bright_magenta",
            "Workspace": "bold bright_white",
            "System": "bold white",
        }
    ),
    "nord": CompanionTheme(
        name="nord",
        banner="bold blue",
        header="bold bright_white",
        table_header="bold blue",
        command="bold bright_cyan",
        category="bold yellow",
        description="white",
        success="bold green",
        warning="bold yellow",
        error="bold red",
        prompt="bold blue",
        border="blue",
        highlight="bright_cyan",
        category_colors={
            "GitHub": "bold bright_cyan",
            "Repository": "bold blue",
            "Utility": "bold green",
            "AI Agent": "bold red",
            "Workspace": "bold yellow",
            "System": "bold white",
        }
    ),
    "synthwave": CompanionTheme(
        name="synthwave",
        banner="bold bright_magenta",        # #ff00ff  — logo
        header="bold bright_cyan",           # #00ffff  — section titles / GC title
        table_header="bold bright_magenta",  # magenta  — table headers
        command="bold bright_cyan",          # cyan     — command names
        category="bold bright_cyan",         # cyan     — category labels
        description="white",                 # white    — body values
        success="bold bright_green",         # #39ff14  — success messages
        warning="bold bright_yellow",        # yellow   — warnings
        error="bold bright_red",             # red      — errors
        prompt="bold bright_magenta",        # magenta  — GC > prompt
        border="bright_magenta",             # magenta  — dividers / borders
        highlight="bright_cyan",             # cyan     — highlighted values
        category_colors={
            "GitHub":     "bold bright_cyan",
            "Repository": "bold bright_magenta",
            "Utility":    "bold bright_yellow",
            "AI Agent":   "bold bright_red",
            "Workspace":  "bold bright_green",
            "System":     "bold bright_magenta",
        }
    ),
    "monokai": CompanionTheme(
        name="monokai",
        banner="bold red",
        header="bold green",
        table_header="bold red",
        command="bold cyan",
        category="bold yellow",
        description="white",
        success="bold green",
        warning="bold yellow",
        error="bold red",
        prompt="bold magenta",
        border="yellow",
        highlight="cyan",
        category_colors={
            "GitHub": "bold cyan",
            "Repository": "bold red",
            "Utility": "bold green",
            "AI Agent": "bold yellow",
            "Workspace": "bold yellow",
            "System": "bold magenta",
        }
    )
}
