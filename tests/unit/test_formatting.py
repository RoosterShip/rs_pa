"""
Unit tests for data formatting functions.

Tests the various data formatting utilities used throughout the application
for displaying dates, status values, and other formatted data.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.ui.models.agent_table_model import AgentTableModel
from src.ui.widgets.status_indicator_widget import ServiceStatus


class TestDateTimeFormatting:
    """Test datetime formatting functionality."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model instance for testing formatting functions."""
        with patch("src.ui.models.agent_table_model.QAbstractTableModel.__init__"):
            return AgentTableModel()

    @pytest.fixture
    def fixed_now(self):
        """Provide a fixed datetime for consistent testing."""
        return datetime(2024, 1, 15, 14, 30, 0)

    def test_format_datetime_just_now(self, mock_model, fixed_now):
        """Test formatting for very recent times (< 1 minute)."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            # Test times within the last minute
            test_times = [
                fixed_now - timedelta(seconds=0),  # Exactly now
                fixed_now - timedelta(seconds=30),  # 30 seconds ago
                fixed_now - timedelta(seconds=59),  # 59 seconds ago
            ]

            for test_time in test_times:
                result = mock_model._format_datetime(test_time)
                assert result == "Just now"

    def test_format_datetime_minutes(self, mock_model, fixed_now):
        """Test formatting for times measured in minutes."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            test_cases = [
                (fixed_now - timedelta(minutes=1), "1m ago"),
                (fixed_now - timedelta(minutes=5), "5m ago"),
                (fixed_now - timedelta(minutes=15), "15m ago"),
                (fixed_now - timedelta(minutes=30), "30m ago"),
                (fixed_now - timedelta(minutes=45), "45m ago"),
                (fixed_now - timedelta(minutes=59), "59m ago"),
            ]

            for test_time, expected in test_cases:
                result = mock_model._format_datetime(test_time)
                assert result == expected

    def test_format_datetime_hours(self, mock_model, fixed_now):
        """Test formatting for times measured in hours."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            test_cases = [
                (fixed_now - timedelta(hours=1), "1h ago"),
                (fixed_now - timedelta(hours=2), "2h ago"),
                (fixed_now - timedelta(hours=6), "6h ago"),
                (fixed_now - timedelta(hours=12), "12h ago"),
                (fixed_now - timedelta(hours=18), "18h ago"),
                (fixed_now - timedelta(hours=23), "23h ago"),
            ]

            for test_time, expected in test_cases:
                result = mock_model._format_datetime(test_time)
                assert result == expected

    def test_format_datetime_days(self, mock_model, fixed_now):
        """Test formatting for times measured in days."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            test_cases = [
                (fixed_now - timedelta(days=1), "1d ago"),
                (fixed_now - timedelta(days=2), "2d ago"),
                (fixed_now - timedelta(days=7), "7d ago"),
                (fixed_now - timedelta(days=30), "30d ago"),
                (fixed_now - timedelta(days=365), "365d ago"),
            ]

            for test_time, expected in test_cases:
                result = mock_model._format_datetime(test_time)
                assert result == expected

    def test_format_datetime_boundary_conditions(self, mock_model, fixed_now):
        """Test datetime formatting at exact boundary conditions."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            # Test exact boundary values
            test_cases = [
                # Exactly 60 seconds - should be 1 minute
                (fixed_now - timedelta(seconds=60), "1m ago"),
                # Exactly 3600 seconds - should be 1 hour
                (fixed_now - timedelta(seconds=3600), "1h ago"),
                # Exactly 86400 seconds - should be 1 day
                (fixed_now - timedelta(seconds=86400), "1d ago"),
            ]

            for test_time, expected in test_cases:
                result = mock_model._format_datetime(test_time)
                assert result == expected

    def test_format_datetime_edge_cases(self, mock_model, fixed_now):
        """Test datetime formatting edge cases."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            # Test with fractional seconds
            fractional_second = fixed_now - timedelta(seconds=30.5)
            result = mock_model._format_datetime(fractional_second)
            assert result == "Just now"

            # Test with microseconds
            microsecond_time = fixed_now - timedelta(microseconds=500000)
            result = mock_model._format_datetime(microsecond_time)
            assert result == "Just now"

    def test_format_datetime_future_times(self, mock_model, fixed_now):
        """Test datetime formatting with future times (edge case)."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now

            # Future times should still work (negative time difference)
            future_time = fixed_now + timedelta(hours=1)
            # Test that the function handles future times gracefully
            mock_model._format_datetime(future_time)


class TestStatusFormatting:
    """Test status formatting functionality."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model instance for testing status formatting."""
        with patch("src.ui.models.agent_table_model.QAbstractTableModel.__init__"):
            return AgentTableModel()

    def test_format_status_all_types(self, mock_model):
        """Test status formatting for all ServiceStatus enum values."""
        expected_formats = {
            ServiceStatus.RUNNING: "🟢 Running",
            ServiceStatus.IDLE: "🟡 Idle",
            ServiceStatus.ERROR: "🔴 Error",
            ServiceStatus.DISABLED: "⚫ Disabled",
            ServiceStatus.CONNECTED: "🟢 Connected",
            ServiceStatus.DISCONNECTED: "🔴 Disconnected",
            ServiceStatus.UNKNOWN: "⚪ Unknown",
        }

        for status, expected in expected_formats.items():
            result = mock_model._format_status(status)
            assert result == expected

    def test_format_status_consistency(self, mock_model):
        """Test that status formatting is consistent across calls."""
        test_status = ServiceStatus.RUNNING

        # Call multiple times and ensure consistent results
        results = [mock_model._format_status(test_status) for _ in range(5)]
        assert all(result == results[0] for result in results)

    def test_format_status_emoji_inclusion(self, mock_model):
        """Test that status formatting includes appropriate emojis."""
        # Test that all status formats include emojis
        for status in ServiceStatus:
            result = mock_model._format_status(status)

            # Should contain at least one emoji character
            emoji_chars = ["🟢", "🟡", "🔴", "⚫", "⚪"]
            assert any(emoji in result for emoji in emoji_chars)

    def test_format_status_text_content(self, mock_model):
        """Test that status formatting includes correct text content."""
        text_mappings = {
            ServiceStatus.RUNNING: "Running",
            ServiceStatus.IDLE: "Idle",
            ServiceStatus.ERROR: "Error",
            ServiceStatus.DISABLED: "Disabled",
            ServiceStatus.CONNECTED: "Connected",
            ServiceStatus.DISCONNECTED: "Disconnected",
            ServiceStatus.UNKNOWN: "Unknown",
        }

        for status, expected_text in text_mappings.items():
            result = mock_model._format_status(status)
            assert expected_text in result

    def test_format_status_unknown_fallback(self, mock_model):
        """Test status formatting fallback for unknown status."""
        # This tests the .get() fallback in the status formatting
        # We can't easily test with an invalid enum, but we can verify
        # the mapping covers all enum values

        all_statuses = set(ServiceStatus)
        formatted_statuses = set()

        for status in all_statuses:
            formatted = mock_model._format_status(status)
            formatted_statuses.add(status)
            assert formatted  # Should not be empty

        assert formatted_statuses == all_statuses


