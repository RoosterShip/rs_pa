"""
Unit tests for core data models and structures.

Tests the fundamental data classes and enums used throughout the application.
"""

from datetime import datetime, timedelta

import pytest

from src.ui.models.agent_table_model import AgentData
from src.ui.widgets.status_indicator_widget import ServiceStatus


class TestServiceStatus:
    """Test cases for the ServiceStatus enum."""

    def test_service_status_values(self):
        """Test that all ServiceStatus enum values are correct."""
        assert ServiceStatus.CONNECTED.value == "connected"
        assert ServiceStatus.DISCONNECTED.value == "disconnected"
        assert ServiceStatus.ERROR.value == "error"
        assert ServiceStatus.UNKNOWN.value == "unknown"
        assert ServiceStatus.RUNNING.value == "running"
        assert ServiceStatus.IDLE.value == "idle"
        assert ServiceStatus.DISABLED.value == "disabled"

    def test_service_status_count(self):
        """Test that we have the expected number of status values."""
        # Ensure we have exactly 7 status types
        assert len(ServiceStatus) == 7

    def test_service_status_uniqueness(self):
        """Test that all ServiceStatus values are unique."""
        values = [status.value for status in ServiceStatus]
        assert len(values) == len(set(values))

    @pytest.mark.parametrize(
        "status",
        [
            ServiceStatus.CONNECTED,
            ServiceStatus.DISCONNECTED,
            ServiceStatus.ERROR,
            ServiceStatus.UNKNOWN,
            ServiceStatus.RUNNING,
            ServiceStatus.IDLE,
            ServiceStatus.DISABLED,
        ],
    )
    def test_service_status_enum_membership(self, status):
        """Test that each status is properly recognized as a ServiceStatus."""
        assert isinstance(status, ServiceStatus)
        assert status in ServiceStatus


