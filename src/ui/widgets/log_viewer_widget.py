"""
Native log viewer widget for monitoring application logs.

This widget provides log viewing capabilities with filtering and search
using native Qt components like QTextBrowser for efficient text display.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for filtering."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogViewerWidget(QWidget):
    """
    Native log viewer widget for displaying application logs.

    Features:
    - Real-time log display
    - Log level filtering
    - Search functionality
    - Auto-scroll option
    - Color-coded log levels
    - Export capabilities
    """

    # Signals
    log_entry_selected = Signal(dict)

    def __init__(self, parent: Optional["QWidget"] = None):
        """
        Initialize the log viewer widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._log_entries: List[Dict[str, Any]] = []
        self._filtered_entries: List[Dict[str, Any]] = []
        self._max_entries = 1000
        self._auto_scroll = True
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header with controls
        self._create_header_controls(layout)

        # Main log display
        self._create_log_display(layout)

        # Initialize with some sample logs
        self._add_initial_logs()

    def _create_header_controls(self, parent_layout: QVBoxLayout) -> None:
        """Create header controls for filtering and search."""
        # Title
        title_label = QLabel("System Logs")
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
        parent_layout.addWidget(title_label)

        # Controls row 1: Search and level filter
        controls1_layout = QHBoxLayout()

        # Search box
        search_label = QLabel("Search:")
        controls1_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #2196f3;
            }
        """
        )
        self.search_input.textChanged.connect(self._apply_filters)
        controls1_layout.addWidget(self.search_input, 1)

        # Log level filter
        level_label = QLabel("Level:")
        controls1_layout.addWidget(level_label)

        self.level_filter = QComboBox()
        self.level_filter.addItems(
            ["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        self.level_filter.setStyleSheet(
            """
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """
        )
        self.level_filter.currentTextChanged.connect(self._apply_filters)
        controls1_layout.addWidget(self.level_filter)

        parent_layout.addLayout(controls1_layout)

        # Controls row 2: Auto-scroll and actions
        controls2_layout = QHBoxLayout()

        # Auto-scroll checkbox
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.toggled.connect(self._set_auto_scroll)
        controls2_layout.addWidget(self.auto_scroll_checkbox)

        controls2_layout.addStretch()

        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:pressed {
                background-color: #ef6c00;
            }
        """
        )
        self.clear_button.clicked.connect(self.clear_logs)
        controls2_layout.addWidget(self.clear_button)

        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """
        )
        self.export_button.clicked.connect(self._export_logs)
        controls2_layout.addWidget(self.export_button)

        parent_layout.addLayout(controls2_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("QFrame { color: #cccccc; }")
        parent_layout.addWidget(line)

    def _create_log_display(self, parent_layout: QVBoxLayout) -> None:
        """Create the main log display area."""
        self.log_display = QTextBrowser()
        self.log_display.setStyleSheet(
            """
            QTextBrowser {
                border: 1px solid #cccccc;
                border-radius: 8px;
                background-color: #fafafa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
                padding: 10px;
            }
        """
        )

        # Set monospace font for better log formatting
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_display.setFont(font)

        parent_layout.addWidget(self.log_display, 1)

    def _setup_timer(self) -> None:
        """Setup timer for simulated log updates."""
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self._add_mock_log)
        self.log_timer.start(8000)  # Every 8 seconds

    def _add_initial_logs(self) -> None:
        """Add initial log entries for demonstration."""
        initial_logs = [
            {
                "level": "INFO",
                "timestamp": datetime.now(),
                "message": "RS Personal Agent logging system initialized",
                "component": "System",
                "details": {},
            },
            {
                "level": "DEBUG",
                "timestamp": datetime.now(),
                "message": "Database connection pool created with 5 connections",
                "component": "Database",
                "details": {"pool_size": 5},
            },
            {
                "level": "INFO",
                "timestamp": datetime.now(),
                "message": "Reimbursement agent successfully loaded",
                "component": "AgentManager",
                "details": {"agent": "ReimbursementAgent"},
            },
            {
                "level": "WARNING",
                "timestamp": datetime.now(),
                "message": "LLM response time slower than expected (3.2s)",
                "component": "LLMManager",
                "details": {"response_time": 3.2, "threshold": 2.0},
            },
        ]

        for log_entry in initial_logs:
            self._add_log_entry_internal(log_entry)

    def add_log_entry(
        self,
        level: str,
        message: str,
        component: str = "System",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a new log entry.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            component: Component that generated the log
            details: Optional additional details
        """
        log_entry = {
            "level": level.upper(),
            "timestamp": datetime.now(),
            "message": message,
            "component": component,
            "details": details or {},
        }

        self._add_log_entry_internal(log_entry)

    def _add_log_entry_internal(self, log_entry: Dict[str, Any]) -> None:
        """Internal method to add log entry."""
        self._log_entries.append(log_entry)

        # Limit entries to prevent memory issues
        if len(self._log_entries) > self._max_entries:
            self._log_entries.pop(0)

        # Apply current filters and update display
        self._apply_filters()

        logger.debug(f"Added log entry: {log_entry['level']} - {log_entry['message']}")

    def _apply_filters(self) -> None:
        """Apply current filters and update display."""
        search_text = self.search_input.text().lower()
        level_filter = self.level_filter.currentText()

        # Filter entries
        filtered_entries = []
        for entry in self._log_entries:
            # Level filter
            if level_filter != "All" and entry["level"] != level_filter:
                continue

            # Search filter
            if search_text and search_text not in entry["message"].lower():
                continue

            filtered_entries.append(entry)

        self._filtered_entries = filtered_entries
        self._update_display()

    def _update_display(self) -> None:
        """Update the log display with filtered entries."""
        self.log_display.clear()

        for entry in self._filtered_entries:
            self._append_log_entry_to_display(entry)

        # Auto-scroll to bottom if enabled
        if self._auto_scroll:
            self.log_display.moveCursor(QTextCursor.MoveOperation.End)

    def _append_log_entry_to_display(self, entry: Dict[str, Any]) -> None:
        """Append a single log entry to the display."""
        timestamp_str = entry["timestamp"].strftime("%H:%M:%S.%f")[:-3]
        level = entry["level"]
        component = entry["component"]
        message = entry["message"]

        # Color based on log level
        color = self._get_level_color(level)

        # Format log line
        log_line = f"[{timestamp_str}] {level:8} [{component}] {message}"

        # Set color and append
        self.log_display.setTextColor(QColor(color))
        self.log_display.append(log_line)

    def _get_level_color(self, level: str) -> str:
        """Get color for log level."""
        colors = {
            "DEBUG": "#666666",
            "INFO": "#2196f3",
            "WARNING": "#ff9800",
            "ERROR": "#f44336",
            "CRITICAL": "#9c27b0",
        }
        return colors.get(level, "#333333")

    def _set_auto_scroll(self, enabled: bool) -> None:
        """Set auto-scroll behavior."""
        self._auto_scroll = enabled
        logger.debug(f"Auto-scroll {'enabled' if enabled else 'disabled'}")

    def _add_mock_log(self) -> None:
        """Add mock log entry for demonstration."""
        import random

        mock_logs = [
            ("DEBUG", "Email processing workflow initiated", "ReimbursementAgent"),
            (
                "INFO",
                "Successfully extracted 2 expense items from email",
                "EmailProcessor",
            ),
            ("WARNING", "Gmail API rate limit approaching (80% used)", "GmailService"),
            ("ERROR", "Failed to parse expense amount from email", "LLMProcessor"),
            ("INFO", "Database backup completed successfully", "Database"),
            ("DEBUG", "Cache hit for LLM prompt (response time: 0.1s)", "LLMCache"),
            ("INFO", "User exported reimbursement report as PDF", "ReportGenerator"),
        ]

        level, message, component = random.choice(mock_logs)
        self.add_log_entry(level, message, component)

    def clear_logs(self) -> None:
        """Clear all log entries."""
        self._log_entries.clear()
        self._filtered_entries.clear()
        self.log_display.clear()

        logger.info("Log viewer cleared by user")

        # Add system log entry for the clear action
        self.add_log_entry("INFO", "Log viewer cleared by user", "LogViewer")

    def _export_logs(self) -> None:
        """Export logs to file (placeholder implementation)."""
        from PySide6.QtWidgets import QMessageBox

        # This would open a file dialog in a real implementation
        QMessageBox.information(
            self,
            "Export Logs",
            f"Would export {len(self._filtered_entries)} log entries to file.\n"
            "(File dialog implementation pending)",
        )

        logger.info(f"Log export requested - {len(self._filtered_entries)} entries")
        self.add_log_entry(
            "INFO",
            f"Log export requested - {len(self._filtered_entries)} entries",
            "LogViewer",
        )

    def get_log_entries(self) -> List[Dict[str, Any]]:
        """
        Get all log entries.

        Returns:
            List of log entry dictionaries
        """
        return self._log_entries.copy()

    def get_filtered_entries(self) -> List[Dict[str, Any]]:
        """
        Get currently filtered log entries.

        Returns:
            List of filtered log entry dictionaries
        """
        return self._filtered_entries.copy()

    def set_log_level_filter(self, level: str) -> None:
        """
        Set the log level filter programmatically.

        Args:
            level: Log level to filter by ("All", "DEBUG", "INFO", etc.)
        """
        index = self.level_filter.findText(level)
        if index >= 0:
            self.level_filter.setCurrentIndex(index)

    def search_logs(self, search_term: str) -> None:
        """
        Search logs programmatically.

        Args:
            search_term: Term to search for
        """
        self.search_input.setText(search_term)

    def start_log_monitoring(self) -> None:
        """Start the log monitoring timer."""
        if not self.log_timer.isActive():
            self.log_timer.start(8000)
            logger.info("Log monitoring started")

    def stop_log_monitoring(self) -> None:
        """Stop the log monitoring timer."""
        if self.log_timer.isActive():
            self.log_timer.stop()
            logger.info("Log monitoring stopped")