class TestDisplayDataFormatting:
    """Test display data formatting for table columns."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for display data testing."""
        with patch("src.ui.models.agent_table_model.QAbstractTableModel.__init__"):
            return AgentTableModel()

    @pytest.fixture
    def sample_agent(self):
        """Provide a sample agent for testing display formatting."""
        from src.ui.models.agent_table_model import AgentData

        return AgentData(
            name="Format Test Agent",
            agent_type="Format Test Type",
            status=ServiceStatus.RUNNING,
            last_run=datetime(2024, 1, 15, 10, 30, 0),
            description="Test agent for formatting",
            tasks_completed=42,
            success_rate=87.5,
        )

    def test_display_data_name_column(self, mock_model, sample_agent):
        """Test display formatting for name column."""
        result = mock_model._get_display_data(sample_agent, AgentTableModel.COLUMN_NAME)
        assert result == "Format Test Agent"
        assert isinstance(result, str)

    def test_display_data_type_column(self, mock_model, sample_agent):
        """Test display formatting for type column."""
        result = mock_model._get_display_data(sample_agent, AgentTableModel.COLUMN_TYPE)
        assert result == "Format Test Type"
        assert isinstance(result, str)

    def test_display_data_status_column(self, mock_model, sample_agent):
        """Test display formatting for status column."""
        result = mock_model._get_display_data(
            sample_agent, AgentTableModel.COLUMN_STATUS
        )
        assert result == "🟢 Running"  # Should be formatted status
        assert isinstance(result, str)

    def test_display_data_last_run_column(self, mock_model, sample_agent):
        """Test display formatting for last run column."""
        with patch("src.ui.models.agent_table_model.datetime") as mock_datetime:
            # Set current time for consistent formatting
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)

            result = mock_model._get_display_data(
                sample_agent, AgentTableModel.COLUMN_LAST_RUN
            )
            assert result == "1h ago"  # Should be formatted datetime
            assert isinstance(result, str)

    def test_display_data_tasks_column(self, mock_model, sample_agent):
        """Test display formatting for tasks column."""
        result = mock_model._get_display_data(
            sample_agent, AgentTableModel.COLUMN_TASKS
        )
        assert result == "42"  # Should be string representation of int
        assert isinstance(result, str)

    def test_display_data_success_rate_column(self, mock_model, sample_agent):
        """Test display formatting for success rate column."""
        result = mock_model._get_display_data(
            sample_agent, AgentTableModel.COLUMN_SUCCESS_RATE
        )
        assert result == "87.5%"  # Should include percentage sign
        assert isinstance(result, str)

    def test_display_data_invalid_column(self, mock_model, sample_agent):
        """Test display formatting for invalid column returns empty string."""
        result = mock_model._get_display_data(sample_agent, -1)  # Invalid column
        assert result == ""

        result = mock_model._get_display_data(sample_agent, 999)  # Invalid column
        assert result == ""

    @pytest.mark.parametrize(
        "success_rate,expected",
        [
            (0.0, "0.0%"),
            (50.0, "50.0%"),
            (100.0, "100.0%"),
            (99.9, "99.9%"),
            (0.1, "0.1%"),
        ],
    )
    def test_display_data_success_rate_variations(
        self, mock_model, success_rate, expected
    ):
        """Test success rate formatting with various values."""
        from src.ui.models.agent_table_model import AgentData

        agent = AgentData(
            name="Test",
            agent_type="Test",
            status=ServiceStatus.IDLE,
            last_run=datetime.now(),
            success_rate=success_rate,
        )

        result = mock_model._get_display_data(
            agent, AgentTableModel.COLUMN_SUCCESS_RATE
        )
        assert result == expected

    @pytest.mark.parametrize(
        "tasks,expected",
        [
            (0, "0"),
            (1, "1"),
            (999, "999"),
            (1000, "1000"),
            (999999, "999999"),
        ],
    )
    def test_display_data_tasks_variations(self, mock_model, tasks, expected):
        """Test tasks formatting with various values."""
        from src.ui.models.agent_table_model import AgentData

        agent = AgentData(
            name="Test",
            agent_type="Test",
            status=ServiceStatus.IDLE,
            last_run=datetime.now(),
            tasks_completed=tasks,
        )

        result = mock_model._get_display_data(agent, AgentTableModel.COLUMN_TASKS)
        assert result == expected


