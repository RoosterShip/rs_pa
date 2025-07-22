"""
Batch progress widget with real-time updates.

This module provides a comprehensive widget for tracking and displaying
the progress of batch processing operations with detailed metrics and controls.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from PySide6.QtCore import (
    QPropertyAnimation,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...agents.reimbursement.workflows.batch_processing import BatchProcessingWorkflow

logger = logging.getLogger(__name__)


class BatchProgressWidget(QWidget):
    """
    Advanced widget for displaying batch processing progress.

    Features:
    - Real-time progress tracking
    - Detailed batch statistics
    - Error monitoring and reporting
    - Performance metrics
    - Pause/resume/cancel controls
    - Visual progress indicators
    """

    batch_cancelled = Signal(str)  # batch_id
    batch_paused = Signal(str)  # batch_id
    batch_resumed = Signal(str)  # batch_id

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.batch_id: Optional[str] = None
        self.batch_workflow: Optional[Any] = None
        self.start_time: Optional[datetime] = None
        self.is_paused = False
        self.update_timer = QTimer()

        self._setup_ui()
        self._connect_signals()
        self._setup_animations()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header with controls
        self._create_header()
        layout.addWidget(self.header_frame)

        # Main progress section
        self._create_main_progress()
        layout.addWidget(self.main_progress_group)

        # Details section with tabs
        self._create_details_section()
        layout.addWidget(self.details_widget)

        # Status and logs section
        self._create_status_section()
        layout.addWidget(self.status_group)

        # Initially hidden until batch starts
        self.setVisible(False)

    def _create_header(self) -> None:
        """Create the header with batch information and controls."""
        self.header_frame = QFrame()
        self.header_frame.setFrameStyle(QFrame.Shape.Box)
        header_layout = QHBoxLayout(self.header_frame)

        # Batch info
        info_layout = QVBoxLayout()

        self.batch_title_label = QLabel("Batch Processing")
        batch_font = QFont()
        batch_font.setBold(True)
        batch_font.setPointSize(12)
        self.batch_title_label.setFont(batch_font)
        info_layout.addWidget(self.batch_title_label)

        self.batch_subtitle_label = QLabel("Ready to process")
        self.batch_subtitle_label.setStyleSheet("color: gray;")
        info_layout.addWidget(self.batch_subtitle_label)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # Control buttons
        controls_layout = QHBoxLayout()

        self.pause_resume_btn = QPushButton("Pause")
        self.pause_resume_btn.setEnabled(False)
        self.pause_resume_btn.setMinimumWidth(80)
        controls_layout.addWidget(self.pause_resume_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumWidth(80)
        controls_layout.addWidget(self.cancel_btn)

        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setMaximumWidth(30)
        self.minimize_btn.setToolTip("Minimize progress widget")
        controls_layout.addWidget(self.minimize_btn)

        header_layout.addLayout(controls_layout)

    def _create_main_progress(self) -> None:
        """Create the main progress indicators."""
        self.main_progress_group = QGroupBox("Progress")
        layout = QVBoxLayout(self.main_progress_group)

        # Overall progress
        overall_layout = QHBoxLayout()

        overall_layout.addWidget(QLabel("Overall Progress:"))

        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimumHeight(25)
        overall_layout.addWidget(self.overall_progress)

        self.overall_percentage_label = QLabel("0%")
        self.overall_percentage_label.setMinimumWidth(40)
        overall_layout.addWidget(self.overall_percentage_label)

        layout.addLayout(overall_layout)

        # Current batch progress
        batch_layout = QHBoxLayout()

        batch_layout.addWidget(QLabel("Current Batch:"))

        self.batch_progress = QProgressBar()
        self.batch_progress.setMinimumHeight(20)
        batch_layout.addWidget(self.batch_progress)

        self.batch_percentage_label = QLabel("0%")
        self.batch_percentage_label.setMinimumWidth(40)
        batch_layout.addWidget(self.batch_percentage_label)

        layout.addLayout(batch_layout)

        # Statistics grid
        stats_grid = QGridLayout()

        # Left column
        stats_grid.addWidget(QLabel("Processed:"), 0, 0)
        self.processed_count_label = QLabel("0")
        stats_grid.addWidget(self.processed_count_label, 0, 1)

        stats_grid.addWidget(QLabel("Remaining:"), 1, 0)
        self.remaining_count_label = QLabel("0")
        stats_grid.addWidget(self.remaining_count_label, 1, 1)

        stats_grid.addWidget(QLabel("Errors:"), 2, 0)
        self.error_count_label = QLabel("0")
        stats_grid.addWidget(self.error_count_label, 2, 1)

        # Right column
        stats_grid.addWidget(QLabel("Speed:"), 0, 2)
        self.processing_speed_label = QLabel("0/min")
        stats_grid.addWidget(self.processing_speed_label, 0, 3)

        stats_grid.addWidget(QLabel("Elapsed:"), 1, 2)
        self.elapsed_time_label = QLabel("00:00:00")
        stats_grid.addWidget(self.elapsed_time_label, 1, 3)

        stats_grid.addWidget(QLabel("ETA:"), 2, 2)
        self.eta_label = QLabel("--:--:--")
        stats_grid.addWidget(self.eta_label, 2, 3)

        layout.addLayout(stats_grid)

    def _create_details_section(self) -> None:
        """Create the detailed information section."""
        self.details_widget = QTabWidget()

        # Batch details tab
        self._create_batch_details_tab()

        # Performance metrics tab
        self._create_performance_tab()

        # Errors tab
        self._create_errors_tab()

    def _create_batch_details_tab(self) -> None:
        """Create the batch details tab."""
        details_tab = QWidget()
        layout = QHBoxLayout(details_tab)

        # Batch queue
        queue_group = QGroupBox("Processing Queue")
        queue_layout = QVBoxLayout(queue_group)

        self.batch_queue_list = QListWidget()
        self.batch_queue_list.setMaximumHeight(150)
        queue_layout.addWidget(self.batch_queue_list)

        layout.addWidget(queue_group)

        # Current batch info
        current_group = QGroupBox("Current Batch")
        current_layout = QVBoxLayout(current_group)

        self.current_batch_table = QTableWidget()
        self.current_batch_table.setColumnCount(3)
        self.current_batch_table.setHorizontalHeaderLabels(["Item", "Status", "Result"])
        self.current_batch_table.horizontalHeader().setStretchLastSection(True)
        self.current_batch_table.setMaximumHeight(150)
        current_layout.addWidget(self.current_batch_table)

        layout.addWidget(current_group)

        self.details_widget.addTab(details_tab, "Batch Details")

    def _create_performance_tab(self) -> None:
        """Create the performance metrics tab."""
        performance_tab = QWidget()
        layout = QVBoxLayout(performance_tab)

        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QGridLayout(metrics_group)

        # Throughput metrics
        metrics_layout.addWidget(QLabel("Items/Second:"), 0, 0)
        self.items_per_second_label = QLabel("0.0")
        metrics_layout.addWidget(self.items_per_second_label, 0, 1)

        metrics_layout.addWidget(QLabel("Avg Processing Time:"), 1, 0)
        self.avg_processing_time_label = QLabel("0ms")
        metrics_layout.addWidget(self.avg_processing_time_label, 1, 1)

        metrics_layout.addWidget(QLabel("Memory Usage:"), 2, 0)
        self.memory_usage_label = QLabel("0 MB")
        metrics_layout.addWidget(self.memory_usage_label, 2, 1)

        # System resources
        metrics_layout.addWidget(QLabel("CPU Usage:"), 0, 2)
        self.cpu_usage_label = QLabel("0%")
        metrics_layout.addWidget(self.cpu_usage_label, 0, 3)

        metrics_layout.addWidget(QLabel("Active Threads:"), 1, 2)
        self.active_threads_label = QLabel("0")
        metrics_layout.addWidget(self.active_threads_label, 1, 3)

        metrics_layout.addWidget(QLabel("Queue Size:"), 2, 2)
        self.queue_size_label = QLabel("0")
        metrics_layout.addWidget(self.queue_size_label, 2, 3)

        layout.addWidget(metrics_group)

        # Performance history (simple text display for now)
        history_group = QGroupBox("Performance History")
        history_layout = QVBoxLayout(history_group)

        self.performance_history_text = QTextEdit()
        self.performance_history_text.setMaximumHeight(100)
        self.performance_history_text.setReadOnly(True)
        history_layout.addWidget(self.performance_history_text)

        layout.addWidget(history_group)

        layout.addStretch()
        self.details_widget.addTab(performance_tab, "Performance")

    def _create_errors_tab(self) -> None:
        """Create the errors monitoring tab."""
        errors_tab = QWidget()
        layout = QVBoxLayout(errors_tab)

        # Error summary
        summary_layout = QHBoxLayout()

        summary_layout.addWidget(QLabel("Total Errors:"))
        self.total_errors_label = QLabel("0")
        summary_layout.addWidget(self.total_errors_label)

        summary_layout.addStretch()

        summary_layout.addWidget(QLabel("Error Rate:"))
        self.error_rate_label = QLabel("0%")
        summary_layout.addWidget(self.error_rate_label)

        summary_layout.addStretch()

        self.clear_errors_btn = QPushButton("Clear Errors")
        self.clear_errors_btn.setEnabled(False)
        summary_layout.addWidget(self.clear_errors_btn)

        layout.addLayout(summary_layout)

        # Errors table
        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(4)
        self.errors_table.setHorizontalHeaderLabels(
            ["Time", "Item", "Error Type", "Description"]
        )
        self.errors_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.errors_table)

        self.details_widget.addTab(errors_tab, "Errors")

    def _create_status_section(self) -> None:
        """Create the status and logs section."""
        self.status_group = QGroupBox("Status & Logs")
        layout = QVBoxLayout(self.status_group)

        # Status bar
        status_layout = QHBoxLayout()

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: gray; font-size: 16px;")
        status_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.auto_scroll_checkbox = QPushButton("Auto-scroll")
        self.auto_scroll_checkbox.setCheckable(True)
        self.auto_scroll_checkbox.setChecked(True)
        status_layout.addWidget(self.auto_scroll_checkbox)

        self.clear_logs_btn = QPushButton("Clear Logs")
        status_layout.addWidget(self.clear_logs_btn)

        layout.addLayout(status_layout)

        # Logs display
        self.logs_display = QTextEdit()
        self.logs_display.setMaximumHeight(120)
        self.logs_display.setReadOnly(True)
        self.logs_display.setStyleSheet("font-family: monospace; font-size: 9pt;")
        layout.addWidget(self.logs_display)

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        self.pause_resume_btn.clicked.connect(self._toggle_pause_resume)
        self.cancel_btn.clicked.connect(self._cancel_batch)
        self.minimize_btn.clicked.connect(self._toggle_minimize)
        self.clear_errors_btn.clicked.connect(self._clear_errors)
        self.clear_logs_btn.clicked.connect(self._clear_logs)

        # Update timer
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.setInterval(1000)  # Update every second

    def _setup_animations(self) -> None:
        """Set up UI animations."""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)

    def start_batch(
        self,
        batch_id: str,
        workflow: BatchProcessingWorkflow,
        total_items: int,
        batch_name: Optional[str] = None,
    ) -> None:
        """
        Start monitoring a batch processing operation.

        Args:
            batch_id: Unique identifier for the batch
            workflow: Batch processing workflow instance
            total_items: Total number of items to process
            batch_name: Optional human-readable batch name
        """
        self.batch_id = batch_id
        self.batch_workflow = workflow
        self.start_time = datetime.now()
        self.is_paused = False

        # Update UI
        title = batch_name or f"Batch {batch_id[:8]}"
        self.batch_title_label.setText(title)
        self.batch_subtitle_label.setText(f"Processing {total_items} items")

        # Initialize progress bars
        self.overall_progress.setMaximum(total_items)
        self.overall_progress.setValue(0)
        self.batch_progress.setMaximum(100)
        self.batch_progress.setValue(0)

        # Initialize statistics
        self.processed_count_label.setText("0")
        self.remaining_count_label.setText(str(total_items))
        self.error_count_label.setText("0")

        # Enable controls
        self.pause_resume_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)

        # Update status
        self._update_status("Running", "green")
        self._add_log_entry("Batch processing started")

        # Show widget and start updates
        self.setVisible(True)
        self.update_timer.start()

    def update_progress(self, progress_data: Dict[str, Any]) -> None:
        """
        Update progress display with new data.

        Args:
            progress_data: Dictionary containing progress information
        """
        if not self.batch_id:
            return

        phase = progress_data.get("phase", "")

        if phase == "batch_complete":
            self._handle_batch_complete(progress_data)
        elif phase == "completed":
            self._handle_processing_complete(progress_data)
        elif phase == "failed":
            self._handle_processing_failed(progress_data)
        else:
            self._handle_progress_update(progress_data)

    def _handle_progress_update(self, data: Dict[str, Any]) -> None:
        """Handle regular progress updates."""
        # Update overall progress
        processed = data.get("processed_count", 0)
        total = data.get("total_emails", 1)
        progress_percent = data.get("progress_percent", 0)

        self.overall_progress.setValue(processed)
        self.overall_percentage_label.setText(f"{progress_percent:.1f}%")

        # Update batch progress
        batch_progress = data.get("batch_progress", 0)
        self.batch_progress.setValue(int(batch_progress))
        self.batch_percentage_label.setText(f"{batch_progress:.0f}%")

        # Update statistics
        self.processed_count_label.setText(str(processed))
        self.remaining_count_label.setText(str(total - processed))

        # Update current batch info
        batch_number = data.get("batch_number", 0)
        total_batches = data.get("total_batches", 0)
        message = data.get("message", "Processing...")

        self.batch_subtitle_label.setText(
            f"Batch {batch_number}/{total_batches} - {message}"
        )
        self._add_log_entry(message)

    def _handle_batch_complete(self, data: Dict[str, Any]) -> None:
        """Handle batch completion."""
        batch_number = data.get("batch_number", 0)
        total_batches = data.get("total_batches", 0)

        self._add_log_entry(f"Completed batch {batch_number}/{total_batches}")

        # Update batch queue display
        self._update_batch_queue(batch_number, total_batches)

    def _handle_processing_complete(self, data: Dict[str, Any]) -> None:
        """Handle complete processing finish."""
        final_stats = data.get("final_stats", {})

        # Update final statistics
        total_processed = final_stats.get("total_emails_processed", 0)
        total_expenses = final_stats.get("total_expenses_found", 0)
        processing_errors = final_stats.get("processing_errors", 0)

        self.processed_count_label.setText(str(total_processed))
        self.remaining_count_label.setText("0")
        self.error_count_label.setText(str(processing_errors))

        # Complete progress bars
        self.overall_progress.setValue(self.overall_progress.maximum())
        self.overall_percentage_label.setText("100%")
        self.batch_progress.setValue(100)
        self.batch_percentage_label.setText("100%")

        # Update status
        self._update_status("Completed", "green")
        self._add_log_entry(
            f"Processing completed successfully! Found {total_expenses} expenses "
            f"from {total_processed} emails"
        )

        # Disable controls
        self.pause_resume_btn.setEnabled(False)
        self.cancel_btn.setText("Close")

    def _handle_processing_failed(self, data: Dict[str, Any]) -> None:
        """Handle processing failure."""
        errors = data.get("errors", [])

        self._update_status("Failed", "red")
        self._add_log_entry(f"Processing failed with {len(errors)} errors")

        # Add errors to errors tab
        for error in errors:
            self._add_error_entry(error)

        # Update error counts
        self.error_count_label.setText(str(len(errors)))
        self.total_errors_label.setText(str(len(errors)))
        self.clear_errors_btn.setEnabled(True)

        # Disable processing controls
        self.pause_resume_btn.setEnabled(False)
        self.cancel_btn.setText("Close")

    def _update_display(self) -> None:
        """Update time-based display elements."""
        if not self.start_time:
            return

        # Calculate elapsed time
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split(".")[0]  # Remove microseconds
        self.elapsed_time_label.setText(elapsed_str)

        # Calculate processing speed
        if elapsed.total_seconds() > 0:
            processed = int(self.processed_count_label.text())
            speed = processed / (elapsed.total_seconds() / 60)  # items per minute
            self.processing_speed_label.setText(f"{speed:.1f}/min")

            # Update items per second
            items_per_sec = processed / elapsed.total_seconds()
            self.items_per_second_label.setText(f"{items_per_sec:.2f}")

        # Calculate ETA
        remaining = int(self.remaining_count_label.text())
        if remaining > 0 and elapsed.total_seconds() > 0:
            processed = int(self.processed_count_label.text())
            if processed > 0:
                rate = processed / elapsed.total_seconds()
                eta_seconds = remaining / rate
                eta_time = timedelta(seconds=int(eta_seconds))
                eta_str = str(eta_time).split(".")[0]
                self.eta_label.setText(eta_str)

    def _update_batch_queue(self, current_batch: int, total_batches: int) -> None:
        """Update the batch queue display."""
        self.batch_queue_list.clear()

        for i in range(1, total_batches + 1):
            if i < current_batch:
                status = "✓ Completed"
                item = QListWidgetItem(f"Batch {i}: {status}")
                item.setForeground(QColor("green"))
            elif i == current_batch:
                status = "⟳ Processing"
                item = QListWidgetItem(f"Batch {i}: {status}")
                item.setForeground(QColor("blue"))
            else:
                status = "◯ Pending"
                item = QListWidgetItem(f"Batch {i}: {status}")
                item.setForeground(QColor("gray"))

            self.batch_queue_list.addItem(item)

    def _add_error_entry(self, error_data: Dict[str, Any]) -> None:
        """Add an error entry to the errors table."""
        row = self.errors_table.rowCount()
        self.errors_table.insertRow(row)

        timestamp = error_data.get("timestamp", datetime.now().isoformat())
        item_id = error_data.get("email_id", "Unknown")
        error_type = type(error_data.get("error", "Unknown")).__name__
        description = str(error_data.get("error", "Unknown error"))

        self.errors_table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.errors_table.setItem(row, 1, QTableWidgetItem(item_id))
        self.errors_table.setItem(row, 2, QTableWidgetItem(error_type))
        self.errors_table.setItem(row, 3, QTableWidgetItem(description))

        # Update error rate
        total_processed = int(self.processed_count_label.text())
        if total_processed > 0:
            error_rate = (self.errors_table.rowCount() / total_processed) * 100
            self.error_rate_label.setText(f"{error_rate:.1f}%")

    def _update_status(self, status: str, color: str) -> None:
        """Update status indicator and label."""
        self.status_indicator.setStyleSheet(f"color: {color}; font-size: 16px;")
        self.status_label.setText(status)

    def _add_log_entry(self, message: str) -> None:
        """Add a log entry to the logs display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.logs_display.append(log_entry)

        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            scrollbar = self.logs_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _toggle_pause_resume(self) -> None:
        """Toggle pause/resume state."""
        if not self.batch_id:
            return

        if self.is_paused:
            self.batch_resumed.emit(self.batch_id)
            self.pause_resume_btn.setText("Pause")
            self._update_status("Running", "green")
            self._add_log_entry("Batch processing resumed")
            self.update_timer.start()
        else:
            self.batch_paused.emit(self.batch_id)
            self.pause_resume_btn.setText("Resume")
            self._update_status("Paused", "orange")
            self._add_log_entry("Batch processing paused")
            self.update_timer.stop()

        self.is_paused = not self.is_paused

    def _cancel_batch(self) -> None:
        """Cancel the current batch."""
        if self.batch_id and self.cancel_btn.text() == "Cancel":
            self.batch_cancelled.emit(self.batch_id)
            self._update_status("Cancelled", "red")
            self._add_log_entry("Batch processing cancelled by user")
            self.update_timer.stop()

            # Disable controls
            self.pause_resume_btn.setEnabled(False)
            self.cancel_btn.setText("Close")
        else:
            # Close the widget
            self.setVisible(False)
            self._reset_widget()

    def _toggle_minimize(self) -> None:
        """Toggle minimize state."""
        if self.details_widget.isVisible():
            self.details_widget.hide()
            self.status_group.hide()
            self.minimize_btn.setText("+")
            self.minimize_btn.setToolTip("Expand progress widget")
        else:
            self.details_widget.show()
            self.status_group.show()
            self.minimize_btn.setText("−")
            self.minimize_btn.setToolTip("Minimize progress widget")

    def _clear_errors(self) -> None:
        """Clear the errors table."""
        self.errors_table.setRowCount(0)
        self.total_errors_label.setText("0")
        self.error_rate_label.setText("0%")
        self.clear_errors_btn.setEnabled(False)
        self._add_log_entry("Error log cleared")

    def _clear_logs(self) -> None:
        """Clear the logs display."""
        self.logs_display.clear()

    def _reset_widget(self) -> None:
        """Reset the widget to initial state."""
        self.batch_id = None
        self.batch_workflow = None
        self.start_time = None
        self.is_paused = False

        # Reset progress bars
        self.overall_progress.setValue(0)
        self.batch_progress.setValue(0)
        self.overall_percentage_label.setText("0%")
        self.batch_percentage_label.setText("0%")

        # Reset statistics
        self.processed_count_label.setText("0")
        self.remaining_count_label.setText("0")
        self.error_count_label.setText("0")
        self.processing_speed_label.setText("0/min")
        self.elapsed_time_label.setText("00:00:00")
        self.eta_label.setText("--:--:--")

        # Reset UI state
        self.batch_title_label.setText("Batch Processing")
        self.batch_subtitle_label.setText("Ready to process")
        self.pause_resume_btn.setText("Pause")
        self.pause_resume_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel")
        self.cancel_btn.setEnabled(False)

        # Clear displays
        self.batch_queue_list.clear()
        self.current_batch_table.setRowCount(0)
        self.errors_table.setRowCount(0)
        self.logs_display.clear()

        # Reset status
        self._update_status("Ready", "gray")

        # Stop timer
        self.update_timer.stop()

    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get current batch statistics."""
        return {
            "batch_id": self.batch_id,
            "processed": int(self.processed_count_label.text()),
            "remaining": int(self.remaining_count_label.text()),
            "errors": int(self.error_count_label.text()),
            "elapsed_time": self.elapsed_time_label.text(),
            "processing_speed": self.processing_speed_label.text(),
            "is_paused": self.is_paused,
            "status": self.status_label.text(),
        }
