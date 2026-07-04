"""
OpenRouter provider — cloud inference with access to many open models via one API key.

OpenRouter exposes an OpenAI-compatible API at https://openrouter.ai/api/v1,
so we use the standard `openai` SDK pointed at a different base_url.

Get a free API key at: https://openrouter.ai/keys
Add it to config/settings.json under "openrouter_api_key".

Supported models include DeepSeek, Qwen, Llama, Mistral and many others.
"""
from __future__ import annotations
import os
import json
import requests
from typing import Any
from types import SimpleNamespace
from rich import print as rprint

from github_companion.ai.providers.base_provider import BaseProvider
from github_companion.services.config_service import CONFIG_PATH


from github_companion.ai.model_registry import get_model_by_display_name_or_id, get_models_by_provider


class OpenRouterProvider(BaseProvider):
    """
    Connects to OpenRouter's cloud inference API.

    Base URL  : https://openrouter.ai/api/v1
    Auth      : Bearer <openrouter_api_key>
    Protocol  : OpenAI-compatible chat completions
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model_name: str, api_key: str):
        try:
            from openai import OpenAI as _OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        # Resolve name via model registry
        self._logical_model = model_name
        reg_model = get_model_by_display_name_or_id(model_name)
        if reg_model:
            self._model = reg_model["model_id"]
        else:
            self._model = model_name

        self._api_key       = api_key
        self._client        = _OpenAI(base_url=self.BASE_URL, api_key=api_key)

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
            rprint(f"Provider: OpenRouter")
            rprint(f"Model: {self._model}")
            rprint(f"API Key Exists: {exists}")
            rprint(f"API Key Length: {length}")
            rprint(f"First 8 characters: {first_8}")
            rprint("====================================================")
            rprint()

    # ── BaseProvider interface ─────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        """Send a chat completion request to OpenRouter using self._api_key."""
        api_key = self._api_key
        api_key_exists = api_key is not None
        api_key_len = len(api_key) if api_key else 0
        first_8 = api_key[:8] if api_key_len >= 8 else (api_key or "")

        endpoint = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/revanth-kumar-02/Github-Companion",
            "X-Title": "GitHub Companion",
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
            rprint(f"Provider                    : OpenRouter")
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

        import time
        max_retries = 3
        backoff = 2
        resp = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(endpoint, json=payload, headers=headers, timeout=60)
                if resp.status_code == 429:
                    rprint(f"[bold yellow]  ⚠  Rate limit hit. Retrying in {backoff}s...[/bold yellow]")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                if resp.status_code in (502, 503, 504):
                    rprint(f"[bold yellow]  ⚠  Server error ({resp.status_code}). Retrying in {backoff}s...[/bold yellow]")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                break
            except Exception as exc:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"OpenRouter request failed: {exc}")
                rprint(f"[bold yellow]  ⚠  Connection error. Retrying in {backoff}s...[/bold yellow]")
                time.sleep(backoff)
                backoff *= 2

        if resp is None:
            raise RuntimeError("OpenRouter request failed with empty response.")

        if debug_mode:
            rprint("====================================================")
            rprint(f"HTTP Status: {resp.status_code}")
            rprint(f"Response Headers: {dict(resp.headers)}")
            rprint(f"Response Body: {resp.text}")
            rprint("====================================================")
            rprint()

        # Handle authentication errors
        if resp.status_code == 401:
            error_msg = """\
[bold red]OpenRouter authentication failed.[/bold red]

Possible causes:
 • API key not loaded
 • Invalid API key
 • Authorization header missing
 • Configuration not saved correctly
"""
            if debug_mode:
                error_msg += f"\n[dim]Original response: {resp.text}[/dim]"
            raise RuntimeError(error_msg)

        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(f"OpenRouter response is not valid JSON. HTTP {resp.status_code}: {resp.text}")

        if "error" in data:
            err_msg = data["error"].get("message", "Unknown OpenRouter error")
            raise RuntimeError(f"OpenRouter API error: {err_msg}")

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
            raise RuntimeError(f"Failed to parse OpenRouter response: {parse_err}. Raw body: {data}")

    def list_models(self) -> list[str]:
        """Return the logical model names available via OpenRouter."""
        return [m["model_id"] for m in get_models_by_provider("openrouter")]

    def health_check(self) -> bool:
        """Return True if a valid (non-placeholder) API key is configured."""
        return bool(
            self._api_key
            and self._api_key not in ("YOUR_OPENROUTER_KEY_HERE", "", "YOUR_KEY")
        )

    def supports_tools(self) -> bool:
        """Return True if the selected model reliably supports tool calling."""
        reg_model = get_model_by_display_name_or_id(self._model)
        if reg_model:
            return reg_model.get("supports_tools", False)
        return True
