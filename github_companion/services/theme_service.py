"""Theme service — manages visual themes and styles for GitHub Companion."""
from github_companion.services.config_service import _load, save_settings
from github_companion.config.themes import CompanionTheme, THEMES


def get_available_themes() -> list[str]:
    """Return list of supported visual theme names."""
    return list(THEMES.keys())


def get_active_theme() -> str:
    """Return the currently configured theme name, defaults to 'default'."""
    return _load().get("theme", "default")


def set_active_theme(theme_name: str) -> bool:
    """Set the active visual theme and save config. Returns True if successful."""
    theme_name = theme_name.lower().strip()
    if theme_name not in THEMES:
        return False
    
    settings = _load()
    settings["theme"] = theme_name
    save_settings(settings)
    return True


def get_active_theme_obj() -> CompanionTheme:
    """Return the active CompanionTheme object, guaranteeing to never fail or raise NameError."""
    try:
        active = get_active_theme()
        if active not in THEMES:
            active = "default"
        if active in THEMES:
            return THEMES[active]
    except Exception as e:
        import sys
        print(f"[dim]Theme warning: Theme loading failed ({e}). Falling back to default theme.[/dim]", file=sys.stderr)
        
    if "default" in THEMES:
        return THEMES["default"]
        
    # Double fallback if registry itself was somehow corrupted
    from github_companion.config.themes import CompanionTheme
    return CompanionTheme(
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
    )


def validate_themes_startup() -> None:
    """Validate that the theme registry is loaded, active theme is present, and falls back to default if not."""
    try:
        # 1. Check registry
        if not THEMES or "default" not in THEMES:
            from github_companion.config.themes import CompanionTheme
            THEMES["default"] = CompanionTheme(
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
            )

        # 2. Check configuration
        settings = _load()
        active = settings.get("theme", "default")
        
        # 3. Fallback
        if active not in THEMES:
            settings["theme"] = "default"
            save_settings(settings)
    except Exception:
        # Gracefully handle all configuration reading or writing issues
        pass


def get_theme_styles() -> dict:
    """Return the styling dict for the active theme (for backwards compatibility)."""
    theme = get_active_theme_obj()
    return {
        "header_style": theme.table_header,
        "border_style": theme.border,
        "category_styles": theme.category_colors
    }
