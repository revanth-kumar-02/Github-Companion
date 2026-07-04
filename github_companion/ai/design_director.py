"""AI Design Director Engine for GitHub Companion."""
from __future__ import annotations
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from github_companion.ai.providers.base_provider import BaseProvider

console = Console()


class DesignDirector:
    """
    Intelligent AI Design Director.
    Generates detailed UI/UX visual specs, color palettes, layouts, and component designs before coding.
    """

    @staticmethod
    def analyze(provider: BaseProvider, project_idea: str, engineering_spec: dict | None = None) -> dict | None:
        """Perform Design Analysis on the project idea and engineering specs."""
        system_prompt = """\
You are an expert UI/UX Product Designer and Frontend Architect.
Analyze the user's project request and the Engineering Analysis specifications.
Formulate a complete visual design system, UI pattern hierarchy, layout architecture, component decisions, typography choices, and animation specifications.
Ensure the resulting application looks professional, polished, modern, and production-grade, avoiding generic/simplistic default layouts.

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
  "components": [
    "Component 1",
    "Component 2"
  ],
  "icon_library": "Lucide / Heroicons / etc.",
  "animation_strategy": [
    "Animation 1",
    "Animation 2"
  ],
  "external_libraries": [
    "Library 1",
    "Library 2"
  ],
  "external_assets": [
    "Asset source 1",
    "Asset source 2"
  ],
  "responsive_strategy": "Desktop/Tablet/Mobile layout guidelines",
  "accessibility_requirements": [
    "Accessibility feature 1",
    "Accessibility feature 2"
  ],
  "quality_checklist": [
    "Quality item 1",
    "Quality item 2"
  ]
}
"""
        eng_ctx = f"\nEngineering Analysis Spec:\n{json.dumps(engineering_spec, indent=2)}\n" if engineering_spec else ""
        prompt = f"Perform Detailed Design Analysis for: '{project_idea}'\n{eng_ctx}"

        try:
            msg = provider.generate([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            content = msg.content or ""
            return DesignDirector._parse_json(content)
        except Exception as exc:
            rprint(f"[bold red]Design analysis failed: {exc}[/bold red]")
            return None

    @staticmethod
    def _parse_json(content: str) -> dict | None:
        try:
            if "```json" in content:
                parts = content.split("```json")
                json_str = parts[1].split("```")[0].strip()
            elif "```" in content:
                parts = content.split("```")
                json_str = parts[1].strip()
            else:
                json_str = content.strip()
            return json.loads(json_str)
        except Exception:
            try:
                return json.loads(content.strip())
            except Exception:
                return None

    @staticmethod
    def display(spec: dict) -> None:
        """Display the Design Analysis Report and the Design Confidence summary block."""
        from github_companion.services.theme_service import get_active_theme_obj
        theme = get_active_theme_obj()
        border_style = theme.border
        highlight_style = theme.highlight
        
        rprint()
        rprint(f"[{theme.header}]====================================================[/{theme.header}]")
        rprint(f"[{theme.header}]               AI DESIGN DIRECTOR REPORT            [/{theme.header}]")
        rprint(f"[{theme.header}]====================================================[/{theme.header}]")
        rprint()

        # Detailed design parameters table
        design_table = Table(show_header=True, header_style=theme.table_header, border_style=border_style)
        design_table.add_column("Design Parameter", style=f"bold {highlight_style}", width=25)
        design_table.add_column("Product Specification", style="white")

        design_table.add_row("Product Vision", spec.get("product_vision", "N/A"))
        design_table.add_row("Visual Style", spec.get("visual_style", "N/A"))

        # Format Color Palette
        cp = spec.get("color_palette", {})
        colors_str = "\n".join(f"• {k.capitalize()}: {v}" for k, v in cp.items())
        design_table.add_row("Color Palette", colors_str if cp else "N/A")

        # Typography
        typo = spec.get("typography", {})
        typo_str = f"Font: {typo.get('primary_font', 'N/A')}\n[dim]{typo.get('details', 'N/A')}[/dim]"
        design_table.add_row("Typography", typo_str)

        # Layout
        lay = spec.get("layout_strategy", {})
        lay_str = f"Layout: {lay.get('structure', 'N/A')}\n[dim]{lay.get('details', 'N/A')}[/dim]"
        design_table.add_row("Layout Strategy", lay_str)

        # Components
        comps = spec.get("components", [])
        design_table.add_row("Inferred Components", "\n".join(f"• {x}" for x in comps) if comps else "N/A")

        # Icons
        design_table.add_row("Icon Library", spec.get("icon_library", "N/A"))

        # Animations
        anims = spec.get("animation_strategy", [])
        design_table.add_row("Animations", "\n".join(f"• {x}" for x in anims) if anims else "N/A")

        # External Libs & Assets
        libs = spec.get("external_libraries", [])
        assets = spec.get("external_assets", [])
        design_table.add_row("External Libs", "\n".join(f"• {x}" for x in libs) if libs else "N/A")
        design_table.add_row("External Assets", "\n".join(f"• {x}" for x in assets) if assets else "N/A")

        # Responsive & A11y
        design_table.add_row("Responsive Plan", spec.get("responsive_strategy", "N/A"))
        a11y = spec.get("accessibility_requirements", [])
        design_table.add_row("Accessibility", "\n".join(f"• {x}" for x in a11y) if a11y else "N/A")

        # Quality
        qual = spec.get("quality_checklist", [])
        design_table.add_row("Design Quality QA", "\n".join(f"• {x}" for x in qual) if qual else "N/A")

        console.print(design_table)
        rprint()

        # ── Design Confidence Block ──────────────────────────────────────────
        rprint(f"[bold {highlight_style}]Design Confidence[/bold {highlight_style}]")
        rprint(f"[{theme.border}]─────────────────[/{theme.border}]")
        
        rprint(f"[bold white]Design Style:[/bold white]")
        rprint(f"  {spec.get('visual_style', 'Modern SaaS UI')}")
        rprint()
        
        # Color Palette representation
        palette_line = " • ".join(f"{v}" for v in cp.values() if v)
        rprint(f"[bold white]Color Palette:[/bold white]")
        rprint(f"  {palette_line or 'N/A'}")
        rprint()
        
        # Frameworks/Libraries
        ui_framework = f"{spec.get('visual_style', 'Tailwind CSS')} + {spec.get('icon_library', 'Lucide')}"
        rprint(f"[bold white]UI Framework:[/bold white]")
        rprint(f"  {ui_framework}")
        rprint()
        
        rprint(f"[bold white]Icons:[/bold white]")
        rprint(f"  {spec.get('icon_library', 'Lucide')}")
        rprint()
        
        # Animations
        rprint(f"[bold white]Animations:[/bold white]")
        anim_summary = ", ".join(anims[:3]) if anims else "Hover and transitions"
        rprint(f"  {anim_summary}")
        rprint()
        
        # External Assets
        rprint(f"[bold white]External Assets:[/bold white]")
        asset_summary = ", ".join(assets[:3]) if assets else "Google Fonts"
        rprint(f"  {asset_summary}")
        rprint()
        
        rprint(f"[bold white]Overall Product Quality:[/bold white]")
        rprint("  [bold green]Professional SaaS Grade[/bold green]")
        rprint()
