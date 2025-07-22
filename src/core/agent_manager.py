"""
Agent manager for LangGraph agent lifecycle management.

This module provides centralized management for all agents in the system,
including LangSmith integration for tracing and monitoring.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Type

from PySide6.QtCore import QObject, Signal

from ..agents.base_agent import BaseAgent
from ..agents.reimbursement.agent import ReimbursementAgent

logger = logging.getLogger(__name__)


class AgentManager(QObject):
    """
    Manager for LangGraph agent lifecycle with LangSmith integration.

    This class handles agent registration, execution, monitoring,
    and integration with LangSmith for tracing and debugging.
    """

    # Signals for UI updates
    agent_registered = Signal(str)  # agent_id
    agent_status_changed = Signal(str, str)  # agent_id, status
    agent_progress_updated = Signal(str, int)  # agent_id, progress
    agent_result_ready = Signal(str, dict)  # agent_id, result
    agent_error_occurred = Signal(str, str)  # agent_id, error_msg

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the agent manager.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        self._agents: Dict[str, BaseAgent] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._langsmith_enabled = False

        # Setup LangSmith integration
        self._setup_langsmith()

        # Register built-in agents
        self._register_builtin_agents()

        logger.info("Agent manager initialized")

    def _setup_langsmith(self) -> None:
        """Setup LangSmith integration if configured."""
        try:
            # Check for LangSmith environment variables
            api_key = os.environ.get("LANGSMITH_API_KEY")
            tracing_enabled = (
                os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"
            )

            if api_key and tracing_enabled:
                # Import and configure LangSmith
                try:
                    from langsmith import Client

                    # Initialize LangSmith client
                    self._langsmith_client = Client(api_key=api_key)

                    # Set environment variables for automatic tracing
                    os.environ["LANGCHAIN_TRACING_V2"] = "true"
                    os.environ["LANGCHAIN_PROJECT"] = "RS Personal Agent"

                    self._langsmith_enabled = True
                    logger.info("LangSmith integration enabled")

                except ImportError:
                    logger.warning(
                        "LangSmith not available - install with 'pip install langsmith'"
                    )
                except Exception as error:
                    logger.warning(f"Failed to setup LangSmith: {error}")
            else:
                logger.info(
                    "LangSmith integration disabled (set LANGSMITH_API_KEY and "
                    "LANGSMITH_TRACING=true to enable)"
                )

        except Exception as error:
            logger.warning(f"Error setting up LangSmith: {error}")

    def _register_builtin_agents(self) -> None:
        """Register built-in agent classes."""
        # Register reimbursement agent
        self.register_agent_class("reimbursement", ReimbursementAgent)

        logger.info("Built-in agents registered")

    def register_agent_class(
        self, agent_type: str, agent_class: Type[BaseAgent]
    ) -> None:
        """
        Register an agent class for later instantiation.

        Args:
            agent_type: Unique agent type identifier
            agent_class: Agent class to register
        """
        self._agent_classes[agent_type] = agent_class
        logger.info(f"Registered agent class: {agent_type}")

    def create_agent(
        self, agent_type: str, agent_id: Optional[str] = None
    ) -> Optional[BaseAgent]:
        """
        Create and register a new agent instance.

        Args:
            agent_type: Type of agent to create
            agent_id: Optional custom agent ID (defaults to agent_type)

        Returns:
            Created agent instance or None if failed
        """
        try:
            if agent_type not in self._agent_classes:
                logger.error(f"Unknown agent type: {agent_type}")
                return None

            # Use agent_type as default ID
            if agent_id is None:
                agent_id = agent_type

            # Check if agent already exists
            if agent_id in self._agents:
                logger.warning(f"Agent {agent_id} already exists")
                return self._agents[agent_id]

            # Create agent instance
            agent_class = self._agent_classes[agent_type]
            # Note: ReimbursementAgent doesn't need agent_id/name in constructor
            agent = agent_class(parent=self)  # type: ignore[call-arg]

            # Initialize the agent
            if not agent.initialize():
                logger.error(f"Failed to initialize agent {agent_id}")
                return None

            # Connect agent signals
            self._connect_agent_signals(agent)

            # Register agent
            self._agents[agent_id] = agent

            logger.info(f"Created agent: {agent_id} (type: {agent_type})")
            self.agent_registered.emit(agent_id)

            return agent

        except Exception as error:
            logger.error(f"Failed to create agent {agent_type}: {error}")
            return None

    def _connect_agent_signals(self, agent: BaseAgent) -> None:
        """Connect agent signals to manager signals."""
        agent.status_changed.connect(
            lambda status: self.agent_status_changed.emit(agent.agent_id, status)
        )
        agent.progress_updated.connect(
            lambda progress: self.agent_progress_updated.emit(agent.agent_id, progress)
        )
        agent.result_ready.connect(
            lambda result: self.agent_result_ready.emit(agent.agent_id, result)
        )
        agent.error_occurred.connect(
            lambda error_msg: self.agent_error_occurred.emit(agent.agent_id, error_msg)
        )

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID to retrieve

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs.

        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent information.

        Args:
            agent_id: Agent ID to get info for

        Returns:
            Agent info dictionary or None if not found
        """
        agent = self._agents.get(agent_id)
        if agent:
            return agent.get_info()
        return None

    def execute_agent(
        self, agent_id: str, input_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Execute an agent.

        Args:
            agent_id: Agent ID to execute
            input_data: Optional input data for the agent

        Returns:
            True if execution started successfully
        """
        agent = self._agents.get(agent_id)
        if not agent:
            logger.error(f"Agent not found: {agent_id}")
            return False

        try:
            # Add LangSmith tracing context if enabled
            if self._langsmith_enabled:
                # You could add additional tracing context here
                pass

            return agent.execute(input_data)

        except Exception as error:
            logger.error(f"Failed to execute agent {agent_id}: {error}")
            return False

    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent execution.

        Args:
            agent_id: Agent ID to stop

        Returns:
            True if stop was successful
        """
        agent = self._agents.get(agent_id)
        if not agent:
            logger.error(f"Agent not found: {agent_id}")
            return False

        try:
            # Check if agent has stop method
            if hasattr(agent, "stop_execution"):
                agent.stop_execution()
            else:
                # Fallback to cleanup
                agent.cleanup()
                agent.reset()

            return True

        except Exception as error:
            logger.error(f"Failed to stop agent {agent_id}: {error}")
            return False

    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the manager.

        Args:
            agent_id: Agent ID to remove

        Returns:
            True if removal was successful
        """
        agent = self._agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent not found: {agent_id}")
            return False

        try:
            # Cleanup agent
            agent.cleanup()

            # Disconnect signals
            agent.status_changed.disconnect()
            agent.progress_updated.disconnect()
            agent.result_ready.disconnect()
            agent.error_occurred.disconnect()

            # Remove from registry
            del self._agents[agent_id]

            logger.info(f"Removed agent: {agent_id}")
            return True

        except Exception as error:
            logger.error(f"Failed to remove agent {agent_id}: {error}")
            return False

    def get_agent_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status summary for all agents.

        Returns:
            Dictionary mapping agent_id to status info
        """
        summary = {}

        for agent_id, agent in self._agents.items():
            summary[agent_id] = {
                "status": agent.status,
                "progress": agent.progress,
                "name": agent.name,
                "info": agent.get_info(),
            }

        return summary

    def cleanup_all_agents(self) -> None:
        """Cleanup all agents."""
        try:
            logger.info("Cleaning up all agents")

            for agent_id in list(self._agents.keys()):
                self.remove_agent(agent_id)

            logger.info("All agents cleaned up")

        except Exception as error:
            logger.error(f"Error during agent cleanup: {error}")

    def is_langsmith_enabled(self) -> bool:
        """Check if LangSmith integration is enabled."""
        return self._langsmith_enabled

    def get_langsmith_client(self) -> Optional[Any]:
        """Get LangSmith client if available."""
        if self._langsmith_enabled:
            return getattr(self, "_langsmith_client", None)
        return None
