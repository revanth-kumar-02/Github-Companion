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
    Infers gameplay/logic, UI/UX, assets, technologies, folder structure, accessibility, performance, testing, best practices, and architecture.
    """

    @staticmethod
    def expand(provider: BaseProvider, project_idea: str) -> dict | None:
        """Analyze intent and expand requirements into a structured specification."""
        system_prompt = """\
You are an expert Principal Systems Analyst and Product Manager.
Analyze the user's project request and perform a thorough intent expansion and requirement elicitation.
Identify all implicit, standard industry-grade features, assets, and UI components that are normally expected for a complete, production-ready product of this type.
Do not assume minimal implementations. Think about modern UX, accessibility, aesthetics, error handling, state, gameplay/business logic, and styling.

Specifically, infer the following key aspects even if the user has not explicitly requested them:
1. UI & Design System (layouts, typography, color palette, custom styling, responsive structure)
2. UX & Micro-interactions/Animations (hover states, animations, smooth transitions, loading cues)
3. Accessibility (A11y) (semantic HTML, keyboard controls, contrast guidelines, screen readers)
4. Performance & Resource Optimization (lazy loading, optimized rendering loops, asset compression)
5. Testing & Quality Assurance (mock requirements, unit/integration test strategies)
6. Best Practices & Architecture (code cleanliness, modular files, configuration, folder layouts)

You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain the following keys:
{
  "inferred_project_title": "Short descriptive title, e.g. Flappy Bird clone",
  "intent_analysis": "Detailed explanation of what the user wants and the implied goals",
  "expanded_requirements": [
    {
      "category": "Gameplay / Core Logic",
      "items": ["Item 1", "Item 2"]
    }
  ],
  "ui_design_system": ["Layout grids & alignment", "Color palette HSL", "Typography selections"],
  "ux_animations": ["Smooth animations/transitions", "Micro-interactions on hover"],
  "accessibility_a11y": ["Semantic HTML elements", "Keyboard control maps"],
  "performance_optimization": ["Optimized canvas loops", "Memory leak protection"],
  "testing_qa": ["Unit test structures", "Validation criteria"],
  "best_practices": ["Configuration separation", "Clean code standards"],
  "recommended_tech_stack": {
    "language": "JavaScript / Python / etc.",
    "libraries": "Vanilla JS, CSS3, Canvas API",
    "explanation": "Brief rationale for selecting this stack"
  },
  "recommended_structure": [
    {
      "path": "index.html",
      "explanation": "Explanation..."
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
        from github_companion.services.theme_service import get_active_theme_obj
        theme = get_active_theme_obj()
        border_style = theme.border
        highlight_style = theme.highlight
        header_style = theme.header
        
        rprint()
        rprint(f"[{theme.header}]====================================================[/{theme.header}]")
        rprint(f"[{theme.header}]        INTELLIGENT REQUIREMENT EXPANSION          [/{theme.header}]")
        rprint(f"[{theme.header}]====================================================[/{theme.header}]")
        rprint()
        
        rprint(f"[bold {highlight_style}]Project Title   :[/bold {highlight_style}] {spec.get('inferred_project_title')}")
        rprint()
        console.print(Panel(spec.get("intent_analysis", ""), title="[bold purple]Intent Analysis[/bold purple]", border_style=border_style))
        rprint()

        # Inferred Requirements table
        req_table = Table(show_header=True, header_style="bold yellow", border_style=border_style)
        req_table.add_column("Category", style=f"bold {highlight_style}", width=25)
        req_table.add_column("Inferred Features / Expectations", style="white")
        
        for category_dict in spec.get("expanded_requirements", []):
            cat_name = category_dict.get("category", "")
            cat_items = "\n".join(f"• {item}" for item in category_dict.get("items", []))
            req_table.add_row(cat_name, cat_items)
            
        console.print(Panel(req_table, title="[bold purple]Inferred Specifications & Features[/bold purple]", border_style=border_style))
        rprint()

        # UI/UX/A11y Panel
        design_table = Table(show_header=True, header_style="bold yellow", border_style=border_style, expand=True)
        design_table.add_column("System Aspect", style=f"bold {highlight_style}", width=25)
        design_table.add_column("Specifications", style="white")
        
        design_table.add_row("UI & Design System", "\n".join(f"• {x}" for x in spec.get("ui_design_system", ["N/A"])))
        design_table.add_row("UX & Animations", "\n".join(f"• {x}" for x in spec.get("ux_animations", ["N/A"])))
        design_table.add_row("Accessibility (A11y)", "\n".join(f"• {x}" for x in spec.get("accessibility_a11y", ["N/A"])))
        design_table.add_row("Performance Optimization", "\n".join(f"• {x}" for x in spec.get("performance_optimization", ["N/A"])))
        design_table.add_row("Testing & QA Strategy", "\n".join(f"• {x}" for x in spec.get("testing_qa", ["N/A"])))
        design_table.add_row("Best Practices", "\n".join(f"• {x}" for x in spec.get("best_practices", ["N/A"])))
        
        console.print(Panel(design_table, title="[bold purple]Inferred Engineering & Architectural Strategies[/bold purple]", border_style=border_style))
        rprint()

        # Technology recommendations
        tech = spec.get("recommended_tech_stack", {})
        tech_table = Table(show_header=True, header_style="bold yellow", border_style=border_style)
        tech_table.add_column("Component", style=f"bold {highlight_style}")
        tech_table.add_column("Details", style="white")
        tech_table.add_row("Language", tech.get("language", "N/A"))
        tech_table.add_row("Libraries/API", tech.get("libraries", "N/A"))
        tech_table.add_row("Rationale", tech.get("explanation", "N/A"))
        console.print(Panel(tech_table, title="[bold purple]Recommended Tech Stack & UI/UX Strategy[/bold purple]", border_style=border_style, expand=False))
        rprint()

        # Recommended Project Structure
        tree = Tree(f"[bold yellow]{spec.get('inferred_project_title', 'project')}/[/bold yellow]")
        for file_entry in spec.get("recommended_structure", []):
            path = file_entry.get("path", "")
            explanation = file_entry.get("explanation", "")
            tree.add(f"[green]{path}[/green] - [dim]{explanation}[/dim]")
            
        console.print(Panel(tree, title="[bold purple]Inferred Architecture / Project Structure[/bold purple]", border_style=border_style))
        rprint()
