"""
Status indicator widget for displaying service status with colored dots.

This module provides a reusable Qt widget for showing status indicators
with colored status dots and text labels.
"""

from enum import Enum
from typing import Optional

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ServiceStatus(Enum):
    """Enum for different service status states."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"
    IDLE = "idle"
    DISABLED = "disabled"


class StatusDot(QWidget):
    """
    A circular status indicator dot with different colors.

    This widget displays a colored dot that can represent different
    status states with appropriate colors.
    """

    def __init__(
        self,
        status: ServiceStatus = ServiceStatus.UNKNOWN,
        size: int = 12,
    ):
        """
        Initialize the status dot.

        Args:
            status: The initial status to display
            size: Size of the dot in pixels
        """
        super().__init__()
        self._status = status
        self._size = size
        self.setFixedSize(size, size)

        # Status color mapping
        self._status_colors = {
            ServiceStatus.CONNECTED: QColor(34, 197, 94),  # Green
            ServiceStatus.RUNNING: QColor(34, 197, 94),  # Green
            ServiceStatus.IDLE: QColor(251, 191, 36),  # Yellow/Amber
            ServiceStatus.DISCONNECTED: QColor(239, 68, 68),  # Red
            ServiceStatus.ERROR: QColor(239, 68, 68),  # Red
            ServiceStatus.DISABLED: QColor(156, 163, 175),  # Gray
            ServiceStatus.UNKNOWN: QColor(156, 163, 175),  # Gray
        }

    def set_status(self, status: ServiceStatus) -> None:
        """
        Update the status and repaint the dot.

        Args:
            status: New status to display
        """
        self._status = status
        self.update()

    def get_status(self) -> ServiceStatus:
        """
        Get the current status.

        Returns:
            Current status
        """
        return self._status

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Paint the status dot.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get color for current status
        color = self._status_colors.get(
            self._status, self._status_colors[ServiceStatus.UNKNOWN]
        )

        # Draw the dot
        painter.setPen(QPen(color.darker(120), 1))
        painter.setBrush(QBrush(color))

        # Draw circle with small margin
        margin = 2
        painter.drawEllipse(
            margin, margin, self._size - 2 * margin, self._size - 2 * margin
        )


class StatusIndicatorWidget(QWidget):
    """
    A complete status indicator with dot and text label.

    This widget combines a status dot with a text label to show
    service status information.
    """

    # Signal emitted when status changes
    status_changed = Signal(str, ServiceStatus)

    def __init__(
        self,
        service_name: str,
        initial_status: ServiceStatus = ServiceStatus.UNKNOWN,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the status indicator.

        Args:
            service_name: Name of the service to display
            initial_status: Initial status state
            parent: Parent widget
        """
        super().__init__(parent)
        self._service_name = service_name
        self._status = initial_status

        self._setup_ui()
        self._setup_update_timer()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Status dot
        self._status_dot = StatusDot(self._status)
        layout.addWidget(self._status_dot)

        # Service name label
        self._name_label = QLabel(self._service_name)
        self._name_label.setStyleSheet(
            """
            QLabel {
                color: #374151;
                font-weight: 500;
                font-size: 14px;
            }
        """
        )
        layout.addWidget(self._name_label)

        # Status text label
        self._status_label = QLabel(self._get_status_text())
        self._status_label.setStyleSheet(
            """
            QLabel {
                color: #6B7280;
                font-size: 12px;
            }
        """
        )
        layout.addWidget(self._status_label)

        layout.addStretch()

    def _setup_update_timer(self) -> None:
        """Set up timer for periodic status updates."""
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_status_display)
        self._update_timer.start(5000)  # Update every 5 seconds

    def _get_status_text(self) -> str:
        """
        Get human-readable status text.

        Returns:
            Status text string
        """
        status_text = {
            ServiceStatus.CONNECTED: "Connected",
            ServiceStatus.RUNNING: "Running",
            ServiceStatus.IDLE: "Idle",
            ServiceStatus.DISCONNECTED: "Disconnected",
            ServiceStatus.ERROR: "Error",
            ServiceStatus.DISABLED: "Disabled",
            ServiceStatus.UNKNOWN: "Unknown",
        }
        return status_text.get(self._status, "Unknown")

    def _update_status_display(self) -> None:
        """Update the status display with current information."""
        self._status_label.setText(self._get_status_text())

        # Update status label color based on status
        colors = {
            ServiceStatus.CONNECTED: "#10B981",  # Green
            ServiceStatus.RUNNING: "#10B981",  # Green
            ServiceStatus.IDLE: "#F59E0B",  # Amber
            ServiceStatus.DISCONNECTED: "#EF4444",  # Red
            ServiceStatus.ERROR: "#EF4444",  # Red
            ServiceStatus.DISABLED: "#9CA3AF",  # Gray
            ServiceStatus.UNKNOWN: "#9CA3AF",  # Gray
        }

        color = colors.get(self._status, "#9CA3AF")
        self._status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 12px;
                font-weight: 500;
            }}
        """
        )

    def set_status(self, status: ServiceStatus) -> None:
        """
        Update the service status.

        Args:
            status: New status to display
        """
        old_status = self._status
        self._status = status

        # Update the status dot
        self._status_dot.set_status(status)

        # Update the display
        self._update_status_display()

        # Emit signal if status changed
        if old_status != status:
            self.status_changed.emit(self._service_name, status)

    def get_status(self) -> ServiceStatus:
        """
        Get the current status.

        Returns:
            Current service status
        """
        return self._status

    def get_service_name(self) -> str:
        """
        Get the service name.

        Returns:
            Service name
        """
        return self._service_name

    def set_service_name(self, name: str) -> None:
        """
        Update the service name.

        Args:
            name: New service name
        """
        self._service_name = name
        self._name_label.setText(name)

    def simulate_status_check(self) -> None:
        """
        Simulate a status check for demonstration purposes.

        This method can be called to simulate checking the actual
        service status. In a real implementation, this would
        connect to the actual service.
        """
        # For now, just cycle through some statuses for demo
        import random

        statuses = [
            ServiceStatus.CONNECTED,
            ServiceStatus.DISCONNECTED,
            ServiceStatus.ERROR,
        ]
        self.set_status(random.choice(statuses))
