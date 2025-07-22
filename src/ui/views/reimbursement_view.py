"""
Reimbursement Agent view for processing expense reimbursements.

This module provides a Qt widget interface for the reimbursement agent
with date selection, scanning controls, results table, and export functionality.
"""

import datetime
from typing import Any, Dict, Optional

from PySide6.QtCore import QDate, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ...agents.reimbursement.agent import ReimbursementAgent
from ..dialogs.expense_detail_dialog import ExpenseDetailDialog
from ..models.reimbursement_results_model import ReimbursementResultsModel
from ..widgets.progress_widget import ProgressWidget


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

        self._setup_ui()
        self._setup_connections()
        self._setup_agent_connections()
        self._setup_mock_data()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header section
        header_widget = self._create_header_section()
        main_layout.addWidget(header_widget)

        # Control section
        control_widget = self._create_control_section()
        main_layout.addWidget(control_widget)

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

        main_layout.addWidget(splitter)

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
        # Button connections
        self._scan_button.clicked.connect(self._handle_scan_request)
        self._export_button.clicked.connect(self._handle_export_request)

        # Filter connection
        self._filter_edit.textChanged.connect(self._handle_filter_change)

        # Model connections
        self._results_model.dataChanged.connect(self._update_summary)
        self._results_model.modelReset.connect(self._update_summary)

    def _setup_agent_connections(self) -> None:
        """Set up reimbursement agent signal connections."""
        self._agent.status_changed.connect(self._handle_agent_status_change)
        self._agent.progress_updated.connect(self._handle_agent_progress)
        self._agent.result_ready.connect(self._handle_agent_result)
        self._agent.error_occurred.connect(self._handle_agent_error)

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

    def _apply_styling(self) -> None:
        """Apply custom styling to the reimbursement view."""
        self.setStyleSheet(
            """
            /* Main reimbursement view styling */
            ReimbursementView {
                background-color: #f8fafc;
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
            #controlGroup, #resultsGroup, #summaryGroup {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            #controlGroup::title, #resultsGroup::title, #summaryGroup::title {
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

            #dateEdit {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                font-size: 12px;
            }

            #dateEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }

            /* Button styling */
            #scanButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
            }

            #scanButton:hover {
                background-color: #059669;
            }

            #scanButton:pressed {
                background-color: #047857;
            }

            #scanButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
            }

            #exportButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 120px;
            }

            #exportButton:hover {
                background-color: #2563eb;
            }

            #exportButton:pressed {
                background-color: #1d4ed8;
            }

            #exportButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
            }

            /* Filter controls */
            #filterLabel {
                font-size: 12px;
                font-weight: bold;
                color: #4b5563;
            }

            #filterEdit {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px 10px;
                background-color: white;
                font-size: 12px;
                min-width: 200px;
            }

            #filterEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }

            /* Summary labels */
            #summaryLabel {
                font-size: 14px;
                color: #374151;
                font-weight: 600;
                padding: 5px;
                background-color: #f9fafb;
                border-radius: 4px;
                border: 1px solid #e5e7eb;
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
