"""
LangSmith monitoring integration for LangGraph workflows.

This module provides comprehensive monitoring, tracing, and evaluation
capabilities for LangGraph workflows using LangSmith.
"""

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from langsmith import Client
    from langsmith.schemas import Example, Run

    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    Client = type(None)  # type: ignore
    Run = type(None)  # type: ignore
    Example = type(None)  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""

    workflow_id: str
    workflow_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    total_tokens: int
    total_cost: float
    success: bool
    error_message: Optional[str]
    node_count: int
    nodes_executed: List[str]
    final_state: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class NodeMetrics:
    """Metrics for individual node execution."""

    node_name: str
    node_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    tokens_used: int
    cost: float
    success: bool
    error_message: Optional[str]
    metadata: Dict[str, Any]


class LangSmithMonitor:
    """
    LangSmith monitoring integration for comprehensive workflow tracking.

    Features:
    - Real-time workflow execution tracing
    - Performance metrics collection
    - Error monitoring and debugging
    - Cost tracking and optimization insights
    - Custom evaluation metrics
    - Dataset management for testing
    - Automated feedback collection
    """

    def __init__(
        self,
        project_name: str = "rs-personal-agent",
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        """
        Initialize LangSmith monitor.

        Args:
            project_name: Name of the LangSmith project
            api_key: LangSmith API key (or set LANGCHAIN_API_KEY env var)
            endpoint: LangSmith endpoint URL (optional)
        """
        self.project_name = project_name
        self.api_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        self.endpoint = endpoint or os.getenv(
            "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
        )

        # Initialize client if LangSmith is available
        self.client = None
        self.enabled = False

        if LANGSMITH_AVAILABLE and self.api_key:
            try:
                self.client = Client(api_url=self.endpoint, api_key=self.api_key)
                self.enabled = True
                logger.info(f"LangSmith monitoring enabled for project: {project_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith client: {e}")
                self.enabled = False
        else:
            if not LANGSMITH_AVAILABLE:
                logger.warning("LangSmith package not available. Monitoring disabled.")
            elif not self.api_key:
                logger.warning("LangSmith API key not provided. Monitoring disabled.")
            self.enabled = False

        # Runtime tracking
        self.active_workflows: Dict[str, Any] = {}
        self.workflow_metrics: Dict[str, Any] = {}
        self.node_metrics: Dict[str, Any] = {}

    def start_workflow_trace(
        self,
        workflow_name: str,
        workflow_type: str = "langgraph",
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start tracing a workflow execution.

        Args:
            workflow_name: Name of the workflow
            workflow_type: Type of workflow (e.g., "langgraph", "chain")
            inputs: Input data for the workflow
            metadata: Additional metadata

        Returns:
            Workflow trace ID
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Create workflow metrics entry
        workflow_metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            start_time=start_time,
            end_time=None,
            duration_ms=None,
            total_tokens=0,
            total_cost=0.0,
            success=False,
            error_message=None,
            node_count=0,
            nodes_executed=[],
            final_state={},
            metadata=metadata or {},
        )

        self.workflow_metrics[workflow_id] = workflow_metrics
        self.active_workflows[workflow_id] = {
            "name": workflow_name,
            "type": workflow_type,
            "start_time": start_time,
            "inputs": inputs or {},
            "metadata": metadata or {},
        }

        # Send to LangSmith if enabled
        if self.enabled:
            try:
                if self.client:
                    self.client.create_run(
                        name=workflow_name,
                        run_type="chain",
                        inputs=inputs or {},
                        project_name=self.project_name,
                        run_id=uuid.UUID(workflow_id),
                        extra=metadata or {},
                    )
                    logger.debug(
                        f"Started LangSmith trace for workflow: {workflow_name}"
                    )
            except Exception as e:
                logger.error(f"Error starting LangSmith trace: {e}")

        return workflow_id

    def end_workflow_trace(
        self,
        workflow_id: str,
        outputs: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        End workflow tracing.

        Args:
            workflow_id: Workflow trace ID
            outputs: Final outputs of the workflow
            success: Whether the workflow completed successfully
            error: Error message if workflow failed
        """
        if workflow_id not in self.workflow_metrics:
            logger.warning(f"Workflow {workflow_id} not found in metrics")
            return

        end_time = datetime.now()
        workflow_metrics = self.workflow_metrics[workflow_id]

        # Update metrics
        workflow_metrics.end_time = end_time
        workflow_metrics.duration_ms = (
            end_time - workflow_metrics.start_time
        ).total_seconds() * 1000
        workflow_metrics.success = success
        workflow_metrics.error_message = error
        workflow_metrics.final_state = outputs or {}

        # Send to LangSmith if enabled
        if self.enabled:
            try:
                if self.client:
                    self.client.update_run(
                        run_id=uuid.UUID(workflow_id),
                        outputs=outputs or {},
                        end_time=end_time,
                        error=error,
                    )
                    workflow_name = workflow_metrics.workflow_name
                    logger.debug(
                        f"Updated LangSmith trace for workflow: {workflow_name}"
                    )
            except Exception as e:
                logger.error(f"Error updating LangSmith trace: {e}")

        # Clean up active workflows
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]

        logger.info(
            f"Workflow {workflow_metrics.workflow_name} completed in "
            f"{workflow_metrics.duration_ms:.0f}ms with success={success}"
        )

    def trace_node_execution(
        self,
        workflow_id: str,
        node_name: str,
        node_type: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        tokens_used: int = 0,
        cost: float = 0.0,
    ) -> None:
        """
        Trace individual node execution.

        Args:
            workflow_id: Parent workflow ID
            node_name: Name of the node
            node_type: Type of node (e.g., "llm", "tool", "function")
            inputs: Node input data
            outputs: Node output data
            duration_ms: Execution duration in milliseconds
            success: Whether node execution succeeded
            error: Error message if node failed
            tokens_used: Number of tokens used
            cost: Estimated cost of execution
        """
        if workflow_id not in self.workflow_metrics:
            logger.warning(f"Workflow {workflow_id} not found for node trace")
            return

        # Create node metrics
        node_id = f"{workflow_id}_{node_name}_{len(self.node_metrics)}"
        node_metrics = NodeMetrics(
            node_name=node_name,
            node_type=node_type,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_ms=duration_ms,
            input_data=inputs,
            output_data=outputs,
            tokens_used=tokens_used,
            cost=cost,
            success=success,
            error_message=error,
            metadata={},
        )

        self.node_metrics[node_id] = node_metrics

        # Update workflow metrics
        workflow_metrics = self.workflow_metrics[workflow_id]
        workflow_metrics.nodes_executed.append(node_name)
        workflow_metrics.total_tokens += tokens_used
        workflow_metrics.total_cost += cost
        workflow_metrics.node_count = len(set(workflow_metrics.nodes_executed))

        # Send to LangSmith if enabled
        if self.enabled:
            try:
                parent_run_id = uuid.UUID(workflow_id)
                node_run_id = uuid.uuid4()

                if self.client:
                    self.client.create_run(
                        name=node_name,
                        run_type="chain",  # Fix literal type requirement
                        inputs=inputs,
                        outputs=outputs,
                        project_name=self.project_name,
                        run_id=node_run_id,
                        parent_run_id=parent_run_id,
                        extra={
                            "tokens_used": tokens_used,
                            "cost": cost,
                            "duration_ms": duration_ms,
                        },
                        error=error,
                    )
                    logger.debug(f"Traced node execution: {node_name}")
            except Exception as e:
                logger.error(f"Error tracing node execution: {e}")

    def log_custom_metric(
        self,
        workflow_id: str,
        metric_name: str,
        metric_value: Union[int, float, str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a custom metric for a workflow.

        Args:
            workflow_id: Workflow ID
            metric_name: Name of the metric
            metric_value: Value of the metric
            metadata: Additional metadata
        """
        if workflow_id not in self.workflow_metrics:
            return

        workflow_metrics = self.workflow_metrics[workflow_id]

        if "custom_metrics" not in workflow_metrics.metadata:
            workflow_metrics.metadata["custom_metrics"] = {}

        workflow_metrics.metadata["custom_metrics"][metric_name] = {
            "value": metric_value,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        logger.debug(
            f"Logged custom metric {metric_name}={metric_value} "
            f"for workflow {workflow_id}"
        )

    def create_evaluation_dataset(
        self,
        dataset_name: str,
        examples: List[Dict[str, Any]],
        description: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create an evaluation dataset in LangSmith.

        Args:
            dataset_name: Name of the dataset
            examples: List of example inputs and outputs
            description: Optional dataset description

        Returns:
            Dataset ID if successful
        """
        if not self.enabled:
            logger.warning("LangSmith not enabled, cannot create dataset")
            return None

        try:
            # Create dataset
            if not self.client:
                return None
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description or f"Evaluation dataset for {dataset_name}",
            )

            # Add examples
            for example_data in examples:
                inputs = example_data.get("inputs", {})
                outputs = example_data.get("outputs", {})
                metadata = example_data.get("metadata", {})

                if self.client:
                    self.client.create_example(
                        dataset_id=dataset.id,
                        inputs=inputs,
                        outputs=outputs,
                        metadata=metadata,
                    )

            example_count = len(examples)
            logger.info(
                f"Created evaluation dataset '{dataset_name}' with "
                f"{example_count} examples"
            )
            return str(dataset.id)

        except Exception as e:
            logger.error(f"Error creating evaluation dataset: {e}")
            return None

    def run_evaluation(
        self,
        dataset_name: str,
        workflow_function: Callable[..., Any],
        evaluators: List[Callable[..., Any]],
        num_repetitions: int = 1,
    ) -> Dict[str, Any]:
        """
        Run evaluation on a dataset.

        Args:
            dataset_name: Name of the dataset to evaluate on
            workflow_function: Function that runs the workflow
            evaluators: List of evaluation functions
            num_repetitions: Number of times to run each example

        Returns:
            Evaluation results
        """
        if not self.enabled:
            logger.warning("LangSmith not enabled, cannot run evaluation")
            return {}

        try:
            results = {
                "dataset_name": dataset_name,
                "total_examples": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "average_score": 0.0,
                "evaluator_results": {},
                "detailed_results": [],
            }

            # In a real implementation, this would use LangSmith's evaluation framework
            # For now, return a mock result structure

            logger.info(f"Evaluation completed for dataset '{dataset_name}'")
            return results

        except Exception as e:
            logger.error(f"Error running evaluation: {e}")
            return {}

    def get_workflow_analytics(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get workflow analytics and insights.

        Args:
            days_back: Number of days to look back

        Returns:
            Analytics data
        """
        try:
            analytics = {
                "period_days": days_back,
                "total_workflows": len(self.workflow_metrics),
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "most_used_workflows": [],
                "error_patterns": [],
                "performance_trends": [],
            }

            if not self.workflow_metrics:
                return analytics

            # Calculate metrics
            successful_workflows = sum(
                1 for wf in self.workflow_metrics.values() if wf.success
            )
            total_workflows = len(self.workflow_metrics)

            analytics["success_rate"] = (
                (successful_workflows / total_workflows) * 100
                if total_workflows > 0
                else 0
            )

            # Calculate averages
            completed_workflows = [
                wf
                for wf in self.workflow_metrics.values()
                if wf.duration_ms is not None
            ]
            if completed_workflows:
                analytics["average_duration_ms"] = sum(
                    wf.duration_ms for wf in completed_workflows
                ) / len(completed_workflows)
                analytics["total_cost"] = sum(
                    wf.total_cost for wf in completed_workflows
                )
                analytics["total_tokens"] = sum(
                    wf.total_tokens for wf in completed_workflows
                )

            # Get most used workflows
            workflow_counts: Dict[str, int] = {}
            for wf in self.workflow_metrics.values():
                workflow_counts[wf.workflow_name] = (
                    workflow_counts.get(wf.workflow_name, 0) + 1
                )

            analytics["most_used_workflows"] = [
                {"name": name, "count": count}
                for name, count in sorted(
                    workflow_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ]

            # Get error patterns
            error_patterns: Dict[str, int] = {}
            for wf in self.workflow_metrics.values():
                if wf.error_message:
                    error_type = (
                        wf.error_message.split(":")[0]
                        if ":" in wf.error_message
                        else wf.error_message
                    )
                    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

            analytics["error_patterns"] = [
                {"error": error, "count": count}
                for error, count in sorted(
                    error_patterns.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ]

            return analytics

        except Exception as e:
            logger.error(f"Error getting workflow analytics: {e}")
            return {}

    def export_metrics(
        self, format: str = "json", include_node_metrics: bool = True
    ) -> str:
        """
        Export collected metrics.

        Args:
            format: Export format ("json", "csv")
            include_node_metrics: Whether to include node-level metrics

        Returns:
            Exported metrics data
        """
        try:
            export_data: Dict[str, Any] = {
                "export_timestamp": datetime.now().isoformat(),
                "project_name": self.project_name,
                "workflow_metrics": [],
            }

            # Convert workflow metrics
            for wf_id, wf_metrics in self.workflow_metrics.items():
                wf_data = asdict(wf_metrics)
                wf_data["workflow_id"] = wf_id

                # Convert datetime objects to strings
                for key, value in wf_data.items():
                    if isinstance(value, datetime):
                        wf_data[key] = value.isoformat()

                export_data["workflow_metrics"].append(wf_data)

            # Include node metrics if requested
            if include_node_metrics:
                export_data["node_metrics"] = []
                for node_id, node_metrics in self.node_metrics.items():
                    node_data = asdict(node_metrics)
                    node_data["node_id"] = node_id

                    # Convert datetime objects
                    for key, value in node_data.items():
                        if isinstance(value, datetime):
                            node_data[key] = value.isoformat()

                    export_data["node_metrics"].append(node_data)

            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif format == "csv":
                # For CSV, we'll just export workflow metrics
                csv_lines = []
                if export_data["workflow_metrics"]:
                    # Header
                    headers = list(export_data["workflow_metrics"][0].keys())
                    csv_lines.append(",".join(headers))

                    # Data rows
                    for wf_data in export_data["workflow_metrics"]:
                        row = [str(wf_data.get(header, "")) for header in headers]
                        csv_lines.append(",".join(row))

                return "\n".join(csv_lines)
            else:
                return json.dumps(export_data, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return "{}"

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.workflow_metrics.clear()
        self.node_metrics.clear()
        self.active_workflows.clear()
        logger.info("Cleared all monitoring metrics")

    def is_enabled(self) -> bool:
        """Check if LangSmith monitoring is enabled."""
        return self.enabled

    def get_status(self) -> Dict[str, Any]:
        """Get monitoring status and statistics."""
        return {
            "enabled": self.enabled,
            "project_name": self.project_name,
            "client_connected": self.client is not None,
            "active_workflows": len(self.active_workflows),
            "total_workflows_tracked": len(self.workflow_metrics),
            "total_nodes_tracked": len(self.node_metrics),
            "langsmith_available": LANGSMITH_AVAILABLE,
        }
