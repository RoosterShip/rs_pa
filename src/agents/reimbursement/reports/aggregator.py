"""
Data aggregation service for expense reporting.

This module provides sophisticated data aggregation capabilities
for expense data analysis and reporting.
"""

import logging
from typing import Any, Dict, List

from ..models import ExpenseResult

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Advanced data aggregation service for expense analysis.

    Provides methods for aggregating expense data across various
    dimensions including time, category, vendor, and amount ranges.
    """

    def __init__(self) -> None:
        """Initialize the data aggregator."""
        logger.info("Data aggregator initialized")

    async def aggregate_by_time_period(
        self, expenses: List[ExpenseResult], period: str = "month"
    ) -> Dict[str, Any]:
        """
        Aggregate expenses by time period.

        Args:
            expenses: List of expense data
            period: Time period ("day", "week", "month", "quarter", "year")

        Returns:
            Aggregated data by time period
        """
        try:
            aggregation: Dict[str, Dict[str, Any]] = {}

            for expense in expenses:
                if not expense.date:
                    continue

                # Simple period key generation
                if period == "month":
                    period_key = expense.date.strftime("%Y-%m")
                elif period == "year":
                    period_key = expense.date.strftime("%Y")
                else:
                    period_key = expense.date.strftime("%Y-%m-%d")

                if period_key not in aggregation:
                    aggregation[period_key] = {
                        "count": 0,
                        "total_amount": 0.0,
                        "reimbursable_amount": 0.0,
                        "categories": set(),
                        "vendors": set(),
                        "avg_amount": 0.0,
                    }

                data = aggregation[period_key]
                data["count"] += 1

                if expense.amount:
                    data["total_amount"] += float(expense.amount)
                    if expense.is_reimbursable:
                        data["reimbursable_amount"] += float(expense.amount)

                if expense.category:
                    data["categories"].add(str(expense.category))

                if expense.vendor:
                    data["vendors"].add(str(expense.vendor))

            # Calculate averages
            for data in aggregation.values():
                if data["count"] > 0:
                    data["avg_amount"] = data["total_amount"] / data["count"]
                # Convert sets to lists for JSON serialization
                data["categories"] = list(data["categories"])
                data["vendors"] = list(data["vendors"])

            return aggregation

        except Exception as e:
            logger.error(f"Error in time period aggregation: {e}")
            return {}

    async def aggregate_by_category(
        self, expenses: List[ExpenseResult], include_subcategories: bool = False
    ) -> Dict[str, Any]:
        """
        Aggregate expenses by category.

        Args:
            expenses: List of expense data
            include_subcategories: Whether to include subcategory breakdown

        Returns:
            Aggregated data by category
        """
        try:
            categories: Dict[str, Dict[str, Any]] = {}

            for expense in expenses:
                category = (
                    str(expense.category) if expense.category else "Uncategorized"
                )

                if category not in categories:
                    categories[category] = {
                        "count": 0,
                        "total_amount": 0.0,
                        "reimbursable_amount": 0.0,
                        "vendors": set(),
                        "date_range": {"earliest": None, "latest": None},
                        "avg_amount": 0.0,
                    }

                cat_data = categories[category]
                cat_data["count"] += 1

                if expense.amount:
                    cat_data["total_amount"] += float(expense.amount)
                    if expense.is_reimbursable:
                        cat_data["reimbursable_amount"] += float(expense.amount)

                if expense.vendor:
                    cat_data["vendors"].add(str(expense.vendor))

                # Track date range
                if expense.date:
                    if (
                        not cat_data["date_range"]["earliest"]
                        or expense.date < cat_data["date_range"]["earliest"]
                    ):
                        cat_data["date_range"]["earliest"] = expense.date
                    if (
                        not cat_data["date_range"]["latest"]
                        or expense.date > cat_data["date_range"]["latest"]
                    ):
                        cat_data["date_range"]["latest"] = expense.date

            # Calculate averages and convert sets
            for cat_data in categories.values():
                if cat_data["count"] > 0:
                    cat_data["avg_amount"] = (
                        cat_data["total_amount"] / cat_data["count"]
                    )
                cat_data["vendors"] = list(cat_data["vendors"])

                # Convert dates to ISO format
                if cat_data["date_range"]["earliest"]:
                    cat_data["date_range"]["earliest"] = cat_data["date_range"][
                        "earliest"
                    ].isoformat()
                if cat_data["date_range"]["latest"]:
                    cat_data["date_range"]["latest"] = cat_data["date_range"][
                        "latest"
                    ].isoformat()

            return categories

        except Exception as e:
            logger.error(f"Error in category aggregation: {e}")
            return {}

    async def aggregate_by_vendor(
        self, expenses: List[ExpenseResult], min_transactions: int = 1
    ) -> Dict[str, Any]:
        """
        Aggregate expenses by vendor.

        Args:
            expenses: List of expense data
            min_transactions: Minimum number of transactions to include vendor

        Returns:
            Aggregated data by vendor
        """
        try:
            vendors: Dict[str, Dict[str, Any]] = {}

            for expense in expenses:
                vendor = str(expense.vendor) if expense.vendor else "Unknown Vendor"

                if vendor not in vendors:
                    vendors[vendor] = {
                        "count": 0,
                        "total_amount": 0.0,
                        "reimbursable_amount": 0.0,
                        "categories": set(),
                        "avg_amount": 0.0,
                    }

                vendor_data = vendors[vendor]
                vendor_data["count"] += 1

                if expense.amount:
                    vendor_data["total_amount"] += float(expense.amount)
                    if expense.is_reimbursable:
                        vendor_data["reimbursable_amount"] += float(expense.amount)

                if expense.category:
                    vendor_data["categories"].add(str(expense.category))

            # Filter by minimum transactions and calculate averages
            filtered_vendors = {}
            for vendor, data in vendors.items():
                if data["count"] >= min_transactions:
                    if data["count"] > 0:
                        data["avg_amount"] = data["total_amount"] / data["count"]
                    data["categories"] = list(data["categories"])
                    filtered_vendors[vendor] = data

            return filtered_vendors

        except Exception as e:
            logger.error(f"Error in vendor aggregation: {e}")
            return {}

    async def get_summary_statistics(
        self, expenses: List[ExpenseResult]
    ) -> Dict[str, Any]:
        """
        Get overall summary statistics for expenses.

        Args:
            expenses: List of expense data

        Returns:
            Summary statistics
        """
        try:
            if not expenses:
                return {
                    "total_count": 0,
                    "total_amount": 0.0,
                    "reimbursable_amount": 0.0,
                    "avg_amount": 0.0,
                    "unique_vendors": 0,
                    "unique_categories": 0,
                    "date_range": {"earliest": None, "latest": None},
                }

            total_amount = sum(
                float(expense.amount) for expense in expenses if expense.amount
            )
            reimbursable_amount = sum(
                float(expense.amount)
                for expense in expenses
                if expense.amount and expense.is_reimbursable
            )

            vendors = set(str(expense.vendor) for expense in expenses if expense.vendor)
            categories = set(
                str(expense.category) for expense in expenses if expense.category
            )

            dates = [expense.date for expense in expenses if expense.date]
            date_range = {
                "earliest": min(dates).isoformat() if dates else None,
                "latest": max(dates).isoformat() if dates else None,
            }

            return {
                "total_count": len(expenses),
                "total_amount": total_amount,
                "reimbursable_amount": reimbursable_amount,
                "avg_amount": total_amount / len(expenses) if expenses else 0.0,
                "unique_vendors": len(vendors),
                "unique_categories": len(categories),
                "date_range": date_range,
            }

        except Exception as e:
            logger.error(f"Error in summary statistics: {e}")
            return {}

    async def detect_anomalies(
        self, expenses: List[ExpenseResult], sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in expense data.

        Args:
            expenses: List of expense data
            sensitivity: Sensitivity level for anomaly detection

        Returns:
            List of detected anomalies
        """
        try:
            anomalies: List[Dict[str, Any]] = []

            if not expenses:
                return anomalies

            amounts = [float(expense.amount) for expense in expenses if expense.amount]
            if not amounts:
                return anomalies

            avg_amount = sum(amounts) / len(amounts)

            # Simple anomaly detection - amounts significantly higher than average
            threshold = avg_amount * sensitivity

            for expense in expenses:
                if expense.amount and float(expense.amount) > threshold:
                    anomalies.append(
                        {
                            "expense_id": expense.id,
                            "amount": float(expense.amount),
                            "avg_amount": avg_amount,
                            "threshold": threshold,
                            "type": "high_amount",
                            "description": (
                                f"Amount {expense.amount} is "
                                f"{float(expense.amount)/avg_amount:.1f}x the average"
                            ),
                        }
                    )

            return anomalies

        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return []

    async def detect_duplicates(
        self, expenses: List[ExpenseResult], similarity_threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Detect potential duplicate expenses.

        Args:
            expenses: List of expense data
            similarity_threshold: Threshold for considering expenses as duplicates

        Returns:
            List of potential duplicate groups
        """
        try:
            duplicates: List[Dict[str, Any]] = []
            seen_transactions: Dict[str, List[ExpenseResult]] = {}

            for expense in expenses:
                # Create a simple key for matching
                if expense.amount and expense.vendor:
                    key = f"{float(expense.amount)}_{str(expense.vendor)}"
                    if key not in seen_transactions:
                        seen_transactions[key] = []
                    seen_transactions[key].append(expense)

            # Find groups with multiple transactions
            for key, expense_group in seen_transactions.items():
                if len(expense_group) > 1:
                    duplicates.append(
                        {
                            "key": key,
                            "count": len(expense_group),
                            "expenses": [expense.id for expense in expense_group],
                            "total_amount": sum(
                                float(exp.amount) for exp in expense_group if exp.amount
                            ),
                        }
                    )

            return duplicates

        except Exception as e:
            logger.error(f"Error in duplicate detection: {e}")
            return []

    async def get_preview_statistics(
        self, expenses: List[ExpenseResult]
    ) -> Dict[str, Any]:
        """
        Get preview statistics for quick display.

        Args:
            expenses: List of expense data

        Returns:
            Preview statistics
        """
        return await self.get_summary_statistics(expenses)
