"""
System metrics panel widget for real-time monitoring.

This widget provides system resource monitoring with native Qt components
including CPU usage, memory usage, and agent statistics.
"""

import logging
from typing import Any, Dict, Optional

import psutil
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class MetricsPanelWidget(QWidget):
    """
    System metrics panel widget for monitoring system resources and agent status.

    Features:
    - CPU and memory usage indicators
    - Active agents count display
    - Task success/failure rate tracking
    - LLM response time monitoring
    """

    # Signals for metric updates
    metrics_updated = Signal(dict)

    def __init__(self, parent: Optional["QWidget"] = None):
        """
        Initialize the metrics panel widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
        self._last_cpu_times = None

        # Initialize metrics data
        self._metrics_data = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "active_agents": 0,
            "success_rate": 100.0,
            "avg_response_time": 0.0,
        }

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # System Resources Group
        self._create_system_resources_group(layout)

        # Agent Status Group
        self._create_agent_status_group(layout)

        # Performance Group
        self._create_performance_group(layout)

        layout.addStretch()

    def _create_system_resources_group(self, parent_layout: QVBoxLayout) -> None:
        """Create system resources monitoring group."""
        group = QGroupBox("System Resources")
        group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )

        layout = QVBoxLayout(group)

        # CPU Usage
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU Usage:"))

        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.7 #FFC107, stop:1 #F44336);
                border-radius: 3px;
            }
        """
        )
        cpu_layout.addWidget(self.cpu_progress, 1)

        self.cpu_label = QLabel("0%")
        self.cpu_label.setMinimumWidth(40)
        self.cpu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cpu_layout.addWidget(self.cpu_label)

        layout.addLayout(cpu_layout)

        # Memory Usage
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Memory Usage:"))

        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setStyleSheet(self.cpu_progress.styleSheet())
        memory_layout.addWidget(self.memory_progress, 1)

        self.memory_label = QLabel("0%")
        self.memory_label.setMinimumWidth(40)
        self.memory_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        memory_layout.addWidget(self.memory_label)

        layout.addLayout(memory_layout)

        parent_layout.addWidget(group)

    def _create_agent_status_group(self, parent_layout: QVBoxLayout) -> None:
        """Create agent status monitoring group."""
        group = QGroupBox("Agent Status")
        group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )

        layout = QVBoxLayout(group)

        # Active Agents Count
        agents_layout = QHBoxLayout()
        agents_layout.addWidget(QLabel("Active Agents:"))

        self.agents_lcd = QLCDNumber(2)
        self.agents_lcd.setStyleSheet(
            """
            QLCDNumber {
                background-color: #2e2e2e;
                color: #00ff00;
                border: 1px solid #666666;
                border-radius: 4px;
            }
        """
        )
        self.agents_lcd.display(0)
        agents_layout.addWidget(self.agents_lcd)
        agents_layout.addStretch()

        layout.addLayout(agents_layout)

        # Success Rate
        success_layout = QHBoxLayout()
        success_layout.addWidget(QLabel("Success Rate:"))

        self.success_label = QLabel("100%")
        self.success_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                color: #4CAF50;
                font-size: 14px;
                padding: 5px;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                background-color: rgba(76, 175, 80, 0.1);
            }
        """
        )
        self.success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_layout.addWidget(self.success_label)
        success_layout.addStretch()

        layout.addLayout(success_layout)

        parent_layout.addWidget(group)

    def _create_performance_group(self, parent_layout: QVBoxLayout) -> None:
        """Create performance monitoring group."""
        group = QGroupBox("Performance")
        group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )

        layout = QVBoxLayout(group)

        # Average Response Time
        response_layout = QHBoxLayout()
        response_layout.addWidget(QLabel("Avg Response:"))

        self.response_label = QLabel("0.0s")
        self.response_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                color: #2196F3;
                font-size: 14px;
                padding: 5px;
                border: 1px solid #2196F3;
                border-radius: 4px;
                background-color: rgba(33, 150, 243, 0.1);
            }
        """
        )
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        response_layout.addWidget(self.response_label)
        response_layout.addStretch()

        layout.addLayout(response_layout)

        parent_layout.addWidget(group)

    def _setup_timer(self) -> None:
        """Setup the metrics update timer."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_metrics)
        self.update_timer.start(5000)  # Update every 5 seconds

        # Initial update
        self._update_metrics()

    def _update_metrics(self) -> None:
        """Update system metrics."""
        try:
            # Ensure _metrics_data is initialized
            if not hasattr(self, '_metrics_data') or self._metrics_data is None:
                self._metrics_data = {
                    "cpu_percent": 0.0,
                    "memory_percent": 0.0,
                    "active_agents": 0,
                    "success_rate": 100.0,
                    "avg_response_time": 0.0,
                }

            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Update metrics data
            self._metrics_data.update(
                {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                }
            )

            # Update UI
            self._update_ui_metrics()

            # Emit signal
            self.metrics_updated.emit(self._metrics_data.copy())

        except Exception as error:
            logger.error(f"Error updating system metrics: {error}")

    def _update_ui_metrics(self) -> None:
        """Update UI with current metrics."""
        cpu_percent = self._metrics_data["cpu_percent"]
        memory_percent = self._metrics_data["memory_percent"]

        # Update CPU
        self.cpu_progress.setValue(int(cpu_percent))
        self.cpu_label.setText(f"{cpu_percent:.1f}%")

        # Update Memory
        self.memory_progress.setValue(int(memory_percent))
        self.memory_label.setText(f"{memory_percent:.1f}%")

        # Update agents count (mock for now)
        self.agents_lcd.display(self._metrics_data["active_agents"])

        # Update success rate with color coding
        success_rate = self._metrics_data["success_rate"]
        if success_rate >= 90:
            color = "#4CAF50"  # Green
        elif success_rate >= 70:
            color = "#FFC107"  # Yellow
        else:
            color = "#F44336"  # Red

        self.success_label.setText(f"{success_rate:.1f}%")
        self.success_label.setStyleSheet(
            f"""
            QLabel {{
                font-weight: bold;
                color: {color};
                font-size: 14px;
                padding: 5px;
                border: 1px solid {color};
                border-radius: 4px;
                background-color: {color}33;
            }}
        """
        )

        # Update response time
        response_time = self._metrics_data["avg_response_time"]
        self.response_label.setText(f"{response_time:.2f}s")

    def update_agent_metrics(self, active_count: int, success_rate: float) -> None:
        """
        Update agent-specific metrics.

        Args:
            active_count: Number of active agents
            success_rate: Success rate percentage (0-100)
        """
        self._metrics_data.update(
            {
                "active_agents": active_count,
                "success_rate": success_rate,
            }
        )
        self._update_ui_metrics()

    def update_performance_metrics(self, avg_response_time: float) -> None:
        """
        Update performance metrics.

        Args:
            avg_response_time: Average response time in seconds
        """
        self._metrics_data["avg_response_time"] = avg_response_time
        self._update_ui_metrics()

    def get_metrics_data(self) -> Dict[str, Any]:
        """
        Get current metrics data.

        Returns:
            Dictionary containing current metrics
        """
        return self._metrics_data.copy()

    def start_monitoring(self) -> None:
        """Start the metrics monitoring timer."""
        if not self.update_timer.isActive():
            self.update_timer.start(5000)
            logger.info("Metrics monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the metrics monitoring timer."""
        if self.update_timer.isActive():
            self.update_timer.stop()
            logger.info("Metrics monitoring stopped")
