"""
LangGraph-based reimbursement agent implementation.

This module provides the main reimbursement agent that uses LangGraph
StateGraph for processing Gmail emails and extracting expense information.
"""

import logging
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer

from ..base_agent import BaseAgent
from .graph import ReimbursementState, create_reimbursement_graph

logger = logging.getLogger(__name__)


class ReimbursementAgent(BaseAgent):  # type: ignore[misc]
    """
    LangGraph-based reimbursement agent for expense detection.

    This agent processes Gmail emails using a stateful LangGraph workflow
    to detect and extract expense information with real-time UI feedback.
    """

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the reimbursement agent.

        Args:
            parent: Parent QObject
        """
        super().__init__(
            agent_id="reimbursement", name="Reimbursement Agent", parent=parent
        )

        # Workflow state
        self._workflow_state: Optional[ReimbursementState] = None
        self._execution_timer = QTimer(self)
        self._execution_timer.timeout.connect(self._check_execution_progress)

        logger.info("Initialized ReimbursementAgent")

    def initialize(self) -> bool:
        """
        Initialize the agent and create the LangGraph workflow.

        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing reimbursement agent workflow")

            # Create the LangGraph workflow
            self._graph = create_reimbursement_graph()

            self.update_status("idle")
            logger.info("Reimbursement agent initialized successfully")
            return True

        except Exception as error:
            error_msg = f"Failed to initialize reimbursement agent: {error}"
            logger.error(error_msg)
            self.emit_error(error_msg)
            return False

    def execute(self, input_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute the agent workflow.

        Args:
            input_data: Input data containing:
                - gmail_query: Gmail search query (optional)
                - max_emails: Maximum number of emails to process (default: 10)

        Returns:
            True if execution started successfully
        """
        if not self._graph:
            self.emit_error("Agent not initialized. Call initialize() first.")
            return False

        if self._status == "running":
            self.emit_error("Agent is already running")
            return False

        try:
            logger.info("Starting reimbursement agent execution")

            # Prepare input data
            input_data = input_data or {}
            gmail_query = input_data.get("gmail_query", "has:attachment")
            max_emails = input_data.get("max_emails", 10)

            # Initialize workflow state with LLM fields
            self._workflow_state = ReimbursementState(
                gmail_query=gmail_query,
                max_emails=max_emails,
                agent_id=self._agent_id,
                current_step="initializing",
                progress=0,
                emails=[],
                processed_emails=0,
                llm_analyses=[],
                confidence_threshold=75.0,  # Configurable confidence threshold
                retry_count=0,
                high_confidence_count=0,
                low_confidence_count=0,
                expense_results=[],
                expenses_found=0,
                total_amount=0.0,
                errors=[],
                llm_errors=[],
                processing_times={},
                scan_id=None,
            )

            self.update_status("running")
            self.update_progress(0)

            # Start execution timer for progress monitoring
            self._execution_timer.start(1000)  # Check every second

            # Execute workflow asynchronously using QTimer
            QTimer.singleShot(100, self._run_workflow)

            logger.info(f"Started reimbursement workflow with query: '{gmail_query}'")
            return True

        except Exception as error:
            error_msg = f"Failed to start reimbursement agent execution: {error}"
            logger.error(error_msg)
            self.emit_error(error_msg)
            return False

    def _run_workflow(self) -> None:
        """Run the LangGraph workflow."""
        try:
            if not self._graph or not self._workflow_state:
                self.emit_error("Workflow not properly initialized")
                return

            logger.info("Executing LangGraph workflow")

            # Run the workflow
            result = self._graph.invoke(self._workflow_state)

            # Update final state
            self._workflow_state = result
            self._execution_timer.stop()

            # Check for errors
            if result.get("errors"):
                error_msg = "; ".join(result["errors"])
                self.emit_error(f"Workflow errors: {error_msg}")
                return

            # Update final progress and status
            self.update_progress(100)
            self.update_status("completed")

            # Emit results
            results = self._format_results(result)
            self.emit_result(results)

            logger.info("Reimbursement workflow completed successfully")

        except Exception as error:
            self._execution_timer.stop()
            error_msg = f"Workflow execution failed: {error}"
            logger.error(error_msg)
            self.emit_error(error_msg)

    def _check_execution_progress(self) -> None:
        """Check and update execution progress."""
        if not self._workflow_state:
            return

        # Update progress from workflow state
        progress = self._workflow_state.get("progress", 0)
        self.update_progress(progress)

        # Update status based on current step
        current_step = self._workflow_state.get("current_step", "unknown")
        logger.debug(f"Workflow progress: {progress}% - {current_step}")

    def _format_results(self, workflow_result: ReimbursementState) -> Dict[str, Any]:
        """
        Format workflow results for UI consumption.

        Args:
            workflow_result: Final workflow state

        Returns:
            Formatted results dictionary
        """
        return {
            "scan_id": workflow_result.get("scan_id"),
            "emails_processed": workflow_result.get("processed_emails", 0),
            "expenses_found": workflow_result.get("expenses_found", 0),
            "total_amount": workflow_result.get("total_amount", 0.0),
            "expense_results": workflow_result.get("expense_results", []),
            "gmail_query": workflow_result.get("gmail_query", ""),
            "execution_time": "N/A",  # Could track this if needed
            "status": "completed",
        }

    def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            logger.info("Cleaning up reimbursement agent")

            # Stop any running timers
            if self._execution_timer.isActive():
                self._execution_timer.stop()

            # Reset state
            self._workflow_state = None
            self._graph = None

            self.update_status("idle")
            self.update_progress(0)

            logger.info("Reimbursement agent cleanup completed")

        except Exception as error:
            logger.error(f"Error during cleanup: {error}")

    def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent expense scan history from database.

        Args:
            limit: Maximum number of scans to retrieve

        Returns:
            List of scan dictionaries
        """
        try:
            from ...core.database import get_database_manager
            from .models import ExpenseScan

            db_manager = get_database_manager()
            session = db_manager.get_session()

            try:
                scans = (
                    session.query(ExpenseScan)
                    .filter_by(agent_id=self._agent_id)
                    .order_by(ExpenseScan.started_at.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": scan.id,
                        "started_at": scan.started_at.isoformat(),
                        "completed_at": (
                            scan.completed_at.isoformat() if scan.completed_at else None
                        ),
                        "status": scan.status,
                        "emails_processed": scan.emails_processed,
                        "expenses_found": scan.expenses_found,
                        "total_amount": scan.total_amount,
                        "gmail_query": scan.gmail_query,
                    }
                    for scan in scans
                ]

            finally:
                session.close()

        except Exception as error:
            logger.error(f"Error retrieving scan history: {error}")
            return []

    def get_scan_results(self, scan_id: int) -> List[Dict[str, Any]]:
        """
        Get expense results for a specific scan.

        Args:
            scan_id: Scan ID to retrieve results for

        Returns:
            List of expense result dictionaries
        """
        try:
            from ...core.database import get_database_manager
            from .models import ExpenseResult

            db_manager = get_database_manager()
            session = db_manager.get_session()

            try:
                results = (
                    session.query(ExpenseResult)
                    .filter_by(scan_id=scan_id)
                    .order_by(ExpenseResult.processed_at.desc())
                    .all()
                )

                return [result.to_dict() for result in results]

            finally:
                session.close()

        except Exception as error:
            logger.error(f"Error retrieving scan results: {error}")
            return []

    def stop_execution(self) -> None:
        """Stop current workflow execution."""
        if self._status == "running":
            logger.info("Stopping reimbursement agent execution")

            self._execution_timer.stop()
            self.update_status("idle")
            self.update_progress(0)

            # Reset workflow state
            self._workflow_state = None
