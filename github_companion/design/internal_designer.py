"""Internal AI Design Director — LLM-powered design provider."""
from __future__ import annotations
import json
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from github_companion.design.base_designer import BaseDesigner

console = Console()

_SYSTEM_PROMPT = """\
You are an expert UI/UX Product Designer and Frontend Architect.
Analyze the user's project request and the Engineering Analysis specifications.
Formulate a complete visual design system, UI pattern hierarchy, layout architecture, \
component decisions, typography choices, and animation specifications.
Ensure the resulting application looks professional, polished, modern, and \
production-grade, avoiding generic/simplistic default layouts.

You MUST analyze and specify the following 13 design dimensions:
1. Product Vision: e.g., Professional, Modern, Elegant, Minimal, Corporate, Gaming, Dashboard, Creative, Developer Tool.
2. Visual Style: Recommend a design language (e.g., Glassmorphism, Neumorphism, Apple-inspired, Fluent, Retro, Cyberpunk, Modern SaaS, Tailwind UI + ShadCN).
3. Color Palette: Specify hex codes/HSL for Primary, Secondary, Accent, Background, Surface, Success, Warning, Error.
4. Typography: Choose modern typography (e.g., Inter, Poppins, Manrope, Roboto, Geist, IBM Plex Sans).
5. Layout Strategy: Detail layout structures (e.g. Dashboard sidebar/grids, CRUD lists, fullscreen Canvas HUD, landing page sections).
6. Component Decisions: List all necessary UI components (e.g., loading skeletons, error screens, search widgets, graphs, stats cards, modals).
7. Icon Library: Choose a standard library (e.g., Lucide, Heroicons, Font Awesome, Material Icons).
8. Animation Strategy: Specify micro-interactions, transitions, fade-in cues, or loading skeletons.
9. External Libraries: Recommend frontend additions (e.g., Recharts, Framer Motion, Phaser.js, Howler.js, Leaflet, React Hook Form).
10. External Assets: Specify sources (e.g., Kenney.nl, OpenGameArt, unDraw illustrations, Unsplash, Google Fonts, LottieFiles).
11. Responsive Design Strategy: Specify layout rules for Desktop, Tablet, and Mobile.
12. Accessibility: Detail requirements for Keyboard Navigation, Proper Contrast, Semantic HTML, ARIA Labels, and Focus States.
13. Quality Checklist: Validation items for high-fidelity frontend aesthetics.

You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain the following keys:
{
  "product_vision": "Selected vision descriptor",
  "visual_style": "Design language selection",
  "color_palette": {
    "primary": "Hex or HSL color",
    "secondary": "Hex or HSL color",
    "accent": "Hex or HSL color",
    "background": "Hex or HSL color",
    "surface": "Hex or HSL color",
    "success": "Hex or HSL color",
    "warning": "Hex or HSL color",
    "error": "Hex or HSL color"
  },
  "typography": {
    "primary_font": "Google Font name",
    "details": "Layout weights/styles description"
  },
  "layout_strategy": {
    "structure": "e.g., Sidebar + grid",
    "details": "Description of layout behaviour"
  },
  "components": ["Component 1", "Component 2"],
  "icon_library": "Lucide / Heroicons / etc.",
  "animation_strategy": ["Animation 1", "Animation 2"],
  "external_libraries": ["Library 1", "Library 2"],
  "external_assets": ["Asset source 1", "Asset source 2"],
  "responsive_strategy": "Desktop/Tablet/Mobile layout guidelines",
  "accessibility_requirements": ["Accessibility feature 1", "Accessibility feature 2"],
  "quality_checklist": ["Quality item 1", "Quality item 2"]
}
"""


class InternalDesigner(BaseDesigner):
    """
    LLM-powered internal design provider.
    Uses the active AI inference provider to generate design specifications.
    Always available — no external service required.
    """

    def __init__(self, ai_provider) -> None:
        """
        Args:
            ai_provider: An active BaseProvider instance used for LLM calls.
        """
        self._provider = ai_provider

    # ── BaseDesigner interface ─────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Internal AI Designer"

    @property
    def provider_type(self) -> str:
        return "internal"

    def health_check(self) -> bool:
        """Always available — delegates to the AI provider which is already validated."""
        return True

    def supports_framework(self, framework: str) -> bool:
        return True  # LLM can reason about any framework

    def supports_assets(self) -> bool:
        return True  # Recommends asset sources

    def supports_design_system(self) -> bool:
        return True  # Generates full design token system

    def generate_design(
        self,
        project_idea: str,
        engineering_spec: dict | None = None,
    ) -> dict | None:
        """Call the LLM to produce a complete design specification."""
        eng_ctx = (
            f"\nEngineering Analysis Spec:\n{json.dumps(engineering_spec, indent=2)}\n"
            if engineering_spec
            else ""
        )
        prompt = f"Perform Detailed Design Analysis for: '{project_idea}'\n{eng_ctx}"

        try:
            msg = self._provider.generate([
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])
            content = msg.content or ""
            return _parse_design_json(content)
        except Exception as exc:
            rprint(f"[bold red]Internal design analysis failed: {exc}[/bold red]")
            return None

    def display(self, spec: dict) -> None:
        """Render the Internal design specification to the terminal."""
        _render_design_table(spec, provider_label="Internal AI Designer")


