"""Requirement Expansion Engine for GitHub Companion."""
from __future__ import annotations
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint

from github_companion.ai.providers.base_provider import BaseProvider

console = Console()

class RequirementExpansionEngine:
    """
    Intelligent Requirement Expansion Engine.
    Infers gameplay, UI/UX, assets, technologies, and architecture before generating plans.
    """

    @staticmethod
    def expand(provider: BaseProvider, project_idea: str) -> dict | None:
        """Analyze intent and expand requirements into a structured specification."""
        system_prompt = """\
You are an expert Principal Systems Analyst and Product Manager.
Analyze the user's project request and perform a thorough intent expansion and requirement elicitation.
Identify all implicit, standard industry-grade features, assets, and UI components that are normally expected for a complete, production-ready product of this type.
Do not assume minimal implementations. Think about modern UX, accessibility, aesthetics, error handling, state, gameplay/business logic, and styling.

You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain the following keys:
{
  "inferred_project_title": "Short descriptive title, e.g. Flappy Bird clone",
  "intent_analysis": "Detailed explanation of what the user wants and the implied goals",
  "expanded_requirements": [
    {
      "category": "Gameplay / Core Logic",
      "items": ["Bird physics & gravity", "Obstacle generation & speed ramping", "Score & high-score tracking", "Collision detection", "Restart & game loop"]
    },
    {
      "category": "UI / UX and Layout",
      "items": ["Modern start screen overlay", "Responsive canvas viewport", "Pause menu & settings", "Game over screen", "Smooth retro animation states", "CSS variables dark/light themes"]
    },
    {
      "category": "Assets & Resources",
      "items": ["Sprite sheet for bird states", "Background scenery tiles", "Clouds / ground decoration particles", "Sound effects for jump, score, collision", "Retro Google Fonts"]
    }
  ],
  "recommended_tech_stack": {
    "language": "JavaScript / Python / etc.",
    "libraries": "Vanilla JS, CSS3, Canvas API",
    "explanation": "Brief rationale for selecting this stack"
  },
  "recommended_structure": [
    {
      "path": "index.html",
      "explanation": "Main entry point with game canvas container and start screen overlays"
    },
    {
      "path": "style.css",
      "explanation": "Custom variables, premium aesthetics, overlays transitions, responsive layout styling"
    },
    {
      "path": "game.js",
      "explanation": "Main canvas game engine loop, sprites rendering, physics handler, collision, score state"
    }
  ]
}
"""
        prompt = f"Perform intent analysis and requirement expansion for: '{project_idea}'"

        try:
            msg = provider.generate([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            content = msg.content or ""
            return RequirementExpansionEngine._parse_json(content)
        except Exception as exc:
            rprint(f"[bold red]Requirement expansion failed: {exc}[/bold red]")
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
        """Display the expanded requirements beautifully using Rich."""
        rprint()
        rprint("[bold yellow]====================================================[/bold yellow]")
        rprint("[bold yellow]        INTELLIGENT REQUIREMENT EXPANSION          [/bold yellow]")
        rprint("[bold yellow]====================================================[/bold yellow]")
        rprint()
        
        # Project Title and Intent Analysis
        rprint(f"[bold cyan]Project Title   :[/bold cyan] {spec.get('inferred_project_title')}")
        rprint()
        console.print(Panel(spec.get("intent_analysis", ""), title="[bold purple]Intent Analysis[/bold purple]", border_style="purple"))
        rprint()

        # Inferred Requirements table
        req_table = Table(show_header=True, header_style="bold yellow", border_style="purple")
        req_table.add_column("Category", style="bold cyan", width=25)
        req_table.add_column("Inferred Features / Expectations", style="white")
        
        for category_dict in spec.get("expanded_requirements", []):
            cat_name = category_dict.get("category", "")
            cat_items = "\n".join(f"• {item}" for item in category_dict.get("items", []))
            req_table.add_row(cat_name, cat_items)
            
        console.print(Panel(req_table, title="[bold purple]Inferred Specifications & Features[/bold purple]", border_style="purple"))
        rprint()

        # Technology recommendations
        tech = spec.get("recommended_tech_stack", {})
        tech_table = Table(show_header=True, header_style="bold yellow", border_style="purple")
        tech_table.add_column("Component", style="bold cyan")
        tech_table.add_column("Details", style="white")
        tech_table.add_row("Language", tech.get("language", "N/A"))
        tech_table.add_row("Libraries/API", tech.get("libraries", "N/A"))
        tech_table.add_row("Rationale", tech.get("explanation", "N/A"))
        console.print(Panel(tech_table, title="[bold purple]Recommended Tech Stack & UI/UX Strategy[/bold purple]", border_style="purple", expand=False))
        rprint()

        # Recommended Project Structure
        tree = Tree(f"[bold yellow]{spec.get('inferred_project_title', 'project')}/[/bold yellow]")
        for file_entry in spec.get("recommended_structure", []):
            path = file_entry.get("path", "")
            explanation = file_entry.get("explanation", "")
            tree.add(f"[green]{path}[/green] - [dim]{explanation}[/dim]")
            
        console.print(Panel(tree, title="[bold purple]Inferred Architecture / Project Structure[/bold purple]", border_style="purple"))
        rprint()
