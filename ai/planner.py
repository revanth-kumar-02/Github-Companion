"""Task planner for the GitHub Companion AI agent."""
from __future__ import annotations

# ── Known multi-step plans ─────────────────────────────────────────────────────
# Displayed before execution so the user can see what the AI intends to do.

_PLANS: dict[str, list[str]] = {
    "publish": [
        "Create GitHub repository via API",
        "Initialize Git  (git init)",
        "Stage all files (git add .)",
        "Create initial commit",
        "Rename branch to main",
        "Add remote origin",
        "Push to GitHub  (git push)",
    ],
    "readme": [
        "Analyze project structure",
        "Generate professional README.md",
        "Write file to project folder",
    ],
    "clone_and_publish": [
        "Read project files for context",
        "Create GitHub repository",
        "Run full git publish workflow",
    ],
}

# Keywords that indicate a complex multi-tool task
_COMPLEX_SIGNALS = {
    "publish", "push to github", "upload", "deploy",
    "initialize and", "set up and", "create and push",
    "generate readme", "make a readme",
}


def is_complex_task(user_input: str) -> bool:
    """Heuristic: return True if the input likely requires multiple tool calls."""
    lower = user_input.lower()
    return any(signal in lower for signal in _COMPLEX_SIGNALS)


def get_plan_for(user_input: str) -> list[str] | None:
    """
    Return a pre-defined step list for the detected task type, or None.

    The plan is purely cosmetic — displayed to the user before execution
    so they can follow along while the agent calls tools.
    """
    lower = user_input.lower()
    if "publish" in lower or ("push" in lower and "project" in lower):
        return _PLANS["publish"]
    if "readme" in lower and ("generate" in lower or "create" in lower or "make" in lower):
        return _PLANS["readme"]
    return None


def format_plan(steps: list[str]) -> str:
    """Format a plan as a numbered list string."""
    return "\n".join(f"    {i + 1}. {step}" for i, step in enumerate(steps))
