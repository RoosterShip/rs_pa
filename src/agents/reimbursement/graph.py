"""
LangGraph workflow definition for reimbursement agent.

This module defines the LangGraph StateGraph workflow for processing
emails and extracting expense information with stateful management.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


class ReimbursementState(TypedDict):
    """
    State schema for the reimbursement agent workflow.

    This defines the state variables that persist throughout
    the LangGraph workflow execution.
    """

    # Input parameters
    gmail_query: str
    max_emails: int
    agent_id: str

    # Processing state
    current_step: str
    progress: int

    # Email data
    emails: List[Dict[str, Any]]
    processed_emails: int

    # Results
    expense_results: List[Dict[str, Any]]
    expenses_found: int
    total_amount: float

    # Error handling
    errors: List[str]

    # Database integration
    scan_id: Optional[int]


def create_reimbursement_graph() -> Any:
    """
    Create and configure the LangGraph workflow for reimbursement processing.

    Returns:
        Configured StateGraph for reimbursement workflow
    """

    # Create the state graph
    workflow = StateGraph(ReimbursementState)

    # Add nodes
    workflow.add_node("fetch_emails", fetch_emails_node)
    workflow.add_node("process_emails", process_emails_node)
    workflow.add_node("extract_data", extract_data_node)
    workflow.add_node("store_results", store_results_node)
    workflow.add_node("handle_error", handle_error_node)

    # Define the workflow flow
    workflow.set_entry_point("fetch_emails")

    # Add conditional edges
    workflow.add_conditional_edges(
        "fetch_emails",
        _should_continue_after_fetch,
        {"continue": "process_emails", "error": "handle_error", "end": END},
    )

    workflow.add_conditional_edges(
        "process_emails",
        _should_continue_after_process,
        {"continue": "extract_data", "error": "handle_error"},
    )

    workflow.add_conditional_edges(
        "extract_data",
        _should_continue_after_extract,
        {"continue": "store_results", "error": "handle_error"},
    )

    workflow.add_edge("store_results", END)
    workflow.add_edge("handle_error", END)

    # Compile the graph
    graph = workflow.compile()

    logger.info("Created reimbursement LangGraph workflow")
    return graph


def fetch_emails_node(state: ReimbursementState) -> ReimbursementState:
    """
    Fetch emails from Gmail based on the query parameters.

    Args:
        state: Current workflow state

    Returns:
        Updated state with fetched emails
    """
    try:
        logger.info(f"Fetching emails with query: {state.get('gmail_query', '')}")

        # Update progress
        state["current_step"] = "fetching_emails"
        state["progress"] = 10

        # Import here to avoid circular imports
        from ...core.gmail_service import GmailService

        # Create Gmail service (in a real implementation, this would be injected)
        gmail_service = GmailService()

        if not gmail_service.is_connected():
            # Try to authenticate
            if not gmail_service.authenticate():
                state["errors"].append("Failed to authenticate with Gmail")
                return state

        # Fetch emails using the Gmail service
        query = state.get("gmail_query", "")
        max_results = state.get("max_emails", 10)

        emails = gmail_service.get_recent_messages(query=query, max_results=max_results)

        # Update state
        state["emails"] = emails
        state["processed_emails"] = 0
        state["progress"] = 25

        logger.info(f"Fetched {len(emails)} emails")

        return state

    except Exception as error:
        error_msg = f"Error fetching emails: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def process_emails_node(state: ReimbursementState) -> ReimbursementState:
    """
    Process fetched emails to identify potential expenses.

    Args:
        state: Current workflow state

    Returns:
        Updated state with processing results
    """
    try:
        logger.info("Processing emails for expense detection")

        state["current_step"] = "processing_emails"
        state["progress"] = 35

        emails = state.get("emails", [])
        potential_expenses = []

        # Define expense keywords for simple detection
        expense_keywords = [
            "receipt",
            "invoice",
            "payment",
            "purchase",
            "expense",
            "reimbursement",
            "bill",
            "charge",
            "transaction",
            "uber",
            "lyft",
            "amazon",
            "hotel",
            "restaurant",
            "airline",
            "travel",
            "taxi",
            "parking",
            "fuel",
            "office",
            "supplies",
            "software",
            "subscription",
        ]

        # Process each email
        for i, email in enumerate(emails):
            try:
                # Simple keyword-based detection
                subject = email.get("subject", "").lower()
                snippet = email.get("snippet", "").lower()

                # Check for expense keywords
                has_expense_keywords = any(
                    keyword in subject or keyword in snippet
                    for keyword in expense_keywords
                )

                if has_expense_keywords:
                    potential_expenses.append(
                        {
                            "email": email,
                            "detection_method": "keyword_match",
                            "confidence": 0.7,  # Basic confidence for keyword matching
                        }
                    )

                # Update progress
                progress = 35 + int((i + 1) / len(emails) * 30)  # 35% to 65%
                state["progress"] = progress

            except Exception as email_error:
                logger.warning(
                    f"Error processing email {email.get('id', 'unknown')}: "
                    f"{email_error}"
                )
                continue

        # Update state
        state["emails"] = potential_expenses
        state["processed_emails"] = len(emails)
        state["progress"] = 65

        logger.info(f"Found {len(potential_expenses)} potential expense emails")

        return state

    except Exception as error:
        error_msg = f"Error processing emails: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def extract_data_node(state: ReimbursementState) -> ReimbursementState:
    """
    Extract expense data from processed emails.

    Args:
        state: Current workflow state

    Returns:
        Updated state with extracted expense data
    """
    try:
        logger.info("Extracting expense data from emails")

        state["current_step"] = "extracting_data"
        state["progress"] = 70

        potential_expenses = state.get("emails", [])
        extracted_results = []
        total_amount = 0.0

        # Process each potential expense
        for i, expense_data in enumerate(potential_expenses):
            try:
                email = expense_data["email"]

                # Extract basic information
                result = {
                    "gmail_message_id": email.get("id"),
                    "gmail_thread_id": email.get("thread_id"),
                    "email_subject": email.get("subject"),
                    "email_from": email.get("from"),
                    "email_date": _parse_email_date(email.get("date")),
                    "detection_method": expense_data.get("detection_method"),
                    "confidence_score": expense_data.get("confidence", 0.5),
                }

                # Try to extract amount using regex
                text_content = f"{email.get('subject', '')} {email.get('snippet', '')}"
                amount = _extract_amount(text_content)
                if amount:
                    result["amount"] = amount
                    total_amount += amount

                # Try to extract vendor
                vendor = _extract_vendor(email.get("from", ""))
                if vendor:
                    result["vendor"] = vendor

                # Simple category detection based on keywords
                category = _detect_category(text_content)
                if category:
                    result["category"] = category

                # Add description (email snippet)
                result["description"] = email.get("snippet", "")[:500]  # Limit length

                extracted_results.append(result)

                # Update progress
                progress = 70 + int(
                    (i + 1) / len(potential_expenses) * 20
                )  # 70% to 90%
                state["progress"] = progress

            except Exception as extract_error:
                logger.warning(f"Error extracting data from email: {extract_error}")
                continue

        # Update state
        state["expense_results"] = extracted_results
        state["expenses_found"] = len(extracted_results)
        state["total_amount"] = total_amount
        state["progress"] = 90

        logger.info(
            f"Extracted data from {len(extracted_results)} expenses, "
            f"total: ${total_amount:.2f}"
        )

        return state

    except Exception as error:
        error_msg = f"Error extracting expense data: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def store_results_node(state: ReimbursementState) -> ReimbursementState:
    """
    Store extracted expense results to the database.

    Args:
        state: Current workflow state

    Returns:
        Updated state with storage results
    """
    try:
        logger.info("Storing expense results to database")

        state["current_step"] = "storing_results"
        state["progress"] = 95

        # Import here to avoid circular imports
        from ...core.database import get_database_manager
        from .models import ExpenseResult, ExpenseScan

        # Get database session
        db_manager = get_database_manager()
        session = db_manager.get_session()

        try:
            # Create or update expense scan record
            scan = ExpenseScan(
                agent_id=state.get("agent_id", "reimbursement"),
                gmail_query=state.get("gmail_query", ""),
                max_emails=state.get("max_emails", 10),
                emails_processed=state.get("processed_emails", 0),
                expenses_found=state.get("expenses_found", 0),
                total_amount=state.get("total_amount", 0.0),
                status="completed",
                completed_at=datetime.utcnow(),
            )

            session.add(scan)
            session.flush()  # Get the scan ID

            # Store expense results
            expense_results = state.get("expense_results", [])
            for result_data in expense_results:
                expense_result = ExpenseResult(scan_id=scan.id, **result_data)
                session.add(expense_result)

            # Commit transaction
            session.commit()

            # Update state
            state["scan_id"] = int(scan.id) if scan.id else None
            state["progress"] = 100

            logger.info(
                f"Stored expense scan {scan.id} with {len(expense_results)} results"
            )

        finally:
            session.close()

        return state

    except Exception as error:
        error_msg = f"Error storing results: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def handle_error_node(state: ReimbursementState) -> ReimbursementState:
    """
    Handle errors that occurred during workflow execution.

    Args:
        state: Current workflow state

    Returns:
        Updated state with error handling
    """
    logger.error(f"Handling workflow errors: {state.get('errors', [])}")

    state["current_step"] = "error"
    state["progress"] = 0

    # In a real implementation, you might want to:
    # - Send error notifications
    # - Log detailed error information
    # - Attempt recovery actions

    return state


# Conditional edge functions


def _should_continue_after_fetch(state: ReimbursementState) -> str:
    """Determine next step after fetching emails."""
    if state.get("errors"):
        return "error"

    emails = state.get("emails", [])
    if not emails:
        return "end"

    return "continue"


def _should_continue_after_process(state: ReimbursementState) -> str:
    """Determine next step after processing emails."""
    if state.get("errors"):
        return "error"

    return "continue"


def _should_continue_after_extract(state: ReimbursementState) -> str:
    """Determine next step after extracting data."""
    if state.get("errors"):
        return "error"

    return "continue"


# Helper functions


def _parse_email_date(date_str: str) -> Optional[datetime]:
    """Parse email date string to datetime object."""
    if not date_str:
        return None

    try:
        # This is a simplified parser - in production you'd want more robust parsing
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(date_str)
    except Exception as error:
        logger.warning(f"Could not parse email date '{date_str}': {error}")
        return None


def _extract_amount(text: str) -> Optional[float]:
    """Extract monetary amount from text using regex."""
    if not text:
        return None

    # Look for currency patterns like $123.45, USD 123.45, 123.45 USD
    patterns = [
        r"\$(\d+(?:\.\d{2})?)",  # $123.45
        r"USD\s*(\d+(?:\.\d{2})?)",  # USD 123.45
        r"(\d+(?:\.\d{2})?)\s*USD",  # 123.45 USD
        r"(\d+(?:\.\d{2})?)\s*dollars?",  # 123.45 dollars
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue

    return None


def _extract_vendor(from_field: str) -> Optional[str]:
    """Extract vendor name from email from field."""
    if not from_field:
        return None

    # Extract name before email address
    # Format: "Vendor Name <vendor@example.com>"
    match = re.match(r"^([^<]+)", from_field.strip())
    if match:
        vendor = match.group(1).strip().strip("\"'")
        if vendor and vendor != from_field:
            return vendor

    # Extract domain name as fallback
    email_match = re.search(r"@([^>]+)", from_field)
    if email_match:
        domain = email_match.group(1).split(".")[0]
        return domain.capitalize()

    return None


def _detect_category(text: str) -> Optional[str]:
    """Detect expense category based on keywords."""
    if not text:
        return None

    text_lower = text.lower()

    categories = {
        "Travel": [
            "uber",
            "lyft",
            "taxi",
            "airline",
            "hotel",
            "airbnb",
            "flight",
            "parking",
        ],
        "Food": [
            "restaurant",
            "food",
            "dining",
            "meal",
            "lunch",
            "dinner",
            "breakfast",
        ],
        "Office": ["office", "supplies", "stationery", "equipment", "furniture"],
        "Software": ["software", "subscription", "saas", "license", "app"],
        "Fuel": ["gas", "fuel", "gasoline", "shell", "exxon", "bp"],
        "Shopping": ["amazon", "purchase", "order", "shopping"],
    }

    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category

    return "Other"
