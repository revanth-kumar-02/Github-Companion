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

from github_companion.ai.providers.base_provider import BaseProvider
from github_companion.services.config_service import CONFIG_PATH


from github_companion.ai.model_registry import get_model_by_display_name_or_id, get_models_by_provider


class NvidiaProvider(BaseProvider):
    """NVIDIA NIM provider class implementing BaseProvider."""

    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self, model_name: str, api_key: str):
        self._logical_model = model_name
        
        # Resolve name via model registry
        reg_model = get_model_by_display_name_or_id(model_name)
        if reg_model:
            self._model = reg_model["model_id"]
        else:
            self._model = model_name

        self._api_key       = api_key

        debug_mode = (
            os.environ.get("DEBUG") == "True"
            or os.environ.get("GC_DEBUG") == "true"
        )
        if debug_mode:
            exists = bool(self._api_key)
            rprint()
            rprint("====================================================")
            rprint("Provider Initialized")
            rprint(f"Configuration Path: {CONFIG_PATH}")
            rprint(f"Provider: NVIDIA NIM")
            rprint(f"Model: {self._model}")
            rprint(f"API Key Configured: {exists}")
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

        endpoint = f"{self.BASE_URL}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

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
            masked_headers = dict(headers)
            if "Authorization" in masked_headers:
                masked_headers["Authorization"] = "Bearer ••••••••"
            rprint("\n[bold yellow]=== NVIDIA Request Diagnostics (DEBUG) ===[/bold yellow]")
            rprint(f"Provider:      NVIDIA NIM")
            rprint(f"Base URL:      {self.BASE_URL}")
            rprint(f"Full Endpoint: {endpoint}")
            rprint(f"Model ID:      {self._model}")
            rprint(f"Headers:       {json.dumps(masked_headers, indent=2)}")
            rprint("[bold yellow]==========================================[/bold yellow]\n")

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
                    raise RuntimeError(
                        f"[bold red]❌ NVIDIA NIM connection failed[/bold red]\n"
                        f"  Endpoint Used: {endpoint}\n"
                        f"  Model Used   : {self._model}\n"
                        f"  Error        : {exc}"
                    )
                rprint(f"[bold yellow]  ⚠  Connection error. Retrying in {backoff}s...[/bold yellow]")
                time.sleep(backoff)
                backoff *= 2

        if resp is None:
            raise RuntimeError(
                f"[bold red]❌ NVIDIA NIM request failed[/bold red]\n"
                f"  Endpoint Used: {endpoint}\n"
                f"  Model Used   : {self._model}\n"
                f"  Error        : Empty response returned from server"
            )

        if debug_mode:
            rprint("\n[bold yellow]=== NVIDIA Response Diagnostics (DEBUG) ===[/bold yellow]")
            rprint(f"Status Code:      {resp.status_code}")
            rprint(f"Response Headers: {json.dumps(dict(resp.headers), indent=2)}")
            rprint(f"Raw Response Body:\n{resp.text}")
            rprint("[bold yellow]===========================================[/bold yellow]\n")

        # Check HTTP status code
        if resp.status_code != 200:
            raise RuntimeError(
                f"[bold red]❌ NVIDIA NIM Request Failed[/bold red]\n"
                f"  HTTP Status  : {resp.status_code}\n"
                f"  Endpoint Used: {endpoint}\n"
                f"  Model Used   : {self._model}\n"
                f"  Response Body: {resp.text}\n"
            )

        is_json = "application/json" in resp.headers.get("Content-Type", "").lower()
        if not is_json:
            raise RuntimeError(
                f"[bold red]❌ NVIDIA NIM Response is not JSON[/bold red]\n"
                f"  HTTP Status  : {resp.status_code}\n"
                f"  Endpoint Used: {endpoint}\n"
                f"  Model Used   : {self._model}\n"
                f"  Response Body: {resp.text}\n"
            )

        try:
            data = resp.json()
        except Exception as parse_err:
            raise RuntimeError(
                f"[bold red]❌ NVIDIA NIM JSON Parsing Failed[/bold red]\n"
                f"  HTTP Status  : {resp.status_code}\n"
                f"  Endpoint Used: {endpoint}\n"
                f"  Model Used   : {self._model}\n"
                f"  Parse Error  : {parse_err}\n"
                f"  Response Body: {resp.text}\n"
            )

        if "error" in data:
            err_msg = data["error"].get("message", "Unknown NVIDIA NIM error")
            raise RuntimeError(
                f"[bold red]❌ NVIDIA NIM API Error[/bold red]\n"
                f"  Endpoint Used: {endpoint}\n"
                f"  Model Used   : {self._model}\n"
                f"  Error Message: {err_msg}\n"
            )

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
        return [m["model_id"] for m in get_models_by_provider("nvidia")]

    def health_check(self) -> bool:
        """
        Thorough health check validating:
        1. Base URL / endpoint reachability
        2. Authentication
        3. Available models list
        4. Chat completions endpoint responsiveness (using a minimal max_tokens=1 request)
        """
        if not self._api_key or self._api_key in ("YOUR_NVIDIA_KEY_HERE", "", "YOUR_KEY"):
            return False
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "accept": "application/json"
            }
            # 1 & 2 & 3. Fetch simple model check (reachable and auth check)
            resp_models = requests.get(f"{self.BASE_URL}/models", headers=headers, timeout=10)
            if resp_models.status_code != 200:
                return False
                
            # 4. Chat completion endpoint responsiveness
            chat_url = f"{self.BASE_URL}/chat/completions"
            payload = {
                "model": self._model,
                "messages": [{"role": "user", "content": "Ping"}],
                "max_tokens": 1
            }
            resp_chat = requests.post(chat_url, headers=headers, json=payload, timeout=10)
            return resp_chat.status_code == 200
        except Exception:
            return False

    def supports_tools(self) -> bool:
        reg_model = get_model_by_display_name_or_id(self._model)
        if reg_model:
            return reg_model.get("supports_tools", False)
        return True
