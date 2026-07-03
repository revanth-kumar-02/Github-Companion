"""Model Registry — Holds registry definitions for all providers and roles."""

MODELS = [
    # ── CODING ROLE ───────────────────────────────────────────────────────────
    {
        "display_name": "Qwen 2.5 Coder",
        "model_id": "qwen2.5-coder",
        "provider": "ollama",
        "role": "coding",
        "description": "Offline optimized code generation",
        "recommended": True,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 32768,
        "local_or_cloud": "local"
    },
    {
        "display_name": "DeepSeek V3",
        "model_id": "deepseek/deepseek-chat",
        "provider": "openrouter",
        "role": "coding",
        "description": "State-of-the-art general purpose model",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 64000,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "DeepSeek R1",
        "model_id": "deepseek-ai/deepseek-r1",
        "provider": "nvidia",
        "role": "coding",
        "description": "High-performance reasoning and coding model",
        "recommended": False,
        "supports_tools": False,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Llama 3.3 70B",
        "model_id": "meta-llama/llama-3.3-70b-instruct",
        "provider": "openrouter",
        "role": "coding",
        "description": "Meta's highly optimized instruction model",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 131072,
        "local_or_cloud": "cloud"
    },

    # ── PLANNING / ARCHITECT ROLE ─────────────────────────────────────────────
    {
        "display_name": "DeepSeek R1",
        "model_id": "deepseek-ai/deepseek-r1",
        "provider": "nvidia",
        "role": "planning",
        "description": "Reasoning models optimized for architect tasks",
        "recommended": True,
        "supports_tools": False,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "QwQ-32B",
        "model_id": "qwen/qwq-32b-preview",
        "provider": "openrouter",
        "role": "planning",
        "description": "Experimental reasoning preview model",
        "recommended": False,
        "supports_tools": False,
        "supports_streaming": True,
        "context_length": 32768,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Llama 3.1 Nemotron Ultra",
        "model_id": "nvidia/llama-3.1-nemotron-51b-instruct",
        "provider": "nvidia",
        "role": "planning",
        "description": "Highly responsive planning assistant",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Mistral Large",
        "model_id": "mistralai/mistral-large",
        "provider": "openrouter",
        "role": "planning",
        "description": "Mistral flagship model with deep planning capabilities",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 128000,
        "local_or_cloud": "cloud"
    },

    # ── CHAT / ASSISTANT ROLE ──────────────────────────────────────────────────
    {
        "display_name": "Llama 3.3",
        "model_id": "meta-llama/llama-3.3-70b-instruct",
        "provider": "openrouter",
        "role": "assistant",
        "description": "General purpose discussion and support",
        "recommended": True,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 131072,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Gemma 3",
        "model_id": "gemma3",
        "provider": "ollama",
        "role": "assistant",
        "description": "Google's lightweight open model",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 8192,
        "local_or_cloud": "local"
    },
    {
        "display_name": "Qwen2.5 Instruct",
        "model_id": "qwen/qwen2.5-72b-instruct",
        "provider": "nvidia",
        "role": "assistant",
        "description": "General purpose conversation",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Mistral Small",
        "model_id": "mistralai/mistral-small",
        "provider": "openrouter",
        "role": "assistant",
        "description": "Compact and cost-efficient cloud assistant",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 32768,
        "local_or_cloud": "cloud"
    },

    # ── CODE REVIEW ROLE ──────────────────────────────────────────────────────
    {
        "display_name": "Llama 3.1 Nemotron Ultra",
        "model_id": "nvidia/llama-3.1-nemotron-51b-instruct",
        "provider": "nvidia",
        "role": "review",
        "description": "Advanced code compliance inspector",
        "recommended": True,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Mistral Large",
        "model_id": "mistralai/mistral-large",
        "provider": "openrouter",
        "role": "review",
        "description": "Precise code quality check",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 128000,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Gemma 3",
        "model_id": "gemma3",
        "provider": "ollama",
        "role": "review",
        "description": "Google's lightweight code review model",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 8192,
        "local_or_cloud": "local"
    },
    {
        "display_name": "Qwen2.5 Instruct",
        "model_id": "qwen/qwen2.5-72b-instruct",
        "provider": "nvidia",
        "role": "review",
        "description": "Instruct model optimized for reviews",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },

    # ── DEBUGGING ROLE ────────────────────────────────────────────────────────
    {
        "display_name": "Devstral",
        "model_id": "mistralai/codestral-7b",
        "provider": "openrouter",
        "role": "debugging",
        "description": "Specifically trained model for debugging and fixing bugs",
        "recommended": True,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 32768,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "CodeLlama 70B",
        "model_id": "codellama:70b",
        "provider": "ollama",
        "role": "debugging",
        "description": "Code Llama optimized for debugging and trace parsing",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "local"
    },
    {
        "display_name": "Llama 3.1 Nemotron Ultra",
        "model_id": "nvidia/llama-3.1-nemotron-51b-instruct",
        "provider": "nvidia",
        "role": "debugging",
        "description": "Accurate root cause logic debugger",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Mistral Large",
        "model_id": "mistralai/mistral-large",
        "provider": "openrouter",
        "role": "debugging",
        "description": "Deep architecture trace diagnostic inspector",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 128000,
        "local_or_cloud": "cloud"
    },

    # ── DOCUMENTATION ROLE ────────────────────────────────────────────────────
    {
        "display_name": "Mistral Large",
        "model_id": "mistralai/mistral-large",
        "provider": "openrouter",
        "role": "documentation",
        "description": "Top-tier documentation and explanation generator",
        "recommended": True,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 128000,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Gemma 3",
        "model_id": "gemma3",
        "provider": "ollama",
        "role": "documentation",
        "description": "Highly descriptive documentation assistant",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 8192,
        "local_or_cloud": "local"
    },
    {
        "display_name": "Llama 3.3",
        "model_id": "meta/llama-3.3-70b-instruct",
        "provider": "nvidia",
        "role": "documentation",
        "description": "Llama 3.3 documentation generator on NIM",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 16384,
        "local_or_cloud": "cloud"
    },
    {
        "display_name": "Qwen2.5 Instruct",
        "model_id": "qwen/qwen-2.5-72b-instruct",
        "provider": "openrouter",
        "role": "documentation",
        "description": "Instruct model for READMEs and Wikis",
        "recommended": False,
        "supports_tools": True,
        "supports_streaming": True,
        "context_length": 131072,
        "local_or_cloud": "cloud"
    }
]

