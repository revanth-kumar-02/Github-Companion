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
        category_colors: dict,
        link: str = "bright_blue",
        muted: str = "grey70",
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
        self.link = link
        self.muted = muted


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
        link="bright_blue",
        muted="grey70",
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
        link="bright_cyan",
        muted="grey70",
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
        link="bright_blue",
        muted="grey70",
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
        banner="bold #FF10F0",           # Neon pink  — GC logo
        header="bold #00F5FF",           # Neon cyan  — section titles / GC title
        table_header="bold #FF10F0",     # Neon pink  — table headers
        command="bold #00F5FF",          # Neon cyan  — command names
        category="bold #00F5FF",         # Neon cyan  — category labels
        description="#FFFFFF",           # White      — body values
        success="bold #39FF14",          # Neon green — success messages
        warning="bold #FFD300",          # Neon amber — warnings
        error="bold #FF3131",            # Neon red   — errors
        prompt="bold #FF10F0",           # Neon pink  — GC > prompt
        border="#FF10F0",                # Neon pink  — dividers / borders
        highlight="#00F5FF",             # Neon cyan  — highlighted values
        link="#00AFFF",                  # Electric blue — hyperlinks
        muted="#A0A0A0",                 # Grey       — muted labels
        category_colors={
            "GitHub":     "bold #00F5FF",
            "Repository": "bold #FF10F0",
            "Utility":    "bold #FFD300",
            "AI Agent":   "bold #FF3131",
            "Workspace":  "bold #39FF14",
            "System":     "bold #FF10F0",
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
        link="bright_blue",
        muted="grey70",
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
