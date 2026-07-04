"""Theme service — manages visual themes and styles for GitHub Companion."""
from services.config_service import _load, save_settings
from config.themes import CompanionTheme, THEMES


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
    """Return the active CompanionTheme object."""
    active = get_active_theme()
    if active not in THEMES:
        active = "default"
    return THEMES[active]


def get_theme_styles() -> dict:
    """Return the styling dict for the active theme (for backwards compatibility)."""
    theme = get_active_theme_obj()
    return {
        "header_style": theme.table_header,
        "border_style": theme.border,
        "category_styles": theme.category_colors
    }
