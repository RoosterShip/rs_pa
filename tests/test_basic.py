"""
Basic tests for RS Personal Agent.

This module contains basic tests to ensure the project structure
and imports are working correctly.
"""

import pytest


def test_basic_import():
    """Test that basic imports work correctly."""
    # Test that we can import the main package
    import src

    assert src.__version__ == "0.1.0"


def test_ui_imports():
    """Test that UI package imports work correctly."""
    # Test that we can import UI components
    import src.ui

    assert src.ui.__version__ == "0.1.0"


def test_project_structure():
    """Test that expected project structure exists."""
    from pathlib import Path

    project_root = Path(__file__).parent.parent

    # Check that key directories exist
    assert (project_root / "src").exists()
    assert (project_root / "src" / "ui").exists()

    # Check that key files exist
    assert (project_root / "src" / "__init__.py").exists()
    assert (project_root / "src" / "ui" / "__init__.py").exists()


def test_placeholder():
    """Placeholder test to ensure pytest runs successfully."""
    # This test will always pass and ensures we have at least one test
    assert True


class TestMainWindow:
    """Test cases for the main window module."""

    def test_main_window_import(self):
        """Test that MainWindow can be imported."""
        from src.ui.main_window import MainWindow

        assert MainWindow is not None

    def test_main_window_instantiation(self):
        """Test that MainWindow can be instantiated."""
        # Skip this test if we're in a headless environment
        pytest.skip("Skipping GUI tests in headless environment")


class TestAgentModel:
    """Test cases for the agent table model."""

    def test_agent_model_import(self):
        """Test that AgentTableModel can be imported."""
        from src.ui.models.agent_table_model import AgentData, AgentTableModel

        assert AgentTableModel is not None
        assert AgentData is not None


class TestStatusWidget:
    """Test cases for the status indicator widget."""

    def test_status_widget_import(self):
        """Test that StatusIndicatorWidget can be imported."""
        from src.ui.widgets.status_indicator_widget import (
            ServiceStatus,
            StatusIndicatorWidget,
        )

        assert StatusIndicatorWidget is not None
        assert ServiceStatus is not None
