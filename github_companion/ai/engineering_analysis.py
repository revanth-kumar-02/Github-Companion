"""Engineering Analysis Engine for GitHub Companion."""
from __future__ import annotations
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint

from github_companion.ai.providers.base_provider import BaseProvider

console = Console()


class EngineeringAnalysisEngine:
    """
    Intelligent Engineering Analysis Engine.
    Analyzes intent, recommends frameworks/libraries, asset sources, and architecture components.
    For Web Games, it automatically infers Phaser.js/PixiJS, Howler.js, Kenney.nl asset packs, 
    and standard game states/architecture.
    """

    @staticmethod
    def analyze(provider: BaseProvider, project_idea: str) -> dict | None:
        """Analyze intent and generate a structured engineering analysis spec."""
        system_prompt = """\
You are a Principal Software Architect and Systems Engineer.
Analyze the user's project request and perform a thorough Engineering Analysis before planning.
Do not assume minimal or simplistic implementations. Reason like a senior software engineer to identify implicit requirements, high-quality frameworks, design patterns, and engineering best practices.

For the user's project, analyze and specify the following 8 key areas:
1. Project Category: Identify classification (e.g. Web Game, Web App, CLI Tool, API, Mobile App).
2. Framework Selection: Recommend the best framework (e.g., React, Phaser.js, Next.js, FastAPI).
3. Library Selection: Specify helper libraries (e.g., Howler.js, Tailwind, Lodash).
4. External Asset Sources: Recommend graphical/audio asset directories (e.g., Kenney.nl, OpenGameArt).
5. UI/UX Requirements: Map out standard user interfaces, layouts, responsiveness, state menus, and animation feedback.
6. Architecture: Formulate clean design patterns (e.g., Scene Manager, Asset Loader, input handling, MVC).
7. Performance Requirements: Specify optimization, asset preloading, frame rate management, or DB caching.
8. Deployment Strategy: Outline hosting, build pipelines, and production bundles.

================================================================================
CRITICAL INSTRUCTION FOR WEB GAMES:
If the project is a Web Game, you MUST automatically recommend and specify:
- Framework: Phaser.js (preferred), PixiJS, or HTML5 Canvas.
- Graphics Assets: Kenney.nl asset packs, OpenGameArt, or custom SVG assets (Backgrounds, animated sprites).
- Audio: Howler.js, free sound effects, background music, volume controls.
- Gameplay components: Start menu, pause/restart screens, game over logic, score/health/level tracking, collision detection, animations, and particle effects.
- Architecture components: Asset Loader, Scene Manager, Input Manager, Audio Manager, Physics system, and Renderer.
- Quality standards: Loading screen, responsive mobile-friendly layouts, FPS management, and clear readme instructions.
================================================================================

You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain the following keys:
{
  "project_title": "Descriptive project title",
  "project_category": "Web Game / Web App / CLI / etc.",
  "framework_selection": {
    "recommended": "Recommended framework name",
    "rationale": "Architectural rationale for this selection"
  },
  "library_selection": [
    "Library name & purpose",
    "Library name & purpose"
  ],
  "external_assets": [
    "Asset source & type of assets needed (e.g., Kenney.nl for sprites)"
  ],
  "ui_ux_requirements": [
    "UI/UX requirement item",
    "UI/UX requirement item"
  ],
  "architecture_components": [
    "Architectural module & description (e.g., Scene Manager for transitions)"
  ],
  "performance_requirements": [
    "Performance target & implementation (e.g., Preload assets to avoid lag)"
  ],
  "deployment_strategy": "Recommended hosting and delivery method",
  "recommended_structure": [
    {
      "path": "path/to/file",
      "explanation": "Role of this file in the architecture"
    }
  ]
}
"""
        prompt = f"Perform detailed Engineering Analysis for: '{project_idea}'"

        try:
            msg = provider.generate([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            content = msg.content or ""
            return EngineeringAnalysisEngine._parse_json(content)
        except Exception as exc:
            rprint(f"[bold red]Engineering analysis failed: {exc}[/bold red]")
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
        """Display the engineering analysis spec beautifully using Rich Tables."""
        from github_companion.services.theme_service import get_active_theme_obj
        theme = get_active_theme_obj()
        border_style = theme.border
        highlight_style = theme.highlight
        
        rprint()
        rprint(f"[{theme.header}]====================================================[/{theme.header}]")
        rprint(f"[{theme.header}]             ENGINEERING ANALYSIS REPORT            [/{theme.header}]")
        rprint(f"[{theme.header}]====================================================[/{theme.header}]")
        rprint()
        
        rprint(f"[bold {highlight_style}]Project Title    :[/bold {highlight_style}] {spec.get('project_title')}")
        rprint(f"[bold {highlight_style}]Project Category :[/bold {highlight_style}] {spec.get('project_category')}")
        rprint()

        # 1. Framework & Libraries
        tech_table = Table(show_header=True, header_style=theme.table_header, border_style=border_style)
        tech_table.add_column("Engineering Aspect", style=f"bold {highlight_style}", width=25)
        tech_table.add_column("Specification & Rationale", style="white")
        
        fw = spec.get("framework_selection", {})
        tech_table.add_row("Recommended Framework", f"{fw.get('recommended', 'N/A')}\n[dim]Rationale: {fw.get('rationale', 'N/A')}[/dim]")
        
        libs = spec.get("library_selection", [])
        tech_table.add_row("Selected Libraries", "\n".join(f"• {x}" for x in libs) if libs else "N/A")
        
        assets = spec.get("external_assets", [])
        tech_table.add_row("Asset Sources", "\n".join(f"• {x}" for x in assets) if assets else "N/A")
        
        console.print(tech_table)
        rprint()

        # 2. UI/UX & Architecture details
        arch_table = Table(show_header=True, header_style=theme.table_header, border_style=border_style)
        arch_table.add_column("System Dimension", style=f"bold {highlight_style}", width=25)
        arch_table.add_column("Architectural Requirements", style="white")
        
        ui = spec.get("ui_ux_requirements", [])
        arch_table.add_row("UI/UX Requirements", "\n".join(f"• {x}" for x in ui) if ui else "N/A")
        
        arch = spec.get("architecture_components", [])
        arch_table.add_row("Architecture Modules", "\n".join(f"• {x}" for x in arch) if arch else "N/A")
        
        perf = spec.get("performance_requirements", [])
        arch_table.add_row("Performance Targets", "\n".join(f"• {x}" for x in perf) if perf else "N/A")
        
        deploy = spec.get("deployment_strategy", "N/A")
        arch_table.add_row("Deployment Strategy", deploy)
        
        console.print(arch_table)
        rprint()

        # 3. Recommended Project Structure
        rprint(f"[bold {highlight_style}]Recommended Folder Structure[/bold {highlight_style}]")
        rprint(f"[{theme.border}]────────────────────────────[/{theme.border}]")
        tree = Tree(f"[bold yellow]{spec.get('project_title', 'project')}/[/bold yellow]")
        for file_entry in spec.get("recommended_structure", []):
            path = file_entry.get("path", "")
            explanation = file_entry.get("explanation", "")
            tree.add(f"[green]{path}[/green] - [dim]{explanation}[/dim]")
            
        console.print(tree)
        rprint()
