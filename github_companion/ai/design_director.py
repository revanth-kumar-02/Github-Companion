"""Backward-compatibility shim for legacy DesignDirector references.

.. deprecated::
    This module is retained for backward compatibility only.
    New code should use the ``github_companion.design`` package directly:

        from github_companion.design.design_registry import select_design_provider
        from github_companion.design.internal_designer import InternalDesigner

    ``DesignDirector.analyze()`` and ``DesignDirector.display()`` delegate to
    ``InternalDesigner`` so existing call-sites continue to work unchanged.
"""
from __future__ import annotations

from github_companion.design.internal_designer import (
    InternalDesigner,
    _parse_design_json,
    _render_design_table,
)


class DesignDirector:
    """
    Legacy design director shim.

    All methods delegate to ``InternalDesigner`` / shared rendering helpers.
    This class exists solely to avoid import errors in modules that were
    written before the design provider system was introduced.
    """

    @staticmethod
    def analyze(provider, project_idea: str, engineering_spec: dict | None = None) -> dict | None:
        """Delegate to InternalDesigner.generate_design()."""
        designer = InternalDesigner(provider)
        return designer.generate_design(project_idea, engineering_spec)

    @staticmethod
    def display(spec: dict) -> None:
        """Delegate to the shared design table renderer."""
        _render_design_table(spec, provider_label="Internal AI Designer")

    @staticmethod
    def _parse_json(content: str) -> dict | None:
        """Delegate to the shared JSON parser."""
        return _parse_design_json(content)
