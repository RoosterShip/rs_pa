"""
Base SQLAlchemy model and database setup for RS Personal Agent.

This module provides the foundational database infrastructure using SQLAlchemy's
declarative base and common model patterns used throughout the application.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    """
    Base model class that provides common fields and functionality for all
    database models.

    All models inherit from this class to ensure consistent field naming,
    timestamps, and database table conventions.
    """

    # Automatically generate table name from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name in snake_case."""
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    # Primary key for all models
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, doc="Primary key identifier"
    )

    # Timestamp fields that are automatically managed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        doc="Timestamp when the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when the record was last updated",
    )

    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Returns:
            dict: Dictionary containing all model attributes and their values
        """
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    @classmethod
    def get_table_name(cls) -> str:
        """Get the database table name for this model."""
        return cls.__tablename__
