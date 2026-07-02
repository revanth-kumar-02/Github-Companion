"""Code command — autonomous AI coding agent mode with project planning, bootstrapping, and automatic GitHub deployment."""
from __future__ import annotations
import datetime
import json
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from ai.agent import Agent
from ai.providers.base_provider import BaseProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from services.config_service import (
    get_custom_models,
    get_ollama_host,
    get_openrouter_api_key,
    get_github_username,
)
from utils.ui import error, success, info

console = Console()


def _get_ollama_with_fallback(model_id: str) -> BaseProvider | None:
    """Check if local Ollama is active, else prompt to retry, configure OpenRouter, or cancel."""
    from services.config_service import _load, save_settings
    from services.setup_wizard import ensure_openrouter_authenticated
    while True:
        ollama = OllamaProvider(model_id, host=get_ollama_host())
        if ollama.health_check():
            return ollama

        rprint(f"\n[bold yellow]Ollama is not installed or offline.[/bold yellow]")
        rprint("Would you like to:")
        rprint("  [bold cyan]1[/bold cyan]. Configure OpenRouter")
        rprint("  [bold cyan]2[/bold cyan]. Retry")
        rprint("  [bold cyan]3[/bold cyan]. Cancel")
        rprint()

        sub_choice = console.input("[bold purple]> [/bold purple]").strip()
        if sub_choice == "1":
            try:
                key = ensure_openrouter_authenticated()
                settings = _load()
                settings["provider"] = "openrouter"
                save_settings(settings)
                return OpenRouterProvider(model_id, api_key=key)
            except Exception as e:
                rprint(f"[bold red]❌ Config error: {e}[/bold red]")
                continue
        elif sub_choice == "2":
            continue
        else:
            return None


