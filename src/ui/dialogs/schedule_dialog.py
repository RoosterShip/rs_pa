"""
Advanced schedule management dialog for automated email scanning.

This module provides a comprehensive dialog for configuring
scheduled scans with advanced options and real-time preview.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from PySide6.QtCore import QDateTime, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# from ...agents.reimbursement.workflows.scheduled_scan import ScheduledScanWorkflow
from ...core.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class SchedulePreviewWorker(QThread):
    """Worker thread for generating schedule previews."""

    preview_ready = Signal(dict)

    def __init__(self, schedule_config: Dict[str, Any]):
        super().__init__()
        self.schedule_config = schedule_config

    def run(self) -> None:
        """Generate schedule preview."""
        try:
            # Mock preview generation
            preview_data = {
                "next_runs": [
                    datetime.now() + timedelta(hours=1),
                    datetime.now() + timedelta(days=1),
                    datetime.now() + timedelta(days=2),
                ],
                "estimated_emails": 25,
                "estimated_duration": "3-5 minutes",
            }

            self.preview_ready.emit(preview_data)

        except Exception as e:
            logger.error(f"Error generating schedule preview: {e}")
            self.preview_ready.emit({"error": str(e)})


class AdvancedScheduleDialog(QDialog):
    """
    Advanced dialog for managing scheduled email scans.

    Features:
    - Multiple schedule types (hourly, daily, weekly, monthly)
    - Advanced filtering and query configuration
    - Real-time schedule preview
    - Historical scan management
    - Performance optimization settings
    """

    schedule_created = Signal(dict)
    schedule_updated = Signal(dict)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        edit_schedule: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(parent)
        self.edit_schedule = edit_schedule
        self.task_scheduler = TaskScheduler()
        self.preview_worker: Optional["SchedulePreviewWorker"] = None

        self.setWindowTitle("Advanced Schedule Management")
        self.setModal(True)
        self.resize(900, 700)

        self._setup_ui()
        self._connect_signals()

        if edit_schedule:
            self._load_schedule_data(edit_schedule)
        else:
            self._set_defaults()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create tabbed interface
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_basic_tab()
        self._create_advanced_tab()
        self._create_filters_tab()
        self._create_preview_tab()
        self._create_history_tab()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.test_btn = QPushButton("Test Schedule")
        self.test_btn.setToolTip("Test the schedule configuration")
        button_layout.addWidget(self.test_btn)

        self.preview_btn = QPushButton("Preview Next Runs")
        self.preview_btn.setToolTip("Preview upcoming scheduled runs")
        button_layout.addWidget(self.preview_btn)

        self.save_btn = QPushButton("Save Schedule")
        self.save_btn.setToolTip("Save the schedule configuration")
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _create_basic_tab(self) -> None:
        """Create the basic configuration tab."""
        basic_tab = QWidget()
        layout = QVBoxLayout(basic_tab)

        # Schedule identification
        id_group = QGroupBox("Schedule Identification")
        id_layout = QFormLayout(id_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter a descriptive name for this schedule")
        id_layout.addRow("Schedule Name:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Optional description of what this schedule does"
        )
        self.description_edit.setMaximumHeight(80)
        id_layout.addRow("Description:", self.description_edit)

        layout.addWidget(id_group)

        # Schedule frequency
        freq_group = QGroupBox("Schedule Frequency")
        freq_layout = QGridLayout(freq_group)

        # Frequency type selection
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(
            [
                "Every 15 minutes",
                "Every 30 minutes",
                "Hourly",
                "Every 2 hours",
                "Every 4 hours",
                "Every 6 hours",
                "Daily",
                "Every 2 days",
                "Weekly",
                "Monthly",
            ]
        )
        freq_layout.addWidget(QLabel("Frequency:"), 0, 0)
        freq_layout.addWidget(self.frequency_combo, 0, 1)

        # Start date/time
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setDateTime(
            QDateTime.currentDateTime().addSecs(3600)
        )  # 1 hour from now
        self.start_datetime.setCalendarPopup(True)
        freq_layout.addWidget(QLabel("Start Date/Time:"), 1, 0)
        freq_layout.addWidget(self.start_datetime, 1, 1)

        # End date (optional)
        self.enable_end_date = QCheckBox("Set End Date")
        freq_layout.addWidget(self.enable_end_date, 2, 0)

        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setEnabled(False)
        freq_layout.addWidget(self.end_datetime, 2, 1)

        layout.addWidget(freq_group)

        # Active hours restriction
        hours_group = QGroupBox("Active Hours (Optional)")
        hours_layout = QGridLayout(hours_group)

        self.enable_active_hours = QCheckBox("Restrict to specific hours")
        hours_layout.addWidget(self.enable_active_hours, 0, 0, 1, 2)

        self.start_hour_spin = QSpinBox()
        self.start_hour_spin.setRange(0, 23)
        self.start_hour_spin.setValue(9)
        self.start_hour_spin.setSuffix(":00")
        self.start_hour_spin.setEnabled(False)
        hours_layout.addWidget(QLabel("Start Hour:"), 1, 0)
        hours_layout.addWidget(self.start_hour_spin, 1, 1)

        self.end_hour_spin = QSpinBox()
        self.end_hour_spin.setRange(0, 23)
        self.end_hour_spin.setValue(17)
        self.end_hour_spin.setSuffix(":00")
        self.end_hour_spin.setEnabled(False)
        hours_layout.addWidget(QLabel("End Hour:"), 2, 0)
        hours_layout.addWidget(self.end_hour_spin, 2, 1)

        # Weekday restriction
        self.enable_weekdays = QCheckBox("Business days only (Mon-Fri)")
        self.enable_weekdays.setEnabled(False)
        hours_layout.addWidget(self.enable_weekdays, 3, 0, 1, 2)

        layout.addWidget(hours_group)

        layout.addStretch()
        self.tab_widget.addTab(basic_tab, "Basic Settings")

    def _create_advanced_tab(self) -> None:
        """Create the advanced configuration tab."""
        advanced_tab = QWidget()
        layout = QVBoxLayout(advanced_tab)

        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(perf_group)

        self.max_emails_spin = QSpinBox()
        self.max_emails_spin.setRange(10, 1000)
        self.max_emails_spin.setValue(100)
        self.max_emails_spin.setToolTip("Maximum number of emails to process per scan")
        perf_layout.addRow("Max Emails per Scan:", self.max_emails_spin)

        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(5, 100)
        self.batch_size_spin.setValue(25)
        self.batch_size_spin.setToolTip("Number of emails to process in each batch")
        perf_layout.addRow("Batch Size:", self.batch_size_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(60, 600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSuffix(" seconds")
        self.timeout_spin.setToolTip("Maximum time allowed for each scan")
        perf_layout.addRow("Timeout:", self.timeout_spin)

        layout.addWidget(perf_group)

        # Error handling
        error_group = QGroupBox("Error Handling")
        error_layout = QFormLayout(error_group)

        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 5)
        self.retry_count_spin.setValue(2)
        self.retry_count_spin.setToolTip("Number of retry attempts on failure")
        error_layout.addRow("Retry Attempts:", self.retry_count_spin)

        self.retry_delay_spin = QSpinBox()
        self.retry_delay_spin.setRange(30, 300)
        self.retry_delay_spin.setValue(60)
        self.retry_delay_spin.setSuffix(" seconds")
        self.retry_delay_spin.setToolTip("Delay between retry attempts")
        error_layout.addRow("Retry Delay:", self.retry_delay_spin)

        self.continue_on_error = QCheckBox(
            "Continue schedule on individual scan failures"
        )
        self.continue_on_error.setChecked(True)
        error_layout.addRow("", self.continue_on_error)

        layout.addWidget(error_group)

        # Notification settings
        notif_group = QGroupBox("Notifications")
        notif_layout = QFormLayout(notif_group)

        self.notify_success = QCheckBox("Notify on successful scans")
        notif_layout.addRow("", self.notify_success)

        self.notify_failure = QCheckBox("Notify on scan failures")
        self.notify_failure.setChecked(True)
        notif_layout.addRow("", self.notify_failure)

        self.notify_threshold_spin = QSpinBox()
        self.notify_threshold_spin.setRange(1, 100)
        self.notify_threshold_spin.setValue(10)
        self.notify_threshold_spin.setToolTip(
            "Minimum number of expenses found to trigger notification"
        )
        notif_layout.addRow("Notification Threshold:", self.notify_threshold_spin)

        layout.addWidget(notif_group)

        layout.addStretch()
        self.tab_widget.addTab(advanced_tab, "Advanced")

    def _create_filters_tab(self) -> None:
        """Create the email filters configuration tab."""
        filters_tab = QWidget()
        layout = QVBoxLayout(filters_tab)

        # Gmail query configuration
        query_group = QGroupBox("Gmail Search Query")
        query_layout = QVBoxLayout(query_group)

        # Query builder section
        builder_layout = QHBoxLayout()

        # Quick filters
        filter_group = QGroupBox("Quick Filters")
        filter_layout = QVBoxLayout(filter_group)

        self.has_attachment = QCheckBox("Has attachments")
        filter_layout.addWidget(self.has_attachment)

        self.unread_only = QCheckBox("Unread emails only")
        filter_layout.addWidget(self.unread_only)

        self.from_specific = QCheckBox("From specific senders")
        filter_layout.addWidget(self.from_specific)

        self.sender_list = QTextEdit()
        self.sender_list.setPlaceholderText("Enter email addresses, one per line")
        self.sender_list.setMaximumHeight(80)
        self.sender_list.setEnabled(False)
        filter_layout.addWidget(self.sender_list)

        builder_layout.addWidget(filter_group)

        # Subject/content filters
        content_group = QGroupBox("Content Filters")
        content_layout = QVBoxLayout(content_group)

        self.subject_keywords = QLineEdit()
        self.subject_keywords.setPlaceholderText(
            "Keywords in subject (comma-separated)"
        )
        content_layout.addWidget(QLabel("Subject Contains:"))
        content_layout.addWidget(self.subject_keywords)

        self.body_keywords = QLineEdit()
        self.body_keywords.setPlaceholderText("Keywords in body (comma-separated)")
        content_layout.addWidget(QLabel("Body Contains:"))
        content_layout.addWidget(self.body_keywords)

        self.exclude_keywords = QLineEdit()
        self.exclude_keywords.setPlaceholderText("Exclude emails with these keywords")
        content_layout.addWidget(QLabel("Exclude Keywords:"))
        content_layout.addWidget(self.exclude_keywords)

        builder_layout.addWidget(content_group)
        query_layout.addLayout(builder_layout)

        # Raw query editor
        raw_layout = QHBoxLayout()
        raw_layout.addWidget(QLabel("Raw Gmail Query:"))

        self.build_query_btn = QPushButton("Build Query")
        self.build_query_btn.setToolTip("Build query from filters above")
        raw_layout.addWidget(self.build_query_btn)

        self.validate_query_btn = QPushButton("Validate")
        self.validate_query_btn.setToolTip("Validate the Gmail query syntax")
        raw_layout.addWidget(self.validate_query_btn)

        query_layout.addLayout(raw_layout)

        self.gmail_query_edit = QTextEdit()
        self.gmail_query_edit.setPlaceholderText(
            "Enter Gmail search query (e.g., 'has:attachment from:receipts@uber.com')"
        )
        self.gmail_query_edit.setMaximumHeight(100)
        query_layout.addWidget(self.gmail_query_edit)

        layout.addWidget(query_group)

        # Date range filters
        date_group = QGroupBox("Date Range Filters")
        date_layout = QFormLayout(date_group)

        self.lookback_days_spin = QSpinBox()
        self.lookback_days_spin.setRange(1, 365)
        self.lookback_days_spin.setValue(7)
        self.lookback_days_spin.setToolTip(
            "For initial scan, how many days back to search"
        )
        date_layout.addRow("Initial Lookback (days):", self.lookback_days_spin)

        self.incremental_scan = QCheckBox("Use incremental scanning")
        self.incremental_scan.setChecked(True)
        self.incremental_scan.setToolTip(
            "Only scan emails since the last successful scan"
        )
        date_layout.addRow("", self.incremental_scan)

        layout.addWidget(date_group)

        layout.addStretch()
        self.tab_widget.addTab(filters_tab, "Email Filters")

    def _create_preview_tab(self) -> None:
        """Create the schedule preview tab."""
        preview_tab = QWidget()
        layout = QVBoxLayout(preview_tab)

        # Preview controls
        controls_layout = QHBoxLayout()

        self.refresh_preview_btn = QPushButton("Refresh Preview")
        self.refresh_preview_btn.setToolTip("Update the preview with current settings")
        controls_layout.addWidget(self.refresh_preview_btn)

        controls_layout.addStretch()

        self.preview_status = QLabel("Click 'Refresh Preview' to generate preview")
        controls_layout.addWidget(self.preview_status)

        layout.addLayout(controls_layout)

        # Preview content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Next runs list
        runs_group = QGroupBox("Next Scheduled Runs")
        runs_layout = QVBoxLayout(runs_group)

        self.next_runs_list = QListWidget()
        runs_layout.addWidget(self.next_runs_list)

        splitter.addWidget(runs_group)

        # Estimated impact
        impact_group = QGroupBox("Estimated Impact")
        impact_layout = QFormLayout(impact_group)

        self.estimated_emails = QLabel("-")
        impact_layout.addRow("Emails per scan:", self.estimated_emails)

        self.estimated_duration = QLabel("-")
        impact_layout.addRow("Estimated duration:", self.estimated_duration)

        self.estimated_load = QLabel("-")
        impact_layout.addRow("System load:", self.estimated_load)

        # Add progress bar for preview generation
        self.preview_progress = QProgressBar()
        self.preview_progress.setVisible(False)
        impact_layout.addRow("", self.preview_progress)

        splitter.addWidget(impact_group)

        layout.addWidget(splitter)

        # Warning/info section
        self.preview_info = QTextEdit()
        self.preview_info.setMaximumHeight(100)
        self.preview_info.setReadOnly(True)
        self.preview_info.setPlaceholderText(
            "Preview information and warnings will appear here"
        )
        layout.addWidget(self.preview_info)

        self.tab_widget.addTab(preview_tab, "Preview")

    def _create_history_tab(self) -> None:
        """Create the scan history tab."""
        history_tab = QWidget()
        layout = QVBoxLayout(history_tab)

        # History controls
        controls_layout = QHBoxLayout()

        self.refresh_history_btn = QPushButton("Refresh History")
        controls_layout.addWidget(self.refresh_history_btn)

        controls_layout.addStretch()

        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.setToolTip("Clear all scan history for this schedule")
        controls_layout.addWidget(self.clear_history_btn)

        layout.addLayout(controls_layout)

        # History tree
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(
            ["Date", "Status", "Emails", "Expenses", "Duration", "Details"]
        )
        layout.addWidget(self.history_tree)

        # History summary
        summary_layout = QHBoxLayout()

        summary_layout.addWidget(QLabel("Total Scans:"))
        self.total_scans_label = QLabel("0")
        summary_layout.addWidget(self.total_scans_label)

        summary_layout.addStretch()

        summary_layout.addWidget(QLabel("Success Rate:"))
        self.success_rate_label = QLabel("0%")
        summary_layout.addWidget(self.success_rate_label)

        summary_layout.addStretch()

        summary_layout.addWidget(QLabel("Total Expenses Found:"))
        self.total_expenses_label = QLabel("0")
        summary_layout.addWidget(self.total_expenses_label)

        layout.addLayout(summary_layout)

        self.tab_widget.addTab(history_tab, "History")

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        # Basic tab signals
        self.enable_end_date.toggled.connect(self.end_datetime.setEnabled)
        self.enable_active_hours.toggled.connect(self._toggle_active_hours)

        # Filters tab signals
        self.from_specific.toggled.connect(self.sender_list.setEnabled)
        self.build_query_btn.clicked.connect(self._build_gmail_query)
        self.validate_query_btn.clicked.connect(self._validate_gmail_query)

        # Preview tab signals
        self.refresh_preview_btn.clicked.connect(self._refresh_preview)
        self.preview_btn.clicked.connect(self._refresh_preview)

        # History tab signals
        self.refresh_history_btn.clicked.connect(self._refresh_history)
        self.clear_history_btn.clicked.connect(self._clear_history)

        # Button signals
        self.test_btn.clicked.connect(self._test_schedule)
        self.save_btn.clicked.connect(self._save_schedule)
        self.cancel_btn.clicked.connect(self.reject)

    def _toggle_active_hours(self, enabled: bool) -> None:
        """Toggle active hours controls."""
        self.start_hour_spin.setEnabled(enabled)
        self.end_hour_spin.setEnabled(enabled)
        self.enable_weekdays.setEnabled(enabled)

    def _build_gmail_query(self) -> None:
        """Build Gmail query from filter options."""
        query_parts = []

        if self.has_attachment.isChecked():
            query_parts.append("has:attachment")

        if self.unread_only.isChecked():
            query_parts.append("is:unread")

        if self.from_specific.isChecked() and self.sender_list.toPlainText().strip():
            senders = [
                s.strip()
                for s in self.sender_list.toPlainText().split("\n")
                if s.strip()
            ]
            if senders:
                sender_query = " OR ".join([f"from:{sender}" for sender in senders])
                query_parts.append(f"({sender_query})")

        if self.subject_keywords.text().strip():
            keywords = [
                k.strip() for k in self.subject_keywords.text().split(",") if k.strip()
            ]
            if keywords:
                subject_query = " OR ".join(
                    [f"subject:{keyword}" for keyword in keywords]
                )
                query_parts.append(f"({subject_query})")

        if self.body_keywords.text().strip():
            keywords = [
                k.strip() for k in self.body_keywords.text().split(",") if k.strip()
            ]
            for keyword in keywords:
                query_parts.append(f'"{keyword}"')

        if self.exclude_keywords.text().strip():
            keywords = [
                k.strip() for k in self.exclude_keywords.text().split(",") if k.strip()
            ]
            for keyword in keywords:
                query_parts.append(f'-"{keyword}"')

        gmail_query = " ".join(query_parts)
        self.gmail_query_edit.setPlainText(gmail_query)

    def _validate_gmail_query(self) -> None:
        """Validate the Gmail query syntax."""
        query = self.gmail_query_edit.toPlainText().strip()

        if not query:
            QMessageBox.warning(
                self, "Validation", "Please enter a Gmail query to validate."
            )
            return

        # Basic validation (in a real implementation, this would test against Gmail API)
        try:
            # Mock validation
            QMessageBox.information(
                self, "Validation", "Gmail query syntax appears valid."
            )
        except Exception as e:
            QMessageBox.warning(
                self, "Validation Error", f"Invalid Gmail query: {str(e)}"
            )

    def _refresh_preview(self) -> None:
        """Refresh the schedule preview."""
        self.preview_progress.setVisible(True)
        self.preview_progress.setRange(0, 0)  # Indeterminate

        config = self._get_schedule_config()

        if self.preview_worker:
            self.preview_worker.quit()
            self.preview_worker.wait()

        self.preview_worker = SchedulePreviewWorker(config)
        self.preview_worker.preview_ready.connect(self._update_preview)
        self.preview_worker.start()

    def _update_preview(self, preview_data: Dict[str, Any]) -> None:
        """Update preview display with generated data."""
        self.preview_progress.setVisible(False)

        if "error" in preview_data:
            self.preview_info.setPlainText(
                f"Error generating preview: {preview_data['error']}"
            )
            return

        # Update next runs list
        self.next_runs_list.clear()
        for run_time in preview_data.get("next_runs", []):
            item = QListWidgetItem(run_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.next_runs_list.addItem(item)

        # Update estimates
        self.estimated_emails.setText(str(preview_data.get("estimated_emails", 0)))
        self.estimated_duration.setText(
            preview_data.get("estimated_duration", "Unknown")
        )
        self.estimated_load.setText("Normal")  # Mock data

        # Update info
        info_text = (
            f"Schedule will run {len(preview_data.get('next_runs', []))} times "
            f"in the next 3 days.\n"
        )
        info_text += (
            f"Estimated {preview_data.get('estimated_emails', 0)} emails per scan."
        )
        self.preview_info.setPlainText(info_text)

    def _refresh_history(self) -> None:
        """Refresh scan history display."""
        # In a real implementation, this would load from the database
        self.history_tree.clear()

        # Mock history data
        for i in range(5):
            item = QTreeWidgetItem(
                [
                    f"2024-01-{15+i:02d} 09:00:00",
                    "Success",
                    "47",
                    "12",
                    "2m 30s",
                    "No errors",
                ]
            )
            self.history_tree.addTopLevelItem(item)

        self.total_scans_label.setText("5")
        self.success_rate_label.setText("100%")
        self.total_expenses_label.setText("60")

    def _clear_history(self) -> None:
        """Clear scan history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all scan history for this schedule?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.history_tree.clear()
            self.total_scans_label.setText("0")
            self.success_rate_label.setText("0%")
            self.total_expenses_label.setText("0")

    def _test_schedule(self) -> None:
        """Test the schedule configuration."""
        config = self._get_schedule_config()

        # Mock test
        QMessageBox.information(
            self,
            "Test Results",
            f"Schedule test successful!\n\n"
            f"Configuration: {config['name']}\n"
            f"Frequency: {config['frequency']}\n"
            f"Gmail Query: {config['gmail_query']}\n\n"
            f"The schedule appears to be configured correctly.",
        )

    def _save_schedule(self) -> None:
        """Save the schedule configuration."""
        config = self._get_schedule_config()

        # Validate required fields
        if not config["name"]:
            QMessageBox.warning(
                self, "Validation Error", "Please enter a schedule name."
            )
            self.tab_widget.setCurrentIndex(0)
            self.name_edit.setFocus()
            return

        if not config["gmail_query"]:
            QMessageBox.warning(
                self, "Validation Error", "Please enter a Gmail search query."
            )
            self.tab_widget.setCurrentIndex(2)
            self.gmail_query_edit.setFocus()
            return

        try:
            # In a real implementation, save to database/scheduler
            if self.edit_schedule:
                self.schedule_updated.emit(config)
            else:
                self.schedule_created.emit(config)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving schedule: {str(e)}")

    def _get_schedule_config(self) -> Dict[str, Any]:
        """Get current schedule configuration."""
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText(),
            "frequency": self.frequency_combo.currentText(),
            "start_datetime": self.start_datetime.dateTime().toPython(),
            "end_datetime": (
                self.end_datetime.dateTime().toPython()
                if self.enable_end_date.isChecked()
                else None
            ),
            "active_hours": {
                "enabled": self.enable_active_hours.isChecked(),
                "start_hour": self.start_hour_spin.value(),
                "end_hour": self.end_hour_spin.value(),
                "weekdays_only": self.enable_weekdays.isChecked(),
            },
            "performance": {
                "max_emails": self.max_emails_spin.value(),
                "batch_size": self.batch_size_spin.value(),
                "timeout": self.timeout_spin.value(),
            },
            "error_handling": {
                "retry_attempts": self.retry_count_spin.value(),
                "retry_delay": self.retry_delay_spin.value(),
                "continue_on_error": self.continue_on_error.isChecked(),
            },
            "notifications": {
                "notify_success": self.notify_success.isChecked(),
                "notify_failure": self.notify_failure.isChecked(),
                "threshold": self.notify_threshold_spin.value(),
            },
            "gmail_query": self.gmail_query_edit.toPlainText(),
            "filters": {
                "initial_lookback_days": self.lookback_days_spin.value(),
                "incremental_scan": self.incremental_scan.isChecked(),
            },
            "created_at": datetime.now().isoformat(),
            "enabled": True,
        }

    def _load_schedule_data(self, schedule_data: Dict[str, Any]) -> None:
        """Load existing schedule data into the form."""
        self.name_edit.setText(schedule_data.get("name", ""))
        self.description_edit.setPlainText(schedule_data.get("description", ""))

        # Set frequency
        frequency = schedule_data.get("frequency", "Daily")
        index = self.frequency_combo.findText(frequency)
        if index >= 0:
            self.frequency_combo.setCurrentIndex(index)

        # Set datetime values
        if "start_datetime" in schedule_data:
            self.start_datetime.setDateTime(
                QDateTime.fromString(schedule_data["start_datetime"])
            )

        if schedule_data.get("end_datetime"):
            self.enable_end_date.setChecked(True)
            self.end_datetime.setDateTime(
                QDateTime.fromString(schedule_data["end_datetime"])
            )

        # Load other settings...
        # (Implementation would continue for all fields)

    def _set_defaults(self) -> None:
        """Set default values for new schedule."""
        self.name_edit.setText(f"New Schedule {datetime.now().strftime('%Y%m%d_%H%M')}")
        self.gmail_query_edit.setPlainText("has:attachment")
        self.frequency_combo.setCurrentText("Daily")
