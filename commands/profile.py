from services.github_service import get_github_profile
from services.theme_service import get_active_theme_obj
from utils.ui import error
from rich import print, box
from rich.panel import Panel
from rich.console import Console
import textwrap

console = Console()

def show_gc_profile():
    try:
        profile = get_github_profile()
    except Exception as e:
        error(f"Failed to fetch GitHub profile: {e}")
        return
    if profile is None:
        error("Unable to fetch GitHub Profile")
        return
    
    theme = get_active_theme_obj()
    icon_color = theme.highlight
    label_style = "bright_cyan"
    value_style = "white"

    login = profile.get("login") or "N/A"
    name = profile.get("name") or "N/A"
    location = profile.get("location") or "N/A"
    blog = profile.get("blog") or "N/A"
    bio = (profile.get("bio") or "N/A").replace("\r\n", " ").replace("\n", " ")
    company = profile.get("company") or "N/A"
    email = profile.get("email") or "N/A"
    twitter = profile.get("twitter_username") or "N/A"
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    public_repos = profile.get("public_repos", 0)
    created_at = profile.get("created_at", "")
    if created_at:
        created_at = created_at.split("T")[0]
    else:
        created_at = "N/A"

    def format_row(icon: str, label: str, value: str, is_url: bool = False) -> str:
        padded_label = f"{label:<14}"
        styled_val = f"[bright_blue underline]{value}[/]" if is_url else f"[{value_style}]{value}[/]"
        prefix = f"  [{icon_color}]{icon}[/] [{label_style}]{padded_label}[/] : "
        
        # Align subsequent wrapped lines exactly under the colon
        indent_spaces = " " * 22  # Padding to line up under value start
        wrapped_lines = textwrap.wrap(value, width=50)
        if not wrapped_lines:
            return f"{prefix}[{value_style}]N/A[/]"
            
        result_lines = []
        if is_url:
            result_lines.append(f"{prefix}[bright_blue underline]{wrapped_lines[0]}[/]")
            for line in wrapped_lines[1:]:
                result_lines.append(f"{indent_spaces}[bright_blue underline]{line}[/]")
        else:
            result_lines.append(f"{prefix}[{value_style}]{wrapped_lines[0]}[/]")
            for line in wrapped_lines[1:]:
                result_lines.append(f"{indent_spaces}[{value_style}]{line}[/]")
                
        return "\n".join(result_lines)

    content = []
    
    # ─── IDENTITY SECTION ───
    content.append(f"[bold {theme.header}]👤 IDENTITY[/]")
    content.append(format_row("👤", "Username", login))
    content.append(format_row("📛", "Name", name))
    if bio != "N/A" and bio:
        content.append(format_row("📝", "Bio", bio))
    if company != "N/A" and company:
        content.append(format_row("🏢", "Company", company))
    if location != "N/A" and location:
        content.append(format_row("📍", "Location", location))
    if email != "N/A" and email:
        content.append(format_row("📧", "Email", email))
    if blog != "N/A" and blog:
        content.append(format_row("🔗", "Website/Blog", blog, is_url=True))
    if twitter != "N/A" and twitter:
        content.append(format_row("🐦", "Twitter/X", f"https://x.com/{twitter}", is_url=True))
        
    content.append("")  # Spacing between sections

    # ─── SOCIAL SECTION ───
    content.append(f"[bold {theme.header}]📊 SOCIAL & REPOS[/]")
    content.append(format_row("👥", "Followers", str(followers)))
    content.append(format_row("🤝", "Following", str(following)))
    content.append(format_row("📦", "Repositories", str(public_repos)))

    content.append("")  # Spacing between sections

    # ─── ACTIVITY SECTION ───
    content.append(f"[bold {theme.header}]📅 ACTIVITY[/]")
    content.append(format_row("📆", "Joined Date", created_at))

    panel = Panel(
        "\n".join(content),
        title=f"[{theme.header}] GitHub Profile: {login} [/{theme.header}]",
        border_style=theme.border,
        box=box.ROUNDED,
        expand=False
    )

    print()
    console.print(panel)
    print()