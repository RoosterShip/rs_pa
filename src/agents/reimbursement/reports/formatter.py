"""
Report formatting service for different output formats.

This module provides formatting capabilities for converting
aggregated expense data into various report formats.
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportFormatter:
    """
    Service for formatting expense reports in various formats.

    Provides methods for converting aggregated data into
    formatted reports including Markdown, HTML, CSV, and JSON.
    """

    def __init__(self) -> None:
        """Initialize the report formatter."""
        logger.info("Report formatter initialized")

    def format_markdown_report(
        self,
        aggregated_data: Dict[str, Any],
        report_metadata: Dict[str, Any],
        sections: Optional[List[str]] = None,
    ) -> str:
        """
        Format a comprehensive Markdown report.

        Args:
            aggregated_data: Aggregated expense data
            report_metadata: Report metadata
            sections: List of sections to include

        Returns:
            Formatted Markdown report
        """
        try:
            sections = sections or [
                "summary",
                "categories",
                "vendors",
                "recommendations",
            ]

            # Report header
            report_id = report_metadata.get("report_id", "N/A")
            generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            period_start = aggregated_data.get("date_range", {}).get("start", "N/A")
            period_end = aggregated_data.get("date_range", {}).get("end", "N/A")

            markdown = f"""# Expense Report

**Report ID:** {report_id}
**Generated:** {generated_time}
**Period:** {period_start} to {period_end}

---

"""

            # Executive Summary
            if "summary" in sections and "summary" in aggregated_data:
                markdown += self._format_summary_section(aggregated_data["summary"])

            # Category Analysis
            if "categories" in sections and "by_category" in aggregated_data:
                markdown += self._format_category_section(
                    aggregated_data["by_category"]
                )

            # Vendor Analysis
            if "vendors" in sections and "by_vendor" in aggregated_data:
                markdown += self._format_vendor_section(aggregated_data["by_vendor"])

            # Time Analysis
            if "time" in sections and "by_month" in aggregated_data:
                markdown += self._format_time_section(aggregated_data["by_month"])

            # Recommendations
            if "recommendations" in sections:
                markdown += self._format_recommendations_section(aggregated_data)

            return markdown

        except Exception as e:
            logger.error(f"Error formatting Markdown report: {e}")
            return f"# Error Generating Report\n\nAn error occurred: {str(e)}"

    def _format_summary_section(self, summary_data: Dict[str, Any]) -> str:
        """Format the executive summary section."""
        return f"""## Executive Summary

| Metric | Value |
|--------|-------|
| Total Expenses | {summary_data.get('total_expenses', 0):,} |
| Total Amount | ${summary_data.get('total_amount', 0):,.2f} |
| Reimbursable Amount | ${summary_data.get('reimbursable_amount', 0):,.2f} |
| Non-Reimbursable Amount | ${summary_data.get('non_reimbursable_amount', 0):,.2f} |
| Average Amount | ${summary_data.get('average_amount', 0):,.2f} |
| Reimbursable Percentage | {summary_data.get('reimbursable_percentage', 0):.1f}% |

