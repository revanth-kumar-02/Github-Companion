"""Model Registry — Holds registry definitions for all providers."""

MODELS = [
    # Ollama
    {
        "name": "Qwen 2.5 Coder",
        "provider": "ollama",
        "model_id": "qwen2.5-coder",
        "role": "Coding",
        "description": "Offline optimized coder model",
        "recommended": "⭐⭐⭐⭐⭐",
        "supports_tools": True,
        "supports_streaming": True
    },
    {
        "name": "DeepSeek R1",
        "provider": "ollama",
        "model_id": "deepseek-r1",
        "role": "Reasoning",
        "description": "Offline reasoning model",
        "recommended": "⭐⭐⭐⭐☆",
        "supports_tools": False,
        "supports_streaming": True
    },
    
    # OpenRouter
    {
        "name": "DeepSeek V3",
        "provider": "openrouter",
        "model_id": "deepseek-v3",
        "role": "Assistant",
        "description": "General assistant & code generation",
        "recommended": "⭐⭐⭐⭐⭐",
        "supports_tools": True,
        "supports_streaming": True
    },
    {
        "name": "QwQ 32B",
        "provider": "openrouter",
        "model_id": "qwq-32b-preview",
        "role": "Planning",
        "description": "Advanced planning/reasoning model",
        "recommended": "⭐⭐⭐⭐⭐",
        "supports_tools": False,
        "supports_streaming": True
    },
    
    # NVIDIA NIM
    {
        "name": "DeepSeek R1",
        "provider": "nvidia",
        "model_id": "deepseek/deepseek-r1",
        "role": "Planning",
        "description": "State-of-the-art reasoning model on NVIDIA hardware",
        "recommended": "⭐⭐⭐⭐⭐",
        "supports_tools": False,
        "supports_streaming": True
    },
    {
        "name": "Llama 3.1 Nemotron Ultra",
        "provider": "nvidia",
        "model_id": "nvidia/llama-3.1-nemotron-51b-instruct",
        "role": "Assistant",
        "description": "Highly responsive assistant model by NVIDIA",
        "recommended": "⭐⭐⭐⭐⭐",
        "supports_tools": True,
        "supports_streaming": True
    },
    {
        "name": "Llama 3.3 70B",
        "provider": "nvidia",
        "model_id": "meta/llama-3.3-70b-instruct",
        "role": "Coding",
        "description": "High capability coding model by Meta on NIM",
        "recommended": "⭐⭐⭐⭐☆",
        "supports_tools": True,
        "supports_streaming": True
    },
    {
        "name": "Qwen2.5 Instruct",
        "provider": "nvidia",
        "model_id": "qwen/qwen2.5-72b-instruct",
        "role": "Assistant",
        "description": "Qwen general purpose instruct model on NIM",
        "recommended": "⭐⭐⭐⭐☆",
        "supports_tools": True,
        "supports_streaming": True
    }
]