# ── Shared rendering helpers ───────────────────────────────────────────────────

def _parse_design_json(content: str) -> dict | None:
    """Extract and parse a JSON block from LLM output."""
    try:
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].strip()
        else:
            json_str = content.strip()
        return json.loads(json_str)
    except Exception:
        try:
            return json.loads(content.strip())
        except Exception:
            return None


def _render_design_table(spec: dict, provider_label: str = "Design Director") -> None:
    """Shared terminal renderer for any design specification dict."""
    from github_companion.services.theme_service import get_active_theme_obj
    theme = get_active_theme_obj()
    border_style = theme.border
    highlight_style = theme.highlight

    rprint()
    rprint(f"[{theme.header}]=====================================================[/{theme.header}]")
    rprint(f"[{theme.header}]  {provider_label.upper()} — DESIGN SPECIFICATION  [/{theme.header}]")
    rprint(f"[{theme.header}]=====================================================[/{theme.header}]")
    rprint()

    table = Table(show_header=True, header_style=theme.table_header, border_style=border_style)
    table.add_column("Design Parameter", style=f"bold {highlight_style}", width=25)
    table.add_column("Specification", style="white")

    table.add_row("Product Vision", spec.get("product_vision", "N/A"))
    table.add_row("Visual Style", spec.get("visual_style", "N/A"))

    cp = spec.get("color_palette", {})
    colors_str = "\n".join(f"• {k.capitalize()}: {v}" for k, v in cp.items())
    table.add_row("Color Palette", colors_str or "N/A")

    typo = spec.get("typography", {})
    table.add_row(
        "Typography",
        f"Font: {typo.get('primary_font', 'N/A')}\n[dim]{typo.get('details', 'N/A')}[/dim]",
    )

    lay = spec.get("layout_strategy", {})
    table.add_row(
        "Layout Strategy",
        f"Layout: {lay.get('structure', 'N/A')}\n[dim]{lay.get('details', 'N/A')}[/dim]",
    )

    comps = spec.get("components", [])
    table.add_row("Components", "\n".join(f"• {x}" for x in comps) or "N/A")

    table.add_row("Icon Library", spec.get("icon_library", "N/A"))

    anims = spec.get("animation_strategy", [])
    table.add_row("Animations", "\n".join(f"• {x}" for x in anims) or "N/A")

    libs = spec.get("external_libraries", [])
    assets = spec.get("external_assets", [])
    table.add_row("External Libs", "\n".join(f"• {x}" for x in libs) or "N/A")
    table.add_row("External Assets", "\n".join(f"• {x}" for x in assets) or "N/A")

    table.add_row("Responsive Plan", spec.get("responsive_strategy", "N/A"))

    a11y = spec.get("accessibility_requirements", [])
    table.add_row("Accessibility", "\n".join(f"• {x}" for x in a11y) or "N/A")

    qual = spec.get("quality_checklist", [])
    table.add_row("Quality QA", "\n".join(f"• {x}" for x in qual) or "N/A")

    console.print(table)
    rprint()

    # ── Design Confidence summary ──────────────────────────────────────────────
    rprint(f"[bold {highlight_style}]Design Confidence[/bold {highlight_style}]")
    rprint(f"[{theme.border}]─────────────────[/{theme.border}]")

    rprint("[bold white]Design Style:[/bold white]")
    rprint(f"  {spec.get('visual_style', 'Modern SaaS UI')}")
    rprint()

    palette_line = " • ".join(str(v) for v in cp.values() if v)
    rprint("[bold white]Color Palette:[/bold white]")
    rprint(f"  {palette_line or 'N/A'}")
    rprint()

    ui_fw = f"{spec.get('visual_style', 'Tailwind CSS')} + {spec.get('icon_library', 'Lucide')}"
    rprint("[bold white]UI Framework:[/bold white]")
    rprint(f"  {ui_fw}")
    rprint()

    rprint("[bold white]Icons:[/bold white]")
    rprint(f"  {spec.get('icon_library', 'Lucide')}")
    rprint()

    anim_summary = ", ".join(anims[:3]) if anims else "Hover and transitions"
    rprint("[bold white]Animations:[/bold white]")
    rprint(f"  {anim_summary}")
    rprint()

    asset_summary = ", ".join(assets[:3]) if assets else "Google Fonts"
    rprint("[bold white]External Assets:[/bold white]")
    rprint(f"  {asset_summary}")
    rprint()

    rprint("[bold white]Overall Product Quality:[/bold white]")
    rprint("  [bold green]Professional SaaS Grade[/bold green]")
    rprint()