def get_models_by_role(role: str) -> list[dict]:
    """Filter models from the registry by active role classification."""
    return [m for m in MODELS if m["role"].lower() == role.lower()]

def get_model_by_display_name_or_id(value: str) -> dict | None:
    """Lookup a model definition by display name, internal model id, or alias."""
    val_lower = value.lower()
    
    # Normalize some common aliases
    alias_map = {
        "deepseek-r1": "deepseek/deepseek-r1",
        "deepseek-v3": "deepseek/deepseek-chat",
        "llama3.3": "meta-llama/llama-3.3-70b-instruct",
        "llama3.3-70b": "meta-llama/llama-3.3-70b-instruct",
        "llama-3.1-nemotron-ultra": "nvidia/llama-3.1-nemotron-51b-instruct",
        "qwen2.5-instruct": "qwen/qwen2.5-72b-instruct",
        "qwq-32b": "qwen/qwq-32b-preview",
        "qwq": "qwen/qwq-32b-preview"
    }
    
    resolved_val = alias_map.get(val_lower, val_lower)
    
    for m in MODELS:
        if (m["display_name"].lower() == val_lower or 
            m["model_id"].lower() == val_lower or 
            m["model_id"].lower() == resolved_val or
            (val_lower == "deepseek-r1" and m["model_id"].lower() == "deepseek-ai/deepseek-r1")):
            return m
    return None

def get_models_by_provider(provider: str) -> list[dict]:
    """Filter models from the registry by provider name."""
    return [m for m in MODELS if m["provider"].lower() == provider.lower()]
