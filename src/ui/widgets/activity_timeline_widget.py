"""
Activity timeline widget for monitoring agent activities.

This widget provides a chronological view of agent activities and system events
using native Qt components with timestamped entries and status indicators.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class ActivityType(Enum):
    """Types of activities for the timeline."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    TASK_COMPLETE = "task_complete"
    LLM_REQUEST = "llm_request"
    SYSTEM_EVENT = "system_event"


class ActivityTimelineWidget(QWidget):
    """
    Activity timeline widget for displaying chronological events.

    Features:
    - Real-time activity updates
    - Color-coded event types
    - Timestamped entries
    - Auto-scroll to latest events
    - Activity filtering
    """

    # Signals
    activity_selected = Signal(dict)

    def __init__(self, parent: Optional["QWidget"] = None):
        """
        Initialize the activity timeline widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._activities: List[Dict[str, Any]] = []
        self._max_activities = 100  # Limit to prevent memory issues
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header with controls
        self._create_header(layout)

        # Activity list
        self._create_activity_list(layout)

    def _create_header(self, parent_layout: QVBoxLayout) -> None:
        """Create header with title and controls."""
        header_layout = QHBoxLayout()

        # Title
        title_label = QLabel("Activity Timeline")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                padding: 5px 0;
            }
        """
        )
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """
        )
        self.clear_button.clicked.connect(self.clear_activities)
        header_layout.addWidget(self.clear_button)

        parent_layout.addLayout(header_layout)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("QFrame { color: #cccccc; }")
        parent_layout.addWidget(line)

    def _create_activity_list(self, parent_layout: QVBoxLayout) -> None:
        """Create the activity list widget."""
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 8px;
                background-color: #fafafa;
                alternate-background-color: #f0f0f0;
                selection-background-color: #e3f2fd;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eeeeee;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
                border-radius: 4px;
            }
        """
        )

        self.activity_list.setAlternatingRowColors(True)
        self.activity_list.itemClicked.connect(self._on_activity_selected)

        parent_layout.addWidget(self.activity_list)

        # Add some initial mock activities
        self._add_initial_activities()

    def _setup_timer(self) -> None:
        """Setup timer for simulated activity updates."""
        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self._add_mock_activity)
        # Start with longer intervals for demonstration
        self.activity_timer.start(10000)  # Every 10 seconds

    def _add_initial_activities(self) -> None:
        """Add some initial activities for demonstration."""
        # Create activities with explicit calls to avoid type issues
        self.add_activity(
            ActivityType.SYSTEM_EVENT,
            "RS Personal Agent started successfully",
            {"component": "System", "status": "Started"},
        )
        self.add_activity(
            ActivityType.AGENT_START,
            "Reimbursement Agent initialized",
            {"agent": "ReimbursementAgent", "status": "Ready"},
        )
        self.add_activity(
            ActivityType.INFO,
            "Database connection established",
            {"database": "sqlite", "connection": "success"},
        )
        self.add_activity(
            ActivityType.SUCCESS,
            "LLM service connected (Llama 4 Scout)",
            {"service": "Ollama", "model": "llama4:scout"},
        )

    def add_activity(
        self,
        activity_type: ActivityType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a new activity to the timeline.

        Args:
            activity_type: Type of activity
            message: Activity message
            details: Optional additional details
        """
        activity = {
            "type": activity_type,
            "message": message,
            "timestamp": datetime.now(),
            "details": details or {},
        }

        self._activities.append(activity)

        # Limit the number of activities
        if len(self._activities) > self._max_activities:
            self._activities.pop(0)

        self._add_activity_item(activity)

        # Auto-scroll to bottom (latest activity)
        self.activity_list.scrollToBottom()

        logger.debug(f"Added activity: {activity_type.value} - {message}")

    def _add_activity_item(self, activity: Dict[str, Any]) -> None:
        """Add activity item to the list widget."""
        item = QListWidgetItem()

        # Format timestamp
        timestamp_str = activity["timestamp"].strftime("%H:%M:%S")

        # Create formatted text with colors
        activity_type = activity["type"]
        icon_char = self._get_activity_icon(activity_type)

        item.setText(f"[{timestamp_str}] {icon_char} {activity['message']}")
        item.setData(Qt.ItemDataRole.UserRole, activity)

        # Set item colors based on activity type
        if activity_type == ActivityType.ERROR:
            item.setBackground(QBrush("#ffebee"))
        elif activity_type == ActivityType.WARNING:
            item.setBackground(QBrush("#fff3e0"))
        elif activity_type == ActivityType.SUCCESS:
            item.setBackground(QBrush("#e8f5e8"))
        elif activity_type == ActivityType.AGENT_START:
            item.setBackground(QBrush("#e3f2fd"))

        self.activity_list.addItem(item)

    def _get_activity_icon(self, activity_type: ActivityType) -> str:
        """Get icon character for activity type."""
        icons = {
            ActivityType.INFO: "ℹ️",
            ActivityType.SUCCESS: "✅",
            ActivityType.WARNING: "⚠️",
            ActivityType.ERROR: "❌",
            ActivityType.AGENT_START: "🚀",
            ActivityType.AGENT_STOP: "⏹️",
            ActivityType.TASK_COMPLETE: "✔️",
            ActivityType.LLM_REQUEST: "🧠",
            ActivityType.SYSTEM_EVENT: "⚙️",
        }
        return icons.get(activity_type, "•")

    def _get_activity_color(self, activity_type: ActivityType) -> str:
        """Get color for activity type."""
        colors = {
            ActivityType.INFO: "#2196f3",
            ActivityType.SUCCESS: "#4caf50",
            ActivityType.WARNING: "#ff9800",
            ActivityType.ERROR: "#f44336",
            ActivityType.AGENT_START: "#9c27b0",
            ActivityType.AGENT_STOP: "#607d8b",
            ActivityType.TASK_COMPLETE: "#4caf50",
            ActivityType.LLM_REQUEST: "#795548",
            ActivityType.SYSTEM_EVENT: "#607d8b",
        }
        return colors.get(activity_type, "#333333")

    def _on_activity_selected(self, item: QListWidgetItem) -> None:
        """Handle activity item selection."""
        activity = item.data(Qt.ItemDataRole.UserRole)
        if activity:
            self.activity_selected.emit(activity)
            logger.debug(f"Activity selected: {activity['message']}")

    def _add_mock_activity(self) -> None:
        """Add mock activity for demonstration."""
        import random

        mock_activities = [
            (ActivityType.LLM_REQUEST, "Processing email for expense detection"),
            (ActivityType.TASK_COMPLETE, "Email scan completed - 3 expenses found"),
            (ActivityType.SUCCESS, "Reimbursement report generated"),
            (ActivityType.INFO, "System health check passed"),
            (ActivityType.WARNING, "High CPU usage detected"),
            (ActivityType.AGENT_START, "Background task scheduler started"),
        ]

        activity_type, message = random.choice(mock_activities)
        self.add_activity(activity_type, message)

    def clear_activities(self) -> None:
        """Clear all activities from the timeline."""
        self._activities.clear()
        self.activity_list.clear()
        logger.info("Activity timeline cleared")

        # Add system event for clearing
        self.add_activity(
            ActivityType.SYSTEM_EVENT, "Activity timeline cleared by user"
        )

    def get_activities(self) -> List[Dict[str, Any]]:
        """
        Get all activities.

        Returns:
            List of activity dictionaries
        """
        return self._activities.copy()

    def filter_activities(self, activity_type: Optional[ActivityType] = None) -> None:
        """
        Filter activities by type (future enhancement).

        Args:
            activity_type: Activity type to filter by, None for all
        """
        # This could be implemented to filter the display
        # For now, just log the request
        if activity_type:
            logger.info(f"Filter requested for activity type: {activity_type.value}")
        else:
            logger.info("Filter cleared - showing all activities")

    def start_activity_monitoring(self) -> None:
        """Start the activity monitoring timer."""
        if not self.activity_timer.isActive():
            self.activity_timer.start(10000)
            logger.info("Activity monitoring started")

    def stop_activity_monitoring(self) -> None:
        """Stop the activity monitoring timer."""
        if self.activity_timer.isActive():
            self.activity_timer.stop()
            logger.info("Activity monitoring stopped")
