"""
Database management for RS Personal Agent.

This module provides SQLAlchemy session management, database connection handling,
and database initialization functionality using environment-based configuration.
"""

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

import structlog
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..models.base import BaseModel

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions for the RS Personal Agent.

    Provides thread-safe database session management with automatic connection
    pooling and supports both development (SQLite) and production database
    configurations.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False,
        backup_before_migration: bool = True,
        backup_count: int = 5,
    ) -> None:
        """
        Initialize the database manager.

        Args:
            database_url: Database connection URL. If None, uses environment
                variable or default
            echo: Whether to echo SQL statements to logs
            backup_before_migration: Whether to backup database before migrations
            backup_count: Number of database backups to keep
        """
        self.database_url = database_url or self._get_database_url()
        self.echo = echo or self._get_debug_mode()
        self.backup_before_migration = backup_before_migration
        self.backup_count = backup_count

        logger.info(
            "Initializing database manager",
            database_url=self._sanitize_url(self.database_url),
            echo=self.echo,
        )

        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Enable foreign key constraints for SQLite
        if self.database_url.startswith("sqlite"):
            self._enable_sqlite_foreign_keys()

    def _get_database_url(self) -> str:
        """Get database URL from environment variables or use default."""
        url = os.getenv("RSPA_DATABASE_URL")
        if url:
            return url

        # Default to SQLite in project data directory
        app_dir = Path.home() / ".rs_personal_agent"
        app_dir.mkdir(exist_ok=True)
        db_path = app_dir / "rs_personal_agent.db"
        return f"sqlite:///{db_path}"

    def _get_debug_mode(self) -> bool:
        """Get debug mode setting from environment variables."""
        debug = os.getenv("RSPA_DATABASE_DEV_MODE", "false").lower()
        return debug in ("true", "1", "yes", "on")

    def _sanitize_url(self, url: str) -> str:
        """Remove sensitive information from database URL for logging."""
        # Simple sanitization - replace password if present
        if "@" in url and "://" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                credentials, host_part = rest.split("@", 1)
                if ":" in credentials:
                    user, _ = credentials.split(":", 1)
                    return f"{protocol}://{user}:***@{host_part}"
        return url

    def _create_engine(self) -> Engine:
        """Create and configure the SQLAlchemy engine."""
        if self.database_url.startswith("sqlite"):
            # SQLite-specific configuration
            engine = create_engine(
                self.database_url,
                echo=self.echo,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False, "timeout": 20},
                pool_pre_ping=True,
            )
        else:
            # Configuration for other database types
            engine = create_engine(
                self.database_url, echo=self.echo, pool_pre_ping=True, pool_recycle=300
            )

        logger.info("Database engine created successfully")
        return engine

    def _enable_sqlite_foreign_keys(self) -> None:
        """Enable foreign key constraints for SQLite databases."""

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.debug("SQLite foreign key constraints enabled")

    def create_database(self) -> None:
        """
        Create all database tables based on the defined models.

        This method creates the database schema by running the DDL for all
        models that inherit from BaseModel.
        """
        logger.info("Creating database tables")
        try:
            BaseModel.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise

    def drop_database(self) -> None:
        """
        Drop all database tables.

        WARNING: This will delete all data in the database. Use with caution.
        """
        logger.warning("Dropping all database tables")
        try:
            BaseModel.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error("Failed to drop database tables", error=str(e))
            raise

    def backup_database(self, backup_path: Optional[str] = None) -> Optional[str]:
        """
        Create a backup of the database (SQLite only).

        Args:
            backup_path: Optional path for the backup file

        Returns:
            Path to the backup file if successful, None otherwise
        """
        if not self.database_url.startswith("sqlite"):
            logger.warning("Database backup only supported for SQLite databases")
            return None

        try:
            # Extract database file path from URL
            db_path = self.database_url.replace("sqlite:///", "")
            db_file = Path(db_path)

            if not db_file.exists():
                logger.warning("Database file does not exist, skipping backup")
                return None

            if backup_path is None:
                backup_path = f"{db_path}.backup"

            shutil.copy2(db_path, backup_path)
            logger.info("Database backed up successfully", backup_path=backup_path)
            return backup_path

        except Exception as e:
            logger.error("Failed to backup database", error=str(e))
            return None

    def get_session(self) -> Session:
        """
        Create a new database session.

        Returns:
            SQLAlchemy session instance
        """
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            SQLAlchemy session with automatic commit/rollback handling
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session rolled back due to error", error=str(e))
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            return False

    def get_database_info(self) -> dict[str, Any]:
        """
        Get information about the database connection.

        Returns:
            Dictionary containing database connection information
        """
        return {
            "database_url": self._sanitize_url(self.database_url),
            "engine_name": self.engine.name,
            "echo": self.echo,
            "pool_size": getattr(self.engine.pool, "size", None),
            "pool_checked_out": getattr(self.engine.pool, "checkedout", None),
        }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(
    database_url: Optional[str] = None, **kwargs: Any
) -> DatabaseManager:
    """
    Get the global database manager instance.

    Args:
        database_url: Optional database URL for initialization
        **kwargs: Additional arguments for DatabaseManager initialization

    Returns:
        Global DatabaseManager instance
    """
    global _db_manager

    if _db_manager is None:
        _db_manager = DatabaseManager(database_url=database_url, **kwargs)

    return _db_manager


def initialize_database(
    database_url: Optional[str] = None, create_tables: bool = True, **kwargs: Any
) -> DatabaseManager:
    """
    Initialize the database system.

    Args:
        database_url: Optional database URL
        create_tables: Whether to create database tables
        **kwargs: Additional arguments for DatabaseManager

    Returns:
        Initialized DatabaseManager instance
    """
    db_manager = get_database_manager(database_url=database_url, **kwargs)

    if create_tables:
        db_manager.create_database()

    return db_manager


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Convenience function to get a database session with automatic cleanup.

    Yields:
        SQLAlchemy session instance
    """
    db_manager = get_database_manager()
    with db_manager.session_scope() as session:
        yield session
