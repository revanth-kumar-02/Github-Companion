"""Abstract base class that every Design Provider must implement."""
from __future__ import annotations
from abc import ABC, abstractmethod


class BaseDesigner(ABC):
    """
    Contract that all Design Providers must satisfy.

    Design providers are NOT AI inference providers — they are dedicated
    UI/UX generation services responsible for producing design specifications
    (palettes, typography, layouts, components, animations) that GitHub
    Companion uses as the authoritative source of truth when implementing
    the frontend layer of a project.

    Methods
    -------
    generate_design(project_idea, engineering_spec)
        Produce a design specification dictionary from the project idea and
        optional engineering analysis context. Returns None on failure.

    health_check()
        Return True if the provider is reachable and ready to serve requests.

    supports_framework(framework)
        Return True if this provider can generate designs targeting the
        specified frontend framework (e.g. 'react', 'html', 'vue').

    supports_assets()
        Return True if this provider can recommend or supply external visual
        assets (icons, illustrations, sprites, etc.).

    supports_design_system()
        Return True if this provider can produce a full design system
        (tokens, spacing scale, component hierarchy, etc.).

    display(spec)
        Render the design specification to the terminal in a styled format.

    Properties
    ----------
    name          : Human-readable provider display name.
    provider_type : Machine-readable identifier ('internal' | 'stitch').
    """

    # ── Abstract interface ─────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider display name."""
        ...

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Machine-readable provider type: 'internal' | 'stitch'."""
        ...

    @abstractmethod
    def generate_design(
        self,
        project_idea: str,
        engineering_spec: dict | None = None,
    ) -> dict | None:
        """
        Generate a complete design specification for the given project.

        Args:
            project_idea     : Raw user description of the project.
            engineering_spec : Optional output from EngineeringAnalysisEngine.

        Returns:
            A dict containing design dimensions (palette, typography, layout,
            components, animations, etc.), or None if generation failed.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider is reachable and operational."""
        ...

    @abstractmethod
    def supports_framework(self, framework: str) -> bool:
        """Return True if the provider supports the given frontend framework."""
        ...

    @abstractmethod
    def supports_assets(self) -> bool:
        """Return True if the provider can recommend/supply external assets."""
        ...

    @abstractmethod
    def supports_design_system(self) -> bool:
        """Return True if the provider can output a full design system."""
        ...

    @abstractmethod
    def display(self, spec: dict) -> None:
        """Render the design specification to the terminal."""
        ...

    # ── Helpers ────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.provider_type!r}>"
