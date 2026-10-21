"""Smoke test for application entry point."""
from github_companion import app


def test_main_imports():
    assert hasattr(app, "main")