def _get_selected_provider() -> BaseProvider | None:
    """Show model selection menu and return the corresponding provider."""
    rprint()
    rprint("[bold bright_white]Choose Coding Model[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    rprint("  [bold cyan]1[/bold cyan]. Qwen 2.5 Coder ⭐ [dim]Recommended[/dim]")
    rprint("  [bold cyan]2[/bold cyan]. DeepSeek V3")
    rprint("  [bold cyan]3[/bold cyan]. DeepSeek R1")
    rprint("  [bold cyan]4[/bold cyan]. Llama 3.3")

    customs = get_custom_models()
    for idx, c in enumerate(customs, start=5):
        rprint(f"  [bold cyan]{idx}[/bold cyan]. {c.get('provider_name')} - {c.get('model_name')} ⭐")

    rprint()

    choice = console.input("[bold yellow]Select model number : [/bold yellow]").strip()

    if choice == "1":
        return _get_ollama_with_fallback("qwen2.5-coder")

    elif choice == "2":
        from services.setup_wizard import ensure_openrouter_authenticated
        try:
            key = ensure_openrouter_authenticated()
            return OpenRouterProvider("deepseek-v3", api_key=key)
        except Exception as e:
            rprint(f"[bold red]❌ Config error: {e}[/bold red]")
            return None

    elif choice == "3":
        return _get_ollama_with_fallback("deepseek-r1")

    elif choice == "4":
        return _get_ollama_with_fallback("llama3.3")

    else:
        try:
            val = int(choice)
            idx = val - 5
            if 0 <= idx < len(customs):
                from ai.providers.custom_provider import CustomProvider
                return CustomProvider(customs[idx])
        except ValueError:
            pass

    return None



def start_code_mode() -> None:
    """Main AI Coding Agent flow (Planning -> Approval -> Bootstrap -> Generation -> Git/GitHub)."""
    try:
        provider = _get_selected_provider()
    except Exception as exc:
        rprint(f"[bold red]❌ Config error:[/bold red] {exc}")
        return

    if not provider:
        error("Invalid selection.")
        return

    rprint(f"[dim]  Selected: {provider.name} ({provider.model})[/dim]\n")

    project_idea = console.input("[bold cyan]What project would you like to build? : [/bold cyan]").strip()
    if not project_idea:
        error("Project idea cannot be empty.")
        return

    # ── Planning Stage ────────────────────────────────────────────────────────
    plan = _generate_plan(provider, project_idea)
    if not plan:
        error("Failed to generate implementation plan.")
        return

    # User review loop
    while True:
        _display_plan(plan)

        rprint("\n[bold yellow]Options:[/bold yellow]")
        rprint("  [bold green]Y[/bold green]. Approve and Start Coding")
        rprint("  [bold cyan]E[/bold cyan]. Edit Plan")
        rprint("  [bold red]N[/bold red]. Cancel")
        rprint()

        action = console.input("[bold yellow]Select option (Y/E/N) : [/bold yellow]").strip().upper()

        if action == "Y":
            break
        elif action == "N":
            rprint("[dim]  Cancelled by user.[/dim]")
            return
        elif action == "E":
            feedback = console.input("\n[bold cyan]What would you like to edit? : [/bold cyan]").strip()
            if feedback:
                with console.status("[bold yellow]  Re-planning project...[/bold yellow]", spinner="dots"):
                    plan = _regenerate_plan(provider, project_idea, plan, feedback)
                if not plan:
                    error("Failed to update implementation plan.")
                    return
        else:
            error("Invalid option.")

    # ── Project Bootstrap Phase ─────────────────────────────────────────────────
    rprint()
    project_name = plan.get("project_name", "my-project").replace(" ", "-").lower()
    project_path = os.path.abspath(os.path.join(os.getcwd(), project_name))

    rprint(f"[bold purple]Creating Project...[/bold purple]")
    os.makedirs(project_path, exist_ok=True)

    # 1. Detect project type
    proj_type = _detect_project_type(plan)

    # 2. Generate .gitignore
    gitignore_content = _get_gitignore_template(proj_type)
    with open(os.path.join(project_path, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    rprint("  [bold green]✓[/bold green] .gitignore")

    # 3. Generate LICENSE
    author_name = get_github_username() or "GitHub Companion User"
    license_content = _get_license_template(author_name)
    with open(os.path.join(project_path, "LICENSE"), "w", encoding="utf-8") as f:
        f.write(license_content)
    rprint("  [bold green]✓[/bold green] LICENSE")

    # 4. Generate README.md
    readme_content = _get_readme_template(plan)
    with open(os.path.join(project_path, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    rprint("  [bold green]✓[/bold green] README.md")

    # 5. Generate dependency files
    dep_file, dep_content = _get_dependency_file(proj_type, plan)
    if dep_file:
        with open(os.path.join(project_path, dep_file), "w", encoding="utf-8") as f:
            f.write(dep_content)
        rprint(f"  [bold green]✓[/bold green] {dep_file}")

    # ── Source Code Generation Stage ──────────────────────────────────────────
    files_to_generate = plan.get("files", [])
    generated_count = 3 + (1 if dep_file else 0)  # README, gitignore, LICENSE, optional deps

    folders_set = set()

    for f_path in files_to_generate:
        # Skip bootstrapping / metadata files if they were listed in plan files
        if f_path.lower() in ("readme.md", ".gitignore", "license", "requirements.txt", "package.json", "cargo.toml", "go.mod"):
            continue

        full_f_path = os.path.join(project_path, f_path)
        os.makedirs(os.path.dirname(full_f_path), exist_ok=True)
        dir_name = os.path.dirname(f_path)
        if dir_name:
            folders_set.add(dir_name)

        with console.status(f"[bold yellow]Generating {f_path}...[/bold yellow]", spinner="dots"):
            code_content = _generate_file_content(provider, plan, f_path)

        if code_content:
            with open(full_f_path, "w", encoding="utf-8") as f:
                f.write(code_content)
            rprint(f"  [bold green]✓[/bold green] {f_path}")
            generated_count += 1
        else:
            rprint(f"  [bold red]❌ Failed to generate {f_path}[/bold red]")

    # ── Git Integration ───────────────────────────────────────────────────────
    rprint("\n[bold purple]Initializing Git Repository...[/bold purple]")
    from services.git_service import git_init, git_add, git_commit, git_branch, git_remote_add, git_push

    git_init(project_path)
    git_add(project_path)
    git_commit(project_path, "Initial project generated by GitHub Companion")
    git_branch(project_path, "main")
    rprint("  [bold green]✓[/bold green] Git Initialized & Initial Commit Created")

    # ── GitHub Integration ────────────────────────────────────────────────────
    published = False
    repo_url = ""

    rprint()
    publish_choice = console.input("[bold yellow]Publish this project to GitHub? (y/n) : [/bold yellow]").strip().lower()

    if publish_choice == "y":
        from services.github_service import repo_create
        rprint("[bold purple]Creating GitHub repository...[/bold purple]")
        resp = repo_create(project_name, plan.get("strategy", ""), private=False)
        if resp.status_code == 201:
            repo_data = resp.json()
            repo_url = repo_data["html_url"]
            username = get_github_username()
            remote_url = f"https://{username}@github.com/{username}/{project_name}.git"

            git_remote_add(project_path, remote_url)
            with console.status("[bold yellow]Pushing to GitHub...[/bold yellow]", spinner="dots"):
                git_push(project_path)
            rprint("  [bold green]✓[/bold green] GitHub Repository Successfully Created & Pushed")
            published = True
        else:
            rprint(f"  [bold red]❌ Failed to create GitHub repository: {resp.json().get('message', 'Unknown error')}[/bold red]")

    # ── Final Output Summary ──────────────────────────────────────────────────
    rprint()
    summary_info = (
        f"[bold white]Project           :[/bold white] {plan.get('project_name', 'Unnamed')}\n"
        f"[bold white]Files Generated   :[/bold white] {generated_count}\n"
        f"[bold white]Folders           :[/bold white] {len(folders_set)}\n"
        f"[bold white]README            :[/bold white] [green]✓[/green]\n"
        f"[bold white].gitignore        :[/bold white] [green]✓[/green]\n"
        f"[bold white]Git Initialized   :[/bold white] [green]✓[/green]\n"
        f"[bold white]Initial Commit    :[/bold white] [green]✓[/green]\n"
        f"[bold white]GitHub Repository :[/bold white] {'[green]✓[/green]' if published else '[dim]Skipped[/dim]'}\n"
        f"[bold white]Project Published :[/bold white] {'[green]✓[/green]' if published else '[dim]Skipped[/dim]'}\n"
    )
    if published:
        summary_info += f"[bold white]Repository        :[/bold white] [underline blue]{repo_url}[/underline blue]"

    console.print(Panel(
        summary_info,
        title="[bold green]🎉 Project Created Successfully[/bold green]",
        border_style="green",
        expand=False,
    ))
    rprint()


# ── Plan generation helpers ──────────────────────────────────────────────────

def _generate_plan(provider: BaseProvider, project_idea: str) -> dict | None:
    """Request the AI to generate a structured implementation plan in JSON."""
    system_prompt = """\
You are a Software Architect. You analyze user requests and produce a structured JSON implementation plan.
You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain these exact keys:
- project_name: string (short, clean project name)
- files_count: integer (estimated total files to create)
- architecture: string (e.g. MVC, Modular, Single-file)
- dependencies: list of strings
- estimated_time: string (e.g. '30 sec', '1 min')
- folder_structure: string (ascii diagram showing folders and files)
- files: list of strings (paths to the files to create)
- features: list of strings (key features of the app)
- complexity: string (Simple, Medium, Complex)
- strategy: string (short description of the implementation strategy)
"""
    prompt = f"Analyze and plan: {project_idea}"

    with console.status("[bold yellow]  Planning project...[/bold yellow]", spinner="dots"):
        try:
            msg = provider.generate(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
            )
            content = msg.content or ""
            return _parse_json_block(content)
        except Exception as exc:
            error(f"Error during planning: {exc}")
            return None


def _regenerate_plan(provider: BaseProvider, project_idea: str, old_plan: dict, feedback: str) -> dict | None:
    """Update implementation plan based on user feedback."""
    system_prompt = """\
You are a Software Architect. Update the implementation plan based on user feedback.
You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Keep the exact same keys as the original JSON.
"""
    prompt = f"""\
Original Idea: {project_idea}
Original Plan: {json.dumps(old_plan, indent=2)}
User request/feedback: {feedback}

Generate the updated JSON plan.
"""
    try:
        msg = provider.generate(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        content = msg.content or ""
        return _parse_json_block(content)
    except Exception as exc:
        error(f"Error updating plan: {exc}")
        return None


def _parse_json_block(content: str) -> dict | None:
    """Parse JSON from markdown code block."""
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


def _display_plan(plan: dict) -> None:
    """Beautifully format the implementation plan using Rich."""
    rprint()
    plan_info = (
        f"[bold white]Project :[/bold white] {plan.get('project_name', 'Unnamed')}\n"
        f"[bold white]Files   :[/bold white] {plan.get('files_count', 0)}\n"
        f"[bold white]Arch    :[/bold white] {plan.get('architecture', 'Standard')}\n"
        f"[bold white]Deps    :[/bold white] {', '.join(plan.get('dependencies', [])) or 'None'}\n"
        f"[bold white]Time    :[/bold white] {plan.get('estimated_time', 'N/A')}\n"
        f"[bold white]Level   :[/bold white] {plan.get('complexity', 'Medium')}"
    )

    console.print(Panel(
        plan_info,
        title="[bold green]📋 Implementation Plan[/bold green]",
        border_style="green",
        expand=False,
    ))

    rprint("\n[bold cyan]✨ Key Features:[/bold cyan]")
    for feat in plan.get("features", []):
        rprint(f"  • {feat}")

    rprint("\n[bold cyan]📁 Target Folder Structure:[/bold cyan]")
    rprint(plan.get("folder_structure", ""))

    rprint("\n[bold cyan]🛠️ Implementation Strategy:[/bold cyan]")
    rprint(plan.get("strategy", ""))


# ── File generation & templates helpers ───────────────────────────────────────

def _generate_file_content(provider: BaseProvider, plan: dict, f_path: str) -> str:
    """Generate complete, high-quality code content for a given path."""
    system_prompt = f"""\
You are an expert Software Engineer.
You are writing the file '{f_path}' for the project '{plan.get('project_name')}'.
Project Plan details:
- Description: {plan.get('strategy')}
- Architecture: {plan.get('architecture')}
- Dependencies: {', '.join(plan.get('dependencies', []))}

Write the COMPLETE, production-ready source code for the file: '{f_path}'.
- Write high-quality, fully functional code with no comments like 'implement later' or placeholders.
- Do NOT output any explanation, notes, or markdown descriptions.
- Output ONLY the raw file content. If you use markdown code block wrapping, write only the code block. We will parse it.
"""
    prompt = f"Generate code for the file: {f_path}"

    try:
        msg = provider.generate([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])
        content = msg.content or ""
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 3:
                code_block = parts[1].strip()
                lines = code_block.splitlines()
                if lines and (lines[0].strip().lower() in ("python", "javascript", "typescript", "html", "css", "json", "rust", "go", "bash", "sh")):
                    code_block = "\n".join(lines[1:])
                return code_block
        return content.strip()
    except Exception:
        return ""


def _detect_project_type(plan: dict) -> str:
    """Heuristically identify the project type from plan fields."""
    deps = [d.lower() for d in plan.get("dependencies", [])]
    files = [f.lower() for f in plan.get("files", [])]

    if any(x in files for x in ("requirements.txt", "pipfile", "pyproject.toml")):
        return "python"
    if any(x in d for d in deps for x in ("flask", "django", "fastapi", "requests", "python", "numpy", "pandas")):
        return "python"

    if "package.json" in files:
        return "node"
    if any(x in d for d in deps for x in ("react", "vue", "express", "node", "next", "angular")):
        return "node"

    if "cargo.toml" in files:
        return "rust"
    if any(x in d for d in deps for x in ("rust", "cargo", "tokio", "serde")):
        return "rust"

    if "go.mod" in files:
        return "go"
    if any(x in d for d in deps for x in ("go", "gin", "gorm")):
        return "go"

    py_files = [f for f in files if f.endswith(".py")]
    js_files = [f for f in files if any(f.endswith(ext) for ext in (".js", ".ts", ".jsx", ".tsx"))]
    rs_files = [f for f in files if f.endswith(".rs")]
    go_files = [f for f in files if f.endswith(".go")]

    if len(py_files) > len(js_files) and len(py_files) > len(rs_files) and len(py_files) > len(go_files):
        return "python"
    if len(js_files) > len(py_files) and len(js_files) > len(rs_files) and len(js_files) > len(go_files):
        return "node"
    if len(rs_files) > len(py_files) and len(rs_files) > len(js_files) and len(rs_files) > len(go_files):
        return "rust"
    if len(go_files) > len(py_files) and len(go_files) > len(js_files) and len(go_files) > len(rs_files):
        return "go"

    return "default"


def _get_gitignore_template(proj_type: str) -> str:
    """Return standard .gitignore content based on project type."""
    templates = {
        "python": """\
__pycache__/
*.py[cod]
*$py.class
*.venv
venv/
env/
.env
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
""",
        "node": """\
node_modules/
dist/
build/
.env
.env.local
.DS_Store
npm-debug.log*
yarn-debug.log*
yarn-error.log*
""",
        "rust": """\
/target
**/*.rs.bk
Cargo.lock
""",
        "go": """\
*.exe
*.exe~
*.dll
*.so
*.dylib
bin/
go.work
""",
        "default": """\
.DS_Store
.env
*.log
""",
    }
    return templates.get(proj_type, templates["default"])


def _get_readme_template(plan: dict) -> str:
    """Return initial markdown README.md template compiled from plan."""
    return f"""# {plan.get('project_name', 'Unnamed Project')}

{plan.get('strategy', 'No description provided.')}

---

## ✨ Features
{chr(10).join(f'- {feat}' for feat in plan.get('features', []))}

---

## 📁 Project Folder Structure
```
{plan.get('folder_structure', '')}
```

---

## ⚙️ Installation
1. Clone the repository.
2. Install the dependencies listed below.

---

## 🛠️ Dependencies
{chr(10).join(f'- {dep}' for dep in plan.get('dependencies', []))}

---

## 📄 License
This project is licensed under the MIT License.
"""


def _get_license_template(author_name: str) -> str:
    """Return standard MIT License content."""
    year = datetime.datetime.now().year
    return f"""MIT License

Copyright (c) {year} {author_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def _get_dependency_file(proj_type: str, plan: dict) -> tuple[str | None, str]:
    """Return dependency filename and package content depending on type."""
    deps = plan.get("dependencies", [])
    if proj_type == "python":
        return "requirements.txt", "\n".join(deps) + "\n"
    elif proj_type == "node":
        dep_dict = {d: "*" for d in deps}
        package_json = {
            "name": plan.get("project_name", "my-project").replace(" ", "-").lower(),
            "version": "1.0.0",
            "description": plan.get("strategy", ""),
            "main": "index.js",
            "dependencies": dep_dict
        }
        return "package.json", json.dumps(package_json, indent=2) + "\n"
    elif proj_type == "rust":
        cargo_toml = f"""[package]
name = "{plan.get('project_name', 'my-project').replace(' ', '-').lower()}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
        return "Cargo.toml", cargo_toml
    return None, ""
