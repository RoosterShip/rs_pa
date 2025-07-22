"""
Report export service for multiple output formats.

This module handles the export of formatted reports to various
file formats and locations including local files, email, and cloud storage.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ReportExporter:
    """
    Service for exporting formatted reports to various destinations.

    Handles export to local files, email delivery, and cloud storage
    with support for multiple formats including PDF, CSV, Excel, and more.
    """

    def __init__(
        self,
        export_directory: str = "exports/reports",
        temp_directory: str = "/tmp/reports",
    ):
        """
        Initialize the report exporter.

        Args:
            export_directory: Base directory for exported reports
            temp_directory: Temporary directory for processing
        """
        self.export_directory = Path(export_directory)
        self.temp_directory = Path(temp_directory)

        # Ensure directories exist
        self.export_directory.mkdir(parents=True, exist_ok=True)
        self.temp_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Report exporter initialized with export dir: {export_directory}")

    def export_to_markdown(
        self, content: str, filename: str, subfolder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export report content to a Markdown file.

        Args:
            content: Markdown content to export
            filename: Base filename (without extension)
            subfolder: Optional subfolder within export directory

        Returns:
            Export result with file path and status
        """
        try:
            # Construct file path
            if subfolder:
                output_dir = self.export_directory / subfolder
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self.export_directory

            file_path = output_dir / f"{filename}.md"

            # Write content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Exported Markdown report to: {file_path}")

            return {
                "status": "success",
                "format": "markdown",
                "file_path": str(file_path),
                "file_size": os.path.getsize(file_path),
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting Markdown report: {e}")
            return {"status": "error", "format": "markdown", "error": str(e)}

    def export_to_csv(
        self, content: str, filename: str, subfolder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export report content to a CSV file.

        Args:
            content: CSV content to export
            filename: Base filename (without extension)
            subfolder: Optional subfolder within export directory

        Returns:
            Export result with file path and status
        """
        try:
            # Construct file path
            if subfolder:
                output_dir = self.export_directory / subfolder
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self.export_directory

            file_path = output_dir / f"{filename}.csv"

            # Write content to file
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(content)

            logger.info(f"Exported CSV report to: {file_path}")

            return {
                "status": "success",
                "format": "csv",
                "file_path": str(file_path),
                "file_size": os.path.getsize(file_path),
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting CSV report: {e}")
            return {"status": "error", "format": "csv", "error": str(e)}

    def export_to_json(
        self,
        data: Dict[str, Any],
        filename: str,
        subfolder: Optional[str] = None,
        pretty_print: bool = True,
    ) -> Dict[str, Any]:
        """
        Export data to a JSON file.

        Args:
            data: Data to export as JSON
            filename: Base filename (without extension)
            subfolder: Optional subfolder within export directory
            pretty_print: Whether to format JSON with indentation

        Returns:
            Export result with file path and status
        """
        try:
            # Construct file path
            if subfolder:
                output_dir = self.export_directory / subfolder
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self.export_directory

            file_path = output_dir / f"{filename}.json"

            # Write JSON to file
            with open(file_path, "w", encoding="utf-8") as f:
                if pretty_print:
                    json.dump(data, f, indent=2, default=str)
                else:
                    json.dump(data, f, default=str)

            logger.info(f"Exported JSON report to: {file_path}")

            return {
                "status": "success",
                "format": "json",
                "file_path": str(file_path),
                "file_size": os.path.getsize(file_path),
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting JSON report: {e}")
            return {"status": "error", "format": "json", "error": str(e)}

    def export_to_html(
        self, content: str, filename: str, subfolder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export report content to an HTML file.

        Args:
            content: HTML content to export
            filename: Base filename (without extension)
            subfolder: Optional subfolder within export directory

        Returns:
            Export result with file path and status
        """
        try:
            # Construct file path
            if subfolder:
                output_dir = self.export_directory / subfolder
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self.export_directory

            file_path = output_dir / f"{filename}.html"

            # Write content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Exported HTML report to: {file_path}")

            return {
                "status": "success",
                "format": "html",
                "file_path": str(file_path),
                "file_size": os.path.getsize(file_path),
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting HTML report: {e}")
            return {"status": "error", "format": "html", "error": str(e)}

    def export_to_pdf(
        self, html_content: str, filename: str, subfolder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export HTML content to a PDF file.

        Args:
            html_content: HTML content to convert to PDF
            filename: Base filename (without extension)
            subfolder: Optional subfolder within export directory

        Returns:
            Export result with file path and status
        """
        try:
            # For PDF generation, we would typically use libraries like:
            # - weasyprint
            # - reportlab
            # - wkhtmltopdf
            #
            # For now, we'll create a placeholder implementation

            if subfolder:
                output_dir = self.export_directory / subfolder
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self.export_directory

            file_path = output_dir / f"{filename}.pdf"

            # Placeholder: In a real implementation, convert HTML to PDF
            # For now, just create a text file indicating PDF generation is needed
            with open(file_path.with_suffix(".txt"), "w") as f:
                f.write(f"PDF generation placeholder for: {filename}\n")
                f.write("HTML content would be converted to PDF here.\n")
                f.write(f"Generated at: {datetime.now().isoformat()}\n")

            logger.info(
                f"PDF export placeholder created: {file_path.with_suffix('.txt')}"
            )

            return {
                "status": "partial",
                "format": "pdf",
                "file_path": str(file_path.with_suffix(".txt")),
                "message": "PDF generation requires additional dependencies",
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting PDF report: {e}")
            return {"status": "error", "format": "pdf", "error": str(e)}

    def export_to_excel(
        self, data: Dict[str, Any], filename: str, subfolder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export data to an Excel file.

        Args:
            data: Data to export to Excel
            filename: Base filename (without extension)
            subfolder: Optional subfolder within export directory

        Returns:
            Export result with file path and status
        """
        try:
            # For Excel generation, we would typically use libraries like:
            # - openpyxl
            # - xlsxwriter
            # - pandas with xlsxwriter engine

            if subfolder:
                output_dir = self.export_directory / subfolder
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self.export_directory

            file_path = output_dir / f"{filename}.xlsx"

            # Placeholder: In a real implementation, create Excel workbook
            # For now, export as JSON with xlsx extension
            with open(file_path.with_suffix(".json"), "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(
                f"Excel export placeholder created: {file_path.with_suffix('.json')}"
            )

            return {
                "status": "partial",
                "format": "excel",
                "file_path": str(file_path.with_suffix(".json")),
                "message": "Excel generation requires additional dependencies",
                "exported_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting Excel report: {e}")
            return {"status": "error", "format": "excel", "error": str(e)}

    def export_multiple_formats(
        self,
        report_data: Dict[str, Any],
        filename_base: str,
        formats: List[str],
        subfolder: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export report to multiple formats.

        Args:
            report_data: Complete report data
            filename_base: Base filename for all exports
            formats: List of formats to export to
            subfolder: Optional subfolder within export directory

        Returns:
            Dictionary with results for each format
        """
        results: Dict[str, List[Dict[str, Any]]] = {"successful": [], "failed": []}

        for format_name in formats:
            try:
                if format_name.lower() == "markdown":
                    content = report_data.get(
                        "markdown_content", "# Report\nNo content available"
                    )
                    result = self.export_to_markdown(content, filename_base, subfolder)

                elif format_name.lower() == "csv":
                    content = report_data.get("csv_content", "No CSV data available")
                    result = self.export_to_csv(content, filename_base, subfolder)

                elif format_name.lower() == "json":
                    data = report_data.get("json_data", {})
                    result = self.export_to_json(data, filename_base, subfolder)

                elif format_name.lower() == "html":
                    content = report_data.get(
                        "html_content", "<html><body>No content</body></html>"
                    )
                    result = self.export_to_html(content, filename_base, subfolder)

                elif format_name.lower() == "pdf":
                    content = report_data.get(
                        "html_content", "<html><body>No content</body></html>"
                    )
                    result = self.export_to_pdf(content, filename_base, subfolder)

                elif format_name.lower() == "excel":
                    data = report_data.get("excel_data", {})
                    result = self.export_to_excel(data, filename_base, subfolder)

                else:
                    result = {
                        "status": "error",
                        "format": format_name,
                        "error": f"Unsupported format: {format_name}",
                    }

                if result["status"] in ["success", "partial"]:
                    results["successful"].append(result)
                else:
                    results["failed"].append(result)

            except Exception as e:
                logger.error(f"Error exporting {format_name} format: {e}")
                results["failed"].append(
                    {"status": "error", "format": format_name, "error": str(e)}
                )

        return results

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported export formats.

        Returns:
            List of supported format names
        """
        return ["markdown", "csv", "json", "html", "pdf", "excel"]

    def get_export_history(
        self, days_back: int = 30, format_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get history of recent exports.

        Args:
            days_back: Number of days to look back
            format_filter: Optional format to filter by

        Returns:
            List of export history entries
        """
        try:
            history = []
            cutoff_date = datetime.now().timestamp() - (days_back * 24 * 60 * 60)

            # Scan export directory for recent files
            for file_path in self.export_directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime > cutoff_date:
                    file_format = file_path.suffix.lstrip(".")

                    if format_filter and file_format != format_filter:
                        continue

                    history.append(
                        {
                            "filename": file_path.name,
                            "format": file_format,
                            "file_path": str(file_path),
                            "file_size": file_path.stat().st_size,
                            "modified_at": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    )

            # Sort by modification time, most recent first
            history.sort(key=lambda x: str(x["modified_at"]), reverse=True)

            return history

        except Exception as e:
            logger.error(f"Error retrieving export history: {e}")
            return []

    def cleanup_old_exports(
        self, days_to_keep: int = 90, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up old export files.

        Args:
            days_to_keep: Number of days of exports to keep
            dry_run: If True, only identify files to delete without deleting them

        Returns:
            Cleanup results
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            files_to_delete: list[dict[str, Union[str, int]]] = []
            total_size = 0

            # Find old files
            for file_path in self.export_directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_date:
                    file_size = file_path.stat().st_size
                    files_to_delete.append(
                        {
                            "path": str(file_path),
                            "size": file_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    )
                    total_size += file_size

            # Delete files if not dry run
            deleted_count = 0
            if not dry_run:
                for file_info in files_to_delete:
                    try:
                        os.remove(str(file_info["path"]))
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {file_info['path']}: {e}")

            result = {
                "status": "success",
                "dry_run": dry_run,
                "files_identified": len(files_to_delete),
                "files_deleted": deleted_count,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "cutoff_date": datetime.fromtimestamp(cutoff_date).isoformat(),
            }

            if dry_run:
                result["files"] = files_to_delete

            status = "simulation" if dry_run else "completed"
            logger.info(
                f"Cleanup {status}: {len(files_to_delete)} files, "
                f"{result['total_size_mb']} MB"
            )

            return result

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"status": "error", "error": str(e)}
