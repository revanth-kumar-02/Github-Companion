"""
Model type selector for the GitHub Companion AI agent.

Classifies user input into one of three model types:
  - "coding"    → coding_model    (e.g. qwen2.5-coder)
  - "reasoning" → reasoning_model (e.g. deepseek-r1)
  - "assistant" → assistant_model (e.g. llama3.3 / deepseek-v3)

The classification is keyword-based and runs in O(n) — fast enough that
it adds no noticeable latency before the LLM call.
"""
from __future__ import annotations

# ── Keyword sets ───────────────────────────────────────────────────────────────

_CODING_KEYWORDS: frozenset[str] = frozenset({
    # Action verbs
    "create", "write", "generate", "implement", "build", "code", "program",
    "refactor", "rewrite", "fix", "debug", "optimize", "edit",
    # Code artifacts
    "function", "class", "method", "module", "script", "snippet", "api",
    "endpoint", "route", "database", "schema", "model", "test", "unittest",
    # Frameworks / languages
    "flask", "django", "fastapi", "react", "node", "express", "typescript",
    "python", "javascript", "rust", "go", "java", "sql", "html", "css",
    # Dev tasks
    "install", "setup", "configure", "deploy", "dockerfile", "requirements",
    "package", "library", "import", "dependency", "cli", "parser",
})

_REASONING_KEYWORDS: frozenset[str] = frozenset({
    # Strategic
    "plan", "design", "architecture", "strategy", "approach", "structure",
    "scalable", "tradeoff", "compare", "evaluate", "recommend", "suggest",
    # Analytical
    "analyze", "analyse", "diagnose", "investigate", "trace", "understand",
    "why", "how should", "what is the best", "which is better",
    # Complex problem solving
    "complex", "difficult", "multi-step", "breakdown", "sequence",
    "workflow", "pipeline", "optimize", "performance", "bottleneck",
    "security", "vulnerability", "edge case",
})

_ASSISTANT_KEYWORDS: frozenset[str] = frozenset({
    # Info retrieval
    "list", "show", "get", "fetch", "display", "what are", "tell me",
    # Explanation
    "explain", "describe", "summarize", "what is", "how does", "overview",
    # Documentation
    "readme", "documentation", "docs", "comment", "docstring",
    # GitHub ops
    "repository", "repo", "profile", "search", "delete", "rename",
    "publish", "push", "commit", "branch",
})


# ── Public API ─────────────────────────────────────────────────────────────────

def select_model_type(user_input: str) -> str:
    """
    Classify user input and return the model type to use.

    Returns:
        "coding"    — for code generation, refactoring, debugging tasks
        "reasoning" — for planning, architecture, complex analysis
        "assistant" — for general questions, GitHub ops, documentation
    """
    lower = user_input.lower()

    coding_score    = _score(lower, _CODING_KEYWORDS)
    reasoning_score = _score(lower, _REASONING_KEYWORDS)
    assistant_score = _score(lower, _ASSISTANT_KEYWORDS)

    scores = {
        "coding":    coding_score,
        "reasoning": reasoning_score,
        "assistant": assistant_score,
    }

    best_type = max(scores, key=lambda k: scores[k])

    # If all scores are equal (no keywords matched), default to assistant
    if scores[best_type] == 0:
        return "assistant"

    return best_type


def describe_model_type(model_type: str) -> str:
    """Return a short emoji-prefixed label for display in the terminal."""
    labels = {
        "coding":    "🔧 Coding",
        "reasoning": "🧠 Reasoning",
        "assistant": "💬 Assistant",
    }
    return labels.get(model_type, model_type)


# ── Internal ───────────────────────────────────────────────────────────────────

def _score(text: str, keywords: frozenset[str]) -> int:
    """Count how many keywords from the set appear in the text."""
    return sum(1 for kw in keywords if kw in text)
