"""
Connection status widget for displaying service connection states.

This module provides a custom Qt widget for showing connection
status with colored indicators and descriptive text.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)


class ConnectionStatusWidget(QWidget):
    """
    Custom widget for displaying connection status with visual indicators.

    This widget shows a colored status dot and descriptive text
    to indicate the connection state of various services.
    """

    # Signal emitted when status changes
    status_changed = Signal(str, str)  # service_name, new_status

    def __init__(
        self,
        service_name: str,
        initial_status: str = "disconnected",
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the connection status widget.

        Args:
            service_name: Name of the service (e.g., "Gmail", "Ollama")
            initial_status: Initial status ("connected", "disconnected", "error")
            parent: Parent widget
        """
        super().__init__(parent)

        self._service_name = service_name
        self._current_status = initial_status

        self._setup_ui()
        self._update_status_display()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        # Status indicator dot
        self._status_dot = QLabel("●")
        self._status_dot.setObjectName("statusDot")
        self._status_dot.setFixedSize(16, 16)
        self._status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_dot)

        # Service name label
        self._service_label = QLabel(self._service_name)
        self._service_label.setObjectName("serviceLabel")
        layout.addWidget(self._service_label)

        # Status text label
        self._status_label = QLabel()
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        # Add stretch to push content to left
        layout.addStretch()

        # Apply initial styling
        self._apply_styling()

    def set_status(self, status: str) -> None:
        """
        Set the connection status.

        Args:
            status: New status ("connected", "disconnected", "error", "connecting")
        """
        if status != self._current_status:
            self._current_status = status
            self._update_status_display()
            self.status_changed.emit(self._service_name, self._current_status)

    def get_status(self) -> str:
        """
        Get the current connection status.

        Returns:
            Current status string
        """
        return self._current_status

    def get_service_name(self) -> str:
        """
        Get the service name.

        Returns:
            Service name string
        """
        return self._service_name

    def _update_status_display(self) -> None:
        """Update the visual display based on current status."""
        status_info = self._get_status_info(self._current_status)

        # Update status text
        self._status_label.setText(status_info["text"])

        # Update dot color via stylesheet
        self._status_dot.setStyleSheet(
            f"""
            QLabel#statusDot {{
                color: {status_info['color']};
                font-size: 14px;
                font-weight: bold;
            }}
        """
        )

    def _get_status_info(self, status: str) -> dict[str, str]:
        """
        Get status information including color and text.

        Args:
            status: Status string

        Returns:
            Dictionary with color and text information
        """
        status_map = {
            "connected": {"color": "#22c55e", "text": "Connected"},  # Green
            "disconnected": {"color": "#6b7280", "text": "Disconnected"},  # Gray
            "error": {"color": "#ef4444", "text": "Error"},  # Red
            "connecting": {"color": "#f59e0b", "text": "Connecting..."},  # Orange
            "authenticating": {
                "color": "#8b5cf6",  # Purple
                "text": "Authenticating...",
            },
        }

        return status_map.get(status, {"color": "#6b7280", "text": "Unknown"})

    def _apply_styling(self) -> None:
        """Apply custom styling to the widget."""
        self.setStyleSheet(
            """
            /* Connection status widget */
            ConnectionStatusWidget {
                background-color: transparent;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 2px;
            }

            /* Service name label */
            #serviceLabel {
                font-size: 13px;
                font-weight: bold;
                color: #374151;
                min-width: 60px;
            }

            /* Status text label */
            #statusLabel {
                font-size: 12px;
                color: #6b7280;
                font-weight: 500;
            }
        """
        )

    def set_service_name(self, name: str) -> None:
        """
        Update the service name.

        Args:
            name: New service name
        """
        self._service_name = name
        self._service_label.setText(name)

    def is_connected(self) -> bool:
        """
        Check if the status indicates a connected state.

        Returns:
            True if status is "connected"
        """
        return self._current_status == "connected"

    def is_error(self) -> bool:
        """
        Check if the status indicates an error state.

        Returns:
            True if status is "error"
        """
        return self._current_status == "error"

    def reset_status(self) -> None:
        """Reset status to disconnected."""
        self.set_status("disconnected")
