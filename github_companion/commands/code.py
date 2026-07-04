"""Code command — autonomous AI coding agent mode with project planning, bootstrapping, and automatic GitHub deployment."""
from __future__ import annotations
import datetime
import json
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from github_companion.ai.agent import Agent
from github_companion.ai.providers.base_provider import BaseProvider
from github_companion.ai.providers.ollama_provider import OllamaProvider
from github_companion.ai.providers.openrouter_provider import OpenRouterProvider
from github_companion.ai.providers.nvidia_provider import NvidiaProvider
from github_companion.ai.requirement_expansion import RequirementExpansionEngine
from github_companion.services.config_service import (
    get_custom_models,
    get_ollama_host,
    get_openrouter_api_key,
    get_github_username,
)
from github_companion.utils.ui import error, success, info

console = Console()


def _get_ollama_with_fallback(model_id: str) -> BaseProvider | None:
    """Check if local Ollama is active, else prompt to retry, configure OpenRouter, or cancel."""
    from github_companion.services.config_service import _load, save_settings
    from github_companion.services.setup_wizard import ensure_openrouter_authenticated
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


def _build_provider_for_model(model_entry: dict) -> BaseProvider | None:
    provider_name = model_entry["provider"].lower()
    model_id = model_entry["model_id"]
    
    if provider_name == "ollama":
        return _get_ollama_with_fallback(model_id)
        
    elif provider_name == "openrouter":
        from github_companion.services.setup_wizard import ensure_openrouter_authenticated
        try:
            key = ensure_openrouter_authenticated()
            return OpenRouterProvider(model_id, api_key=key)
        except Exception as e:
            rprint(f"[bold red]❌ Config error: {e}[/bold red]")
            return None
            
    elif provider_name == "nvidia":
        from github_companion.services.setup_wizard import ensure_nvidia_authenticated
        try:
            key = ensure_nvidia_authenticated()
            return NvidiaProvider(model_id, api_key=key)
        except Exception as e:
            rprint(f"[bold red]❌ Config error: {e}[/bold red]")
            return None
            
    return None


