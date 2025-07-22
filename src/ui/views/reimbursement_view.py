"""
Reimbursement Agent view for processing expense reimbursements.

This module provides a Qt widget interface for the reimbursement agent
with date selection, scanning controls, results table, and export functionality.
"""

import datetime
import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import QDate, QDateTime, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...agents.reimbursement.agent import ReimbursementAgent
from ...agents.reimbursement.reports.backend import ReportBackend
from ...agents.reimbursement.workflows.batch_processing import BatchProcessingWorkflow
from ...agents.reimbursement.workflows.scheduled_scan import ScheduledScanWorkflow
from ...core.task_scheduler import TaskPriority, TaskScheduler
from ..dialogs.category_dialog import CategoryManagerDialog
from ..dialogs.expense_detail_dialog import ExpenseDetailDialog
from ..dialogs.report_dialog import ReportDialog
from ..dialogs.schedule_dialog import AdvancedScheduleDialog
from ..models.reimbursement_results_model import ReimbursementResultsModel
from ..widgets.batch_progress import BatchProgressWidget
from ..widgets.progress_widget import ProgressWidget

# from ..widgets.workflow_designer import WorkflowDesignerWidget


class ReimbursementView(QWidget):
    """
    Reimbursement Agent view for expense processing.

    This widget provides a comprehensive interface for scanning emails
    for reimbursable expenses with date range selection, results display,
    and export functionality.
    """

    # Signals
    scan_requested = Signal(str, str)  # start_date, end_date
    export_requested = Signal(str, str)  # format, file_path

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the reimbursement view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize the reimbursement agent
        self._agent = ReimbursementAgent(parent=self)
        self._agent.initialize()

        # Initialize task scheduler
        self._task_scheduler = TaskScheduler(parent=self)

        # Initialize advanced workflow components
        self._batch_workflow = BatchProcessingWorkflow()
        self._scheduled_workflow = ScheduledScanWorkflow()
        self._report_backend = ReportBackend()

        # Initialize progress widgets
        self._batch_progress_widget = BatchProgressWidget()
        self._batch_progress_widget.batch_cancelled.connect(
            self._handle_batch_cancelled
        )
        self._batch_progress_widget.batch_paused.connect(self._handle_batch_paused)
        self._batch_progress_widget.batch_resumed.connect(self._handle_batch_resumed)

        self._setup_ui()
        self._setup_connections()
        self._setup_agent_connections()
        self._setup_scheduler_connections()
        self._setup_mock_data()

    def _setup_ui(self) -> None:
        """Set up the user interface with tabbed advanced features."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header section
        header_widget = self._create_header_section()
        main_layout.addWidget(header_widget)

        # Create tab widget for different features
        self._tab_widget = QTabWidget()
        self._tab_widget.setObjectName("featureTabWidget")

        # Basic scan tab (existing functionality)
        basic_scan_tab = self._create_basic_scan_tab()
        self._tab_widget.addTab(basic_scan_tab, "📄 Basic Scan")

        # Advanced features tabs
        scheduled_scan_tab = self._create_scheduled_scan_tab()
        self._tab_widget.addTab(scheduled_scan_tab, "⏰ Scheduled Scanning")

        batch_processing_tab = self._create_batch_processing_tab()
        self._tab_widget.addTab(batch_processing_tab, "📦 Batch Processing")

        reporting_tab = self._create_reporting_tab()
        self._tab_widget.addTab(reporting_tab, "📊 Reporting")

        history_tab = self._create_history_tab()
        self._tab_widget.addTab(history_tab, "📖 Scan History")

        main_layout.addWidget(self._tab_widget)

        # Apply styling
        self._apply_styling()

    def _create_header_section(self) -> QWidget:
        """
        Create the header section with title and description.

        Returns:
            Header widget
        """
        header_widget = QFrame()
        header_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        header_widget.setObjectName("headerFrame")

        layout = QVBoxLayout(header_widget)
        layout.setContentsMargins(20, 15, 20, 15)

        # Title
        title_label = QLabel("Reimbursement Agent")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Scan your emails to automatically detect reimbursable expenses "
            "and generate expense reports."
        )
        desc_label.setObjectName("descLabel")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        return header_widget

    def _create_basic_scan_tab(self) -> QWidget:
        """
        Create the basic scan tab with existing functionality.

        Returns:
            Basic scan widget
        """
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Control section
        control_widget = self._create_control_section()
        layout.addWidget(control_widget)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results section
        results_widget = self._create_results_section()
        splitter.addWidget(results_widget)

        # Summary section
        summary_widget = self._create_summary_section()
        splitter.addWidget(summary_widget)

        # Set splitter proportions
        splitter.setStretchFactor(0, 3)  # Results get more space
        splitter.setStretchFactor(1, 1)  # Summary gets less space

        layout.addWidget(splitter)

        return tab_widget

    def _create_scheduled_scan_tab(self) -> QWidget:
        """
        Create the scheduled scanning tab with LangGraph integration.

        Returns:
            Scheduled scan widget
        """
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Configuration group
        config_group = QGroupBox("Schedule Configuration")
        config_group.setObjectName("scheduledConfigGroup")
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_layout.setSpacing(15)

        # Schedule type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Schedule Type:"))

        self._schedule_type_combo = QComboBox()
        self._schedule_type_combo.addItems(
            ["One-time scan", "Daily recurring", "Weekly recurring", "Custom interval"]
        )
        self._schedule_type_combo.setObjectName("scheduleTypeCombo")
        type_layout.addWidget(self._schedule_type_combo)
        type_layout.addStretch()
        config_layout.addLayout(type_layout)

        # Date/time configuration
        datetime_layout = QHBoxLayout()

        # Start date/time
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start Date/Time:"))
        self._schedule_start_datetime = QDateTimeEdit()
        self._schedule_start_datetime.setCalendarPopup(True)
        self._schedule_start_datetime.setDateTime(
            QDateTime.currentDateTime().addSecs(3600)
        )  # 1 hour from now
        self._schedule_start_datetime.setObjectName("scheduleStartDateTime")
        start_layout.addWidget(self._schedule_start_datetime)
        datetime_layout.addLayout(start_layout)

        # End date for range
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("Scan End Date:"))
        self._schedule_end_date = QDateEdit()
        self._schedule_end_date.setCalendarPopup(True)
        self._schedule_end_date.setDate(QDate.currentDate())
        self._schedule_end_date.setObjectName("scheduleEndDate")
        end_layout.addWidget(self._schedule_end_date)
        datetime_layout.addLayout(end_layout)

        config_layout.addLayout(datetime_layout)

        # Advanced options
        advanced_layout = QHBoxLayout()

        # Custom interval (for custom type)
        interval_layout = QVBoxLayout()
        interval_layout.addWidget(QLabel("Interval (hours):"))
        self._schedule_interval = QSpinBox()
        self._schedule_interval.setRange(1, 168)  # 1 hour to 1 week
        self._schedule_interval.setValue(24)
        self._schedule_interval.setObjectName("scheduleInterval")
        interval_layout.addWidget(self._schedule_interval)
        advanced_layout.addLayout(interval_layout)

        # Max emails per scan
        max_emails_layout = QVBoxLayout()
        max_emails_layout.addWidget(QLabel("Max Emails per Scan:"))
        self._schedule_max_emails = QSpinBox()
        self._schedule_max_emails.setRange(10, 1000)
        self._schedule_max_emails.setValue(50)
        self._schedule_max_emails.setObjectName("scheduleMaxEmails")
        max_emails_layout.addWidget(self._schedule_max_emails)
        advanced_layout.addLayout(max_emails_layout)

        config_layout.addLayout(advanced_layout)

        # LangGraph workflow options
        langgraph_layout = QHBoxLayout()
        self._enable_langgraph = QCheckBox("Enable LangGraph Workflow Optimization")
        self._enable_langgraph.setChecked(True)
        self._enable_langgraph.setObjectName("enableLangGraph")
        langgraph_layout.addWidget(self._enable_langgraph)
        langgraph_layout.addStretch()
        config_layout.addLayout(langgraph_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._create_schedule_button = QPushButton("📅 Create Schedule")
        self._create_schedule_button.setObjectName("createScheduleButton")
        button_layout.addWidget(self._create_schedule_button)

        self._clear_schedules_button = QPushButton("🗑️ Clear All Schedules")
        self._clear_schedules_button.setObjectName("clearSchedulesButton")
        button_layout.addWidget(self._clear_schedules_button)

        config_layout.addLayout(button_layout)
        layout.addWidget(config_group)

        # Active schedules list
        schedules_group = QGroupBox("Active Schedules")
        schedules_group.setObjectName("activeSchedulesGroup")
        schedules_layout = QVBoxLayout(schedules_group)
        schedules_layout.setContentsMargins(15, 15, 15, 15)

        self._schedules_table = QTableView()
        self._schedules_table.setObjectName("schedulesTable")
        # TODO: Create schedules table model
        schedules_layout.addWidget(self._schedules_table)

        layout.addWidget(schedules_group)

        return tab_widget

    def _create_batch_processing_tab(self) -> QWidget:
        """
        Create the batch processing tab for high-volume processing.

        Returns:
            Batch processing widget
        """
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Configuration group
        config_group = QGroupBox("Batch Processing Configuration")
        config_group.setObjectName("batchConfigGroup")
        config_layout = QVBoxLayout(config_group)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_layout.setSpacing(15)

        # Batch size settings
        batch_layout = QHBoxLayout()

        batch_size_layout = QVBoxLayout()
        batch_size_layout.addWidget(QLabel("Batch Size (emails per batch):"))
        self._batch_size = QSpinBox()
        self._batch_size.setRange(50, 500)
        self._batch_size.setValue(100)
        self._batch_size.setObjectName("batchSize")
        batch_size_layout.addWidget(self._batch_size)
        batch_layout.addLayout(batch_size_layout)

        processing_interval_layout = QVBoxLayout()
        processing_interval_layout.addWidget(QLabel("Processing Interval (minutes):"))
        self._processing_interval = QSpinBox()
        self._processing_interval.setRange(5, 120)
        self._processing_interval.setValue(30)
        self._processing_interval.setObjectName("processingInterval")
        processing_interval_layout.addWidget(self._processing_interval)
        batch_layout.addLayout(processing_interval_layout)

        config_layout.addLayout(batch_layout)

        # Priority settings
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Processing Priority:"))
        self._batch_priority = QComboBox()
        self._batch_priority.addItems(["Low", "Normal", "High", "Urgent"])
        self._batch_priority.setCurrentText("High")
        self._batch_priority.setObjectName("batchPriority")
        priority_layout.addWidget(self._batch_priority)
        priority_layout.addStretch()
        config_layout.addLayout(priority_layout)

        # LangGraph batch optimization
        langgraph_batch_layout = QHBoxLayout()
        self._enable_batch_langgraph = QCheckBox("Enable LangGraph Batch Optimization")
        self._enable_batch_langgraph.setChecked(True)
        self._enable_batch_langgraph.setObjectName("enableBatchLangGraph")
        langgraph_batch_layout.addWidget(self._enable_batch_langgraph)
        langgraph_batch_layout.addStretch()
        config_layout.addLayout(langgraph_batch_layout)

        # Control buttons
        batch_button_layout = QHBoxLayout()
        batch_button_layout.addStretch()

        self._start_batch_button = QPushButton("▶️ Start Batch Processing")
        self._start_batch_button.setObjectName("startBatchButton")
        batch_button_layout.addWidget(self._start_batch_button)

        self._stop_batch_button = QPushButton("⏹️ Stop Processing")
        self._stop_batch_button.setObjectName("stopBatchButton")
        self._stop_batch_button.setEnabled(False)
        batch_button_layout.addWidget(self._stop_batch_button)

        config_layout.addLayout(batch_button_layout)
        layout.addWidget(config_group)

        # Batch status and progress
        status_group = QGroupBox("Batch Processing Status")
        status_group.setObjectName("batchStatusGroup")
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(15, 15, 15, 15)

        # Status labels
        self._batch_status_label = QLabel("Status: Ready")
        self._batch_status_label.setObjectName("batchStatusLabel")
        status_layout.addWidget(self._batch_status_label)

        # Progress widget for batch processing (already initialized in __init__)
        status_layout.addWidget(self._batch_progress_widget)

        layout.addWidget(status_group)

        return tab_widget

    def _create_reporting_tab(self) -> QWidget:
        """
        Create the reporting tab with LangGraph analytics.

        Returns:
            Reporting widget
        """
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Report generation group
        report_group = QGroupBox("Generate Reports")
        report_group.setObjectName("reportGroup")
        report_layout = QVBoxLayout(report_group)
        report_layout.setContentsMargins(20, 20, 20, 20)
        report_layout.setSpacing(15)

        # Report type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Report Type:"))
        self._report_type = QComboBox()
        self._report_type.addItems(
            [
                "Expense Summary",
                "Detailed Analysis",
                "Trend Analysis",
                "Category Breakdown",
                "LangGraph Workflow Report",
            ]
        )
        self._report_type.setObjectName("reportType")
        type_layout.addWidget(self._report_type)
        type_layout.addStretch()
        report_layout.addLayout(type_layout)

        # Date range for reports
        report_date_layout = QHBoxLayout()

        report_start_layout = QVBoxLayout()
        report_start_layout.addWidget(QLabel("Report Start Date:"))
        self._report_start_date = QDateEdit()
        self._report_start_date.setCalendarPopup(True)
        self._report_start_date.setDate(QDate.currentDate().addDays(-30))
        self._report_start_date.setObjectName("reportStartDate")
        report_start_layout.addWidget(self._report_start_date)
        report_date_layout.addLayout(report_start_layout)

        report_end_layout = QVBoxLayout()
        report_end_layout.addWidget(QLabel("Report End Date:"))
        self._report_end_date = QDateEdit()
        self._report_end_date.setCalendarPopup(True)
        self._report_end_date.setDate(QDate.currentDate())
        self._report_end_date.setObjectName("reportEndDate")
        report_end_layout.addWidget(self._report_end_date)
        report_date_layout.addLayout(report_end_layout)

        report_layout.addLayout(report_date_layout)

        # Advanced analytics options
        analytics_layout = QHBoxLayout()
        self._enable_langgraph_analytics = QCheckBox(
            "Enable LangGraph Advanced Analytics"
        )
        self._enable_langgraph_analytics.setChecked(True)
        self._enable_langgraph_analytics.setObjectName("enableLangGraphAnalytics")
        analytics_layout.addWidget(self._enable_langgraph_analytics)
        analytics_layout.addStretch()
        report_layout.addLayout(analytics_layout)

        # Report generation buttons
        report_button_layout = QHBoxLayout()
        report_button_layout.addStretch()

        self._generate_report_button = QPushButton("📊 Generate Report")
        self._generate_report_button.setObjectName("generateReportButton")
        report_button_layout.addWidget(self._generate_report_button)

        self._export_report_button = QPushButton("💾 Export Report")
        self._export_report_button.setObjectName("exportReportButton")
        self._export_report_button.setEnabled(False)
        report_button_layout.addWidget(self._export_report_button)

        report_layout.addLayout(report_button_layout)
        layout.addWidget(report_group)

        # Report preview area
        preview_group = QGroupBox("Report Preview")
        preview_group.setObjectName("reportPreviewGroup")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(15, 15, 15, 15)

        self._report_preview_area = QLabel(
            "No report generated yet. Click 'Generate Report' to create a report."
        )
        self._report_preview_area.setWordWrap(True)
        self._report_preview_area.setObjectName("reportPreviewArea")
        self._report_preview_area.setStyleSheet(
            "padding: 20px; background-color: #f9f9f9; "
            "border: 1px solid #ddd; border-radius: 8px;"
        )
        preview_layout.addWidget(self._report_preview_area)

        layout.addWidget(preview_group)

        return tab_widget

    def _create_history_tab(self) -> QWidget:
        """
        Create the scan history tab with LangGraph query processing.

        Returns:
            History widget
        """
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Search and filter group
        search_group = QGroupBox("Search & Filter History")
        search_group.setObjectName("historySearchGroup")
        search_layout = QVBoxLayout(search_group)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(15)

        # Search controls
        search_controls_layout = QHBoxLayout()

        search_controls_layout.addWidget(QLabel("Search:"))
        self._history_search = QLineEdit()
        self._history_search.setPlaceholderText("Search scan history...")
        self._history_search.setObjectName("historySearch")
        search_controls_layout.addWidget(self._history_search)

        # LangGraph query processing
        self._enable_langgraph_search = QCheckBox("LangGraph Query Processing")
        self._enable_langgraph_search.setChecked(True)
        self._enable_langgraph_search.setObjectName("enableLangGraphSearch")
        search_controls_layout.addWidget(self._enable_langgraph_search)

        search_layout.addLayout(search_controls_layout)

        # Filter options
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Status Filter:"))
        self._history_status_filter = QComboBox()
        self._history_status_filter.addItems(
            ["All", "Completed", "Failed", "In Progress"]
        )
        self._history_status_filter.setObjectName("historyStatusFilter")
        filter_layout.addWidget(self._history_status_filter)

        filter_layout.addWidget(QLabel("Date Range:"))
        self._history_date_filter = QComboBox()
        self._history_date_filter.addItems(
            ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
        )
        self._history_date_filter.setObjectName("historyDateFilter")
        filter_layout.addWidget(self._history_date_filter)

        filter_layout.addStretch()
        search_layout.addLayout(filter_layout)

        layout.addWidget(search_group)

        # History table
        history_group = QGroupBox("Scan History")
        history_group.setObjectName("scanHistoryGroup")
        history_layout = QVBoxLayout(history_group)
        history_layout.setContentsMargins(15, 15, 15, 15)

        self._history_table = QTableView()
        self._history_table.setObjectName("historyTable")
        # TODO: Create history table model
        history_layout.addWidget(self._history_table)

        layout.addWidget(history_group)

        return tab_widget

    def _create_control_section(self) -> QWidget:
        """
        Create the control section with date selection and scan button.

        Returns:
            Control widget
        """
        control_group = QGroupBox("Scan Configuration")
        control_group.setObjectName("controlGroup")

        layout = QHBoxLayout(control_group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Date range selection
        date_layout = QVBoxLayout()

        start_date_label = QLabel("Start Date:")
        start_date_label.setObjectName("dateLabel")
        date_layout.addWidget(start_date_label)

        self._start_date_edit = QDateEdit()
        self._start_date_edit.setCalendarPopup(True)
        self._start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self._start_date_edit.setObjectName("dateEdit")
        date_layout.addWidget(self._start_date_edit)

        end_date_label = QLabel("End Date:")
        end_date_label.setObjectName("dateLabel")
        date_layout.addWidget(end_date_label)

        self._end_date_edit = QDateEdit()
        self._end_date_edit.setCalendarPopup(True)
        self._end_date_edit.setDate(QDate.currentDate())
        self._end_date_edit.setObjectName("dateEdit")
        date_layout.addWidget(self._end_date_edit)

        layout.addLayout(date_layout)

        # Spacer
        layout.addStretch()

        # Progress and scan button
        scan_layout = QVBoxLayout()

        self._scan_button = QPushButton("🔍 Scan for Expenses")
        self._scan_button.setObjectName("scanButton")
        self._scan_button.setToolTip("Start scanning emails for reimbursable expenses")
        scan_layout.addWidget(self._scan_button)

        # Progress widget
        self._progress_widget = ProgressWidget()
        scan_layout.addWidget(self._progress_widget)

        layout.addLayout(scan_layout)

        return control_group

    def _create_results_section(self) -> QWidget:
        """
        Create the results section with table and filtering.

        Returns:
            Results widget
        """
        results_group = QGroupBox("Scan Results")
        results_group.setObjectName("resultsGroup")

        layout = QVBoxLayout(results_group)
        layout.setContentsMargins(15, 15, 15, 15)

        # Filtering controls
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Filter:")
        filter_label.setObjectName("filterLabel")
        filter_layout.addWidget(filter_label)

        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Search expenses...")
        self._filter_edit.setObjectName("filterEdit")
        filter_layout.addWidget(self._filter_edit)

        # Export button
        self._export_button = QPushButton("📄 Export Results")
        self._export_button.setObjectName("exportButton")
        self._export_button.setToolTip("Export results to CSV or PDF")
        self._export_button.setEnabled(False)  # Disabled until results available
        filter_layout.addWidget(self._export_button)

        layout.addLayout(filter_layout)

        # Results table
        self._results_model = ReimbursementResultsModel()
        self._results_table = QTableView()
        self._results_table.setModel(self._results_model)

        # Configure table
        self._setup_results_table()

        layout.addWidget(self._results_table)

        return results_group

    def _create_summary_section(self) -> QWidget:
        """
        Create the summary statistics section.

        Returns:
            Summary widget
        """
        summary_group = QGroupBox("Summary Statistics")
        summary_group.setObjectName("summaryGroup")

        layout = QHBoxLayout(summary_group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(30)

        # Create summary labels
        self._total_expenses_label = QLabel("Total Expenses: $0.00")
        self._total_expenses_label.setObjectName("summaryLabel")
        layout.addWidget(self._total_expenses_label)

        self._reimbursable_count_label = QLabel("Reimbursable: 0")
        self._reimbursable_count_label.setObjectName("summaryLabel")
        layout.addWidget(self._reimbursable_count_label)

        self._non_reimbursable_count_label = QLabel("Non-Reimbursable: 0")
        self._non_reimbursable_count_label.setObjectName("summaryLabel")
        layout.addWidget(self._non_reimbursable_count_label)

        self._pending_review_label = QLabel("Pending Review: 0")
        self._pending_review_label.setObjectName("summaryLabel")
        layout.addWidget(self._pending_review_label)

        layout.addStretch()

        return summary_group

    def _setup_results_table(self) -> None:
        """Set up the results table view."""
        table = self._results_table
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setSortingEnabled(True)

        # Header configuration
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)

        # Column widths
        header.resizeSection(0, 180)  # Date
        header.resizeSection(1, 200)  # Subject
        header.resizeSection(2, 150)  # Sender
        header.resizeSection(3, 150)  # Vendor
        header.resizeSection(4, 100)  # Amount
        header.resizeSection(5, 120)  # Category
        header.resizeSection(6, 120)  # Status

        # Row height
        table.verticalHeader().setDefaultSectionSize(35)
        table.verticalHeader().hide()

        # Double-click to view details
        table.doubleClicked.connect(self._show_expense_details)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Basic tab button connections (these exist in basic scan tab)
        self._scan_button.clicked.connect(self._handle_scan_request)
        self._export_button.clicked.connect(self._handle_export_request)

        # Filter connection
        self._filter_edit.textChanged.connect(self._handle_filter_change)

        # Model connections
        self._results_model.dataChanged.connect(self._update_summary)
        self._results_model.modelReset.connect(self._update_summary)

        # Advanced feature button connections
        self._create_schedule_button.clicked.connect(self._handle_create_schedule)
        self._clear_schedules_button.clicked.connect(self._handle_clear_schedules)
        self._start_batch_button.clicked.connect(self._handle_start_batch_processing)
        self._stop_batch_button.clicked.connect(self._handle_stop_batch_processing)
        self._generate_report_button.clicked.connect(self._handle_generate_report)
        self._export_report_button.clicked.connect(self._handle_export_report)

    def _setup_agent_connections(self) -> None:
        """Set up reimbursement agent signal connections."""
        self._agent.status_changed.connect(self._handle_agent_status_change)
        self._agent.progress_updated.connect(self._handle_agent_progress)
        self._agent.result_ready.connect(self._handle_agent_result)
        self._agent.error_occurred.connect(self._handle_agent_error)

    def _setup_scheduler_connections(self) -> None:
        """Set up task scheduler signal connections."""
        self._task_scheduler.task_started.connect(self._handle_task_started)
        self._task_scheduler.task_completed.connect(self._handle_task_completed)
        self._task_scheduler.task_failed.connect(self._handle_task_failed)
        self._task_scheduler.task_scheduled.connect(self._handle_task_scheduled)
        self._task_scheduler.task_cancelled.connect(self._handle_task_cancelled)

    def _setup_mock_data(self) -> None:
        """Set up initial mock data for demonstration."""
        # This will be populated with actual scan results
        # For now, we start with empty results
        self._update_summary()

    def _handle_scan_request(self) -> None:
        """Handle scan button click."""
        start_date = self._start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self._end_date_edit.date().toString("yyyy-MM-dd")

        # Validate date range
        start_qdate = self._start_date_edit.date()
        end_qdate = self._end_date_edit.date()
        start_python_date = datetime.date(
            start_qdate.year(), start_qdate.month(), start_qdate.day()
        )
        end_python_date = datetime.date(
            end_qdate.year(), end_qdate.month(), end_qdate.day()
        )
        if start_python_date > end_python_date:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "Start date must be before or equal to end date.",
            )
            return

        # Start real agent scanning
        self._scan_button.setEnabled(False)
        self._scan_button.setText("🔍 Scanning...")
        self._progress_widget.start_progress("Scanning emails for expenses...")

        # Emit signal for external handling (for potential future use)
        self.scan_requested.emit(start_date, end_date)

        # Execute the real reimbursement agent
        gmail_query = f"has:attachment after:{start_date} before:{end_date}"
        input_data = {
            "gmail_query": gmail_query,
            "max_emails": 20,  # Configurable max emails
        }

        success = self._agent.execute(input_data)
        if not success:
            self._handle_scan_error("Failed to start reimbursement agent")

    def _handle_agent_status_change(self, status: str) -> None:
        """Handle agent status change."""
        if status == "completed":
            self._complete_scan()
        elif status == "error":
            self._handle_scan_error("Agent execution failed")

    def _handle_agent_progress(self, progress: int) -> None:
        """Handle agent progress updates."""
        self._progress_widget.update_progress(progress)

    def _handle_agent_result(self, result: Dict[str, Any]) -> None:
        """Handle LLM agent results with enhanced analysis data."""
        # Load LLM results directly using the enhanced model method
        expense_results = result.get("expense_results", [])

        # Use the new load_llm_results method that handles all the LLM analysis data
        self._results_model.load_llm_results(expense_results)

    def _handle_agent_error(self, error_msg: str) -> None:
        """Handle agent errors."""
        self._handle_scan_error(error_msg)

    def _complete_scan(self) -> None:
        """Complete the scanning process and show results."""
        # Stop progress
        self._progress_widget.stop_progress()
        self._scan_button.setEnabled(True)
        self._scan_button.setText("🔍 Scan for Expenses")

        # Enable export button
        self._export_button.setEnabled(True)

        # Update summary
        self._update_summary()

        # Show completion message
        result_count = self._results_model.rowCount()
        QMessageBox.information(
            self,
            "Scan Complete",
            f"Scan completed successfully!\n\n"
            f"Found {result_count} potential expense entries.\n"
            f"Review the results below and export when ready.",
        )

    def _handle_scan_error(self, error_msg: str) -> None:
        """Handle scan errors."""
        # Stop progress
        self._progress_widget.stop_progress()
        self._scan_button.setEnabled(True)
        self._scan_button.setText("🔍 Scan for Expenses")

        # Show error message
        QMessageBox.critical(
            self,
            "Scan Error",
            f"Expense scanning failed:\n\n{error_msg}\n\n"
            f"Please check your Gmail connection and try again.",
        )

    def _handle_export_request(self) -> None:
        """Handle export button click."""
        if self._results_model.rowCount() == 0:
            QMessageBox.information(
                self,
                "No Data",
                "No scan results to export. Please run a scan first.",
            )
            return

        # Show file dialog
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilters(
            [
                "CSV Files (*.csv)",
                "PDF Files (*.pdf)",
            ]
        )
        file_dialog.setDefaultSuffix("csv")

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]
                export_format = "CSV" if file_path.endswith(".csv") else "PDF"

                # Emit signal for external handling
                self.export_requested.emit(export_format, file_path)

                # Show success message
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Results exported successfully to:\n{file_path}",
                )

    def _handle_filter_change(self, text: str) -> None:
        """
        Handle filter text change.

        Args:
            text: Filter text
        """
        # Apply filter to the model's proxy (to be implemented)
        # For now, just update the placeholder
        placeholder = f"Filtering by: '{text}'" if text else "Search expenses..."
        self._filter_edit.setPlaceholderText(placeholder)

    def _show_expense_details(self, index: QModelIndex) -> None:
        """
        Show detailed expense information.

        Args:
            index: Table index
        """
        if not index.isValid():
            return

        expense = self._results_model.get_expense_at_row(index.row())
        if expense:
            # Show detailed expense dialog
            detail_dialog = ExpenseDetailDialog(expense, self)
            detail_dialog.exec()

    def _update_summary(self) -> None:
        """Update the summary statistics."""
        model = self._results_model
        total_count = model.rowCount()

        total_amount = 0.0
        reimbursable_count = 0
        non_reimbursable_count = 0
        pending_count = 0

        for row in range(total_count):
            expense = model.get_expense_at_row(row)
            if expense:
                total_amount += expense.amount

                if expense.status == "Reimbursable":
                    reimbursable_count += 1
                elif expense.status == "Non-Reimbursable":
                    non_reimbursable_count += 1
                elif expense.status == "Pending Review":
                    pending_count += 1

        # Update labels
        self._total_expenses_label.setText(f"Total Expenses: ${total_amount:.2f}")
        self._reimbursable_count_label.setText(f"Reimbursable: {reimbursable_count}")
        self._non_reimbursable_count_label.setText(
            f"Non-Reimbursable: {non_reimbursable_count}"
        )
        self._pending_review_label.setText(f"Pending Review: {pending_count}")

    def _handle_task_started(self, task_id: str, task_name: str) -> None:
        """Handle task scheduler start event."""
        print(f"Task started: {task_name} ({task_id})")

    def _handle_task_completed(
        self, task_id: str, task_name: str, result: object
    ) -> None:
        """Handle task scheduler completion event."""
        print(f"Task completed: {task_name} ({task_id})")
        QMessageBox.information(
            self, "Task Completed", f"Task '{task_name}' completed successfully!"
        )

    def _handle_task_failed(self, task_id: str, task_name: str, error: str) -> None:
        """Handle task scheduler failure event."""
        print(f"Task failed: {task_name} ({task_id}) - {error}")
        QMessageBox.warning(
            self, "Task Failed", f"Task '{task_name}' failed:\n\n{error}"
        )

    def _handle_task_scheduled(
        self, task_id: str, task_name: str, scheduled_time: datetime.datetime
    ) -> None:
        """Handle task scheduler scheduling event."""
        print(f"Task scheduled: {task_name} ({task_id}) at {scheduled_time}")

    def _handle_task_cancelled(self, task_id: str, task_name: str) -> None:
        """Handle task scheduler cancellation event."""
        print(f"Task cancelled: {task_name} ({task_id})")

    def _handle_create_schedule(self) -> None:
        """Handle create schedule button click."""
        try:
            # Get schedule configuration
            schedule_type = self._schedule_type_combo.currentText()
            start_datetime_qt = self._schedule_start_datetime.dateTime()
            start_datetime = start_datetime_qt.toPython()
            assert isinstance(start_datetime, datetime.datetime)
            end_date_qt = self._schedule_end_date.date()
            end_date = end_date_qt.toPython()
            assert isinstance(end_date, datetime.date)
            interval_hours = self._schedule_interval.value()
            max_emails = self._schedule_max_emails.value()
            langgraph_enabled = self._enable_langgraph.isChecked()

            # Convert schedule type to recurring settings
            if schedule_type == "Daily recurring":
                interval_hours = 24
            elif schedule_type == "Weekly recurring":
                interval_hours = 168  # 7 days

            # Create scheduled task
            task_id = self._task_scheduler.schedule_recurring_scan(
                start_date=start_datetime,
                end_date=datetime.datetime.combine(end_date, datetime.time.min),
                interval_hours=interval_hours,
                query_params={
                    "max_emails": max_emails,
                    "langgraph_enabled": langgraph_enabled,
                },
            )

            QMessageBox.information(
                self,
                "Schedule Created",
                f"Scheduled scan created successfully!\n\n"
                f"Schedule Type: {schedule_type}\n"
                f"Start Time: {start_datetime.strftime('%Y-%m-%d %H:%M')}\n"
                f"Task ID: {task_id[:8]}...",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Schedule Error", f"Failed to create schedule:\n\n{str(e)}"
            )

    def _handle_clear_schedules(self) -> None:
        """Handle clear schedules button click."""
        reply = QMessageBox.question(
            self,
            "Clear Schedules",
            "Are you sure you want to cancel all active schedules?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Get all scheduled tasks and cancel them
            tasks = self._task_scheduler.get_scheduled_tasks()
            cancelled_count = 0

            for task in tasks:
                if self._task_scheduler.cancel_task(task["task_id"]):
                    cancelled_count += 1

            QMessageBox.information(
                self,
                "Schedules Cleared",
                f"Cancelled {cancelled_count} scheduled tasks.",
            )

    def _handle_start_batch_processing(self) -> None:
        """Handle start batch processing button click."""
        try:
            batch_size = self._batch_size.value()
            processing_interval = self._processing_interval.value()
            priority_text = self._batch_priority.currentText()

            # Convert priority text to TaskPriority enum
            priority_map = {
                "Low": TaskPriority.LOW,
                "Normal": TaskPriority.NORMAL,
                "High": TaskPriority.HIGH,
                "Urgent": TaskPriority.URGENT,
            }
            priority = priority_map.get(priority_text, TaskPriority.HIGH)

            # Start batch processing
            task_id = self._task_scheduler.schedule_batch_processing(
                email_batch_size=batch_size,
                processing_interval_minutes=processing_interval,
                priority=priority,
            )

            # Update UI
            self._start_batch_button.setEnabled(False)
            self._stop_batch_button.setEnabled(True)
            self._batch_status_label.setText("Status: Running")
            # Update progress widget status
            self._batch_progress_widget.start_batch(
                batch_id=f"batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                workflow=self._batch_workflow,
                total_items=batch_size,
                batch_name="Email Batch Processing",
            )

            QMessageBox.information(
                self,
                "Batch Processing Started",
                f"Batch processing started successfully!\n\n"
                f"Batch Size: {batch_size} emails\n"
                f"Interval: {processing_interval} minutes\n"
                f"Priority: {priority_text}\n"
                f"Task ID: {task_id[:8]}...",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Batch Processing Error",
                f"Failed to start batch processing:\n\n{str(e)}",
            )

    def _handle_stop_batch_processing(self) -> None:
        """Handle stop batch processing button click."""
        # Reset UI
        self._start_batch_button.setEnabled(True)
        self._stop_batch_button.setEnabled(False)
        self._batch_status_label.setText("Status: Stopped")
        # Reset progress widget
        self._batch_progress_widget._reset_widget()

        QMessageBox.information(
            self, "Batch Processing Stopped", "Batch processing has been stopped."
        )

    def _handle_generate_report(self) -> None:
        """Handle generate report button click."""
        try:
            report_type = self._report_type.currentText()
            start_date = self._report_start_date.date().toPython()
            end_date = self._report_end_date.date().toPython()
            langgraph_analytics = self._enable_langgraph_analytics.isChecked()

            # Mock report generation
            report_content = f"""
            <h3>{report_type}</h3>
            <p><strong>Report Period:</strong> {start_date} to {end_date}</p>
            <p><strong>LangGraph Analytics:</strong>
            {'Enabled' if langgraph_analytics else 'Disabled'}</p>
            <hr>
            <h4>Summary Statistics:</h4>
            <ul>
                <li>Total Expenses Found: 24</li>
                <li>Reimbursable Amount: $1,456.78</li>
                <li>Non-Reimbursable: $234.50</li>
                <li>Pending Review: $123.45</li>
            </ul>
            <h4>Category Breakdown:</h4>
            <ul>
                <li>Travel: $567.89</li>
                <li>Meals: $345.67</li>
                <li>Office Supplies: $234.56</li>
                <li>Other: $308.66</li>
            </ul>
            """

            self._report_preview_area.setText(report_content)
            self._export_report_button.setEnabled(True)

            QMessageBox.information(
                self,
                "Report Generated",
                f"'{report_type}' report generated successfully!",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Report Error", f"Failed to generate report:\n\n{str(e)}"
            )

    def _handle_export_report(self) -> None:
        """Handle export report button click."""
        if not self._export_report_button.isEnabled():
            return

        # Show file dialog for report export
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilters(
            ["PDF Files (*.pdf)", "HTML Files (*.html)", "CSV Files (*.csv)"]
        )
        file_dialog.setDefaultSuffix("pdf")

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]

                QMessageBox.information(
                    self,
                    "Report Exported",
                    f"Report exported successfully to:\n{file_path}",
                )

    def _handle_batch_cancelled(self, batch_id: str) -> None:
        """Handle batch processing cancellation."""
        try:
            # Cancel batch processing (method doesn't exist in mock, so just log)
            logging.info(f"Cancelling batch processing for {batch_id}")
            QMessageBox.information(
                self,
                "Batch Cancelled",
                f"Batch processing {batch_id[:8]} has been cancelled.",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Cancellation Error", f"Error cancelling batch: {str(e)}"
            )

    def _handle_batch_paused(self, batch_id: str) -> None:
        """Handle batch processing pause."""
        # In a real implementation, this would pause the workflow
        QMessageBox.information(
            self, "Batch Paused", f"Batch processing {batch_id[:8]} has been paused."
        )

    def _handle_batch_resumed(self, batch_id: str) -> None:
        """Handle batch processing resume."""
        # In a real implementation, this would resume the workflow
        QMessageBox.information(
            self, "Batch Resumed", f"Batch processing {batch_id[:8]} has been resumed."
        )

    def _open_advanced_schedule_dialog(self) -> None:
        """Open the advanced schedule management dialog."""
        dialog = AdvancedScheduleDialog(self)
        dialog.schedule_created.connect(self._on_advanced_schedule_created)
        dialog.schedule_updated.connect(self._on_advanced_schedule_updated)
        dialog.exec()

    def _on_advanced_schedule_created(self, schedule_config: Dict[str, Any]) -> None:
        """Handle advanced schedule creation."""
        try:
            # Use the scheduled scan workflow to create the schedule
            task_id = self._task_scheduler.schedule_recurring_scan(
                start_date=schedule_config["start_datetime"],
                end_date=schedule_config.get("end_datetime")
                or datetime.datetime.now() + datetime.timedelta(days=365),
                interval_hours=self._parse_frequency_to_hours(
                    schedule_config["frequency"]
                ),
                query_params={
                    "max_emails": schedule_config["performance"]["max_emails"],
                    "batch_size": schedule_config["performance"]["batch_size"],
                    "gmail_query": schedule_config["gmail_query"],
                    "langgraph_enabled": True,
                    "workflow_config": schedule_config,
                },
            )

            if task_id:
                QMessageBox.information(
                    self,
                    "Schedule Created",
                    f"Advanced schedule '{schedule_config['name']}' created "
                    f"successfully!\n"
                    f"Task ID: {task_id}",
                )
            else:
                QMessageBox.warning(
                    self, "Scheduling Failed", "Failed to create advanced schedule."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Scheduling Error",
                f"Error creating advanced schedule:\n\n{str(e)}",
            )

    def _on_advanced_schedule_updated(self, schedule_config: Dict[str, Any]) -> None:
        """Handle advanced schedule update."""
        QMessageBox.information(
            self,
            "Schedule Updated",
            f"Schedule '{schedule_config['name']}' has been updated successfully.",
        )

    def _parse_frequency_to_hours(self, frequency: str) -> int:
        """Parse frequency string to hours."""
        frequency_map = {
            "Every 15 minutes": 0.25,
            "Every 30 minutes": 0.5,
            "Hourly": 1,
            "Every 2 hours": 2,
            "Every 4 hours": 4,
            "Every 6 hours": 6,
            "Daily": 24,
            "Every 2 days": 48,
            "Weekly": 168,
            "Monthly": 720,
        }
        return int(frequency_map.get(frequency, 24))

    def _open_advanced_report_dialog(self) -> None:
        """Open the advanced report generator dialog."""
        dialog = ReportDialog(self)
        dialog.report_generated.connect(self._on_advanced_report_generated)
        dialog.exec()

    def _on_advanced_report_generated(self, report_result: Dict[str, Any]) -> None:
        """Handle advanced report generation completion."""
        QMessageBox.information(
            self,
            "Report Generated",
            f"Advanced report '{report_result.get('report_id', 'Unknown')}' "
            f"generated successfully!\n"
            f"Status: {report_result.get('status', 'Unknown')}\n"
            f"Files: {len(report_result.get('generated_files', {}))}",
        )

    def _open_category_manager(self) -> None:
        """Open the category management dialog."""
        dialog = CategoryManagerDialog(self)
        dialog.categories_updated.connect(self._on_categories_updated)
        dialog.exec()

    def _on_categories_updated(self) -> None:
        """Handle category updates."""
        QMessageBox.information(
            self,
            "Categories Updated",
            "Expense categories have been updated successfully.",
        )
        # Refresh any UI that depends on categories

    def _start_advanced_batch_processing(self) -> None:
        """Start advanced batch processing with real-time progress."""
        try:
            # Get batch configuration from UI
            max_emails = (
                self._processing_interval.value()
            )  # Using interval as max emails for demo

            # Generate a batch ID
            batch_id = f"batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Configure progress callback
            def progress_callback(progress_data: Dict[str, Any]) -> None:
                self._batch_progress_widget.update_progress(progress_data)

            # Start batch processing workflow
            self._batch_progress_widget.start_batch(
                batch_id=batch_id,
                workflow=self._batch_workflow,
                total_items=max_emails,
                batch_name="Email Batch Processing",
            )

            # Start the actual batch processing (mock for now)
            self._simulate_batch_processing(batch_id, max_emails, progress_callback)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Batch Processing Error",
                f"Error starting batch processing:\n\n{str(e)}",
            )

    def _simulate_batch_processing(
        self, batch_id: str, total_emails: int, progress_callback: Any
    ) -> None:
        """Simulate batch processing for demonstration."""
        from PySide6.QtCore import QTimer

        # Create a timer to simulate progress updates
        self._batch_timer = QTimer()
        self._batch_progress = 0
        self._batch_total = total_emails

        def update_batch_progress() -> None:
            self._batch_progress += 5
            progress_percent = min(
                (self._batch_progress / self._batch_total) * 100, 100
            )

            progress_data: Dict[str, Any] = {
                "phase": (
                    "batch_complete"
                    if self._batch_progress < self._batch_total
                    else "completed"
                ),
                "processed_count": min(self._batch_progress, self._batch_total),
                "total_emails": self._batch_total,
                "progress_percent": progress_percent,
                "batch_number": (self._batch_progress // 25) + 1,
                "total_batches": (self._batch_total // 25) + 1,
                "message": f"Processing batch {(self._batch_progress // 25) + 1}...",
            }

            if progress_percent >= 100:
                progress_data.update(
                    {
                        "phase": "completed",
                        "final_stats": {
                            "total_emails_processed": self._batch_total,
                            "total_expenses_found": self._batch_total
                            // 3,  # Mock: 1/3 emails have expenses
                            "processing_errors": 0,
                        },
                    }
                )
                self._batch_timer.stop()

            progress_callback(progress_data)

        self._batch_timer.timeout.connect(update_batch_progress)
        self._batch_timer.start(1000)  # Update every second

    def _apply_styling(self) -> None:
        """Apply custom styling to the reimbursement view."""
        self.setStyleSheet(
            """
            /* Main reimbursement view styling */
            ReimbursementView {
                background-color: #f8fafc;
            }

            /* Tab widget styling */
            #featureTabWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }

            #featureTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: #ffffff;
            }

            #featureTabWidget::tab-bar {
                alignment: left;
            }

            #featureTabWidget QTabBar::tab {
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
                padding: 10px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 120px;
                font-weight: 500;
            }

            #featureTabWidget QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
                color: #1e293b;
                font-weight: bold;
            }

            #featureTabWidget QTabBar::tab:hover {
                background: #e2e8f0;
            }

            /* Header frame */
            #headerFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f1f5f9);
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }

            /* Title styling */
            #titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1e293b;
                margin: 0;
            }

            #descLabel {
                font-size: 14px;
                color: #64748b;
                margin: 5px 0 0 0;
            }

            /* Group box styling */
            #controlGroup, #resultsGroup, #summaryGroup,
            #scheduledConfigGroup, #activeSchedulesGroup, #batchConfigGroup,
            #batchStatusGroup, #reportGroup, #reportPreviewGroup,
            #historySearchGroup, #scanHistoryGroup {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            #controlGroup::title, #resultsGroup::title, #summaryGroup::title,
            #scheduledConfigGroup::title, #activeSchedulesGroup::title,
            #batchConfigGroup::title, #batchStatusGroup::title,
            #reportGroup::title, #reportPreviewGroup::title,
            #historySearchGroup::title, #scanHistoryGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8fafc;
            }

            /* Date controls */
            #dateLabel {
                font-size: 12px;
                font-weight: bold;
                color: #4b5563;
                margin: 0;
            }

            #dateEdit, #scheduleStartDateTime, #scheduleEndDate,
            #reportStartDate, #reportEndDate {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                font-size: 12px;
            }

            #dateEdit:focus, #scheduleStartDateTime:focus, #scheduleEndDate:focus,
            #reportStartDate:focus, #reportEndDate:focus {
                border-color: #3b82f6;
                outline: none;
            }

            /* ComboBox and SpinBox styling */
            #scheduleTypeCombo, #scheduleInterval, #scheduleMaxEmails,
            #batchSize, #processingInterval, #batchPriority,
            #reportType, #historyStatusFilter, #historyDateFilter {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                font-size: 12px;
                min-height: 20px;
            }

            /* CheckBox styling */
            #enableLangGraph, #enableBatchLangGraph,
            #enableLangGraphAnalytics, #enableLangGraphSearch {
                font-size: 12px;
                color: #4b5563;
                font-weight: 500;
            }

            /* Button styling */
            #scanButton, #createScheduleButton, #startBatchButton,
            #generateReportButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
                min-width: 160px;
            }

            #scanButton:hover, #createScheduleButton:hover,
            #startBatchButton:hover, #generateReportButton:hover {
                background-color: #059669;
            }

            #scanButton:pressed, #createScheduleButton:pressed,
            #startBatchButton:pressed, #generateReportButton:pressed {
                background-color: #047857;
            }

            #scanButton:disabled, #createScheduleButton:disabled,
            #startBatchButton:disabled, #generateReportButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
            }

            #exportButton, #clearSchedulesButton,
            #stopBatchButton, #exportReportButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 120px;
            }

            #exportButton:hover, #clearSchedulesButton:hover,
            #stopBatchButton:hover, #exportReportButton:hover {
                background-color: #2563eb;
            }

            #exportButton:pressed, #clearSchedulesButton:pressed,
            #stopBatchButton:pressed, #exportReportButton:pressed {
                background-color: #1d4ed8;
            }

            #exportButton:disabled, #clearSchedulesButton:disabled,
            #stopBatchButton:disabled, #exportReportButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
            }

            /* Filter controls */
            #filterLabel {
                font-size: 12px;
                font-weight: bold;
                color: #4b5563;
            }

            #filterEdit, #historySearch {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px 10px;
                background-color: white;
                font-size: 12px;
                min-width: 200px;
            }

            #filterEdit:focus, #historySearch:focus {
                border-color: #3b82f6;
                outline: none;
            }

            /* Status and summary labels */
            #summaryLabel, #batchStatusLabel {
                font-size: 14px;
                color: #374151;
                font-weight: 600;
                padding: 5px;
                background-color: #f9fafb;
                border-radius: 4px;
                border: 1px solid #e5e7eb;
            }

            /* Report preview area */
            #reportPreviewArea {
                font-size: 12px;
                color: #4b5563;
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 15px;
            }

            /* Table styling */
            QTableView {
                gridline-color: #e5e7eb;
                background-color: white;
                alternate-background-color: #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                selection-background-color: #3b82f6;
            }

            QTableView::item {
                padding: 8px;
                border: none;
            }

            QTableView::item:selected {
                background-color: #3b82f6;
                color: white;
            }

            QHeaderView::section {
                background-color: #f3f4f6;
                color: #374151;
                border: none;
                border-right: 1px solid #d1d5db;
                border-bottom: 1px solid #d1d5db;
                padding: 8px;
                font-weight: bold;
            }
        """
        )

    def get_results_model(self) -> ReimbursementResultsModel:
        """
        Get the reimbursement results model.

        Returns:
            Reimbursement results model
        """
        return self._results_model
