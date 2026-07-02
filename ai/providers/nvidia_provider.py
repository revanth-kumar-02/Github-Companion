"""
NVIDIA NIM provider — high-performance optimized cloud inference.

API base URL : https://integrate.api.nvidia.com/v1
Auth         : Bearer <nvidia_api_key>
Protocol     : OpenAI-compatible chat completions
"""
from __future__ import annotations
import os
import json
import requests
from typing import Any
from types import SimpleNamespace
from rich import print as rprint

from ai.providers.base_provider import BaseProvider
from services.config_service import CONFIG_PATH


_MODEL_MAP = {
    "deepseek-r1": "deepseek/deepseek-r1",
    "llama-3.1-nemotron-ultra": "nvidia/llama-3.1-nemotron-51b-instruct",
    "llama-3.3-70b": "meta/llama-3.3-70b-instruct",
    "qwen2.5-instruct": "qwen/qwen2.5-72b-instruct"
}

_NO_TOOLS_MODELS: tuple[str, ...] = (
    "deepseek/deepseek-r1",
)


class NvidiaProvider(BaseProvider):
    """NVIDIA NIM provider class implementing BaseProvider."""

    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self, model_name: str, api_key: str):
        self._logical_model = model_name
        self._model         = _MODEL_MAP.get(model_name, model_name)
        self._api_key       = api_key

        debug_mode = (
            os.environ.get("DEBUG") == "True"
            or os.environ.get("GC_DEBUG") == "true"
        )
        if debug_mode:
            exists = self._api_key is not None
            length = len(self._api_key) if self._api_key else 0
            first_8 = self._api_key[:8] if length >= 8 else (self._api_key or "")
            rprint()
            rprint("====================================================")
            rprint("Provider Initialized")
            rprint(f"Configuration Path: {CONFIG_PATH}")
            rprint(f"Provider: NVIDIA NIM")
            rprint(f"Model: {self._model}")
            rprint(f"API Key Exists: {exists}")
            rprint(f"API Key Length: {length}")
            rprint(f"First 8 characters: {first_8}")
            rprint("====================================================")
            rprint()

    @property
    def name(self) -> str:
        return "nvidia"

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        """Send a completions request to NVIDIA NIM API."""
        api_key = self._api_key
        api_key_exists = api_key is not None
        api_key_len = len(api_key) if api_key else 0
        first_8 = api_key[:8] if api_key_len >= 8 else (api_key or "")

        endpoint = f"{self.BASE_URL}/chat/completions"

        headers = {
            "Content-Type": "application/json",
        }
        
        auth_present = False
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            auth_present = True

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2048,
        }
        if tools and self.supports_tools():
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        debug_mode = (
            os.environ.get("DEBUG") == "True"
            or os.environ.get("GC_DEBUG") == "true"
        )

        if debug_mode:
            masked_key = f"Bearer {first_8}" + "*" * (api_key_len - 8) if api_key else "None"
            rprint()
            rprint("====================================================")
            rprint(f"Configuration Path          : {CONFIG_PATH}")
            rprint(f"Provider                    : NVIDIA NIM")
            rprint(f"Model                       : {self._model}")
            rprint(f"API Key Exists              : {api_key_exists}")
            rprint(f"API Key Length              : {api_key_len}")
            rprint(f"Provider Received API Key   : {first_8}...")
            rprint(f"Provider Stored API Key     : {first_8}...")
            rprint(f"Authorization Header Exists : {auth_present}")
            rprint(f"Authorization Header        : {masked_key}")
            rprint(f"Endpoint                    : {endpoint}")
            rprint("====================================================")
            rprint("Request")
            rprint(f"URL: {endpoint}")
            rprint(f"Model: {self._model}")
            rprint(f"Messages: {json.dumps(messages, indent=2)}")
            rprint("====================================================")
            rprint()

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        except Exception as exc:
            raise RuntimeError(f"NVIDIA NIM request failed: {exc}")

        if debug_mode:
            rprint("====================================================")
            rprint(f"HTTP Status: {resp.status_code}")
            rprint(f"Response Headers: {dict(resp.headers)}")
            rprint(f"Response Body: {resp.text}")
            rprint("====================================================")
            rprint()

        if resp.status_code == 401:
            raise RuntimeError(
                "[bold red]NVIDIA NIM authentication failed.[/bold red]\n"
                "Please verify your NVIDIA API Key is correct and active."
            )

        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(f"NVIDIA NIM response is not valid JSON. HTTP {resp.status_code}: {resp.text}")

        if "error" in data:
            err_msg = data["error"].get("message", "Unknown NVIDIA NIM error")
            raise RuntimeError(f"NVIDIA NIM API error: {err_msg}")

        try:
            choices = data["choices"]
            message_data = choices[0]["message"]
            content = message_data.get("content")
            raw_tool_calls = message_data.get("tool_calls")
            
            tool_calls = None
            if raw_tool_calls:
                tool_calls = []
                for tc in raw_tool_calls:
                    fn = SimpleNamespace(
                        name=tc.get("function", {}).get("name", ""),
                        arguments=tc.get("function", {}).get("arguments", "{}")
                    )
                    tool_calls.append(SimpleNamespace(
                        id=tc.get("id", ""),
                        type=tc.get("type", "function"),
                        function=fn
                    ))

            return SimpleNamespace(content=content, tool_calls=tool_calls)
        except Exception as parse_err:
            raise RuntimeError(f"Failed to parse NVIDIA NIM response: {parse_err}. Raw body: {data}")

    def list_models(self) -> list[str]:
        return list(_MODEL_MAP.keys())

    def health_check(self) -> bool:
        """Perform key validation against models endpoint."""
        if not self._api_key or self._api_key in ("YOUR_NVIDIA_KEY_HERE", "", "YOUR_KEY"):
            return False
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            # Fetch simple model check
            resp = requests.get(f"{self.BASE_URL}/models", headers=headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def supports_tools(self) -> bool:
        return not any(self._model.startswith(m) for m in _NO_TOOLS_MODELS)
