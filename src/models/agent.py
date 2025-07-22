"""
Agent model for RS Personal Agent.

This module defines the Agent model which represents individual AI agents
in the system with their configuration, status, and metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class AgentStatus(str, Enum):
    """Enumeration of possible agent statuses."""

    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    DISABLED = "disabled"


class AgentType(str, Enum):
    """Enumeration of possible agent types."""

    EMAIL_SCANNER = "email_scanner"
    TASK_MANAGER = "task_manager"
    CALENDAR_AGENT = "calendar_agent"
    DOCUMENT_PROCESSOR = "document_processor"
    REIMBURSEMENT_AGENT = "reimbursement_agent"


class Agent(BaseModel):
    """
    Model representing an AI agent in the system.

    Each agent has a name, type, current status, configuration, and runtime metadata.
    Agents can be in various states (running, idle, error, disabled) and contain
    configuration data specific to their function.
    """

    # Agent identification and metadata
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique name identifier for the agent",
    )

    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type category of the agent (e.g., email_scanner, task_manager)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Optional description of what this agent does"
    )

    # Agent status and runtime information
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AgentStatus.IDLE.value,
        index=True,
        doc="Current operational status of the agent",
    )

    last_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the agent's last execution",
    )

    last_error: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Last error message if the agent encountered an issue"
    )

    run_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        doc="Total number of times this agent has been executed",
    )

    # Configuration and settings
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, doc="Agent-specific configuration data stored as JSON"
    )

    # Agent management flags
    enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        doc="Whether the agent is enabled and can be executed",
    )

    auto_start: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        doc="Whether the agent should start automatically on system startup",
    )

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"<Agent(id={self.id}, name='{self.name}', "
            f"type='{self.agent_type}', status='{self.status}')>"
        )

    def is_running(self) -> bool:
        """Check if the agent is currently in running status."""
        return self.status == AgentStatus.RUNNING

    def is_enabled(self) -> bool:
        """Check if the agent is enabled for execution."""
        return self.enabled

    def has_error(self) -> bool:
        """Check if the agent is currently in error status."""
        return self.status == AgentStatus.ERROR

    def update_status(
        self, status: AgentStatus, error_message: Optional[str] = None
    ) -> None:
        """
        Update the agent's status and optionally record an error message.

        Args:
            status: New status for the agent
            error_message: Optional error message if status is ERROR
        """
        self.status = status
        if error_message:
            self.last_error = error_message
        elif status != AgentStatus.ERROR:
            # Clear error message if not in error state
            self.last_error = None

    def record_execution(self) -> None:
        """Record that the agent was executed by updating run metadata."""
        self.run_count += 1
        self.last_run = datetime.utcnow()

    def get_display_name(self) -> str:
        """Get a human-readable display name for the agent."""
        return self.name.replace("_", " ").title()

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value with optional default.

        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        if not self.config:
            return default
        return self.config.get(key, default)

    @property
    def agent_type_enum(self) -> AgentType:
        """Get the agent type as an enum value."""
        try:
            return AgentType(self.agent_type)
        except ValueError:
            return AgentType.EMAIL_SCANNER  # Default fallback

    @agent_type_enum.setter
    def agent_type_enum(self, value: AgentType) -> None:
        """Set the agent type from an enum value."""
        self.agent_type = value.value

    @property
    def status_enum(self) -> AgentStatus:
        """Get the status as an enum value."""
        try:
            return AgentStatus(self.status)
        except ValueError:
            return AgentStatus.IDLE  # Default fallback

    @status_enum.setter
    def status_enum(self, value: AgentStatus) -> None:
        """Set the status from an enum value."""
        self.status = value.value