class TestTooltipFormatting:
    """Test tooltip formatting and content."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for tooltip testing."""
        with patch("src.ui.models.agent_table_model.QAbstractTableModel.__init__"):
            return AgentTableModel()

    def test_tooltip_contains_all_info(self, mock_model):
        """Test that tooltip contains all agent information."""
        from src.ui.models.agent_table_model import AgentData

        agent = AgentData(
            name="Tooltip Test Agent",
            agent_type="Tooltip Test Type",
            status=ServiceStatus.RUNNING,
            last_run=datetime(2024, 1, 15, 14, 30, 0),
            description="This is a test description for tooltip",
            tasks_completed=123,
            success_rate=92.7,
        )

        tooltip = mock_model._get_tooltip(agent)

        # Verify all information is present
        assert "Tooltip Test Agent" in tooltip
        assert "Tooltip Test Type" in tooltip
        assert "Running" in tooltip  # Status without emoji
        assert "This is a test description for tooltip" in tooltip
        assert "123" in tooltip
        assert "92.7%" in tooltip
        assert "2024-01-15 14:30:00" in tooltip

    def test_tooltip_html_formatting(self, mock_model):
        """Test that tooltip uses proper HTML formatting."""
        from src.ui.models.agent_table_model import AgentData

        agent = AgentData(
            name="HTML Test",
            agent_type="Test",
            status=ServiceStatus.IDLE,
            last_run=datetime.now(),
        )

        tooltip = mock_model._get_tooltip(agent)

        # Should contain HTML tags
        assert "<b>" in tooltip
        assert "</b>" in tooltip
        assert "<br/>" in tooltip

    def test_tooltip_emoji_removal(self, mock_model):
        """Test that emojis are properly removed from status in tooltip."""
        from src.ui.models.agent_table_model import AgentData

        test_cases = [
            (ServiceStatus.RUNNING, "Running"),
            (ServiceStatus.ERROR, "Error"),
            (ServiceStatus.IDLE, "Idle"),
            (ServiceStatus.DISABLED, "Disabled"),
        ]

        for status, expected_text in test_cases:
            agent = AgentData(
                name="Emoji Test",
                agent_type="Test",
                status=status,
                last_run=datetime.now(),
            )

            tooltip = mock_model._get_tooltip(agent)

            # Should contain status text without emojis
            assert expected_text in tooltip

            # Should not contain emoji characters
            emoji_chars = ["🟢", "🟡", "🔴", "⚫", "⚪"]
            for emoji in emoji_chars:
                assert emoji not in tooltip
