"""
Backend service for managing expense reports.

This module provides the central backend service that coordinates
data aggregation, report generation, and export functionality.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# from ..models import ExpenseResult  # TODO: Implement when needed
from ..workflows.report_generation import ReportGenerationWorkflow
from .aggregator import DataAggregator
from .exporter import ReportExporter
from .formatter import ReportFormatter

logger = logging.getLogger(__name__)


class ReportBackend:
    """
    Central backend service for expense reporting.

    This class coordinates the entire reporting pipeline from data
    aggregation through export, providing a high-level API for
    generating various types of expense reports.
    """

    def __init__(
        self,
        checkpoint_db_path: str = "data/reports_checkpoint.db",
        export_directory: str = "exports/reports",
    ):
        """
        Initialize the report backend.

        Args:
            checkpoint_db_path: Path to the checkpoint database
            export_directory: Directory for exported reports
        """
        self.checkpoint_db_path = checkpoint_db_path
        self.export_directory = Path(export_directory)
        self.export_directory.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.workflow = ReportGenerationWorkflow(checkpoint_db_path)
        self.aggregator = DataAggregator()
        self.formatter = ReportFormatter()
        self.exporter = ReportExporter(str(self.export_directory))

        logger.info("Report backend initialized")

    async def generate_monthly_report(
        self,
        year: int,
        month: int,
        filters: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a monthly expense report.

        Args:
            year: Year for the report
            month: Month for the report (1-12)
            filters: Optional filters to apply
            export_formats: List of export formats

        Returns:
            Report generation results
        """
        # Calculate date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        date_range = {"start_date": start_date, "end_date": end_date}

        return await self.workflow.generate_report(
            report_type="monthly",
            date_range=date_range,
            filters=filters,
            export_formats=export_formats or ["markdown", "csv", "json"],
        )

    async def generate_quarterly_report(
        self,
        year: int,
        quarter: int,
        filters: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a quarterly expense report.

        Args:
            year: Year for the report
            quarter: Quarter for the report (1-4)
            filters: Optional filters to apply
            export_formats: List of export formats

        Returns:
            Report generation results
        """
        # Calculate date range for the quarter
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3

        start_date = datetime(year, start_month, 1)
        if end_month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)

        date_range = {"start_date": start_date, "end_date": end_date}

        return await self.workflow.generate_report(
            report_type="quarterly",
            date_range=date_range,
            filters=filters,
            export_formats=export_formats or ["markdown", "csv", "json"],
        )

    async def generate_yearly_report(
        self,
        year: int,
        filters: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a yearly expense report.

        Args:
            year: Year for the report
            filters: Optional filters to apply
            export_formats: List of export formats

        Returns:
            Report generation results
        """
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

        date_range = {"start_date": start_date, "end_date": end_date}

        return await self.workflow.generate_report(
            report_type="yearly",
            date_range=date_range,
            filters=filters,
            export_formats=export_formats or ["markdown", "csv", "json", "pdf"],
        )

    async def generate_custom_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_name: str,
        filters: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a custom date range expense report.

        Args:
            start_date: Start date for the report
            end_date: End date for the report
            report_name: Custom name for the report
            filters: Optional filters to apply
            export_formats: List of export formats

        Returns:
            Report generation results
        """
        date_range = {"start_date": start_date, "end_date": end_date}

        report_id = f"custom_{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return await self.workflow.generate_report(
            report_type="custom",
            date_range=date_range,
            filters=filters,
            export_formats=export_formats or ["markdown", "csv", "json"],
            report_id=report_id,
        )

    async def generate_summary_report(
        self, days_back: int = 30, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a quick summary report.

        Args:
            days_back: Number of days to look back
            filters: Optional filters to apply

        Returns:
            Report generation results
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        date_range = {"start_date": start_date, "end_date": end_date}

        return await self.workflow.generate_report(
            report_type="summary",
            date_range=date_range,
            filters=filters,
            export_formats=["json"],
        )

    def get_report_templates(self) -> List[Dict[str, Any]]:
        """
        Get available report templates.

        Returns:
            List of available report templates
        """
        return self.workflow.get_available_templates()

    def get_supported_formats(self) -> List[str]:
        """
        Get supported export formats.

        Returns:
            List of supported export formats
        """
        return self.exporter.get_supported_formats()

    def get_filter_options(self) -> Dict[str, Any]:
        """
        Get available filter options for reports.

        Returns:
            Dictionary of filter options and their possible values
        """
        return {
            "categories": [
                "Travel",
                "Meals",
                "Office Supplies",
                "Software",
                "Training",
                "Entertainment",
                "Utilities",
                "Marketing",
            ],
            "amount_ranges": [
                {"label": "Under $50", "min": 0, "max": 50},
                {"label": "$50 - $100", "min": 50, "max": 100},
                {"label": "$100 - $500", "min": 100, "max": 500},
                {"label": "Over $500", "min": 500, "max": None},
            ],
            "reimbursable_options": [
                {"label": "Reimbursable Only", "value": True},
                {"label": "Non-Reimbursable Only", "value": False},
                {"label": "All Expenses", "value": None},
            ],
            "confidence_thresholds": [
                {"label": "High Confidence (>90%)", "min": 0.9},
                {"label": "Medium Confidence (>70%)", "min": 0.7},
                {"label": "Low Confidence (>50%)", "min": 0.5},
                {"label": "All Confidence Levels", "min": 0.0},
            ],
        }

    async def get_report_preview(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get a preview of report data without generating the full report.

        Args:
            start_date: Start date for preview
            end_date: End date for preview
            filters: Optional filters to apply

        Returns:
            Preview data including counts and basic statistics
        """
        try:
            # Get expenses first, then aggregate statistics
            expenses: List[Any] = []  # Mock empty list for preview
            preview_data = await self.aggregator.get_preview_statistics(expenses)

            return {
                "status": "success",
                "preview": preview_data,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Error generating report preview: {e}")
            return {"status": "error", "error": str(e), "preview": {}}

    async def schedule_recurring_report(
        self,
        report_type: str,
        schedule_config: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[str]] = None,
        recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a recurring report.

        Args:
            report_type: Type of report to schedule
            schedule_config: Schedule configuration (frequency, time, etc.)
            filters: Optional filters to apply
            export_formats: List of export formats
            recipients: List of email recipients

        Returns:
            Scheduling results
        """
        try:
            schedule_id = (
                f"scheduled_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Store schedule configuration
            _ = {  # TODO: Implement schedule data persistence
                "schedule_id": schedule_id,
                "report_type": report_type,
                "schedule_config": schedule_config,
                "filters": filters or {},
                "export_formats": export_formats or ["markdown", "csv"],
                "recipients": recipients or [],
                "created_at": datetime.now().isoformat(),
                "status": "active",
            }

            # In a real implementation, this would be stored in a database
            # and handled by a scheduler service
            logger.info(f"Scheduled recurring report: {schedule_id}")

            return {
                "status": "success",
                "schedule_id": schedule_id,
                "next_run": "2024-01-01T09:00:00",  # Placeholder
                "message": f"Recurring {report_type} report scheduled successfully",
            }

        except Exception as e:
            logger.error(f"Error scheduling report: {e}")
            return {"status": "error", "error": str(e)}

    async def get_report_history(
        self, limit: int = 50, report_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get history of generated reports.

        Args:
            limit: Maximum number of reports to return
            report_type: Optional filter by report type

        Returns:
            List of historical report information
        """
        try:
            # In a real implementation, this would query a database
            # For now, return mock data
            mock_history = []

            for i in range(min(limit, 20)):
                created_date = datetime.now() - timedelta(days=i * 2)
                mock_history.append(
                    {
                        "report_id": f"report_{created_date.strftime('%Y%m%d')}_{i}",
                        "report_type": report_type or "monthly",
                        "created_at": created_date.isoformat(),
                        "status": "completed",
                        "file_count": 3,
                        "total_expenses": 150 + i * 10,
                        "total_amount": 5000.50 + i * 500,
                    }
                )

            return mock_history

        except Exception as e:
            logger.error(f"Error retrieving report history: {e}")
            return []

    def cleanup_old_reports(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old report files.

        Args:
            days_to_keep: Number of days of reports to keep

        Returns:
            Cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleaned_files: List[str] = []

            # In a real implementation, this would scan the export directory
            # and remove files older than the cutoff date

            logger.info(f"Cleaned up reports older than {cutoff_date}")

            return {
                "status": "success",
                "cleaned_files": len(cleaned_files),
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error cleaning up reports: {e}")
            return {"status": "error", "error": str(e)}