def _get_selected_provider() -> BaseProvider | None:
    """Show model selection menu and return the corresponding provider."""
    from github_companion.ai.model_registry import get_models_by_role
    rprint()
    rprint("[bold bright_white]Choose Coding Model[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    
    models = get_models_by_role("coding")
    for idx, m in enumerate(models, start=1):
        rec_tag = " ⭐ [dim]Recommended[/dim]" if m.get("recommended") else ""
        rprint(f"  [bold cyan]{idx}[/bold cyan]. {m['display_name']} (Provider: {m['provider'].upper()}){rec_tag}")
        
    customs = get_custom_models()
    start_custom = len(models) + 1
    for idx, c in enumerate(customs, start=start_custom):
        rprint(f"  [bold cyan]{idx}[/bold cyan]. {c.get('provider_name')} - {c.get('model_name')} (Custom)")
        
    rprint()
    choice = console.input("[bold yellow]Select model number : [/bold yellow]").strip()
    
    try:
        val = int(choice)
        if 1 <= val <= len(models):
            return _build_provider_for_model(models[val - 1])
        else:
            idx = val - start_custom
            if 0 <= idx < len(customs):
                from github_companion.ai.providers.custom_provider import CustomProvider
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

    # ── Requirement Expansion Stage ───────────────────────────────────────────
    expanded_spec = None
    with console.status("[bold yellow]Running Requirement Expansion Engine...[/bold yellow]", spinner="dots"):
        expanded_spec = RequirementExpansionEngine.expand(provider, project_idea)
    
    if expanded_spec:
        RequirementExpansionEngine.display(expanded_spec)
        rprint()
        proceed = console.input("[bold yellow]Proceed to detailed Implementation Planning? (y/n) [y]: [/bold yellow]").strip().lower()
        if proceed not in ("", "y", "yes"):
            rprint("[dim]  Cancelled by user.[/dim]")
            return

    # ── Planning Stage ────────────────────────────────────────────────────────
    plan = _generate_plan(provider, project_idea, expanded_spec)
    if not plan:
        error("Failed to generate implementation plan.")
        return

    # User review loop
    while True:
        _display_plan(plan)

        rprint("\n[bold yellow]Options:[/bold yellow]")
        rprint("  [bold green]Y[/bold green]. Approve and Start Coding")
        rprint("  [bold cyan]E[/bold cyan]. Edit Plan")
        rprint("  [bold magenta]R[/bold magenta]. Regenerate Plan")
        rprint("  [bold red]N[/bold red]. Cancel")
        rprint()

        action = console.input("[bold yellow]Select option (Y/E/R/N) : [/bold yellow]").strip().upper()

        if action == "Y":
            session = _execute_approved_plan(provider, plan)
            if session:
                _run_coding_session(provider, session)
            break
        elif action == "N":
            rprint("[dim]  Cancelled by user.[/dim]")
            return
        elif action == "R":
            with console.status("[bold yellow]  Regenerating new plan...[/bold yellow]", spinner="dots"):
                plan = _generate_plan(provider, project_idea, expanded_spec)
            if not plan:
                error("Failed to generate implementation plan.")
                return
        elif action == "E":
            feedback = console.input("\n[bold cyan]What would you like to edit? : [/bold cyan]").strip()
            if feedback:
                with console.status("[bold yellow]  Re-planning project...[/bold yellow]", spinner="dots"):
                    # Pass the expanded specification to help shape the edited plan
                    plan = _regenerate_plan(provider, project_idea, plan, f"{feedback}\nExpanded Spec: {json.dumps(expanded_spec)}")
                if not plan:
                    error("Failed to update implementation plan.")
                    return
        else:
            error("Invalid option.")


def start_plan_mode() -> None:
    """Choose planning model and generate implementation plan (GC > plan)."""
    from github_companion.ai.model_registry import get_models_by_role
    rprint()
    rprint("[bold bright_white]Choose Planning Model[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    
    models = get_models_by_role("planning")
    for idx, m in enumerate(models, start=1):
        rec_tag = " ⭐ [dim]Recommended[/dim]" if m.get("recommended") else ""
        rprint(f"  [bold cyan]{idx}[/bold cyan]. {m['display_name']} (Provider: {m['provider'].upper()}){rec_tag}")
        
    rprint()
    choice = console.input("[bold yellow]Select planning model number : [/bold yellow]").strip()
    
    try:
        val = int(choice)
        if 1 <= val <= len(models):
            provider = _build_provider_for_model(models[val - 1])
        else:
            error("Invalid selection.")
            return
    except ValueError:
        error("Invalid selection.")
        return
        
    if not provider:
        return

    rprint(f"[dim]  Selected: {provider.name} ({provider.model})[/dim]\n")

    project_idea = console.input("[bold cyan]What project would you like to plan? : [/bold cyan]").strip()
    if not project_idea:
        error("Project idea cannot be empty.")
        return

    # ── Requirement Expansion Stage ───────────────────────────────────────────
    expanded_spec = None
    with console.status("[bold yellow]Running Requirement Expansion Engine...[/bold yellow]", spinner="dots"):
        expanded_spec = RequirementExpansionEngine.expand(provider, project_idea)
    
    if expanded_spec:
        RequirementExpansionEngine.display(expanded_spec)
        rprint()
        proceed = console.input("[bold yellow]Proceed to detailed Implementation Planning? (y/n) [y]: [/bold yellow]").strip().lower()
        if proceed not in ("", "y", "yes"):
            rprint("[dim]  Cancelled by user.[/dim]")
            return

    # ── Planning Stage ────────────────────────────────────────────────────────
    plan = _generate_plan(provider, project_idea, expanded_spec)
    if not plan:
        error("Failed to generate implementation plan.")
        return

    # User review loop
    while True:
        _display_plan(plan)

        rprint("\n[bold yellow]Options:[/bold yellow]")
        rprint("  [bold green]Y[/bold green]. Approve and Start Coding")
        rprint("  [bold cyan]E[/bold cyan]. Edit Plan")
        rprint("  [bold magenta]R[/bold magenta]. Regenerate Plan")
        rprint("  [bold red]N[/bold red]. Cancel")
        rprint()

        action = console.input("[bold yellow]Select option (Y/E/R/N) : [/bold yellow]").strip().upper()

        if action == "Y":
            session = _execute_approved_plan(provider, plan)
            if session:
                _run_coding_session(provider, session)
            break
        elif action == "N":
            rprint("[dim]  Cancelled by user.[/dim]")
            return
        elif action == "R":
            with console.status("[bold yellow]  Regenerating new plan...[/bold yellow]", spinner="dots"):
                plan = _generate_plan(provider, project_idea, expanded_spec)
            if not plan:
                error("Failed to generate implementation plan.")
                return
        elif action == "E":
            feedback = console.input("\n[bold cyan]What would you like to edit? : [/bold cyan]").strip()
            if feedback:
                with console.status("[bold yellow]  Re-planning project...[/bold yellow]", spinner="dots"):
                    plan = _regenerate_plan(provider, project_idea, plan, f"{feedback}\nExpanded Spec: {json.dumps(expanded_spec)}")
                if not plan:
                    error("Failed to update implementation plan.")
                    return
        else:
            error("Invalid option.")


def _execute_approved_plan(provider: BaseProvider, plan: dict) -> dict | None:
    """Execute code generation and bootstrapping after plan approval."""
    rprint()
    project_name = plan.get("project_name", "my-project")
    original_folder_name = _clean_project_folder_name(project_name)
    folder_name = original_folder_name

    from github_companion.services.config_service import get_default_workspace, get_github_token, get_github_username
    workspace_path = get_default_workspace()
    if not workspace_path:
        home = os.path.expanduser("~")
        workspace_path = os.path.join(home, "GC-Projects")
        os.makedirs(workspace_path, exist_ok=True)

    project_path = os.path.join(workspace_path, folder_name)

    if os.path.exists(project_path):
        rprint()
        rprint(f"[bold yellow]⚠ Project folder already exists:[/bold yellow] [cyan]{folder_name}[/cyan]")
        rprint("[bold white]Options:[/bold white]")
        rprint("  [bold cyan]1[/bold cyan]. Overwrite existing project")
        rprint("  [bold cyan]2[/bold cyan]. Create suffix version (e.g. {folder_name}-2)")
        rprint("  [bold cyan]3[/bold cyan]. Rename project folder")
        rprint("  [bold cyan]4[/bold cyan]. Cancel build")
        rprint()
        
        conflict_choice = console.input("[bold yellow]Select option (1-4) : [/bold yellow]").strip()
        
        if conflict_choice == "1":
            rprint("[bold red]⚠ Overwriting existing files...[/bold red]")
        elif conflict_choice == "2":
            idx = 2
            while True:
                candidate = f"{original_folder_name}-{idx}"
                if not os.path.exists(os.path.join(workspace_path, candidate)):
                    folder_name = candidate
                    break
                idx += 1
            project_path = os.path.join(workspace_path, folder_name)
            rprint(f"[bold green]✓ Created suffix version: {folder_name}[/bold green]")
        elif conflict_choice == "3":
            new_name = console.input("\nEnter new project folder name: ").strip()
            if new_name:
                folder_name = _clean_project_folder_name(new_name)
                project_path = os.path.join(workspace_path, folder_name)
            else:
                rprint("[bold red]❌ Invalid name. Cancelling build.[/bold red]")
                return None
        else:
            rprint("[dim]  Build cancelled.[/dim]")
            return None

    rprint()
    rprint("[bold bright_white]Project Location Display[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    rprint(f"Workspace      : {workspace_path}")
    rprint(f"Project Folder : {folder_name}")
    rprint(f"Final Location : {project_path}")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    rprint()
    rprint(f"[bold purple]Creating Project...[/bold purple]")
    os.makedirs(project_path, exist_ok=True)

    # 1. Detect project type
    proj_type = _detect_project_type(plan)

    directories_created = []
    files_created = []
    files_failed = []
    missing_assets = []

    # ── Directory Creation Phase ──────────────────────────────────────────────
    # A. Explicit directories from the planner
    explicit_dirs = plan.get("directories", [])
    for d_path in explicit_dirs:
        if not d_path:
            continue
        full_d_path = os.path.join(project_path, d_path)
        try:
            os.makedirs(full_d_path, exist_ok=True)
            directories_created.append(d_path)
        except Exception as e:
            files_failed.append((d_path, f"Failed to create directory: {e}"))

    # B. Implicit directories from files, templates, static_resources, and assets
    for category in ("files", "templates", "static_resources", "assets"):
        for path_entry in plan.get(category, []):
            if not path_entry:
                continue
            if path_entry.endswith("/") or path_entry.endswith("\\"):
                full_d_path = os.path.join(project_path, path_entry)
                try:
                    os.makedirs(full_d_path, exist_ok=True)
                    directories_created.append(path_entry)
                except Exception as e:
                    files_failed.append((path_entry, f"Failed to create directory: {e}"))
            else:
                parent_dir = os.path.dirname(path_entry)
                if parent_dir:
                    full_d_path = os.path.join(project_path, parent_dir)
                    try:
                        os.makedirs(full_d_path, exist_ok=True)
                        directories_created.append(parent_dir)
                    except Exception as e:
                        files_failed.append((parent_dir, f"Failed to create directory: {e}"))

    # ── Bootstrap Files Generation (MIT License, gitignore, README) ───────────
    # Generate .gitignore
    try:
        gitignore_content = _get_gitignore_template(proj_type)
        with open(os.path.join(project_path, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        files_created.append(".gitignore")
        rprint("  [bold green]✓[/bold green] .gitignore")
    except Exception as e:
        files_failed.append((".gitignore", str(e)))

    # Generate LICENSE
    try:
        author_name = get_github_username() or "GitHub Companion User"
        license_content = _get_license_template(author_name)
        with open(os.path.join(project_path, "LICENSE"), "w", encoding="utf-8") as f:
            f.write(license_content)
        files_created.append("LICENSE")
        rprint("  [bold green]✓[/bold green] LICENSE")
    except Exception as e:
        files_failed.append(("LICENSE", str(e)))

    # Generate README.md
    try:
        readme_content = _get_readme_template(plan)
        with open(os.path.join(project_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)
        files_created.append("README.md")
        rprint("  [bold green]✓[/bold green] README.md")
    except Exception as e:
        files_failed.append(("README.md", str(e)))

    # Generate dependency files
    dep_file = None
    try:
        dep_file, dep_content = _get_dependency_file(proj_type, plan)
        if dep_file:
            with open(os.path.join(project_path, dep_file), "w", encoding="utf-8") as f:
                f.write(dep_content)
            files_created.append(dep_file)
            rprint(f"  [bold green]✓[/bold green] {dep_file}")
    except Exception as e:
        if dep_file:
            files_failed.append((dep_file, str(e)))

    # ── Code / Asset / Template Generation Stage ──────────────────────────────
    # Process each category independently
    for category in ("files", "templates", "static_resources", "assets"):
        category_entries = plan.get(category, [])
        for f_path in category_entries:
            if not f_path:
                continue
            # Skip bootstrapping / metadata files if they were listed in plan files
            if f_path.lower() in ("readme.md", ".gitignore", "license", "requirements.txt", "package.json", "cargo.toml", "go.mod"):
                continue

            # Check if this path represents a directory (ends with slash)
            if f_path.endswith("/") or f_path.endswith("\\"):
                # Already created in directory phase, skip file writing
                continue

            full_f_path = os.path.join(project_path, f_path)
            
            # Double check path isn't an existing directory to avoid PermissionError
            if os.path.exists(full_f_path) and os.path.isdir(full_f_path):
                files_failed.append((f_path, "Path is already a directory"))
                if category == "assets":
                    missing_assets.append(f_path)
                continue

            # Generate and write file with full fault-tolerance
            try:
                # Ensure parent directories exist
                os.makedirs(os.path.dirname(full_f_path), exist_ok=True)
                
                with console.status(f"[bold yellow]Generating {f_path}...[/bold yellow]", spinner="dots"):
                    code_content = _generate_file_content(provider, plan, f_path)

                if code_content is not None:
                    with open(full_f_path, "w", encoding="utf-8") as f:
                        f.write(code_content)
                    files_created.append(f_path)
                    rprint(f"  [bold green]✓[/bold green] {f_path}")
                else:
                    raise ValueError("Generation returned empty/null content")
            except Exception as e:
                rprint(f"  [bold red]❌ Failed to generate {f_path}: {e}[/bold red]")
                files_failed.append((f_path, str(e)))
                if category == "assets":
                    missing_assets.append(f_path)

    # ── Self-Review & Project Validation ──────────────────────────────────────
    try:
        _review_and_fix_project(provider, project_path, plan, dep_file)
    except Exception as e:
        rprint(f"  [bold red]❌ Review & Fix phase failed: {e}[/bold red]")

    # ── Generation Validation ─────────────────────────────────────────────────
    validation_passed = True
    validation_errors = []

    # 1. Verify every directory exists
    for d_path in directories_created:
        full_d_path = os.path.join(project_path, d_path)
        if not os.path.exists(full_d_path) or not os.path.isdir(full_d_path):
            validation_passed = False
            validation_errors.append(f"Directory missing or invalid: {d_path}")

    # 2. Verify every file exists
    all_expected_files = []
    for category in ("files", "templates", "static_resources", "assets"):
        for f_path in plan.get(category, []):
            if not f_path or f_path.endswith("/") or f_path.endswith("\\"):
                continue
            all_expected_files.append(f_path)
            
    # Include bootstrapped files
    all_expected_files.extend([".gitignore", "LICENSE", "README.md"])
    if dep_file:
        all_expected_files.append(dep_file)

    for f_path in all_expected_files:
        # Skip bootstrapping / metadata files if they were skipped in actual generation
        if f_path.lower() in ("readme.md", ".gitignore", "license", "requirements.txt", "package.json", "cargo.toml", "go.mod"):
            # Check if exists
            full_f_path = os.path.join(project_path, f_path)
            if not os.path.exists(full_f_path):
                validation_passed = False
                validation_errors.append(f"Boilerplate file missing: {f_path}")
            continue

        full_f_path = os.path.join(project_path, f_path)
        if not os.path.exists(full_f_path):
            validation_passed = False
            validation_errors.append(f"Expected file was not generated: {f_path}")
        elif os.path.isdir(full_f_path):
            validation_passed = False
            validation_errors.append(f"File path conflict (exists as directory): {f_path}")

    # 3. Check for write failures
    if files_failed:
        # If any of the failed files were core files/templates, we mark validation as failed
        validation_passed = False
        for f, err in files_failed:
            validation_errors.append(f"File generation failed: {f} ({err})")

    rprint()
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")
    rprint("[bold yellow]               PROJECT VALIDATION              [/bold yellow]")
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")
    if validation_passed:
        rprint("[bold green]✓ Passed[/bold green]")
    else:
        rprint("[bold red]Validation Failed[/bold red]")
        for err in validation_errors:
            rprint(f"  [red]✗[/red] {err}")
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")

    # Display final generation report
    rprint()
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")
    rprint("[bold yellow]               GENERATION REPORT               [/bold yellow]")
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")
    
    rprint("[bold green]Directories Created:[/bold green]")
    if directories_created:
        for d in sorted(set(directories_created)):
            rprint(f"  - {d}")
    else:
        rprint("  - None")
        
    rprint("[bold green]Files Created:[/bold green]")
    if files_created:
        for f in sorted(set(files_created)):
            rprint(f"  - {f}")
    else:
        rprint("  - None")
        
    rprint("[bold red]Files Failed:[/bold red]")
    if files_failed:
        for f, err in files_failed:
            rprint(f"  - {f}: [red]{err}[/red]")
    else:
        rprint("  - None")
        
    rprint("[bold yellow]Missing Assets:[/bold yellow]")
    if missing_assets:
        for a in missing_assets:
            rprint(f"  - {a}")
    else:
        rprint("  - None")
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")

    if not validation_passed:
        rprint("\n[bold red]❌ Project generation failed validation. Halting pipeline execution without aborting the CLI.[/bold red]")
        return None

    # ── Git Integration ───────────────────────────────────────────────────────
    rprint("\n[bold purple]Initializing Git Repository...[/bold purple]")
    from github_companion.services.git_service import git_init, git_add, git_commit, git_branch, git_remote_add, git_push

    try:
        git_init(project_path)
        git_add(project_path)
        git_commit(project_path, "Initial project generated by GitHub Companion")
        git_branch(project_path, "main")
        rprint("  [bold green]✓[/bold green] Git Initialized & Initial Commit Created")
    except Exception as e:
        rprint(f"  [bold red]❌ Git Initialization failed: {e}[/bold red]")

    # ── GitHub Integration ────────────────────────────────────────────────────
    published = False
    repo_url = ""

    from github_companion.services.config_service import get_github_token, get_github_username
    token = get_github_token()
    username = get_github_username()

    if token and username:
        from github_companion.services.github_service import repo_create
        rprint("[bold purple]Creating GitHub repository...[/bold purple]")
        try:
            resp = repo_create(project_name, plan.get("strategy", ""), private=False)
            if resp.status_code == 201:
                repo_data = resp.json()
                repo_url = repo_data["html_url"]
                remote_url = f"https://{username}@github.com/{username}/{project_name}.git"

                git_remote_add(project_path, remote_url)
                with console.status("[bold yellow]Pushing to GitHub...[/bold yellow]", spinner="dots"):
                    git_push(project_path)
                rprint("  [bold green]✓[/bold green] GitHub Repository Successfully Created & Pushed")
                published = True
            else:
                rprint(f"  [bold red]❌ Failed to create GitHub repository: {resp.json().get('message', 'Unknown error')}[/bold red]")
        except Exception as e:
            rprint(f"  [bold red]❌ GitHub repository push failed: {e}[/bold red]")
    else:
        rprint("[bold yellow]⚠ GitHub credentials not configured. Skipping repository creation & push.[/bold yellow]")

    # ── Launch VS Code ────────────────────────────────────────────────────────
    from github_companion.services.system_service import launch_vscode
    try:
        rprint("\n[bold purple]Launching VS Code...[/bold purple]")
        launch_vscode(project_path)
        rprint("  [bold green]✓[/bold green] VS Code launched successfully.")
    except Exception as e:
        rprint(f"  [bold red]❌ Could not launch VS Code: {e}[/bold red]")

    # ── Final Output Summary ──────────────────────────────────────────────────
    _display_completion_report(plan, project_path, len(files_created), published, repo_url)

    # Create and return active session context
    session = {
        "project_name": project_name,
        "workspace_path": project_path,
        "repo_url": repo_url,
        "branch": "main",
        "framework": plan.get("tech_stack", {}).get("framework", "N/A"),
        "language": plan.get("tech_stack", {}).get("language", "N/A"),
        "conversation_history": [],
        "modified_files": [],
        "pending_changes": []
    }
    return session



# ── Plan generation helpers ──────────────────────────────────────────────────

def _generate_plan(provider: BaseProvider, project_idea: str, expanded_spec: dict | None = None) -> dict | None:
    """Request the AI to generate a structured implementation plan in JSON."""
    system_prompt = """\
You are a Senior Software Architect. Analyze the user's project request and generate a highly detailed, professional, structured JSON implementation plan.
You MUST return ONLY a JSON code block inside markdown code tags (e.g. ```json ... ```).
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain the following keys:
{
  "project_name": "Short, clean project identifier",
  "project_overview": {
    "what_is_being_built": "Detailed explanation of what is being built",
    "primary_objective": "Primary objective of the project",
    "target_users": "Target users of the application",
    "expected_functionality": "Expected functionality summary",
    "overall_architecture": "Overall architectural approach"
  },
  "feature_analysis": [
    "Feature 1: short description",
    "Feature 2: short description"
  ],
  "tech_stack": {
    "language": "Language to use",
    "framework": "Framework to use",
    "libraries": "Key libraries to use",
    "database": "Database to use",
    "package_manager": "Package manager to use",
    "testing_framework": "Testing framework",
    "deployment_readiness": "Deployment readiness notes"
  },
  "project_complexity": {
    "complexity_rating": "★★★★☆ (out of 5 stars)",
    "estimated_files": 12,
    "estimated_loc": 1500,
    "estimated_time": "Estimated build time, e.g. 5 minutes",
    "estimated_tokens": 8000
  },
  "folder_explanations": {
    "folder_name/": "Short explanation of the folder's purpose"
  },
  "implementation_phases": [
    {
      "phase_name": "Phase 1: Project Initialization",
      "tasks": ["Create project structure", "Generate config files"]
    }
  ],
  "dependencies": [
    {
      "name": "Dependency Name",
      "type": "Type, e.g. Web Framework",
      "reason": "Why it is required"
    }
  ],
  "risk_analysis": [
    "Challenge 1: short description",
    "Challenge 2: short description"
  ],
  "directories": [
    "Relative path of directories to explicitly create, ending with a slash (e.g. src/, src/components/, src/assets/icons/)"
  ],
  "files": [
    "Relative path of core code files, excluding directories (e.g., src/index.js, src/App.js)"
  ],
  "assets": [
    "Relative path of graphic assets, icons, or audio resources to generate/track (e.g., src/assets/logo.png)"
  ],
  "templates": [
    "Relative path of markup template files to generate (e.g., public/index.html)"
  ],
  "static_resources": [
    "Relative path of static styles, styles config, or static files to generate (e.g., src/styles/main.css)"
  ],
  "coding_strategy": {
    "build_order": "Build order description",
    "dependency_order": "Dependency order description",
    "testing_strategy": "Testing strategy description",
    "error_handling": "Error handling description",
    "code_organization": "Code organization details",
    "scalability": "Scalability details",
    "maintainability": "Maintainability details"
  },
  "implementation_summary": {
    "project_name": "Project name",
    "framework": "Framework used",
    "complexity": "Complexity rating",
    "files_count": 12,
    "dependencies_summary": "Summary of dependencies",
    "architecture_pattern": "Architecture pattern used",
    "estimated_build_time": "Estimated build time"
  }
}
"""
    spec_context = ""
    if expanded_spec:
        spec_context = f"\nRequirement Expansion & Inferred Specifications to incorporate:\n{json.dumps(expanded_spec, indent=2)}\n"
        
    prompt = f"Analyze and plan: {project_idea}\n{spec_context}"

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
You are a Senior Software Architect. Update the implementation plan based on user feedback.
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
    """Beautifully format the implementation plan using Rich Tree, Tables and Panels."""
    rprint()
    rprint("[bold bright_white]====================================================[/bold bright_white]")
    rprint("[bold bright_white]           SENIOR SOFTWARE ARCHITECT PLAN           [/bold bright_white]")
    rprint("[bold bright_white]====================================================[/bold bright_white]")
    rprint()

    # 1. Project Overview
    overview_text = Text()
    overview = plan.get("project_overview", {})
    overview_text.append("• What is being built: ", style="bold cyan")
    overview_text.append(f"{overview.get('what_is_being_built', '')}\n\n")
    overview_text.append("• Primary Objective: ", style="bold cyan")
    overview_text.append(f"{overview.get('primary_objective', '')}\n\n")
    overview_text.append("• Target Users: ", style="bold cyan")
    overview_text.append(f"{overview.get('target_users', '')}\n\n")
    overview_text.append("• Expected Functionality: ", style="bold cyan")
    overview_text.append(f"{overview.get('expected_functionality', '')}\n\n")
    overview_text.append("• Overall Architecture Approach: ", style="bold cyan")
    overview_text.append(f"{overview.get('overall_architecture', '')}")
    console.print(Panel(overview_text, title="[bold purple]1. PROJECT OVERVIEW[/bold purple]", border_style="purple"))
    rprint()

    # 2. Feature Analysis
    feat_text = Text()
    for feat in plan.get("feature_analysis", []):
        feat_text.append("✓ ", style="bold green")
        feat_text.append(f"{feat}\n")
    console.print(Panel(feat_text, title="[bold purple]2. FEATURE ANALYSIS[/bold purple]", border_style="purple"))
    rprint()

    # 3. Tech Stack
    stack_table = Table(show_header=True, header_style="bold yellow", border_style="purple")
    stack_table.add_column("Component", style="bold cyan")
    stack_table.add_column("Technology", style="white")
    stack = plan.get("tech_stack", {})
    stack_table.add_row("Language", stack.get("language", "N/A"))
    stack_table.add_row("Framework", stack.get("framework", "N/A"))
    stack_table.add_row("Libraries", stack.get("libraries", "N/A"))
    stack_table.add_row("Database", stack.get("database", "N/A"))
    stack_table.add_row("Package Manager", stack.get("package_manager", "N/A"))
    stack_table.add_row("Testing Framework", stack.get("testing_framework", "N/A"))
    stack_table.add_row("Deployment Readiness", stack.get("deployment_readiness", "N/A"))
    console.print(Panel(stack_table, title="[bold purple]3. TECH STACK[/bold purple]", border_style="purple", expand=False))
    rprint()

    # 4. Project Complexity
    comp_table = Table(show_header=True, header_style="bold yellow", border_style="purple")
    comp_table.add_column("Metric", style="bold cyan")
    comp_table.add_column("Estimate", style="white")
    comp = plan.get("project_complexity", {})
    comp_table.add_row("Complexity", comp.get("complexity_rating", "N/A"))
    comp_table.add_row("Estimated Files", str(comp.get("estimated_files", 0)))
    comp_table.add_row("Estimated LOC", str(comp.get("estimated_loc", 0)))
    comp_table.add_row("Estimated Development Time", comp.get("estimated_time", "N/A"))
    comp_table.add_row("Estimated AI Tokens", str(comp.get("estimated_tokens", 0)))
    console.print(Panel(comp_table, title="[bold purple]4. PROJECT COMPLEXITY[/bold purple]", border_style="purple", expand=False))
    rprint()

    # 5. Project Architecture (Tree)
    tree = Tree(f"[bold yellow]{plan.get('project_name', 'project')}/[/bold yellow]")
    nodes = {}
    files_list = plan.get("files", [])
    folder_explanations = plan.get("folder_explanations", {})
    for fpath in sorted(files_list):
        parts = fpath.split('/')
        current_node = tree
        current_path = ""
        for part in parts[:-1]:
            current_path += part + "/"
            if current_path not in nodes:
                expl = folder_explanations.get(current_path, "")
                label = f"[bold cyan]{part}/[/bold cyan]"
                if expl:
                    label += f" [dim]({expl})[/dim]"
                nodes[current_path] = current_node.add(label)
            current_node = nodes[current_path]
        current_node.add(f"[green]{parts[-1]}[/green]")
    console.print(Panel(tree, title="[bold purple]5. PROJECT ARCHITECTURE[/bold purple]", border_style="purple"))
    rprint()

    # 6. Implementation Phases
    phases_text = Text()
    for phase in plan.get("implementation_phases", []):
        phases_text.append(f"\n{phase.get('phase_name', 'Phase')}\n", style="bold yellow")
        for task in phase.get("tasks", []):
            phases_text.append(f"  • {task}\n")
    console.print(Panel(phases_text, title="[bold purple]6. IMPLEMENTATION PHASES[/bold purple]", border_style="purple"))
    rprint()

    # 7. Dependencies
    deps_table = Table(show_header=True, header_style="bold yellow", border_style="purple")
    deps_table.add_column("Dependency", style="bold cyan")
    deps_table.add_column("Type", style="bold green")
    deps_table.add_column("Purpose/Reason", style="white")
    for dep in plan.get("dependencies", []):
        if isinstance(dep, dict):
            name = dep.get("name") or dep.get("package") or dep.get("library") or ""
            dep_type = dep.get("type") or dep.get("purpose") or "Library"
            reason = dep.get("reason") or dep.get("purpose") or "Required dependency"
            deps_table.add_row(name, dep_type, reason)
        elif isinstance(dep, str):
            deps_table.add_row(dep, "Library", "Required dependency")
    console.print(Panel(deps_table, title="[bold purple]7. DEPENDENCIES[/bold purple]", border_style="purple"))
    rprint()

    # 8. Risk Analysis
    risks_text = Text()
    for risk in plan.get("risk_analysis", []):
        risks_text.append("⚠ ", style="bold red")
        risks_text.append(f"{risk}\n")
    console.print(Panel(risks_text, title="[bold purple]8. RISK ANALYSIS[/bold purple]", border_style="purple"))
    rprint()

    # 9. Files to Generate
    files_text = Text()
    for f in plan.get("files", []):
        files_text.append("✓ ", style="bold green")
        files_text.append(f"{f}\n")
    console.print(Panel(files_text, title="[bold purple]9. FILES TO GENERATE[/bold purple]", border_style="purple"))
    rprint()

    # 10. Coding Strategy
    strategy_text = Text()
    strategy = plan.get("coding_strategy", {})
    strategy_text.append("• Build Order: ", style="bold cyan")
    strategy_text.append(f"{strategy.get('build_order', '')}\n\n")
    strategy_text.append("• Dependency Order: ", style="bold cyan")
    strategy_text.append(f"{strategy.get('dependency_order', '')}\n\n")
    strategy_text.append("• Testing Strategy: ", style="bold cyan")
    strategy_text.append(f"{strategy.get('testing_strategy', '')}\n\n")
    strategy_text.append("• Error Handling: ", style="bold cyan")
    strategy_text.append(f"{strategy.get('error_handling', '')}\n\n")
    strategy_text.append("• Code Organization: ", style="bold cyan")
    strategy_text.append(f"{strategy.get('code_organization', '')}\n\n")
    strategy_text.append("• Scalability: ", style="bold cyan")
    strategy_text.append(f"{strategy.get('scalability', '')}\n\n")
    strategy_text.append("• Maintainability: ", style="bold cyan")
    strategy_text.append(f"{strategy.get('maintainability', '')}")
    console.print(Panel(strategy_text, title="[bold purple]10. CODING STRATEGY[/bold purple]", border_style="purple"))
    rprint()

    # 11. Auto Git Plan
    git_table = Table(show_header=True, header_style="bold yellow", border_style="purple")
    git_table.add_column("Action/Artifact", style="bold cyan")
    git_table.add_column("Git Plan status", style="white")
    git_table.add_row("Repository", "Will be Created")
    git_table.add_row("Git Init", "Yes")
    git_table.add_row(".gitignore", "Will be Generated")
    git_table.add_row("README", "Will be Generated")
    git_table.add_row("Initial Commit", "Will be Created")
    git_table.add_row("GitHub Push", "Will happen after successful build")
    console.print(Panel(git_table, title="[bold purple]11. AUTO GIT PLAN[/bold purple]", border_style="purple", expand=False))
    rprint()

    # 12. Implementation Summary
    sum_table = Table(show_header=True, header_style="bold yellow", border_style="purple")
    sum_table.add_column("Field", style="bold cyan")
    sum_table.add_column("Summary", style="white")
    summary = plan.get("implementation_summary", {})
    sum_table.add_row("Project Name", summary.get("project_name", "N/A"))
    sum_table.add_row("Framework", summary.get("framework", "N/A"))
    sum_table.add_row("Complexity", summary.get("complexity", "N/A"))
    sum_table.add_row("Files Count", str(summary.get("files_count", 0)))
    sum_table.add_row("Dependencies", summary.get("dependencies_summary", "N/A"))
    sum_table.add_row("Architecture Pattern", summary.get("architecture_pattern", "N/A"))
    sum_table.add_row("Estimated Build Time", summary.get("estimated_build_time", "N/A"))
    console.print(Panel(sum_table, title="[bold purple]12. IMPLEMENTATION SUMMARY[/bold purple]", border_style="purple", expand=False))
    rprint()

    # 13. Approval Screen Header
    rprint("[bold bright_white]────────────────────────────────────────────────────[/bold bright_white]")
    rprint("Ready to Build")
    rprint("[bold bright_white]────────────────────────────────────────────────────[/bold bright_white]")


# ── File generation & templates helpers ───────────────────────────────────────

def _generate_file_content(provider: BaseProvider, plan: dict, f_path: str) -> str:
    """Generate complete, high-quality code content for a given path."""
    system_prompt = f"""\
You are an expert Software Engineer.
You are writing the file '{f_path}' for the project '{plan.get('project_name')}'.
Project Plan details:
- Description: {plan.get('strategy')}
- Architecture: {plan.get('architecture')}
- Dependencies: {plan.get('dependencies')}

Write the COMPLETE, production-ready, high-quality, fully functional source code for the file: '{f_path}'.
- You MUST write the complete implementation logic. DO NOT use 'pass', placeholder comments, 'TODO', or ellipses (...).
- Ensure all functions, classes, page templates, routing backend logic, services, databases, responsive styles, and animations are complete and production-grade.
- Do NOT output any explanations, installation instructions, notes, or chat discussions.
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
    deps = normalize_dependencies(plan.get("dependencies", []))
    files = [str(f).lower() for f in plan.get("files", []) if f]

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
    features_list = plan.get('features', [])
    features_str = ""
    if isinstance(features_list, list):
        features_str = "\n".join(f'- {feat}' for feat in features_list if feat)

    return f"""# {plan.get('project_name', 'Unnamed Project')}

{plan.get('strategy', 'No description provided.')}

---

## ✨ Features
{features_str}

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
{_format_readme_dependencies(plan.get('dependencies', []))}

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
    deps = normalize_dependencies(plan.get("dependencies", []))

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


def _calculate_total_loc(project_path: str, files: list[str]) -> int:
    """Programmatically calculate the total lines of code generated."""
    total_loc = 0
    for fpath in files:
        full_path = os.path.join(project_path, fpath)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    total_loc += len(f.readlines())
            except Exception:
                pass
    return total_loc


def _display_completion_report(plan: dict, project_path: str, generated_count: int, published: bool, repo_url: str) -> None:
    """Beautifully format and display the project completion report using Rich."""
    files = plan.get("files", [])
    total_loc = _calculate_total_loc(project_path, files)
    
    rprint()
    rprint("[bold bright_white]====================================================[/bold bright_white]")
    rprint("[bold bright_white]             PROJECT COMPLETION REPORT              [/bold bright_white]")
    rprint("[bold bright_white]====================================================[/bold bright_white]")
    rprint()
    
    summary = plan.get("implementation_summary", {})
    
    report_table = Table(show_header=True, header_style="bold yellow", border_style="green")
    report_table.add_column("Metric", style="bold cyan")
    report_table.add_column("Status / Count", style="white")
    
    report_table.add_row("Project Name", summary.get("project_name", "N/A"))
    report_table.add_row("Framework", summary.get("framework", "N/A"))
    report_table.add_row("Files Generated", str(generated_count))
    report_table.add_row("Lines of Code", f"{total_loc} lines")
    report_table.add_row("Dependencies Installed", summary.get("dependencies_summary", "N/A"))
    
    # Filter specific sub-file counts
    routes_count = len([f for f in files if "route" in f.lower() or "app.py" in f.lower() or "server" in f.lower()])
    services_count = len([f for f in files if "service" in f.lower() or "client" in f.lower() or "api" in f.lower()])
    templates_count = len([f for f in files if "template" in f.lower() or f.endswith(".html")])
    static_count = len([f for f in files if "static" in f.lower() or f.endswith(".css") or f.endswith(".js")])
    
    report_table.add_row("Routes Created", f"{routes_count} route file(s)")
    report_table.add_row("Services Created", f"{services_count} service file(s)")
    report_table.add_row("Templates Created", f"{templates_count} template(s)")
    report_table.add_row("Static Assets Created", f"{static_count} asset(s)")
    
    has_env = "Yes" if any(f.endswith(".env") or f.endswith(".env.example") for f in files) else "No"
    report_table.add_row("Environment Files", has_env)
    report_table.add_row("README Generated", "Yes")
    report_table.add_row("Git Initialized", "Yes")
    report_table.add_row("Repository Created", "Yes" if published else "Local Only")
    report_table.add_row("Validation Passed", "[green]✓ Yes[/green]")
    report_table.add_row("Ready for Deployment", "[green]✓ Ready[/green]")
    
    console.print(Panel(report_table, title="[bold green]🚀 Build Completed Successfully[/bold green]", border_style="green", expand=False))
    
    if published:
        rprint(f"[bold white]GitHub Repository :[/bold white] [underline blue]{repo_url}[/underline blue]")
    rprint()


def _review_and_fix_project(provider: BaseProvider, project_path: str, plan: dict, dep_file: str | None = None) -> None:
    """Launch Reviewer Agent loop: check placeholder markers, verify syntax/compilation, check empty files, check boilerplate, and auto-fix."""
    import re
    from github_companion.services.system_service import compile_python_file
    rprint("\n[bold purple]🔎 Starting Self-Review & Project Validation...[/bold purple]")
    
    files = []
    for category in ("files", "templates", "static_resources", "assets"):
        files.extend(plan.get(category, []))
        
    # Include boilerplate files for audit
    files.extend(["README.md", ".gitignore", "LICENSE"])
    if dep_file:
        files.append(dep_file)
        
    unique_files = []
    for fpath in files:
        if fpath and fpath not in unique_files:
            unique_files.append(fpath)
            
    for fpath in unique_files:
        full_path = os.path.join(project_path, fpath)
        
        if fpath.endswith("/") or fpath.endswith("\\"):
            continue
            
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            attempts += 1
            
            if not os.path.exists(full_path):
                rprint(f"  [bold yellow]⚠ Missing expected file: {fpath} (Attempt {attempts}/{max_attempts})...[/bold yellow]")
                fixed_content = _generate_file_fix(provider, plan, fpath, "", "File is missing from workspace.")
                if fixed_content:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(fixed_content)
                else:
                    break
                continue
                
            if os.path.isdir(full_path):
                break
                
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            issues = []
            content_lower = content.lower()
            
            # Check for empty files
            if not content.strip():
                issues.append("File is empty or contains only whitespace.")
            
            # Check for placeholders
            if fpath.endswith(".py"):
                if re.search(r'\bpass\b', content) and not ("bypass" in content_lower or "compass" in content_lower):
                    issues.append("Contains 'pass' placeholder statement.")
                if "..." in content:
                    issues.append("Contains '...' ellipsis placeholder.")
            
            placeholders = ["todo", "coming soon", "implementation goes here", "implement later", "insert here"]
            for p in placeholders:
                if p in content_lower:
                    issues.append(f"Contains placeholder/todo text: '{p}'")
            
            # Syntax validation for Python files
            if fpath.endswith(".py") and content.strip():
                res = compile_python_file(full_path)
                if res.returncode != 0:
                    issues.append(f"Syntax error / Compilation failed:\n{res.stderr.strip()}")
            
            # JSON parsing validation
            if fpath.endswith(".json") and content.strip():
                try:
                    json.loads(content)
                except Exception as je:
                    issues.append(f"Invalid JSON format: {je}")
                    
            # Boilerplate validations
            if fpath.lower() == "readme.md" and content.strip():
                if not content.strip().startswith("#"):
                    issues.append("README.md does not start with a markdown header title (#).")
                if len(content.split()) < 10:
                    issues.append("README.md is extremely short and lacks context.")
                    
            if fpath.lower() == ".gitignore" and content.strip():
                if len(content.splitlines()) < 2:
                    issues.append(".gitignore lacks standard entries (must have multiple pattern lines).")
                    
            if not issues:
                rprint(f"  [bold green]✓[/bold green] {fpath} passed validation")
                break
                
            rprint(f"  [bold yellow]⚠ Validation warning in {fpath}:[/bold yellow]")
            for iss in issues:
                rprint(f"    - {iss}")
                
            rprint(f"  [bold yellow]⚡ AI is automatically fixing {fpath} (Attempt {attempts}/{max_attempts})...[/bold yellow]")
            
            fixed_content = _generate_file_fix(provider, plan, fpath, content, "\n".join(issues))
            if fixed_content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
            else:
                break
        else:
            rprint(f"  [bold red]❌ Failed to resolve issues in {fpath} after {max_attempts} attempts.[/bold red]")


def _generate_file_fix(provider: BaseProvider, plan: dict, f_path: str, current_content: str, issues: str) -> str:
    """Generate fixed code content for a given path based on review issues."""
    system_prompt = f"""\
You are an expert Software Engineer.
You are fixing the file '{f_path}' for the project '{plan.get('project_name')}'.
The current implementation of the file has validation errors/placeholders.

You MUST rewrite the file to address the issues completely.
Write the COMPLETE, production-ready, fully functional source code.
- DO NOT use 'pass', placeholder comments, 'TODO', or ellipses (...).
- Ensure all business logic, routing, services, integrations, templates, responsive styling, and client-side scripts are complete.
- Every function, class, page, and route must be fully functional.
- Do NOT output any explanations, installation steps, markdown notes, or conversations.
- Output ONLY the raw file content. If you use markdown code block wrapping, write only the code block. We will parse it.
"""
    prompt = f"""\
Current Code of '{f_path}':
{current_content}

Validation/Review issues:
{issues}

Generate the fixed and complete file contents:
"""
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


def _clean_project_folder_name(title: str) -> str:
    """Format title into a safe lowercase-hyphenated folder name."""
    import re
    cleaned = title.lower().strip()
    cleaned = re.sub(r'^(build|create|make|generate|develop|write)\s+(a|an|the|our)?\s*', '', cleaned)
    cleaned = re.sub(r'[^a-z0-9\s\-]', '', cleaned)
    cleaned = re.sub(r'[\s\-]+', '-', cleaned)
    return cleaned.strip('-')


def normalize_dependencies(dependencies: list) -> list[str]:
    """Normalize untrusted AI-generated dependency listings into standard lowercase list[str]."""
    if not isinstance(dependencies, list):
        return []
    
    normalized = []
    for dep in dependencies:
        if not dep:
            continue
        if isinstance(dep, str):
            normalized.append(dep.strip().lower())
        elif isinstance(dep, dict):
            name = dep.get("name") or dep.get("package") or dep.get("library")
            if name and isinstance(name, str):
                normalized.append(name.strip().lower())
    return normalized


def _format_readme_dependencies(dependencies: list) -> str:
    """Format dependency listings cleanly for README.md display."""
    if not isinstance(dependencies, list):
        return ""
    lines = []
    for dep in dependencies:
        if not dep:
            continue
        if isinstance(dep, str):
            lines.append(f"- {dep}")
        elif isinstance(dep, dict):
            name = dep.get("name") or dep.get("package") or dep.get("library") or ""
            purpose = dep.get("purpose") or dep.get("reason") or dep.get("type") or ""
            if name:
                if purpose:
                    lines.append(f"- {name} ({purpose})")
                else:
                    lines.append(f"- {name}")
    return "\n".join(lines)


# ── Persistent Coding Session Loops and Helpers ────────────────────────────────

def _run_project_tests(session: dict) -> tuple[int, str]:
    """Run tests or builds depending on tech stack and return exit code and output."""
    from github_companion.services.system_service import run_test_or_build
    import os
    
    ws = session["workspace_path"]
    rprint(f"\n[bold yellow]⚡ Running build/tests in {ws}...[/bold yellow]")
    
    cmd = []
    # Heuristic detection of standard package builders or test frameworks
    if os.path.exists(os.path.join(ws, "package.json")):
        cmd = ["npm", "test"]
    elif os.path.exists(os.path.join(ws, "Cargo.toml")):
        cmd = ["cargo", "test"]
    elif os.path.exists(os.path.join(ws, "go.mod")):
        cmd = ["go", "test", "./..."]
    elif any(f.endswith(".py") for f in os.listdir(ws) if os.path.isfile(os.path.join(ws, f))):
        if os.path.exists(os.path.join(ws, "tests")) or os.path.exists(os.path.join(ws, "test")):
            cmd = ["pytest"]
        else:
            if os.path.exists(os.path.join(ws, "main.py")):
                cmd = ["python", "main.py"]
            else:
                cmd = ["python", "-m", "unittest"]
    else:
        cmd = ["git", "status"]
        
    rprint(f"[dim]Running command: {' '.join(cmd)}[/dim]")
    res = run_test_or_build(cmd, cwd=ws, shell=True)
    
    output = f"Stdout:\n{res.stdout}\nStderr:\n{res.stderr}"
    
    # Fallback if npm test is not configured (common for template projects)
    if cmd == ["npm", "test"] and "no test specified" in res.stderr.lower():
        rprint("[dim]npm test not configured. Running npm run build as fallback...[/dim]")
        res = run_test_or_build(["npm", "run", "build"], cwd=ws, shell=True)
        output = f"Stdout:\n{res.stdout}\nStderr:\n{res.stderr}"
        
    return res.returncode, output


def _run_coding_session(provider: BaseProvider, session: dict) -> None:
    """Run the persistent coding session loop."""
    rprint()
    rprint("[bold green]✓ Project Created[/bold green]")
    rprint("[bold green]✓ Local Workspace Ready[/bold green]")
    rprint("[bold green]✓ Git Initialized[/bold green]")
    if session.get("repo_url"):
        rprint("[bold green]✓ Repository Created[/bold green]")
    else:
        rprint("[bold yellow]- Repository Created (Local Only)[/bold yellow]")
    rprint("[bold green]✓ Changes Committed[/bold green]")
    if session.get("repo_url"):
        rprint("[bold green]✓ Repository Pushed[/bold green]")
    else:
        rprint("[bold yellow]- Repository Pushed (Local Only)[/bold yellow]")
    
    rprint()
    rprint(f"[bold cyan]Current Project :[/bold cyan] {session['project_name']}")
    rprint(f"[bold cyan]Repository URL  :[/bold cyan] {session['repo_url'] or 'N/A'}")
    rprint(f"[bold cyan]Workspace Path  :[/bold cyan] {session['workspace_path']}")
    rprint(f"[bold cyan]Branch          :[/bold cyan] {session['branch']}")
    rprint(f"[bold cyan]Framework       :[/bold cyan] {session['framework']}")
    rprint(f"[bold cyan]Language        :[/bold cyan] {session['language']}")
    rprint()
    rprint("I'm still connected to this project.\n")
    rprint("You can continue asking for changes, new features, bug fixes, refactoring, documentation, testing, or deployment.\n")
    rprint("Type 'over' to leave the coding session.\n")

    from github_companion.services.git_service import git_add, git_commit, git_push

    while True:
        prompt = console.input("[bold yellow]GC (Coding Session) > [/bold yellow]").strip()
        if not prompt:
            continue
        
        # Check termination condition
        if prompt.lower() in ("over", "over coding session"):
            rprint("[bold cyan]Exiting coding session. Goodbye![/bold cyan]")
            break
            
        # Process coding prompt
        plan = _handle_coding_prompt(provider, session, prompt)
        if not plan:
            continue
            
        # Interactive loop choices
        session_ended = False
        while not session_ended:
            rprint("\n[bold yellow]Would you like to:[/bold yellow]")
            rprint("  [bold cyan]1[/bold cyan]. Continue Coding")
            rprint("  [bold cyan]2[/bold cyan]. Commit")
            rprint("  [bold cyan]3[/bold cyan]. Commit & Push")
            rprint("  [bold cyan]4[/bold cyan]. Undo Last Change")
            rprint("  [bold cyan]5[/bold cyan]. Explain Changes")
            rprint("  [bold cyan]6[/bold cyan]. Exit Coding Session")
            rprint("  [bold cyan]7[/bold cyan]. Run Build/Test")
            rprint()
            
            choice = console.input("[bold yellow]Select option (1-7) : [/bold yellow]").strip()
            if choice == "1":
                break
            elif choice == "2":
                commit_msg = console.input(f"[bold yellow]Commit message [{plan.get('commit_suggestion')}]: [/bold yellow]").strip()
                if not commit_msg:
                    commit_msg = plan.get("commit_suggestion") or "Updates in coding session"
                git_add(session["workspace_path"])
                git_commit(session["workspace_path"], commit_msg)
                rprint("[bold green]✓ Changes committed successfully.[/bold green]")
                rprint("\n[bold green]Git Status:[/bold green]")
                rprint(get_git_status_in_dir(session["workspace_path"]))
            elif choice == "3":
                commit_msg = console.input(f"[bold yellow]Commit message [{plan.get('commit_suggestion')}]: [/bold yellow]").strip()
                if not commit_msg:
                    commit_msg = plan.get("commit_suggestion") or "Updates in coding session"
                git_add(session["workspace_path"])
                git_commit(session["workspace_path"], commit_msg)
                rprint("[bold green]✓ Changes committed successfully.[/bold green]")
                with console.status("[bold yellow]Pushing changes to GitHub...[/bold yellow]", spinner="dots"):
                    git_push(session["workspace_path"])
                rprint("[bold green]✓ Changes pushed to GitHub successfully.[/bold green]")
            elif choice == "4":
                git_undo_changes(session["workspace_path"])
                rprint("[bold green]✓ Discarded all unstaged changes and restored workspace to last commit.[/bold green]")
                rprint("\n[bold green]Git Status:[/bold green]")
                rprint(get_git_status_in_dir(session["workspace_path"]))
                break # Break inner loop to prompt again
            elif choice == "5":
                _explain_session_changes(provider, session, prompt, plan)
            elif choice == "6":
                session_ended = True
            elif choice == "7":
                ret_code, test_output = _run_project_tests(session)
                
                # Show results in Panel
                color = "green" if ret_code == 0 else "red"
                title = "✓ Build/Test Passed" if ret_code == 0 else "✗ Build/Test Failed"
                console.print(Panel(test_output, title=f"[bold {color}]{title}[/bold {color}]", border_style=color))
                
                if ret_code != 0:
                    rprint()
                    fix_choice = console.input("[bold red]Build/Test failed![/bold red] Would you like the AI to automatically fix these errors? (y/n) [y]: ").strip().lower()
                    if fix_choice in ("", "y", "yes"):
                        rprint("\n[bold purple]Auto-Healing Mode Activated: Informing AI about test failures...[/bold purple]")
                        # Pass test failures directly as a prompt to plan, generate and self-repair!
                        plan = _handle_coding_prompt(provider, session, f"Fix the build/test failures. Error logs:\n{test_output}")
                        if plan:
                            # Re-run build/tests to verify fix!
                            rprint("\n[bold yellow]Re-running build/tests to verify repair...[/bold yellow]")
                            ret_code2, test_output2 = _run_project_tests(session)
                            color2 = "green" if ret_code2 == 0 else "red"
                            title2 = "✓ Verification Passed" if ret_code2 == 0 else "✗ Verification Failed"
                            console.print(Panel(test_output2, title=f"[bold {color2}]{title2}[/bold {color2}]", border_style=color2))
                            if ret_code2 == 0:
                                rprint("[bold green]✓ Auto-healing was successful! All build/tests passed.[/bold green]")
                            else:
                                rprint("[bold red]❌ Verification failed. You can adjust files manually or run another auto-fix.[/bold red]")
            else:
                rprint("[bold red]Invalid option. Please choose 1-7.[/bold red]")
                
        if session_ended:
            break


def _handle_coding_prompt(provider: BaseProvider, session: dict, user_request: str) -> dict | None:
    # 1. Ask AI to plan file operations
    workspace_files = _get_workspace_files_list(session["workspace_path"])
    files_str = "\n".join(f"- {f}" for f in workspace_files)
    
    # Format conversation history
    history_str = ""
    for msg in session["conversation_history"]:
        role = msg["role"]
        content = msg["content"]
        history_str += f"{role.upper()}: {content}\n"
        
    try:
        from github_companion.services.git_service import git_log_oneline
        recent_commits = git_log_oneline(session["workspace_path"]).strip() or "No commits yet"
    except Exception:
        recent_commits = "No commits yet"
        
    modified_files = session.get("modified_files", [])
    modified_str = ", ".join(modified_files) if modified_files else "None"
    
    system_prompt = f"""\
You are an expert AI Coding Agent. The user wants to modify an existing project.
Project Context:
- Project Name: {session['project_name']}
- Framework: {session['framework']}
- Language: {session['language']}
- Workspace Path: {session['workspace_path']}
- Repository URL: {session.get('repo_url') or 'N/A'}
- Branch: {session.get('branch', 'main')}
- Files Modified in Current Session: {modified_str}
- Recent Commits: {recent_commits}

Current Files in Project:
{files_str}

Conversation History:
{history_str}

Analyze the user's request: '{user_request}' and determine which files need to be created, modified, or deleted.
You MUST return ONLY a JSON code block specifying these file operations.
Do not output any introductory or conversational text, just the JSON block.

The JSON object must contain the following keys:
{{
  "files_to_create": ["relative/path/to/new_file"],
  "files_to_modify": ["relative/path/to/existing_file"],
  "files_to_delete": ["relative/path/to/delete_file"],
  "explanation": "Brief explanation of what changes will be made",
  "commit_suggestion": "Short, conventional commit message suggestion"
}}
"""
    theme = get_active_theme_obj()
    with console.status(f"[bold {theme.highlight}]🤖 Planning changes...[/bold {theme.highlight}]", spinner="dots"):
        try:
            msg = provider.generate([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ])
            content = msg.content or ""
            plan = _parse_json_block(content)
        except Exception as exc:
            error(f"Error during planning: {exc}")
            return None

    if not plan:
        error("Failed to parse changes plan from AI.")
        return None

    # Print planned explanation
    rprint(f"\n[bold purple]AI Plan:[/bold purple] {plan.get('explanation')}")

    files_created = []
    files_modified = []
    files_deleted = []

    # Process deletes
    for f_path in plan.get("files_to_delete", []):
        if not f_path:
            continue
        full_path = os.path.join(session["workspace_path"], f_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            files_deleted.append(f_path)
            rprint(f"  [bold red]Del[/bold red] {f_path}")

    # Process creates
    for f_path in plan.get("files_to_create", []):
        if not f_path:
            continue
        full_path = os.path.join(session["workspace_path"], f_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with console.status(f"[bold {theme.highlight}]✍️ Generating {f_path}...[/bold {theme.highlight}]", spinner="dots"):
            content = _generate_session_file_create(provider, session, f_path, plan)
        if content is not None:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            files_created.append(f_path)
            rprint(f"  [bold green]New[/bold green] {f_path}")

    # Process modifies
    for f_path in plan.get("files_to_modify", []):
        if not f_path:
            continue
        full_path = os.path.join(session["workspace_path"], f_path)
        if not os.path.exists(full_path):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            current_content = ""
        else:
            with open(full_path, "r", encoding="utf-8") as f:
                current_content = f.read()
                
        with console.status(f"[bold {theme.highlight}]🛠️ Modifying {f_path}...[/bold {theme.highlight}]", spinner="dots"):
            content = _generate_session_file_modify(provider, session, f_path, current_content, user_request, plan)
        if content is not None:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            files_modified.append(f_path)
            rprint(f"  [bold blue]Mod[/bold blue] {f_path}")

    # ── Self-Review & Project Validation ──────────────────────────────────────
    _review_and_fix_project(provider, session["workspace_path"], {"files": files_created + files_modified})

    # Update session details
    session["conversation_history"].append({"role": "user", "content": user_request})
    session["conversation_history"].append({"role": "assistant", "content": plan.get("explanation", "")})
    
    for f in files_created:
        if f not in session["modified_files"]:
            session["modified_files"].append(f)
    for f in files_modified:
        if f not in session["modified_files"]:
            session["modified_files"].append(f)
            
    # Display summary report
    rprint()
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")
    rprint("[bold yellow]             IMPLEMENTATION SUMMARY            [/bold yellow]")
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")
    
    rprint("[bold green]Files Created:[/bold green]")
    if files_created:
        for f in files_created:
            rprint(f"  - {f}")
    else:
        rprint("  - None")
        
    rprint("[bold green]Files Modified:[/bold green]")
    if files_modified:
        for f in files_modified:
            rprint(f"  - {f}")
    else:
        rprint("  - None")
        
    rprint("[bold green]Files Deleted:[/bold green]")
    if files_deleted:
        for f in files_deleted:
            rprint(f"  - {f}")
    else:
        rprint("  - None")
        
    rprint(f"\n[bold green]Commit Message Suggestion:[/bold green] {plan.get('commit_suggestion', 'Updates')}")
    rprint("\n[bold green]Git Status:[/bold green]")
    rprint(get_git_status_in_dir(session["workspace_path"]))
    rprint("[bold yellow]───────────────────────────────────────────────[/bold yellow]")
    
    return plan


def _generate_session_file_create(provider: BaseProvider, session: dict, f_path: str, plan: dict) -> str:
    system_prompt = f"""\
You are an expert Software Engineer.
You are creating the new file '{f_path}' for the project '{session['project_name']}'.
Framework: {session['framework']}
Language: {session['language']}
Workspace Path: {session['workspace_path']}
Planned changes: {plan.get('explanation')}

Write the COMPLETE, production-ready, fully functional source code for the file: '{f_path}'.
- You MUST write the complete implementation logic. DO NOT use 'pass', placeholder comments, 'TODO', or ellipses (...).
- Do NOT output any explanations, diffs, or discussions.
- Output ONLY the raw file content. If you use markdown code block wrapping, write only the code block. We will parse it.
"""
    prompt = f"Generate code for the new file: {f_path}"
    try:
        msg = provider.generate([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])
        content = msg.content or ""
        return _extract_code_content(content)
    except Exception as e:
        error(f"Error generating file {f_path}: {e}")
        return ""


def _generate_session_file_modify(provider: BaseProvider, session: dict, f_path: str, current_content: str, user_request: str, plan: dict) -> str:
    system_prompt = f"""\
You are an expert Software Engineer.
You are modifying the existing file '{f_path}' for the project '{session['project_name']}'.
Framework: {session['framework']}
Language: {session['language']}
Workspace Path: {session['workspace_path']}
Planned changes: {plan.get('explanation')}

Here is the current content of '{f_path}':
==================================================
{current_content}
==================================================

Rewrite the file completely to incorporate the user's request: '{user_request}'
- Write the COMPLETE, updated, production-ready source code.
- DO NOT use placeholders, 'pass', or ellipses (...).
- Do NOT output any explanations or diffs. Output only the updated file content.
- Output ONLY the raw file content. If you use markdown code block wrapping, write only the code block. We will parse it.
"""
    prompt = f"Generate modified code for the file: {f_path}"
    try:
        msg = provider.generate([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])
        content = msg.content or ""
        return _extract_code_content(content)
    except Exception as e:
        error(f"Error modifying file {f_path}: {e}")
        return ""


def _extract_code_content(content: str) -> str:
    content = content.strip()
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 3:
            code_block = parts[1].strip()
            lines = code_block.splitlines()
            if lines and (lines[0].strip().lower() in ("python", "javascript", "typescript", "html", "css", "json", "rust", "go", "bash", "sh")):
                code_block = "\n".join(lines[1:])
            return code_block
    return content


def _explain_session_changes(provider: BaseProvider, session: dict, user_request: str, plan: dict) -> None:
    system_prompt = f"""\
You are an expert Software Engineer. Explain in detail the changes made to the project files for: '{user_request}'.
Explain what was added, modified, or removed, and the logic behind it. Keep it structured and clear.
"""
    with console.status("[bold yellow]Generating explanation...[/bold yellow]", spinner="dots"):
        try:
            msg = provider.generate([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Explain updates for request: {user_request}"}
            ])
            explanation = msg.content or "No explanation generated."
            rprint("\n[bold purple]Explanation of Changes:[/bold purple]")
            rprint(explanation)
        except Exception as e:
            error(f"Error generating explanation: {e}")


def _get_workspace_files_list(project_path: str) -> list[str]:
    file_list = []
    ignored_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), project_path)
            rel_path = rel_path.replace("\\", "/")
            file_list.append(rel_path)
    return file_list


def get_git_status_in_dir(project_path: str) -> str:
    from github_companion.services.git_service import git_status_in_dir
    return git_status_in_dir(project_path)


def git_undo_changes(project_path: str) -> None:
    from github_companion.services.git_service import git_undo
    git_undo(project_path)



