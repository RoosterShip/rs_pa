"""
Performance monitoring backend for system and application metrics.

This module provides comprehensive performance monitoring capabilities
including system resources, agent performance, and LLM response times.
"""

import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics being tracked."""

    SYSTEM_CPU = "system_cpu"
    SYSTEM_MEMORY = "system_memory"
    SYSTEM_DISK = "system_disk"
    AGENT_EXECUTION = "agent_execution"
    LLM_RESPONSE_TIME = "llm_response_time"
    LLM_TOKEN_USAGE = "llm_token_usage"
    DATABASE_QUERY = "database_query"
    API_REQUEST = "api_request"
    CUSTOM = "custom"


@dataclass
class MetricReading:
    """Individual metric reading."""

    timestamp: datetime
    metric_type: MetricType
    name: str
    value: float
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Performance statistics for a metric."""

    current: float
    average: float
    minimum: float
    maximum: float
    count: int
    trend: str  # "increasing", "decreasing", "stable"


class PerformanceMonitor(QObject):
    """
    Performance monitoring system for tracking various application metrics.

    Features:
    - Real-time system resource monitoring
    - Agent performance tracking
    - LLM response time analysis
    - Database query performance
    - Custom metric support
    - Historical data retention
    """

    # Signals for real-time updates
    metric_updated = Signal(MetricReading)
    stats_updated = Signal(str, PerformanceStats)  # metric_name, stats
    alert_triggered = Signal(str, str, float)  # metric_name, alert_type, value

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the performance monitor.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        # Metric storage (limited retention)
        self._metrics: Dict[str, "deque[MetricReading]"] = {}
        self._max_readings_per_metric = 1000
        self._retention_hours = 24

        # Performance statistics cache
        self._stats_cache: Dict[str, PerformanceStats] = {}
        self._stats_cache_timeout = 30  # seconds
        self._last_stats_update: Dict[str, datetime] = {}

        # Alert thresholds
        self._alert_thresholds: Dict[str, Dict[str, float]] = {
            "system_cpu": {"warning": 80.0, "critical": 95.0},
            "system_memory": {"warning": 80.0, "critical": 95.0},
            "llm_response_time": {"warning": 5.0, "critical": 10.0},
            "agent_execution_time": {"warning": 30.0, "critical": 60.0},
        }

        # Background monitoring
        self._monitoring_active = False
        self._monitoring_interval = 5.0  # seconds
        self._setup_monitoring_timer()

        # Thread safety
        self._lock = threading.Lock()

        logger.info("Performance monitor initialized")

    def _setup_monitoring_timer(self) -> None:
        """Setup timer for background monitoring."""
        self._monitoring_timer = QTimer(self)
        self._monitoring_timer.timeout.connect(self._collect_system_metrics)

    def start_monitoring(self) -> None:
        """Start background performance monitoring."""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._monitoring_timer.start(int(self._monitoring_interval * 1000))
            logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background performance monitoring."""
        if self._monitoring_active:
            self._monitoring_active = False
            self._monitoring_timer.stop()
            logger.info("Performance monitoring stopped")

    def record_metric(
        self,
        metric_type: MetricType,
        name: str,
        value: float,
        unit: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a performance metric.

        Args:
            metric_type: Type of metric
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            metadata: Additional metadata
        """
        reading = MetricReading(
            timestamp=datetime.now(),
            metric_type=metric_type,
            name=name,
            value=value,
            unit=unit,
            metadata=metadata or {},
        )

        with self._lock:
            # Initialize metric storage if needed
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self._max_readings_per_metric)

            # Add reading
            self._metrics[name].append(reading)

            # Cleanup old readings
            self._cleanup_old_readings(name)

        # Emit signals
        self.metric_updated.emit(reading)

        # Check for alerts
        self._check_alerts(name, value)

        # Invalidate stats cache for this metric
        if name in self._last_stats_update:
            del self._last_stats_update[name]

        logger.debug(f"Recorded metric: {name} = {value} {unit}")

    def _collect_system_metrics(self) -> None:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.record_metric(MetricType.SYSTEM_CPU, "system_cpu", cpu_percent, "%")

            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric(
                MetricType.SYSTEM_MEMORY,
                "system_memory",
                memory.percent,
                "%",
                {"available": memory.available, "total": memory.total},
            )

            # Disk usage for main drive
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric(
                MetricType.SYSTEM_DISK,
                "system_disk",
                disk_percent,
                "%",
                {"used": disk.used, "total": disk.total},
            )

        except Exception as error:
            logger.error(f"Error collecting system metrics: {error}")

    def _cleanup_old_readings(self, metric_name: str) -> None:
        """Remove readings older than retention period."""
        if metric_name not in self._metrics:
            return

        cutoff_time = datetime.now() - timedelta(hours=self._retention_hours)
        readings = self._metrics[metric_name]

        # Remove old readings (from left side of deque)
        while readings and readings[0].timestamp < cutoff_time:
            readings.popleft()

    def _check_alerts(self, metric_name: str, value: float) -> None:
        """Check if metric value triggers any alerts."""
        if metric_name in self._alert_thresholds:
            thresholds = self._alert_thresholds[metric_name]

            if value >= thresholds.get("critical", float("inf")):
                self.alert_triggered.emit(metric_name, "critical", value)
            elif value >= thresholds.get("warning", float("inf")):
                self.alert_triggered.emit(metric_name, "warning", value)

    def get_metric_stats(self, metric_name: str) -> Optional[PerformanceStats]:
        """
        Get performance statistics for a metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Performance statistics or None if metric not found
        """
        # Check cache first
        now = datetime.now()
        if (
            metric_name in self._stats_cache
            and metric_name in self._last_stats_update
            and (now - self._last_stats_update[metric_name]).seconds
            < self._stats_cache_timeout
        ):
            return self._stats_cache[metric_name]

        # Calculate fresh stats
        stats = self._calculate_stats(metric_name)
        if stats:
            self._stats_cache[metric_name] = stats
            self._last_stats_update[metric_name] = now

        return stats

    def _calculate_stats(self, metric_name: str) -> Optional[PerformanceStats]:
        """Calculate statistics for a metric."""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return None

        readings = list(self._metrics[metric_name])
        values = [r.value for r in readings]

        if not values:
            return None

        current = values[-1]
        average = sum(values) / len(values)
        minimum = min(values)
        maximum = max(values)
        count = len(values)

        # Calculate trend (simple comparison of recent vs older values)
        if len(values) >= 10:
            recent_avg = sum(values[-5:]) / 5
            older_avg = sum(values[:5]) / 5

            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        stats = PerformanceStats(
            current=current,
            average=average,
            minimum=minimum,
            maximum=maximum,
            count=count,
            trend=trend,
        )

        # Emit stats update signal
        self.stats_updated.emit(metric_name, stats)

        return stats

    def get_recent_readings(
        self, metric_name: str, minutes: int = 60
    ) -> List[MetricReading]:
        """
        Get recent readings for a metric.

        Args:
            metric_name: Name of the metric
            minutes: Number of minutes of history to return

        Returns:
            List of recent readings
        """
        if metric_name not in self._metrics:
            return []

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        readings = self._metrics[metric_name]

        return [r for r in readings if r.timestamp >= cutoff_time]

    def record_agent_execution(
        self, agent_name: str, duration: float, success: bool
    ) -> None:
        """
        Record agent execution metrics.

        Args:
            agent_name: Name of the agent
            duration: Execution duration in seconds
            success: Whether execution was successful
        """
        self.record_metric(
            MetricType.AGENT_EXECUTION,
            f"agent_execution_{agent_name}",
            duration,
            "seconds",
            {"agent": agent_name, "success": success},
        )

        # Also record overall execution time
        self.record_metric(
            MetricType.AGENT_EXECUTION,
            "agent_execution_time",
            duration,
            "seconds",
            {"agent": agent_name, "success": success},
        )

    def record_llm_request(
        self, model_name: str, response_time: float, token_count: Optional[int] = None
    ) -> None:
        """
        Record LLM request metrics.

        Args:
            model_name: Name of the LLM model
            response_time: Response time in seconds
            token_count: Number of tokens in response (optional)
        """
        self.record_metric(
            MetricType.LLM_RESPONSE_TIME,
            "llm_response_time",
            response_time,
            "seconds",
            {"model": model_name, "tokens": token_count},
        )

        if token_count is not None:
            self.record_metric(
                MetricType.LLM_TOKEN_USAGE,
                f"llm_tokens_{model_name}",
                token_count,
                "tokens",
                {"model": model_name},
            )

    def record_database_query(self, query_type: str, duration: float) -> None:
        """
        Record database query performance.

        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            duration: Query duration in seconds
        """
        self.record_metric(
            MetricType.DATABASE_QUERY,
            f"db_query_{query_type.lower()}",
            duration,
            "seconds",
            {"query_type": query_type},
        )

    def set_alert_threshold(
        self, metric_name: str, warning_threshold: float, critical_threshold: float
    ) -> None:
        """
        Set alert thresholds for a metric.

        Args:
            metric_name: Name of the metric
            warning_threshold: Warning threshold value
            critical_threshold: Critical threshold value
        """
        self._alert_thresholds[metric_name] = {
            "warning": warning_threshold,
            "critical": critical_threshold,
        }

        logger.info(
            f"Set alert thresholds for {metric_name}: "
            f"warning={warning_threshold}, critical={critical_threshold}"
        )

    def get_all_metric_names(self) -> List[str]:
        """
        Get all available metric names.

        Returns:
            List of metric names
        """
        return list(self._metrics.keys())

    def get_system_overview(self) -> Dict[str, Any]:
        """
        Get system performance overview.

        Returns:
            Dictionary with system overview metrics
        """
        overview: Dict[str, Any] = {
            "timestamp": datetime.now(),
            "metrics": {},
            "alerts": {"warning": 0, "critical": 0},
        }

        # Get current values for key system metrics
        key_metrics = [
            "system_cpu",
            "system_memory",
            "system_disk",
            "llm_response_time",
        ]

        for metric_name in key_metrics:
            stats = self.get_metric_stats(metric_name)
            if stats:
                overview["metrics"][metric_name] = {
                    "current": stats.current,
                    "average": stats.average,
                    "trend": stats.trend,
                }

                # Check alert levels
                if metric_name in self._alert_thresholds:
                    thresholds = self._alert_thresholds[metric_name]
                    if stats.current >= thresholds.get("critical", float("inf")):
                        overview["alerts"]["critical"] += 1
                    elif stats.current >= thresholds.get("warning", float("inf")):
                        overview["alerts"]["warning"] += 1

        return overview

    def clear_metrics(self, metric_name: Optional[str] = None) -> None:
        """
        Clear metric data.

        Args:
            metric_name: Specific metric to clear, or None to clear all
        """
        with self._lock:
            if metric_name:
                if metric_name in self._metrics:
                    self._metrics[metric_name].clear()
                    if metric_name in self._stats_cache:
                        del self._stats_cache[metric_name]
                    if metric_name in self._last_stats_update:
                        del self._last_stats_update[metric_name]
                    logger.info(f"Cleared metrics for: {metric_name}")
            else:
                self._metrics.clear()
                self._stats_cache.clear()
                self._last_stats_update.clear()
                logger.info("Cleared all metrics")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()

    return _performance_monitor