class TestAgentData:
    """Test cases for the AgentData dataclass."""

    @pytest.fixture
    def sample_datetime(self):
        """Provide a consistent datetime for testing."""
        return datetime(2024, 1, 15, 10, 30, 0)

    @pytest.fixture
    def minimal_agent_data(self, sample_datetime):
        """Provide minimal valid AgentData for testing."""
        return AgentData(
            name="Test Agent",
            agent_type="Test Type",
            status=ServiceStatus.RUNNING,
            last_run=sample_datetime,
        )

    @pytest.fixture
    def full_agent_data(self, sample_datetime):
        """Provide fully populated AgentData for testing."""
        return AgentData(
            name="Email Scanner",
            agent_type="Email Processing",
            status=ServiceStatus.RUNNING,
            last_run=sample_datetime,
            description="Scans emails for reimbursable expenses",
            tasks_completed=156,
            success_rate=94.2,
        )

    def test_agent_data_required_fields(self, sample_datetime):
        """Test that AgentData can be created with only required fields."""
        agent = AgentData(
            name="Test Agent",
            agent_type="Test Type",
            status=ServiceStatus.IDLE,
            last_run=sample_datetime,
        )

        assert agent.name == "Test Agent"
        assert agent.agent_type == "Test Type"
        assert agent.status == ServiceStatus.IDLE
        assert agent.last_run == sample_datetime

    def test_agent_data_default_values(self, minimal_agent_data):
        """Test that AgentData has correct default values for optional fields."""
        agent = minimal_agent_data

        assert agent.description == ""
        assert agent.tasks_completed == 0
        assert agent.success_rate == 0.0

    def test_agent_data_full_initialization(self, sample_datetime):
        """Test that AgentData can be fully initialized with all fields."""
        agent = AgentData(
            name="Full Agent",
            agent_type="Full Type",
            status=ServiceStatus.ERROR,
            last_run=sample_datetime,
            description="Full description",
            tasks_completed=100,
            success_rate=85.5,
        )

        assert agent.name == "Full Agent"
        assert agent.agent_type == "Full Type"
        assert agent.status == ServiceStatus.ERROR
        assert agent.last_run == sample_datetime
        assert agent.description == "Full description"
        assert agent.tasks_completed == 100
        assert agent.success_rate == 85.5

    def test_agent_data_type_validation(self, sample_datetime):
        """Test that AgentData fields have correct types."""
        agent = AgentData(
            name="Type Test",
            agent_type="Type Test Type",
            status=ServiceStatus.CONNECTED,
            last_run=sample_datetime,
            description="Test description",
            tasks_completed=50,
            success_rate=75.0,
        )

        assert isinstance(agent.name, str)
        assert isinstance(agent.agent_type, str)
        assert isinstance(agent.status, ServiceStatus)
        assert isinstance(agent.last_run, datetime)
        assert isinstance(agent.description, str)
        assert isinstance(agent.tasks_completed, int)
        assert isinstance(agent.success_rate, float)

    def test_agent_data_equality(self, sample_datetime):
        """Test AgentData equality comparison."""
        agent1 = AgentData(
            name="Same Agent",
            agent_type="Same Type",
            status=ServiceStatus.RUNNING,
            last_run=sample_datetime,
            tasks_completed=10,
        )

        agent2 = AgentData(
            name="Same Agent",
            agent_type="Same Type",
            status=ServiceStatus.RUNNING,
            last_run=sample_datetime,
            tasks_completed=10,
        )

        agent3 = AgentData(
            name="Different Agent",
            agent_type="Same Type",
            status=ServiceStatus.RUNNING,
            last_run=sample_datetime,
            tasks_completed=10,
        )

        assert agent1 == agent2
        assert agent1 != agent3

    def test_agent_data_immutable_fields(self, full_agent_data):
        """Test that AgentData fields can be accessed correctly."""
        agent = full_agent_data

        # Test that we can read all fields
        assert agent.name is not None
        assert agent.agent_type is not None
        assert agent.status is not None
        assert agent.last_run is not None
        assert agent.description is not None
        assert agent.tasks_completed is not None
        assert agent.success_rate is not None

    @pytest.mark.parametrize(
        "status",
        [
            ServiceStatus.CONNECTED,
            ServiceStatus.DISCONNECTED,
            ServiceStatus.ERROR,
            ServiceStatus.UNKNOWN,
            ServiceStatus.RUNNING,
            ServiceStatus.IDLE,
            ServiceStatus.DISABLED,
        ],
    )
    def test_agent_data_with_all_status_types(self, sample_datetime, status):
        """Test AgentData creation with each possible status type."""
        agent = AgentData(
            name=f"Agent {status.value}",
            agent_type="Test Type",
            status=status,
            last_run=sample_datetime,
        )

        assert agent.status == status

    def test_agent_data_realistic_values(self, sample_datetime):
        """Test AgentData with realistic production-like values."""
        # Test with realistic agent names and types
        realistic_agents = [
            (
                "Email Scanner",
                "Email Processing",
                ServiceStatus.RUNNING,
                156,
                94.2,
            ),
            ("Task Manager", "Productivity", ServiceStatus.IDLE, 89, 87.5),
            ("Calendar Agent", "Scheduling", ServiceStatus.ERROR, 234, 76.8),
            (
                "Document Processor",
                "Document Analysis",
                ServiceStatus.DISABLED,
                45,
                92.1,
            ),
            ("Financial Tracker", "Finance", ServiceStatus.RUNNING, 312, 98.4),
        ]

        for name, agent_type, status, tasks, success_rate in realistic_agents:
            agent = AgentData(
                name=name,
                agent_type=agent_type,
                status=status,
                last_run=sample_datetime,
                description=f"Test description for {name}",
                tasks_completed=tasks,
                success_rate=success_rate,
            )

            assert agent.name == name
            assert agent.agent_type == agent_type
            assert agent.status == status
            assert agent.tasks_completed == tasks
            assert agent.success_rate == success_rate

    def test_agent_data_edge_case_values(self, sample_datetime):
        """Test AgentData with edge case values."""
        # Test with zero values
        agent_zero = AgentData(
            name="",  # Empty name
            agent_type="",  # Empty type
            status=ServiceStatus.UNKNOWN,
            last_run=sample_datetime,
            description="",
            tasks_completed=0,
            success_rate=0.0,
        )

        assert agent_zero.tasks_completed == 0
        assert agent_zero.success_rate == 0.0

        # Test with very high values
        agent_high = AgentData(
            name="High Value Agent",
            agent_type="High Value Type",
            status=ServiceStatus.RUNNING,
            last_run=sample_datetime,
            tasks_completed=999999,
            success_rate=100.0,
        )

        assert agent_high.tasks_completed == 999999
        assert agent_high.success_rate == 100.0

    def test_agent_data_datetime_variations(self):
        """Test AgentData with different datetime scenarios."""
        now = datetime.now()
        past = now - timedelta(days=30)
        future = now + timedelta(hours=1)

        # Test with past datetime
        agent_past = AgentData(
            name="Past Agent",
            agent_type="Past Type",
            status=ServiceStatus.IDLE,
            last_run=past,
        )
        assert agent_past.last_run == past

        # Test with current datetime
        agent_now = AgentData(
            name="Current Agent",
            agent_type="Current Type",
            status=ServiceStatus.RUNNING,
            last_run=now,
        )
        assert agent_now.last_run == now

        # Test with future datetime (edge case)
        agent_future = AgentData(
            name="Future Agent",
            agent_type="Future Type",
            status=ServiceStatus.UNKNOWN,
            last_run=future,
        )
        assert agent_future.last_run == future
