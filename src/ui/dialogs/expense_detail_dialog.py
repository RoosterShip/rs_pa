"""
Expense detail dialog for viewing individual expense information.

This module provides a QDialog for displaying detailed information
about a specific expense entry from the reimbursement scan results.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models.reimbursement_results_model import ExpenseData


class ExpenseDetailDialog(QDialog):
    """
    Dialog for displaying detailed expense information.

    This dialog shows comprehensive information about an expense entry
    including all metadata, AI analysis, and description details.
    """

    def __init__(self, expense: ExpenseData, parent: Optional[QWidget] = None):
        """
        Initialize the expense detail dialog.

        Args:
            expense: Expense data to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._expense = expense

        self._setup_dialog()
        self._setup_ui()
        self._populate_data()

    def _setup_dialog(self) -> None:
        """Set up basic dialog properties."""
        self.setWindowTitle(f"Expense Details - {self._expense.vendor}")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        self.resize(600, 700)

        # Center on parent
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, "geometry"):
            parent_geo = parent_widget.geometry()
            dialog_geo = self.geometry()
            x = parent_geo.center().x() - dialog_geo.width() // 2
            y = parent_geo.center().y() - dialog_geo.height() // 2
            self.move(x, y)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)

        # Header section
        header_widget = self._create_header_section()
        content_layout.addWidget(header_widget)

        # Basic information section
        basic_info_widget = self._create_basic_info_section()
        content_layout.addWidget(basic_info_widget)

        # Email information section
        email_info_widget = self._create_email_info_section()
        content_layout.addWidget(email_info_widget)

        # AI Analysis section
        ai_analysis_widget = self._create_ai_analysis_section()
        content_layout.addWidget(ai_analysis_widget)

        # Description section
        description_widget = self._create_description_section()
        content_layout.addWidget(description_widget)

        # Add stretch to push content to top
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Apply styling
        self._apply_styling()

    def _create_header_section(self) -> QWidget:
        """
        Create the header section with vendor and amount.

        Returns:
            Header widget
        """
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")

        layout = QVBoxLayout(header_widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # Vendor name
        vendor_label = QLabel(self._expense.vendor)
        vendor_label.setObjectName("vendorLabel")
        layout.addWidget(vendor_label)

        # Amount
        amount_label = QLabel(f"${self._expense.amount:.2f}")
        amount_label.setObjectName("amountLabel")
        layout.addWidget(amount_label)

        # Status
        status_label = QLabel(self._expense.status)
        status_label.setObjectName(
            f"status{self._expense.status.replace(' ', '').replace('-', '')}"
        )
        layout.addWidget(status_label)

        return header_widget

    def _create_basic_info_section(self) -> QWidget:
        """
        Create the basic information section.

        Returns:
            Basic info widget
        """
        basic_group = QGroupBox("Basic Information")
        basic_group.setObjectName("infoGroup")

        layout = QFormLayout(basic_group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Date
        date_label = QLabel(self._expense.date.strftime("%A, %B %d, %Y at %I:%M %p"))
        date_label.setObjectName("infoValue")
        layout.addRow("Date:", date_label)

        # Category
        category_label = QLabel(self._expense.category)
        category_label.setObjectName("infoValue")
        layout.addRow("Category:", category_label)

        # Email ID (if available)
        if self._expense.email_id:
            email_id_label = QLabel(self._expense.email_id)
            email_id_label.setObjectName("infoValue")
            layout.addRow("Email ID:", email_id_label)

        return basic_group

    def _create_email_info_section(self) -> QWidget:
        """
        Create the email information section.

        Returns:
            Email info widget
        """
        email_group = QGroupBox("Email Information")
        email_group.setObjectName("infoGroup")

        layout = QFormLayout(email_group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Subject
        subject_label = QLabel(self._expense.subject)
        subject_label.setObjectName("infoValue")
        subject_label.setWordWrap(True)
        layout.addRow("Subject:", subject_label)

        # Sender
        sender_label = QLabel(self._expense.sender)
        sender_label.setObjectName("infoValue")
        layout.addRow("Sender:", sender_label)

        return email_group

    def _create_ai_analysis_section(self) -> QWidget:
        """
        Create the AI analysis section.

        Returns:
            AI analysis widget
        """
        ai_group = QGroupBox("AI Analysis")
        ai_group.setObjectName("infoGroup")

        layout = QFormLayout(ai_group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Confidence score
        confidence_widget = QWidget()
        confidence_layout = QHBoxLayout(confidence_widget)
        confidence_layout.setContentsMargins(0, 0, 0, 0)

        confidence_label = QLabel(f"{self._expense.confidence:.1f}%")
        confidence_label.setObjectName("confidenceValue")
        confidence_layout.addWidget(confidence_label)

        # Confidence bar (visual representation)
        confidence_bar = self._create_confidence_bar()
        confidence_layout.addWidget(confidence_bar)
        confidence_layout.addStretch()

        layout.addRow("Confidence:", confidence_widget)

        # Status explanation
        status_explanation = self._get_status_explanation()
        explanation_label = QLabel(status_explanation)
        explanation_label.setObjectName("explanationText")
        explanation_label.setWordWrap(True)
        layout.addRow("Analysis:", explanation_label)

        return ai_group

    def _create_description_section(self) -> QWidget:
        """
        Create the description section.

        Returns:
            Description widget
        """
        desc_group = QGroupBox("Description")
        desc_group.setObjectName("infoGroup")

        layout = QVBoxLayout(desc_group)
        layout.setContentsMargins(15, 15, 15, 15)

        # Description text
        desc_text = QTextEdit()
        desc_text.setObjectName("descriptionText")
        desc_text.setPlainText(self._expense.description)
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(100)
        layout.addWidget(desc_text)

        return desc_group

    def _create_confidence_bar(self) -> QWidget:
        """
        Create a visual confidence bar.

        Returns:
            Confidence bar widget
        """
        bar_widget = QWidget()
        bar_widget.setObjectName("confidenceBar")
        bar_widget.setFixedHeight(10)
        bar_widget.setMinimumWidth(100)
        bar_widget.setMaximumWidth(150)

        # Set dynamic background based on confidence
        confidence_percent = int(self._expense.confidence)
        color = self._get_confidence_color(confidence_percent)

        # Split long gradient lines for readability
        confidence_ratio = confidence_percent / 100
        bar_widget.setStyleSheet(
            f"""
            #confidenceBar {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: {confidence_ratio:.2f}, y2: 0,
                    stop: 0 {color}, stop: 1 {color}
                ),
                qlineargradient(
                    x1: {confidence_ratio:.2f}, y1: 0, x2: 1, y2: 0,
                    stop: 0 #e5e7eb, stop: 1 #e5e7eb
                );
                border: 1px solid #d1d5db;
                border-radius: 5px;
            }}
        """
        )

        return bar_widget

    def _get_confidence_color(self, confidence: int) -> str:
        """
        Get color based on confidence level.

        Args:
            confidence: Confidence percentage (0-100)

        Returns:
            Color hex string
        """
        if confidence >= 90:
            return "#22c55e"  # Green
        elif confidence >= 75:
            return "#eab308"  # Yellow
        elif confidence >= 50:
            return "#f97316"  # Orange
        else:
            return "#ef4444"  # Red

    def _get_status_explanation(self) -> str:
        """
        Get explanation text for the current status.

        Returns:
            Status explanation text
        """
        explanations = {
            "Reimbursable": (
                "This expense has been identified as eligible for "
                "reimbursement based on company policy and the information "
                "extracted from the email."
            ),
            "Non-Reimbursable": (
                "This expense has been identified as personal or otherwise "
                "not eligible for reimbursement based on the email content "
                "and company policy."
            ),
            "Pending Review": (
                "This expense requires manual review to determine "
                "reimbursement eligibility. The AI was unable to make "
                "a definitive classification."
            ),
        }

        return explanations.get(
            self._expense.status, "No explanation available for this status."
        )

    def _populate_data(self) -> None:
        """Populate the dialog with expense data."""
        # Data is populated during widget creation
        pass

    def _apply_styling(self) -> None:
        """Apply custom styling to the dialog."""
        self.setStyleSheet(
            """
            /* Dialog background */
            ExpenseDetailDialog {
                background-color: #f8fafc;
            }

            /* Header widget */
            #headerWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f1f5f9);
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                margin-bottom: 10px;
            }

            /* Vendor label */
            #vendorLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1e293b;
                margin: 0;
            }

            /* Amount label */
            #amountLabel {
                font-size: 18px;
                font-weight: bold;
                color: #059669;
                margin: 5px 0 0 0;
            }

            /* Status labels */
            #statusReimbursable {
                font-size: 14px;
                font-weight: bold;
                color: #22c55e;
                background-color: #dcfce7;
                padding: 4px 8px;
                border-radius: 4px;
                margin: 5px 0 0 0;
            }

            #statusNonReimbursable {
                font-size: 14px;
                font-weight: bold;
                color: #ef4444;
                background-color: #fee2e2;
                padding: 4px 8px;
                border-radius: 4px;
                margin: 5px 0 0 0;
            }

            #statusPendingReview {
                font-size: 14px;
                font-weight: bold;
                color: #f59e0b;
                background-color: #fef3c7;
                padding: 4px 8px;
                border-radius: 4px;
                margin: 5px 0 0 0;
            }

            /* Group boxes */
            #infoGroup {
                font-size: 14px;
                font-weight: bold;
                color: #374151;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            #infoGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8fafc;
            }

            /* Info values */
            #infoValue {
                font-size: 13px;
                color: #1f2937;
                font-weight: normal;
                padding: 2px 0;
            }

            /* Confidence value */
            #confidenceValue {
                font-size: 14px;
                font-weight: bold;
                color: #059669;
                margin-right: 10px;
            }

            /* Explanation text */
            #explanationText {
                font-size: 12px;
                color: #4b5563;
                font-weight: normal;
                font-style: italic;
                line-height: 1.4;
            }

            /* Description text */
            #descriptionText {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 12px;
                color: #374151;
                font-family: "Consolas", "Monaco", monospace;
                padding: 8px;
            }

            /* Scroll area */
            QScrollArea {
                border: none;
                background-color: transparent;
            }

            /* Scroll bars */
            QScrollBar:vertical {
                background-color: #f3f4f6;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #d1d5db;
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #9ca3af;
            }

            /* Button box */
            QDialogButtonBox {
                margin-top: 15px;
            }

            QDialogButtonBox QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }

            QDialogButtonBox QPushButton:hover {
                background-color: #2563eb;
            }

            QDialogButtonBox QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """
        )
