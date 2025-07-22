"""
Reimbursement results table model for Qt Model-View architecture.

This module provides a QAbstractTableModel for displaying expense scan results
in a QTableView with proper sorting, filtering, and custom styling.
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Optional, Union

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import QWidget


@dataclass
class ExpenseData:
    """Data class representing an expense entry from email scan."""

    date: datetime
    subject: str
    sender: str
    vendor: str
    amount: float
    category: str
    status: str  # "Reimbursable", "Non-Reimbursable", "Pending Review"
    description: str = ""
    confidence: float = 0.0  # AI confidence score (0-100)
    email_id: Optional[str] = None


class ReimbursementResultsModel(QAbstractTableModel):
    """
    Table model for displaying reimbursement expense scan results.

    This model provides data for displaying expense entries with columns for
    date, subject, sender, vendor, amount, category, and status.
    """

    # Column definitions
    COLUMN_DATE = 0
    COLUMN_SUBJECT = 1
    COLUMN_SENDER = 2
    COLUMN_VENDOR = 3
    COLUMN_AMOUNT = 4
    COLUMN_CATEGORY = 5
    COLUMN_STATUS = 6

    COLUMN_COUNT = 7

    COLUMN_HEADERS = [
        "Date",
        "Email Subject",
        "Sender",
        "Vendor",
        "Amount",
        "Category",
        "Status",
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the reimbursement results table model.

        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self._expenses: List[ExpenseData] = []

    def generate_mock_results(self) -> None:
        """Generate mock expense scan results for demonstration."""
        self.beginResetModel()

        # Mock data for demonstration
        mock_expenses = [
            ExpenseData(
                date=datetime.now() - timedelta(days=2),
                subject="Receipt - Office Supplies Purchase",
                sender="receipts@staples.com",
                vendor="Staples Inc.",
                amount=127.89,
                category="Office Supplies",
                status="Reimbursable",
                description="Paper, pens, and folders for quarterly reports",
                confidence=95.2,
                email_id="msg001",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=5),
                subject="Your Uber Receipt",
                sender="noreply@uber.com",
                vendor="Uber Technologies",
                amount=34.50,
                category="Transportation",
                status="Reimbursable",
                description="Airport to client meeting - Project Alpha",
                confidence=92.8,
                email_id="msg002",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=7),
                subject="Hotel Confirmation - Downtown Convention Center",
                sender="reservations@marriott.com",
                vendor="Marriott Hotels",
                amount=289.99,
                category="Accommodation",
                status="Pending Review",
                description="2 nights for conference attendance",
                confidence=87.5,
                email_id="msg003",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=10),
                subject="Lunch Receipt - Client Meeting",
                sender="receipts@thenicerestaurant.com",
                vendor="The Nice Restaurant",
                amount=156.78,
                category="Meals & Entertainment",
                status="Reimbursable",
                description="Lunch with potential client - Project Beta discussion",
                confidence=88.9,
                email_id="msg004",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=12),
                subject="Amazon Order Confirmation",
                sender="auto-confirm@amazon.com",
                vendor="Amazon.com",
                amount=89.99,
                category="Electronics",
                status="Non-Reimbursable",
                description="Personal purchase - wireless headphones",
                confidence=91.3,
                email_id="msg005",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=15),
                subject="Gas Station Receipt",
                sender="receipts@shell.com",
                vendor="Shell",
                amount=45.67,
                category="Transportation",
                status="Reimbursable",
                description="Fuel for client visit trip",
                confidence=85.4,
                email_id="msg006",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=18),
                subject="Software Subscription Renewal",
                sender="billing@adobe.com",
                vendor="Adobe Systems",
                amount=52.99,
                category="Software",
                status="Pending Review",
                description="Creative Cloud subscription - monthly",
                confidence=94.7,
                email_id="msg007",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=20),
                subject="Coffee Shop Receipt",
                sender="receipts@starbucks.com",
                vendor="Starbucks",
                amount=12.45,
                category="Meals & Entertainment",
                status="Non-Reimbursable",
                description="Personal coffee purchase",
                confidence=76.2,
                email_id="msg008",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=22),
                subject="Conference Registration Confirmation",
                sender="events@techconf2024.com",
                vendor="TechConf 2024",
                amount=599.00,
                category="Training & Education",
                status="Reimbursable",
                description="Annual technology conference registration",
                confidence=98.1,
                email_id="msg009",
            ),
            ExpenseData(
                date=datetime.now() - timedelta(days=25),
                subject="Parking Receipt - Downtown",
                sender="receipts@parkingco.com",
                vendor="City Parking",
                amount=18.00,
                category="Transportation",
                status="Reimbursable",
                description="Client meeting parking - 4 hours",
                confidence=82.6,
                email_id="msg010",
            ),
        ]

        # Add some randomization to make it more realistic
        for expense in mock_expenses:
            # Add small random variations to amounts
            variance = random.uniform(-0.05, 0.05) * expense.amount
            expense.amount += variance
            expense.amount = round(expense.amount, 2)

            # Add small random variations to confidence
            conf_variance = random.uniform(-3, 3)
            expense.confidence += conf_variance
            expense.confidence = max(50.0, min(99.9, expense.confidence))
            expense.confidence = round(expense.confidence, 1)

        self._expenses = mock_expenses
        self.endResetModel()

    def rowCount(
        self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()
    ) -> int:
        """
        Return the number of rows in the model.

        Args:
            parent: Parent index

        Returns:
            Number of expenses
        """
        return len(self._expenses)

    def columnCount(
        self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()
    ) -> int:
        """
        Return the number of columns in the model.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        return self.COLUMN_COUNT

    def data(
        self,
        index: Union[QModelIndex, QPersistentModelIndex],
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """
        Return data for the given index and role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data for the index and role
        """
        if not index.isValid() or index.row() >= len(self._expenses):
            return None

        expense = self._expenses[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(expense, column)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self._get_background_color(expense)
        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_text_color(expense)
        elif role == Qt.ItemDataRole.FontRole:
            return self._get_font(expense, column)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._get_tooltip(expense)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return self._get_alignment(column)

        return None

    def _get_display_data(self, expense: ExpenseData, column: int) -> str:
        """
        Get display data for a specific column.

        Args:
            expense: Expense data
            column: Column index

        Returns:
            Display string
        """
        if column == self.COLUMN_DATE:
            return expense.date.strftime("%Y-%m-%d")
        elif column == self.COLUMN_SUBJECT:
            return expense.subject
        elif column == self.COLUMN_SENDER:
            return expense.sender
        elif column == self.COLUMN_VENDOR:
            return expense.vendor
        elif column == self.COLUMN_AMOUNT:
            return f"${expense.amount:.2f}"
        elif column == self.COLUMN_CATEGORY:
            return expense.category
        elif column == self.COLUMN_STATUS:
            return self._format_status_with_icon(expense.status)

        return ""

    def _format_status_with_icon(self, status: str) -> str:
        """
        Format status with appropriate icon.

        Args:
            status: Status string

        Returns:
            Formatted status with icon
        """
        status_icons = {
            "Reimbursable": "✅ Reimbursable",
            "Non-Reimbursable": "❌ Non-Reimbursable",
            "Pending Review": "⏳ Pending Review",
        }
        return status_icons.get(status, f"❓ {status}")

    def _get_background_color(self, expense: ExpenseData) -> QBrush:
        """
        Get background color based on expense status.

        Args:
            expense: Expense data

        Returns:
            Background brush
        """
        colors = {
            "Reimbursable": QColor(240, 253, 244),  # Light green
            "Non-Reimbursable": QColor(254, 242, 242),  # Light red
            "Pending Review": QColor(255, 251, 235),  # Light yellow
        }

        color = colors.get(expense.status, QColor(255, 255, 255))
        return QBrush(color)

    def _get_text_color(self, expense: ExpenseData) -> QBrush:
        """
        Get text color based on expense status.

        Args:
            expense: Expense data

        Returns:
            Text color brush
        """
        colors = {
            "Reimbursable": QColor(22, 163, 74),  # Green
            "Non-Reimbursable": QColor(220, 38, 38),  # Red
            "Pending Review": QColor(217, 119, 6),  # Orange
        }

        color = colors.get(expense.status, QColor(17, 24, 39))  # Default dark
        return QBrush(color)

    def _get_font(self, expense: ExpenseData, column: int) -> QFont:
        """
        Get font for a specific cell.

        Args:
            expense: Expense data
            column: Column index

        Returns:
            Font object
        """
        font = QFont()

        # Make vendor and amount bold
        if column in [self.COLUMN_VENDOR, self.COLUMN_AMOUNT]:
            font.setBold(True)

        # Make status column slightly larger
        if column == self.COLUMN_STATUS:
            font.setPointSize(font.pointSize() + 1)

        return font

    def _get_tooltip(self, expense: ExpenseData) -> str:
        """
        Get tooltip text for an expense.

        Args:
            expense: Expense data

        Returns:
            Tooltip string
        """
        return f"""<b>{expense.vendor}</b> - ${expense.amount:.2f}<br/>
<b>Date:</b> {expense.date.strftime('%Y-%m-%d %H:%M')}<br/>
<b>Category:</b> {expense.category}<br/>
<b>Status:</b> {expense.status}<br/>
<b>Confidence:</b> {expense.confidence:.1f}%<br/>
<b>Email:</b> {expense.subject}<br/>
<b>From:</b> {expense.sender}<br/><br/>
<b>Description:</b><br/>
{expense.description}"""

    def _get_alignment(self, column: int) -> int:
        """
        Get text alignment for a column.

        Args:
            column: Column index

        Returns:
            Alignment flag
        """
        if column == self.COLUMN_AMOUNT:
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        elif column == self.COLUMN_STATUS:
            return Qt.AlignmentFlag.AlignCenter
        else:
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """
        Return header data.

        Args:
            section: Section index
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if 0 <= section < len(self.COLUMN_HEADERS):
                return self.COLUMN_HEADERS[section]
        elif (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.FontRole
        ):
            font = QFont()
            font.setBold(True)
            return font

        return None

    def get_expense_at_row(self, row: int) -> Optional[ExpenseData]:
        """
        Get expense data for a specific row.

        Args:
            row: Row index

        Returns:
            Expense data or None if invalid row
        """
        if 0 <= row < len(self._expenses):
            return self._expenses[row]
        return None

    def clear_results(self) -> None:
        """Clear all results from the model."""
        self.beginResetModel()
        self._expenses = []
        self.endResetModel()

    def add_expense(self, expense: ExpenseData) -> None:
        """
        Add a new expense to the model.

        Args:
            expense: Expense data to add
        """
        row_count = len(self._expenses)
        self.beginInsertRows(QModelIndex(), row_count, row_count)
        self._expenses.append(expense)
        self.endInsertRows()

    def update_expense_status(self, row: int, new_status: str) -> bool:
        """
        Update the status of an expense.

        Args:
            row: Row index
            new_status: New status

        Returns:
            True if updated successfully
        """
        if 0 <= row < len(self._expenses):
            self._expenses[row].status = new_status

            # Emit data changed signal
            start_index = self.index(row, 0)
            end_index = self.index(row, self.COLUMN_COUNT - 1)
            self.dataChanged.emit(start_index, end_index)

            return True

        return False

    def get_summary_statistics(self) -> dict[str, Union[float, int]]:
        """
        Get summary statistics for all expenses.

        Returns:
            Dictionary with summary statistics
        """
        if not self._expenses:
            return {
                "total_amount": 0.0,
                "reimbursable_count": 0,
                "non_reimbursable_count": 0,
                "pending_count": 0,
                "total_count": 0,
            }

        total_amount = sum(expense.amount for expense in self._expenses)
        reimbursable_count = sum(
            1 for expense in self._expenses if expense.status == "Reimbursable"
        )
        non_reimbursable_count = sum(
            1 for expense in self._expenses if expense.status == "Non-Reimbursable"
        )
        pending_count = sum(
            1 for expense in self._expenses if expense.status == "Pending Review"
        )

        return {
            "total_amount": total_amount,
            "reimbursable_count": reimbursable_count,
            "non_reimbursable_count": non_reimbursable_count,
            "pending_count": pending_count,
            "total_count": len(self._expenses),
        }
