"""
LangGraph workflow definition for reimbursement agent.

This module defines the LangGraph StateGraph workflow for processing
emails and extracting expense information with stateful management.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from .prompts import ReimbursementPrompts

logger = logging.getLogger(__name__)


class ReimbursementState(TypedDict):
    """
    State schema for the reimbursement agent workflow.

    This defines the state variables that persist throughout
    the LangGraph workflow execution with advanced LLM integration.
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

    # LLM Processing data
    llm_analyses: List[Dict[str, Any]]  # Store LLM analysis results
    confidence_threshold: float  # Minimum confidence for auto-acceptance
    retry_count: int  # Track retries for failed LLM calls

    # Results
    expense_results: List[Dict[str, Any]]
    expenses_found: int
    total_amount: float
    high_confidence_count: int  # Track high-confidence detections
    low_confidence_count: int  # Track low-confidence detections

    # Error handling and performance
    errors: List[str]
    llm_errors: List[str]  # Specific LLM-related errors
    processing_times: Dict[str, float]  # Track node processing times

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

    # Add nodes for advanced LLM workflow
    workflow.add_node("fetch_emails", fetch_emails_node)
    workflow.add_node("preprocess_emails", preprocess_emails_node)
    workflow.add_node("llm_bill_detection", llm_bill_detection_node)
    workflow.add_node("llm_information_extraction", llm_information_extraction_node)
    workflow.add_node("confidence_evaluation", confidence_evaluation_node)
    workflow.add_node("validate_results", validate_results_node)
    workflow.add_node("store_results", store_results_node)
    workflow.add_node("handle_error", handle_error_node)
    workflow.add_node("retry_llm", retry_llm_node)

    # Define the workflow flow with advanced routing
    workflow.set_entry_point("fetch_emails")

    # Add conditional edges for sophisticated workflow
    workflow.add_conditional_edges(
        "fetch_emails",
        _should_continue_after_fetch,
        {"continue": "preprocess_emails", "error": "handle_error", "end": END},
    )

    workflow.add_conditional_edges(
        "preprocess_emails",
        _should_continue_after_preprocess,
        {"continue": "llm_bill_detection", "error": "handle_error"},
    )

    workflow.add_conditional_edges(
        "llm_bill_detection",
        _should_continue_after_detection,
        {
            "continue": "llm_information_extraction",
            "error": "handle_error",
            "retry": "retry_llm",
            "skip": "store_results",
        },
    )

    workflow.add_conditional_edges(
        "llm_information_extraction",
        _should_continue_after_extraction,
        {
            "continue": "confidence_evaluation",
            "error": "handle_error",
            "retry": "retry_llm",
        },
    )

    workflow.add_conditional_edges(
        "confidence_evaluation",
        _should_continue_after_confidence,
        {
            "continue": "validate_results",
            "error": "handle_error",
            "review": "store_results",  # Store with review flag
        },
    )

    workflow.add_conditional_edges(
        "validate_results",
        _should_continue_after_validation,
        {"continue": "store_results", "error": "handle_error"},
    )

    workflow.add_conditional_edges(
        "retry_llm",
        _should_continue_after_retry,
        {
            "detection": "llm_bill_detection",
            "extraction": "llm_information_extraction",
            "error": "handle_error",
        },
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

        # Update state with new LLM-related fields
        state["emails"] = emails
        state["processed_emails"] = 0
        state["llm_analyses"] = []
        state["confidence_threshold"] = 75.0  # Default confidence threshold
        state["retry_count"] = 0
        state["high_confidence_count"] = 0
        state["low_confidence_count"] = 0
        state["llm_errors"] = []
        state["processing_times"] = {}
        state["progress"] = 20

        logger.info(f"Fetched {len(emails)} emails for LLM processing")

        return state

    except Exception as error:
        error_msg = f"Error fetching emails: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def preprocess_emails_node(state: ReimbursementState) -> ReimbursementState:
    """
    Preprocess fetched emails for LLM analysis.

    Args:
        state: Current workflow state

    Returns:
        Updated state with preprocessed email data
    """
    try:
        start_time = datetime.utcnow().timestamp()
        logger.info("Preprocessing emails for LLM analysis")

        state["current_step"] = "preprocessing_emails"
        state["progress"] = 25

        emails = state.get("emails", [])
        processed_emails = []

        for i, email in enumerate(emails):
            try:
                # Clean and normalize email content
                subject = email.get("subject", "").strip()
                snippet = email.get("snippet", "").strip()
                from_field = email.get("from", "").strip()

                # Extract meaningful text content
                if len(snippet) > 500:
                    snippet = snippet[:500] + "..."

                # Remove excessive whitespace and normalize
                subject = re.sub(r"\s+", " ", subject)
                snippet = re.sub(r"\s+", " ", snippet)

                # Create preprocessed email data
                processed_email = {
                    "id": email.get("id"),
                    "thread_id": email.get("thread_id"),
                    "subject": subject,
                    "snippet": snippet,
                    "from": from_field,
                    "date": email.get("date"),
                    "original": email,  # Keep original for reference
                    "text_length": len(subject + " " + snippet),
                    "preprocessing_notes": [],
                }

                # Add preprocessing notes if needed
                if len(email.get("snippet", "")) > 500:
                    processed_email["preprocessing_notes"].append("Content truncated")

                if not subject:
                    processed_email["preprocessing_notes"].append("No subject")

                if not snippet:
                    processed_email["preprocessing_notes"].append("No content")

                processed_emails.append(processed_email)

                # Update progress
                progress = 25 + int((i + 1) / len(emails) * 10)  # 25% to 35%
                state["progress"] = progress

            except Exception as email_error:
                logger.warning(
                    f"Error preprocessing email {email.get('id')}: {email_error}"
                )
                state["llm_errors"].append(f"Preprocessing error: {email_error}")
                continue

        # Update state
        state["emails"] = processed_emails
        state["progress"] = 35

        # Record processing time
        processing_time = datetime.utcnow().timestamp() - start_time
        state["processing_times"]["preprocess"] = processing_time

        logger.info(
            f"Preprocessed {len(processed_emails)} emails in {processing_time:.2f}s"
        )

        return state

    except Exception as error:
        error_msg = f"Error preprocessing emails: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def llm_bill_detection_node(state: ReimbursementState) -> ReimbursementState:
    """
    Use LLM to detect bills and reimbursable expenses in emails.

    Args:
        state: Current workflow state

    Returns:
        Updated state with LLM detection results
    """
    try:
        start_time = datetime.utcnow().timestamp()
        logger.info("Starting LLM-powered bill detection")

        state["current_step"] = "llm_bill_detection"
        state["progress"] = 40

        # Import LLM manager
        from ...core.llm_manager import get_llm_manager

        llm_manager = get_llm_manager()
        if not llm_manager or not llm_manager.is_connected():
            error_msg = "LLM manager not available or not connected"
            state["llm_errors"].append(error_msg)
            logger.error(error_msg)
            return state

        emails = state.get("emails", [])
        llm_analyses = []
        potential_expenses = []

        # Process each email with LLM
        for i, email in enumerate(emails):
            try:
                # Create detection prompt
                prompt = ReimbursementPrompts.get_bill_detection_prompt(
                    email_subject=email.get("subject", ""),
                    email_snippet=email.get("snippet", ""),
                    email_from=email.get("from", ""),
                )

                # Call LLM for detection
                response = llm_manager.invoke_sync([HumanMessage(content=prompt)])

                # Parse JSON response
                try:
                    analysis_result = json.loads(response)
                except json.JSONDecodeError as json_error:
                    logger.warning(
                        f"Failed to parse LLM response as JSON: {json_error}"
                    )
                    # Fallback to keyword detection
                    analysis_result = _fallback_keyword_detection(email)

                # Store analysis result
                analysis_result["email_id"] = email.get("id")
                analysis_result["processing_method"] = "llm_detection"
                analysis_result["timestamp"] = datetime.utcnow().isoformat()
                llm_analyses.append(analysis_result)

                # Add to potential expenses if reimbursable
                if analysis_result.get("is_reimbursable", False):
                    potential_expenses.append(
                        {
                            "email": email,
                            "llm_analysis": analysis_result,
                            "detection_method": "llm_analysis",
                            "confidence": analysis_result.get("confidence", 0),
                        }
                    )

                    # Track confidence levels
                    confidence = analysis_result.get("confidence", 0)
                    if confidence >= state.get("confidence_threshold", 75):
                        state["high_confidence_count"] += 1
                    else:
                        state["low_confidence_count"] += 1

                # Update progress
                progress = 40 + int((i + 1) / len(emails) * 25)  # 40% to 65%
                state["progress"] = progress

            except Exception as email_error:
                logger.warning(
                    f"Error in LLM detection for email {email.get('id')}: {email_error}"
                )
                state["llm_errors"].append(f"LLM detection error: {email_error}")

                # Fallback to keyword detection
                fallback_result = _fallback_keyword_detection(email)
                llm_analyses.append(fallback_result)

                if fallback_result.get("is_reimbursable", False):
                    potential_expenses.append(
                        {
                            "email": email,
                            "llm_analysis": fallback_result,
                            "detection_method": "fallback_keyword",
                            "confidence": fallback_result.get("confidence", 0),
                        }
                    )
                continue

        # Update state
        state["emails"] = potential_expenses
        state["llm_analyses"] = llm_analyses
        state["processed_emails"] = len(emails)
        state["progress"] = 65

        # Record processing time
        processing_time = datetime.utcnow().timestamp() - start_time
        state["processing_times"]["llm_detection"] = processing_time

        logger.info(
            f"LLM detected {len(potential_expenses)} potential expenses from "
            f"{len(emails)} emails in {processing_time:.2f}s"
        )

        return state

    except Exception as error:
        error_msg = f"Error in LLM bill detection: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["llm_errors"].append(error_msg)
        return state


def llm_information_extraction_node(state: ReimbursementState) -> ReimbursementState:
    """
    Use LLM to extract detailed information from detected expenses.

    Args:
        state: Current workflow state

    Returns:
        Updated state with extracted information
    """
    try:
        start_time = datetime.utcnow().timestamp()
        logger.info("Starting LLM information extraction")

        state["current_step"] = "llm_information_extraction"
        state["progress"] = 70

        # Import LLM manager
        from ...core.llm_manager import get_llm_manager

        llm_manager = get_llm_manager()
        if not llm_manager or not llm_manager.is_connected():
            error_msg = "LLM manager not available for information extraction"
            state["llm_errors"].append(error_msg)
            logger.error(error_msg)
            return state

        potential_expenses = state.get("emails", [])
        extracted_results = []
        total_amount = 0.0

        # Extract information from each potential expense
        for i, expense_data in enumerate(potential_expenses):
            try:
                email = expense_data["email"]

                # Create extraction prompt
                prompt = ReimbursementPrompts.get_information_extraction_prompt(
                    email_subject=email.get("subject", ""),
                    email_snippet=email.get("snippet", ""),
                    email_from=email.get("from", ""),
                    email_date=email.get("date"),
                )

                # Call LLM for extraction
                response = llm_manager.invoke_sync([HumanMessage(content=prompt)])

                # Parse JSON response
                try:
                    extraction_result = json.loads(response)
                except json.JSONDecodeError as json_error:
                    logger.warning(f"Failed to parse extraction response: {json_error}")
                    # Fallback to basic extraction
                    extraction_result = _fallback_information_extraction(email)

                # Create final result record
                result = {
                    "gmail_message_id": email.get("id"),
                    "gmail_thread_id": email.get("thread_id"),
                    "email_subject": email.get("subject"),
                    "email_from": email.get("from"),
                    "email_date": _parse_email_date(email.get("date")),
                    # LLM extracted information
                    "amount": extraction_result.get("amount"),
                    "amount_confidence": extraction_result.get("amount_confidence", 0),
                    "vendor": extraction_result.get("vendor"),
                    "vendor_confidence": extraction_result.get("vendor_confidence", 0),
                    "category": extraction_result.get("category"),
                    "category_confidence": extraction_result.get(
                        "category_confidence", 0
                    ),
                    "description": extraction_result.get("description"),
                    "transaction_date": extraction_result.get("transaction_date"),
                    "currency": extraction_result.get("currency", "USD"),
                    "overall_confidence": extraction_result.get(
                        "overall_confidence", 0
                    ),
                    # Detection information
                    "detection_method": expense_data.get("detection_method"),
                    "detection_confidence": expense_data.get("confidence", 0),
                    "llm_analysis": expense_data.get("llm_analysis", {}),
                    # Processing metadata
                    "extraction_method": "llm_extraction",
                    "extraction_timestamp": datetime.utcnow().isoformat(),
                }

                extracted_results.append(result)

                # Add to total amount if available
                amount = extraction_result.get("amount")
                if amount and isinstance(amount, (int, float)):
                    total_amount += float(amount)

                # Update progress
                progress = 70 + int(
                    (i + 1) / len(potential_expenses) * 15
                )  # 70% to 85%
                state["progress"] = progress

            except Exception as extraction_error:
                logger.warning(f"Error extracting from email: {extraction_error}")
                state["llm_errors"].append(f"Extraction error: {extraction_error}")
                continue

        # Update state
        state["expense_results"] = extracted_results
        state["expenses_found"] = len(extracted_results)
        state["total_amount"] = total_amount
        state["progress"] = 85

        # Record processing time
        processing_time = datetime.utcnow().timestamp() - start_time
        state["processing_times"]["llm_extraction"] = processing_time

        logger.info(
            f"Extracted information from {len(extracted_results)} expenses, "
            f"total: ${total_amount:.2f} in {processing_time:.2f}s"
        )

        return state

    except Exception as error:
        error_msg = f"Error in LLM information extraction: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["llm_errors"].append(error_msg)
        return state


def confidence_evaluation_node(state: ReimbursementState) -> ReimbursementState:
    """
    Evaluate confidence and quality of LLM analysis results.

    Args:
        state: Current workflow state

    Returns:
        Updated state with confidence evaluation
    """
    try:
        start_time = datetime.utcnow().timestamp()
        logger.info("Starting confidence evaluation")

        state["current_step"] = "confidence_evaluation"
        state["progress"] = 87

        # Get LLM manager
        from ...core.llm_manager import get_llm_manager

        llm_manager = get_llm_manager()
        if not llm_manager or not llm_manager.is_connected():
            logger.warning("LLM manager not available for confidence evaluation")
            # Skip evaluation but continue
            state["progress"] = 90
            return state

        expense_results = state.get("expense_results", [])
        llm_analyses = state.get("llm_analyses", [])

        evaluated_results = []
        high_quality_count = 0

        # Evaluate each result
        for result in expense_results:
            try:
                # Find corresponding detection analysis
                email_id = result.get("gmail_message_id")
                detection_analysis = None
                for analysis in llm_analyses:
                    if analysis.get("email_id") == email_id:
                        detection_analysis = analysis
                        break

                if detection_analysis:
                    # Create evaluation prompt
                    prompt = ReimbursementPrompts.get_confidence_evaluation_prompt(
                        detection_result=detection_analysis, extraction_result=result
                    )

                    # Call LLM for evaluation
                    response = llm_manager.invoke_sync([HumanMessage(content=prompt)])

                    # Parse evaluation result
                    try:
                        evaluation = json.loads(response)
                        result["confidence_evaluation"] = evaluation
                        result["final_confidence"] = evaluation.get(
                            "overall_confidence", 0
                        )
                        result["quality_score"] = evaluation.get("quality_score", 0)
                        result["needs_review"] = (
                            evaluation.get("final_decision") == "REVIEW"
                        )

                        if evaluation.get("quality_score", 0) >= 80:
                            high_quality_count += 1

                    except json.JSONDecodeError:
                        logger.warning("Failed to parse confidence evaluation response")
                        result["confidence_evaluation"] = {"error": "parsing_failed"}
                        result["needs_review"] = True

                evaluated_results.append(result)

            except Exception as eval_error:
                logger.warning(f"Error evaluating result: {eval_error}")
                result["confidence_evaluation"] = {"error": str(eval_error)}
                result["needs_review"] = True
                evaluated_results.append(result)
                continue

        # Update state
        state["expense_results"] = evaluated_results
        state["progress"] = 90

        # Record processing time and stats
        processing_time = datetime.utcnow().timestamp() - start_time
        state["processing_times"]["confidence_evaluation"] = processing_time

        logger.info(
            f"Evaluated {len(evaluated_results)} results, "
            f"{high_quality_count} high-quality in {processing_time:.2f}s"
        )

        return state

    except Exception as error:
        error_msg = f"Error in confidence evaluation: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def validate_results_node(state: ReimbursementState) -> ReimbursementState:
    """
    Validate extracted expense data for accuracy and completeness.

    Args:
        state: Current workflow state

    Returns:
        Updated state with validated results
    """
    try:
        start_time = datetime.utcnow().timestamp()
        logger.info("Starting results validation")

        state["current_step"] = "validating_results"
        state["progress"] = 92

        expense_results = state.get("expense_results", [])
        validated_results = []

        for result in expense_results:
            try:
                # Basic validation checks
                validation_notes = []
                validation_score = 100

                # Check required fields
                if not result.get("amount"):
                    validation_notes.append("Missing amount")
                    validation_score -= 30

                if not result.get("vendor"):
                    validation_notes.append("Missing vendor")
                    validation_score -= 20

                if not result.get("category"):
                    validation_notes.append("Missing category")
                    validation_score -= 15

                # Check data quality
                amount = result.get("amount")
                if amount is not None and amount <= 0:
                    validation_notes.append("Invalid amount value")
                    validation_score -= 25

                # Check confidence levels
                overall_confidence = result.get("overall_confidence", 0)
                if overall_confidence < 60:
                    validation_notes.append("Low extraction confidence")
                    validation_score -= 20

                # Set validation status
                if validation_score >= 80:
                    validation_status = "PASS"
                elif validation_score >= 60:
                    validation_status = "WARNING"
                else:
                    validation_status = "FAIL"

                # Add validation metadata
                result["validation"] = {
                    "status": validation_status,
                    "score": validation_score,
                    "notes": validation_notes,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                validated_results.append(result)

            except Exception as validation_error:
                logger.warning(f"Error validating result: {validation_error}")
                result["validation"] = {
                    "status": "ERROR",
                    "score": 0,
                    "notes": [f"Validation error: {validation_error}"],
                    "timestamp": datetime.utcnow().isoformat(),
                }
                validated_results.append(result)
                continue

        # Update state
        state["expense_results"] = validated_results
        state["progress"] = 95

        # Record processing time
        processing_time = datetime.utcnow().timestamp() - start_time
        state["processing_times"]["validation"] = processing_time

        # Count validation results
        pass_count = sum(
            1
            for r in validated_results
            if r.get("validation", {}).get("status") == "PASS"
        )
        warning_count = sum(
            1
            for r in validated_results
            if r.get("validation", {}).get("status") == "WARNING"
        )
        fail_count = sum(
            1
            for r in validated_results
            if r.get("validation", {}).get("status") == "FAIL"
        )

        logger.info(
            f"Validated {len(validated_results)} results in {processing_time:.2f}s: "
            f"{pass_count} passed, {warning_count} warnings, {fail_count} failed"
        )

        return state

    except Exception as error:
        error_msg = f"Error in results validation: {error}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def retry_llm_node(state: ReimbursementState) -> ReimbursementState:
    """
    Handle LLM retries with exponential backoff.

    Args:
        state: Current workflow state

    Returns:
        Updated state with retry handling
    """
    try:
        logger.info("Handling LLM retry")

        retry_count = state.get("retry_count", 0)
        max_retries = 3

        if retry_count >= max_retries:
            error_msg = f"Maximum LLM retries ({max_retries}) exceeded"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

        # Increment retry count
        state["retry_count"] = retry_count + 1

        # Exponential backoff (simulated with processing delay)
        import time

        backoff_delay = 2**retry_count
        logger.info(
            f"Retrying LLM operation (attempt {retry_count + 1}) "
            f"with {backoff_delay}s backoff"
        )
        time.sleep(min(backoff_delay, 10))  # Cap at 10 seconds

        # Reset current step for retry
        state["current_step"] = "retrying_llm"

        return state

    except Exception as error:
        error_msg = f"Error in LLM retry handling: {error}"
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


# Conditional edge functions for advanced LLM workflow


def _should_continue_after_fetch(state: ReimbursementState) -> str:
    """Determine next step after fetching emails."""
    if state.get("errors"):
        return "error"

    emails = state.get("emails", [])
    if not emails:
        return "end"

    return "continue"


def _should_continue_after_preprocess(state: ReimbursementState) -> str:
    """Determine next step after preprocessing emails."""
    if state.get("errors"):
        return "error"

    emails = state.get("emails", [])
    if not emails:
        return "error"  # No emails to process

    return "continue"


def _should_continue_after_detection(state: ReimbursementState) -> str:
    """Determine next step after LLM bill detection."""
    if state.get("errors"):
        return "error"

    # Check for LLM-specific errors
    llm_errors = state.get("llm_errors", [])
    retry_count = state.get("retry_count", 0)

    if llm_errors and retry_count < 3:
        return "retry"

    potential_expenses = state.get("emails", [])
    if not potential_expenses:
        return "skip"  # No expenses detected, skip to storage

    return "continue"


def _should_continue_after_extraction(state: ReimbursementState) -> str:
    """Determine next step after LLM information extraction."""
    if state.get("errors"):
        return "error"

    # Check for extraction errors
    llm_errors = state.get("llm_errors", [])
    retry_count = state.get("retry_count", 0)

    if llm_errors and retry_count < 3:
        return "retry"

    return "continue"


def _should_continue_after_confidence(state: ReimbursementState) -> str:
    """Determine next step after confidence evaluation."""
    if state.get("errors"):
        return "error"

    expense_results = state.get("expense_results", [])
    if not expense_results:
        return "error"  # No results to validate

    # Check if any results need review
    needs_review = any(result.get("needs_review", False) for result in expense_results)

    if needs_review:
        return "review"  # Store with review flags

    return "continue"


def _should_continue_after_validation(state: ReimbursementState) -> str:
    """Determine next step after results validation."""
    if state.get("errors"):
        return "error"

    return "continue"


def _should_continue_after_retry(state: ReimbursementState) -> str:
    """Determine which node to retry after LLM failure."""
    current_step = state.get("current_step", "")

    if "detection" in current_step or state.get("retry_count", 0) == 1:
        return "detection"
    elif "extraction" in current_step or state.get("retry_count", 0) == 2:
        return "extraction"
    else:
        return "error"  # Too many retries


# Helper functions for advanced LLM workflow


def _fallback_keyword_detection(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback keyword-based detection when LLM fails.

    Args:
        email: Email data dictionary

    Returns:
        Detection result in LLM format
    """
    try:
        subject = email.get("subject", "").lower()
        snippet = email.get("snippet", "").lower()

        # Expense keywords
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

        # Check for expense keywords
        has_expense_keywords = any(
            keyword in subject or keyword in snippet for keyword in expense_keywords
        )

        return {
            "is_reimbursable": has_expense_keywords,
            "confidence": 60 if has_expense_keywords else 30,
            "reasoning": "Keyword-based detection fallback",
            "expense_category": "Other" if has_expense_keywords else None,
            "detected_amount": None,
            "vendor": _extract_vendor(email.get("from", "")),
            "email_id": email.get("id"),
            "processing_method": "fallback_keyword",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as error:
        logger.warning(f"Error in fallback detection: {error}")
        return {
            "is_reimbursable": False,
            "confidence": 0,
            "reasoning": f"Fallback detection error: {error}",
            "expense_category": None,
            "detected_amount": None,
            "vendor": None,
            "email_id": email.get("id"),
            "processing_method": "fallback_error",
            "timestamp": datetime.utcnow().isoformat(),
        }


def _fallback_information_extraction(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback information extraction when LLM fails.

    Args:
        email: Email data dictionary

    Returns:
        Extraction result in LLM format
    """
    try:
        subject = email.get("subject", "")
        snippet = email.get("snippet", "")
        text_content = f"{subject} {snippet}"

        return {
            "amount": _extract_amount(text_content),
            "amount_confidence": 40 if _extract_amount(text_content) else 0,
            "vendor": _extract_vendor(email.get("from", "")),
            "vendor_confidence": 50 if _extract_vendor(email.get("from", "")) else 0,
            "category": _detect_category(text_content),
            "category_confidence": 45 if _detect_category(text_content) else 0,
            "description": snippet[:200] if snippet else subject[:200],
            "transaction_date": None,
            "currency": "USD",
            "overall_confidence": 35,
        }

    except Exception as error:
        logger.warning(f"Error in fallback extraction: {error}")
        return {
            "amount": None,
            "amount_confidence": 0,
            "vendor": None,
            "vendor_confidence": 0,
            "category": "Other",
            "category_confidence": 0,
            "description": "Extraction failed",
            "transaction_date": None,
            "currency": "USD",
            "overall_confidence": 0,
        }


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