"""

    def _format_category_section(self, category_data: Dict[str, Any]) -> str:
        """Format the category analysis section."""
        section = "## Category Analysis\n\n"

        if "totals" in category_data:
            section += "| Category | Amount | Count | Average | % of Total |\n"
            section += "|----------|--------|-------|---------|------------|\n"

            # Sort categories by amount
            sorted_categories = sorted(
                category_data["totals"].items(), key=lambda x: x[1], reverse=True
            )

            total_amount = sum(category_data["totals"].values())

            for category, amount in sorted_categories:
                count = category_data.get("counts", {}).get(category, 0)
                avg = amount / count if count > 0 else 0
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0

                section += (
                    f"| {category} | ${amount:,.2f} | {count} | ${avg:,.2f} | "
                    f"{percentage:.1f}% |\n"
                )

        section += "\n"
        return section

    def _format_vendor_section(self, vendor_data: Dict[str, Any]) -> str:
        """Format the vendor analysis section."""
        section = "## Top Vendors\n\n"

        if "totals" in vendor_data:
            section += "| Vendor | Amount | Transactions |\n"
            section += "|--------|--------|--------------|\n"

            # Sort vendors by amount and take top 10
            sorted_vendors = sorted(
                vendor_data["totals"].items(), key=lambda x: x[1], reverse=True
            )[:10]

            for vendor, amount in sorted_vendors:
                count = vendor_data.get("counts", {}).get(vendor, 0)
                section += f"| {vendor} | ${amount:,.2f} | {count} |\n"

        section += "\n"
        return section

    def _format_time_section(self, time_data: Dict[str, Any]) -> str:
        """Format the time analysis section."""
        section = "## Monthly Breakdown\n\n"

        section += "| Month | Amount |\n"
        section += "|-------|--------|\n"

        # Sort months chronologically
        sorted_months = sorted(time_data.items())

        for month, amount in sorted_months:
            section += f"| {month} | ${amount:,.2f} |\n"

        section += "\n"
        return section

    def _format_recommendations_section(self, aggregated_data: Dict[str, Any]) -> str:
        """Format the recommendations section."""
        section = "## Recommendations\n\n"

        # Analyze data for recommendations
        summary = aggregated_data.get("summary", {})
        categories = aggregated_data.get("by_category", {}).get("totals", {})

        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            section += (
                f"1. **Cost Control in {top_category[0]}**: This category has the "
                f"highest expenses (${top_category[1]:,.2f}). Consider reviewing "
                f"these transactions for potential savings.\n\n"
            )

        reimbursable_pct = summary.get("reimbursable_percentage", 0)
        if reimbursable_pct < 50:
            section += (
                f"2. **Reimbursement Tracking**: Only {reimbursable_pct:.1f}% of "
                f"expenses are marked as reimbursable. Review expense policies to "
                f"ensure proper categorization.\n\n"
            )

        section += (
            "3. **Regular Reviews**: Consider implementing monthly expense "
            "reviews to identify trends and opportunities for optimization.\n\n"
        )
        section += (
            "4. **Automated Tracking**: Explore automated expense tracking "
            "tools for frequently used vendors.\n\n"
        )

        return section

    def format_html_report(
        self,
        aggregated_data: Dict[str, Any],
        report_metadata: Dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """
        Format an HTML report with optional charts.

        Args:
            aggregated_data: Aggregated expense data
            report_metadata: Report metadata
            include_charts: Whether to include chart visualizations

        Returns:
            Formatted HTML report
        """
        try:
            chart_script = (
                '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
                if include_charts
                else ""
            )
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Expense Report - {report_metadata.get('report_id', 'N/A')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .chart-container {{ margin: 20px 0; height: 400px; }}
    </style>
    {chart_script}
</head>
<body>
    <h1>Expense Report</h1>
    <div class="summary">
        <h2>Report Information</h2>
        <p><strong>Report ID:</strong> {report_metadata.get('report_id', 'N/A')}</p>
        <p><strong>Generated:</strong>
           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Period:</strong>
           {aggregated_data.get('date_range', {}).get('start', 'N/A')} to
           {aggregated_data.get('date_range', {}).get('end', 'N/A')}</p>
    </div>
"""

            # Add summary table
            if "summary" in aggregated_data:
                html += self._format_html_summary_table(aggregated_data["summary"])

            # Add category table
            if "by_category" in aggregated_data:
                html += self._format_html_category_table(aggregated_data["by_category"])

            # Add charts if requested
            if include_charts and "by_category" in aggregated_data:
                html += self._format_html_charts(aggregated_data)

            html += """
</body>
</html>"""

            return html

        except Exception as e:
            logger.error(f"Error formatting HTML report: {e}")
            return (
                f"<html><body><h1>Error</h1>"
                f"<p>An error occurred: {str(e)}</p></body></html>"
            )

    def _format_html_summary_table(self, summary_data: Dict[str, Any]) -> str:
        """Format HTML summary table."""
        return f"""
    <h2>Executive Summary</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Expenses</td>
            <td>{summary_data.get('total_expenses', 0):,}</td></tr>
        <tr><td>Total Amount</td>
            <td>${summary_data.get('total_amount', 0):,.2f}</td></tr>
        <tr><td>Reimbursable Amount</td>
            <td>${summary_data.get('reimbursable_amount', 0):,.2f}</td></tr>
        <tr><td>Average Amount</td>
            <td>${summary_data.get('average_amount', 0):,.2f}</td></tr>
        <tr><td>Reimbursable Percentage</td>
            <td>{summary_data.get('reimbursable_percentage', 0):.1f}%</td></tr>
    </table>
"""

    def _format_html_category_table(self, category_data: Dict[str, Any]) -> str:
        """Format HTML category table."""
        html = """
    <h2>Category Breakdown</h2>
    <table>
        <tr><th>Category</th><th>Amount</th><th>Count</th><th>Average</th></tr>
"""

        if "totals" in category_data:
            sorted_categories = sorted(
                category_data["totals"].items(), key=lambda x: x[1], reverse=True
            )

            for category, amount in sorted_categories:
                count = category_data.get("counts", {}).get(category, 0)
                avg = amount / count if count > 0 else 0
                html += (
                    f"        <tr><td>{category}</td><td>${amount:,.2f}</td>"
                    f"<td>{count}</td><td>${avg:,.2f}</td></tr>\n"
                )

        html += "    </table>\n"
        return html

    def _format_html_charts(self, aggregated_data: Dict[str, Any]) -> str:
        """Format HTML charts section."""
        categories = aggregated_data.get("by_category", {}).get("totals", {})

        if not categories:
            return ""

        # Generate chart data
        labels = list(categories.keys())
        values = list(categories.values())

        return f"""
    <h2>Visual Analysis</h2>
    <div class="chart-container">
        <canvas id="categoryChart"></canvas>
    </div>
    <script>
        const ctx = document.getElementById('categoryChart').getContext('2d');
        new Chart(ctx, {{
            type: 'pie',
            data: {{
                labels: {labels},
                datasets: [{{
                    data: {values},
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Expenses by Category'
                    }}
                }}
            }}
        }});
    </script>
"""

    def format_csv_export(
        self, expenses: List[Any], include_headers: bool = True
    ) -> str:
        """
        Format expense data as CSV.

        Args:
            expenses: List of expense data objects
            include_headers: Whether to include column headers

        Returns:
            CSV formatted string
        """
        try:
            output = io.StringIO()
            writer = csv.writer(output)

            if include_headers:
                writer.writerow(
                    [
                        "Date",
                        "Amount",
                        "Currency",
                        "Description",
                        "Vendor",
                        "Category",
                        "Reimbursable",
                        "Confidence Score",
                        "Email ID",
                        "Scan ID",
                        "Receipt URL",
                    ]
                )

            for expense in expenses:
                writer.writerow(
                    [
                        expense.date.isoformat() if expense.date else "",
                        expense.amount,
                        expense.currency or "USD",
                        expense.description or "",
                        expense.vendor or "",
                        expense.category or "",
                        "Yes" if expense.is_reimbursable else "No",
                        (
                            f"{expense.confidence_score:.2f}"
                            if expense.confidence_score
                            else ""
                        ),
                        expense.email_id or "",
                        expense.scan_id or "",
                        expense.receipt_url or "",
                    ]
                )

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error formatting CSV export: {e}")
            return f"Error,{str(e)}\n"

    def format_json_export(
        self,
        aggregated_data: Dict[str, Any],
        report_metadata: Dict[str, Any],
        include_raw_data: bool = False,
    ) -> str:
        """
        Format data as JSON export.

        Args:
            aggregated_data: Aggregated expense data
            report_metadata: Report metadata
            include_raw_data: Whether to include raw expense records

        Returns:
            JSON formatted string
        """
        try:
            export_data = {
                "report_metadata": report_metadata,
                "generated_at": datetime.now().isoformat(),
                "aggregated_data": aggregated_data,
            }

            if include_raw_data and "raw_expenses" in report_metadata:
                export_data["raw_expenses"] = report_metadata["raw_expenses"]

            return json.dumps(export_data, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error formatting JSON export: {e}")
            return json.dumps({"error": str(e)}, indent=2)

    def format_summary_text(
        self, aggregated_data: Dict[str, Any], max_lines: int = 10
    ) -> str:
        """
        Format a brief text summary.

        Args:
            aggregated_data: Aggregated expense data
            max_lines: Maximum number of lines in summary

        Returns:
            Brief text summary
        """
        try:
            summary = aggregated_data.get("summary", {})
            lines = []

            lines.append("Expense Summary:")
            total_amount = summary.get("total_amount", 0)
            total_expenses = summary.get("total_expenses", 0)
            lines.append(
                f"- Total: ${total_amount:,.2f} ({total_expenses} transactions)"
            )
            reimb_amount = summary.get("reimbursable_amount", 0)
            reimb_pct = summary.get("reimbursable_percentage", 0)
            lines.append(f"- Reimbursable: ${reimb_amount:,.2f} ({reimb_pct:.1f}%)")
            lines.append(f"- Average: ${summary.get('average_amount', 0):,.2f}")

            # Add top category if available
            categories = aggregated_data.get("by_category", {}).get("totals", {})
            if categories:
                top_category = max(categories.items(), key=lambda x: x[1])
                lines.append(
                    f"- Top Category: {top_category[0]} (${top_category[1]:,.2f})"
                )

            return "\n".join(lines[:max_lines])

        except Exception as e:
            logger.error(f"Error formatting summary text: {e}")
            return f"Error generating summary: {str(e)}"
