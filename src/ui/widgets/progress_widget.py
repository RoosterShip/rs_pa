"""
Progress widget for showing operation progress with status text.

This module provides a custom Qt widget that combines a progress bar
with status text for displaying operation progress.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class ProgressWidget(QWidget):
    """
    Custom progress widget with progress bar and status text.

    This widget provides a clean interface for showing operation progress
    with both visual progress indication and descriptive text.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the progress widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._is_active = False

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setObjectName("progressStatusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.hide()  # Hidden by default
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("progressBar")
        self._progress_bar.hide()  # Hidden by default
        layout.addWidget(self._progress_bar)

        # Apply styling
        self._apply_styling()

    def start_progress(
        self, status_text: str = "Processing...", progress: Optional[int] = None
    ) -> None:
        """
        Start showing progress with optional status text.

        Args:
            status_text: Text to display above progress bar
            progress: Specific progress value (0-100), or None for indeterminate
        """
        self._is_active = True

        # Set status text
        if status_text:
            self._status_label.setText(status_text)
            self._status_label.show()
        else:
            self._status_label.hide()

        # Configure progress bar
        if progress is not None:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(progress)
        else:
            # Indeterminate progress
            self._progress_bar.setRange(0, 0)

        self._progress_bar.show()

    def update_progress(self, progress: int, status_text: Optional[str] = None) -> None:
        """
        Update progress value and optional status text.

        Args:
            progress: Progress value (0-100)
            status_text: Optional new status text
        """
        if not self._is_active:
            return

        # Update progress bar
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(max(0, min(100, progress)))

        # Update status text if provided
        if status_text is not None:
            if status_text:
                self._status_label.setText(status_text)
                self._status_label.show()
            else:
                self._status_label.hide()

    def update_status(self, status_text: str) -> None:
        """
        Update only the status text without changing progress.

        Args:
            status_text: New status text
        """
        if not self._is_active:
            return

        if status_text:
            self._status_label.setText(status_text)
            self._status_label.show()
        else:
            self._status_label.hide()

    def stop_progress(self) -> None:
        """Stop and hide the progress display."""
        self._is_active = False
        self._progress_bar.hide()
        self._status_label.hide()

    def is_active(self) -> bool:
        """
        Check if progress widget is currently active.

        Returns:
            True if showing progress, False otherwise
        """
        return self._is_active

    def set_indeterminate(self) -> None:
        """Set progress bar to indeterminate mode."""
        if self._is_active:
            self._progress_bar.setRange(0, 0)

    def set_determinate(self, progress: int = 0) -> None:
        """
        Set progress bar to determinate mode.

        Args:
            progress: Initial progress value (0-100)
        """
        if self._is_active:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(max(0, min(100, progress)))

    def _apply_styling(self) -> None:
        """Apply custom styling to the progress widget."""
        self.setStyleSheet(
            """
            /* Progress status label */
            #progressStatusLabel {
                font-size: 12px;
                color: #4b5563;
                font-weight: 500;
                padding: 2px 0;
            }

            /* Progress bar styling */
            #progressBar {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: #f3f4f6;
                height: 16px;
                text-align: center;
            }

            #progressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3b82f6, stop: 1 #1d4ed8);
                border-radius: 5px;
                margin: 1px;
            }

            #progressBar:disabled {
                border-color: #e5e7eb;
                background-color: #f9fafb;
            }

            #progressBar:disabled::chunk {
                background-color: #d1d5db;
            }
        """
        )
