"""
SQLAlchemy models for reimbursement agent data structures.

This module defines database models for expense scans and results
used by the reimbursement agent.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ...models.base import BaseModel


class ExpenseScan(BaseModel):
    """
    Model for expense scan sessions.

    Represents a scanning session where the agent processes emails
    looking for expenses and reimbursements.
    """

    __tablename__ = "expense_scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100), nullable=False, index=True)

    # Scan metadata
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(
        String(50), default="running", nullable=False
    )  # running, completed, error

    # Scan parameters
    gmail_query = Column(String(500), nullable=True)  # Gmail search query used
    max_emails = Column(Integer, default=10, nullable=False)

    # Results summary
    emails_processed = Column(Integer, default=0, nullable=False)
    expenses_found = Column(Integer, default=0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)

    # Error information
    error_message = Column(Text, nullable=True)

    # Relationships
    expense_results = relationship(
        "ExpenseResult", back_populates="scan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ExpenseScan(id={self.id}, agent_id='{self.agent_id}', "
            f"status='{self.status}')>"
        )


class ExpenseResult(BaseModel):
    """
    Model for individual expense detection results.

    Represents a detected expense from an email with extracted
    information and metadata.
    """

    __tablename__ = "expense_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(
        Integer, ForeignKey("expense_scans.id", ondelete="CASCADE"), nullable=False
    )

    # Gmail message information
    gmail_message_id = Column(String(100), nullable=False, index=True)
    gmail_thread_id = Column(String(100), nullable=True)

    # Email metadata
    email_subject = Column(String(500), nullable=True)
    email_from = Column(String(200), nullable=True)
    email_date = Column(DateTime, nullable=True)

    # Extracted expense information
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    vendor = Column(String(200), nullable=True)
    expense_date = Column(DateTime, nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Detection confidence and metadata
    confidence_score = Column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    detection_method = Column(
        String(100), nullable=True
    )  # e.g., "keyword_match", "llm_extraction"

    # Reimbursement status
    is_reimbursable = Column(Boolean, default=False, nullable=False)

    # Processing metadata
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scan = relationship("ExpenseScan", back_populates="expense_results")

    @property
    def date(self) -> Optional[datetime]:
        """Return the most relevant date (expense_date or email_date)."""
        expense_date = getattr(self, "expense_date", None)
        email_date = getattr(self, "email_date", None)
        return expense_date or email_date

    @property
    def email_id(self) -> str:
        """Alias for gmail_message_id for compatibility."""
        return str(getattr(self, "gmail_message_id", ""))

    def __repr__(self) -> str:
        return (
            f"<ExpenseResult(id={self.id}, amount={self.amount}, "
            f"vendor='{self.vendor}')>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "gmail_message_id": self.gmail_message_id,
            "email_subject": self.email_subject,
            "email_from": self.email_from,
            "email_date": self.email_date.isoformat() if self.email_date else None,
            "amount": self.amount,
            "currency": self.currency,
            "vendor": self.vendor,
            "expense_date": (
                self.expense_date.isoformat() if self.expense_date else None
            ),
            "category": self.category,
            "description": self.description,
            "confidence_score": self.confidence_score,
            "detection_method": self.detection_method,
            "processed_at": self.processed_at.isoformat(),
        }
