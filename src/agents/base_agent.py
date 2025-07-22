"""
Base agent class with LangGraph StateGraph integration.

This module provides the abstract base class for all agents in the system,
integrating with LangGraph for stateful workflow management.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# StateGraph is referenced in type annotations
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class BaseAgentMeta(type(QObject), type(ABC)):  # type: ignore[misc]
    """Metaclass that combines QObject and ABC metaclasses."""

    pass


class BaseAgent(QObject, ABC, metaclass=BaseAgentMeta):
    """
    Abstract base class for all agents with LangGraph integration.

    This class provides the foundation for stateful agents using LangGraph
    StateGraph for workflow management and Qt signals for UI integration.
    """

    # Signals for UI updates
    status_changed = Signal(str)  # "idle", "running", "error", "completed"
    progress_updated = Signal(int)  # Progress percentage (0-100)
    result_ready = Signal(dict)  # Results dictionary
    error_occurred = Signal(str)  # Error message

    def __init__(self, agent_id: str, name: str, parent: Optional[QObject] = None):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            parent: Parent QObject
        """
        super().__init__(parent)
        self._agent_id = agent_id
        self._name = name
        self._status = "idle"
        self._progress = 0
        self._graph: Optional[Any] = None
        self._state: Dict[str, Any] = {}

        logger.info(f"Initialized agent {self._name} with ID {self._agent_id}")

    @property
    def agent_id(self) -> str:
        """Get agent unique identifier."""
        return self._agent_id

    @property
    def name(self) -> str:
        """Get agent name."""
        return self._name

    @property
    def status(self) -> str:
        """Get current agent status."""
        return self._status

    @property
    def progress(self) -> int:
        """Get current progress percentage."""
        return self._progress

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        return self._state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set agent state."""
        self._state = state.copy()
        logger.debug(f"Agent {self._agent_id} state updated")

    def update_status(self, status: str) -> None:
        """
        Update agent status and emit signal.

        Args:
            status: New status ("idle", "running", "error", "completed")
        """
        if status != self._status:
            self._status = status
            logger.info(f"Agent {self._agent_id} status changed to {status}")
            self.status_changed.emit(status)

    def update_progress(self, progress: int) -> None:
        """
        Update agent progress and emit signal.

        Args:
            progress: Progress percentage (0-100)
        """
        progress = max(0, min(100, progress))  # Clamp to 0-100
        if progress != self._progress:
            self._progress = progress
            self.progress_updated.emit(progress)

    def emit_result(self, result: Dict[str, Any]) -> None:
        """
        Emit result signal with data.

        Args:
            result: Results dictionary
        """
        logger.info(f"Agent {self._agent_id} emitted result")
        self.result_ready.emit(result)

    def emit_error(self, error_msg: str) -> None:
        """
        Emit error signal and update status.

        Args:
            error_msg: Error message
        """
        logger.error(f"Agent {self._agent_id} error: {error_msg}")
        self.update_status("error")
        self.error_occurred.emit(error_msg)

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the agent and create the LangGraph workflow.

        This method should create the StateGraph, define nodes and edges,
        and prepare the agent for execution.

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    def execute(self, input_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute the agent workflow.

        This method should run the LangGraph workflow with the provided
        input data and manage state transitions.

        Args:
            input_data: Optional input data for the workflow

        Returns:
            True if execution started successfully
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up agent resources.

        This method should clean up any resources, save state if needed,
        and prepare the agent for shutdown.
        """
        pass

    def reset(self) -> None:
        """Reset agent to initial state."""
        self._state = {}
        self._progress = 0
        self.update_status("idle")
        logger.info(f"Agent {self._agent_id} reset to initial state")

    def get_info(self) -> Dict[str, Any]:
        """
        Get agent information dictionary.

        Returns:
            Dictionary with agent information
        """
        return {
            "agent_id": self._agent_id,
            "name": self._name,
            "status": self._status,
            "progress": self._progress,
            "state_size": len(self._state),
            "has_graph": self._graph is not None,
        }
