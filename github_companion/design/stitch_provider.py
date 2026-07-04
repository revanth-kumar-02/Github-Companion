"""Google Stitch Design Provider for GitHub Companion.

Google Stitch is treated as an external Design Service — not an AI inference
model. It is responsible for generating professional UI layouts, design
systems, color palettes, typography recommendations, and component hierarchies.

API Status (as of 2025):
    Google Stitch's public REST API is in early access / preview. This
    provider implements the full HTTP client architecture so it is ready
    the moment the API becomes generally available. In the meantime,
    health_check() detects unavailability and the design_registry
    automatically falls back to InternalDesigner with a notification.

Configuration keys in ~/.gc/config.json:
    stitch_api_key   : Google Stitch API key (for REST endpoint auth)
    stitch_mcp_server: Name of the Stitch MCP server tool (alternative auth)
"""
from __future__ import annotations
import json
from rich import print as rprint
from rich.console import Console

from github_companion.design.base_designer import BaseDesigner
from github_companion.design.internal_designer import _render_design_table, _parse_design_json

console = Console()

# Target Stitch REST API endpoint (future-ready)
_STITCH_BASE_URL = "https://stitch.googleapis.com/v1"
_STITCH_HEALTH_URL = f"{_STITCH_BASE_URL}/health"
_STITCH_DESIGN_URL = f"{_STITCH_BASE_URL}/designs:generate"

# Supported frameworks for Stitch-generated designs
_SUPPORTED_FRAMEWORKS = {"react", "vue", "html", "next", "svelte", "angular"}


class StitchProvider(BaseDesigner):
    """
    Google Stitch Design Provider.

    Responsibilities:
    - Generate professional UI layouts via Google Stitch API
    - Produce complete design systems (tokens, spacing, color scales)
    - Recommend typography, icons, animations, and responsive strategies
    - Supply design metadata as authoritative source of truth for frontend generation

    Fallback:
    If the Stitch API is unreachable (key invalid, API not yet public, or
    network error), health_check() returns False. The design_registry will
    catch this and automatically switch to InternalDesigner.
    """

    def __init__(self, api_key: str = "", mcp_server: str = "") -> None:
        self._api_key = api_key.strip()
        self._mcp_server = mcp_server.strip()

    # ── BaseDesigner interface ─────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Google Stitch"

    @property
    def provider_type(self) -> str:
        return "stitch"

    def health_check(self) -> bool:
        """
        Test connectivity to the Google Stitch API.

        Returns True only when:
        1. An API key is configured, AND
        2. The Stitch health endpoint responds with HTTP 200.

        Returns False (triggering graceful fallback) when:
        - No API key is set
        - The API endpoint is unreachable (network error)
        - The endpoint returns 4xx / 5xx (API not yet public)
        """
        if not self._api_key and not self._mcp_server:
            return False

        # Try REST API health check if API key is set
        if self._api_key:
            try:
                import urllib.request
                import urllib.error
                req = urllib.request.Request(
                    _STITCH_HEALTH_URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.status == 200
            except Exception:
                pass  # Fall through to MCP check

        # Try MCP server availability if configured
        if self._mcp_server:
            return self._check_mcp_available()

        return False

    def supports_framework(self, framework: str) -> bool:
        return framework.lower() in _SUPPORTED_FRAMEWORKS

    def supports_assets(self) -> bool:
        return True  # Stitch can recommend Google Material assets, icons, etc.

    def supports_design_system(self) -> bool:
        return True  # Stitch generates full Material 3 / design token systems

    def generate_design(
        self,
        project_idea: str,
        engineering_spec: dict | None = None,
    ) -> dict | None:
        """
        Request a design specification from Google Stitch.

        Tries the REST API first (if api_key is set), then MCP server (if
        configured). Returns None if both fail (registry will auto-fallback).
        """
        if self._api_key:
            result = self._generate_via_rest(project_idea, engineering_spec)
            if result:
                return result

        if self._mcp_server:
            result = self._generate_via_mcp(project_idea, engineering_spec)
            if result:
                return result

        return None

    def display(self, spec: dict) -> None:
        """Render the Stitch design specification with a ⭐ Stitch watermark."""
        _render_design_table(spec, provider_label="Google Stitch ⭐")

    # ── Private REST API implementation ───────────────────────────────────────

    def _generate_via_rest(
        self,
        project_idea: str,
        engineering_spec: dict | None,
    ) -> dict | None:
        """Call the Stitch REST API to generate a design spec."""
        try:
            import urllib.request
            import urllib.error

            eng_ctx = json.dumps(engineering_spec, indent=2) if engineering_spec else ""
            payload = json.dumps({
                "prompt": project_idea,
                "engineering_context": eng_ctx,
                "framework": "html",
                "output_format": "design_spec_json",
                "style": "modern_saas",
            }).encode("utf-8")

            req = urllib.request.Request(
                _STITCH_DESIGN_URL,
                data=payload,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                # Stitch may return the spec directly or nested under "design_spec"
                return data.get("design_spec") or data

        except Exception:
            return None

    def _generate_via_mcp(
        self,
        project_idea: str,
        engineering_spec: dict | None,
    ) -> dict | None:
        """Call the configured Stitch MCP server to generate a design spec."""
        # MCP tool integration is runtime-dependent; we attempt a best-effort call
        try:
            # MCP servers are discovered at runtime through the user's MCP config.
            # If the user has configured a Stitch MCP server, we format a structured
            # prompt and pass it to the server as a tool call.
            rprint(
                f"[dim]  Attempting Stitch MCP server: {self._mcp_server}[/dim]"
            )
            # Placeholder: MCP integration requires the MCP SDK which is runtime-wired.
            # Return None to trigger fallback until full MCP SDK integration is complete.
            return None
        except Exception:
            return None

    def _check_mcp_available(self) -> bool:
        """Check if the configured Stitch MCP server is accessible."""
        # MCP availability depends on the runtime environment.
        # Return False until full MCP SDK integration is in place.
        return False
