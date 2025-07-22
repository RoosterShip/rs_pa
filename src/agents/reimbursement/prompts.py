"""
Structured prompts for LangGraph-based reimbursement agent.

This module provides optimized prompts for Llama 4 model integration
with multi-shot examples and confidence scoring for bill detection.
"""

import json
from typing import Any, Dict, List, Optional


class ReimbursementPrompts:
    """
    Prompt templates optimized for Llama 4 reimbursement agent workflows.

    All prompts are designed for structured JSON output with confidence
    scoring and detailed reasoning for AI-powered bill detection.
    """

    @staticmethod
    def get_bill_detection_prompt(
        email_subject: str, email_snippet: str, email_from: str
    ) -> str:
        """
        Generate bill detection classification prompt.

        Args:
            email_subject: Email subject line
            email_snippet: Email snippet/preview text
            email_from: Email sender information

        Returns:
            Formatted prompt for bill detection
        """
        return (
            f"""You are an expert expense detection AI. Analyze the following """
            f"""email to """
            f"""determine if it contains a reimbursable business expense or bill.

EMAIL DETAILS:
From: {email_from}
Subject: {email_subject}
Content: {email_snippet}

INSTRUCTIONS:
1. Carefully analyze the email content for expense-related information
2. Look for receipts, invoices, purchase confirmations, or expense reports
3. Consider if this would typically be a reimbursable business expense
4. Provide your reasoning and confidence level

EXAMPLES:
Example 1 - REIMBURSABLE:
From: "Uber Receipts <noreply@uber.com>"
Subject: "Your trip receipt - $23.45"
Content: "Thanks for riding with Uber. Your business trip cost $23.45 from Office to \
Airport."
Analysis: This is clearly a business travel expense with a receipt and amount.
Result: YES (Confidence: 95%)

Example 2 - NOT REIMBURSABLE:
From: "Netflix <info@netflix.com>"
Subject: "Your Netflix subscription payment"
Content: "Your monthly Netflix subscription for $15.99 has been processed."
Analysis: Personal entertainment subscription, not a business expense.
Result: NO (Confidence: 90%)

Example 3 - REIMBURSABLE:
From: "Amazon Business <no-reply@amazon.com>"
Subject: "Your order #123-456 has shipped - Office supplies"
Content: "Your order for office supplies totaling $87.50 has been shipped to your \
office."
Analysis: Office supplies are typically reimbursable business expenses.
Result: YES (Confidence: 85%)

OUTPUT FORMAT (JSON only):
{{
    "is_reimbursable": boolean,
    "confidence": number (0-100),
    "reasoning": "detailed explanation of decision",
    "expense_category": "category if reimbursable, null otherwise",
    "detected_amount": number or null,
    "vendor": "vendor name if detected"
}}

Analyze the provided email and respond with JSON only:"""
        )

    @staticmethod
    def get_information_extraction_prompt(
        email_subject: str,
        email_snippet: str,
        email_from: str,
        email_date: Optional[str] = None,
    ) -> str:
        """
        Generate information extraction prompt for confirmed expenses.

        Args:
            email_subject: Email subject line
            email_snippet: Email snippet/preview text
            email_from: Email sender information
            email_date: Email date if available

        Returns:
            Formatted prompt for information extraction
        """
        date_info = f"Date: {email_date}\n" if email_date else ""

        return (
            f"""You are an expert expense information extractor. Extract detailed """
            f"""information from this confirmed business expense email.

EMAIL DETAILS:
From: {email_from}
Subject: {email_subject}
{date_info}Content: {email_snippet}

EXTRACTION INSTRUCTIONS:
1. Extract the exact expense amount (look for currency symbols, numbers)
2. Identify the vendor/merchant name
3. Determine the expense category (Travel, Food, Office, Software, etc.)
4. Extract transaction date if mentioned
5. Provide a clear description of the expense
6. Rate your confidence in each extracted field

AMOUNT EXTRACTION PATTERNS:
- Look for: $XX.XX, USD XX.XX, XX.XX dollars, £XX.XX, €XX.XX
- Extract the numerical value only
- If multiple amounts, choose the total/final amount

CATEGORY DETECTION:
- Travel: Uber, Lyft, airlines, hotels, parking, mileage
- Food: restaurants, catering, meal delivery, coffee shops
- Office: supplies, equipment, furniture, stationery
- Software: subscriptions, licenses, SaaS, apps
- Fuel: gas stations, fuel cards
- Other: miscellaneous business expenses

EXAMPLES:
Example 1:
From: "Uber Receipts <noreply@uber.com>"
Subject: "Trip receipt - Downtown to Airport"
Content: "Trip total: $34.50 on March 15, 2024. Payment method: Business \
Visa."
Result: Amount: 34.50, Vendor: "Uber", Category: "Travel", Description: \
"Uber ride from Downtown to Airport"

Example 2:
From: "Office Depot <receipts@officedepot.com>"
Subject: "Your order confirmation #OD789123"
Content: "Thank you for your $127.89 purchase of office supplies including \
paper, pens, and folders."
Result: Amount: 127.89, Vendor: "Office Depot", Category: "Office", \
Description: "Office supplies - paper, pens, and folders"

OUTPUT FORMAT (JSON only):
{{
    "amount": number or null,
    "amount_confidence": number (0-100),
    "vendor": "extracted vendor name",
    "vendor_confidence": number (0-100),
    "category": "expense category",
    "category_confidence": number (0-100),
    "description": "clear expense description",
    "transaction_date": "YYYY-MM-DD or null",
    "currency": "USD or detected currency",
    "overall_confidence": number (0-100)
}}

Extract information from the provided email and respond with JSON only:"""
        )

    @staticmethod
    def get_confidence_evaluation_prompt(
        detection_result: Dict[str, Any], extraction_result: Dict[str, Any]
    ) -> str:
        """
        Generate confidence evaluation prompt for AI decisions.

        Args:
            detection_result: Result from bill detection
            extraction_result: Result from information extraction

        Returns:
            Formatted prompt for confidence evaluation
        """
        return (
            f"""You are an AI decision quality evaluator. Assess the confidence """
            f"""and accuracy of these expense analysis results.

DETECTION RESULT:
{json.dumps(detection_result, indent=2)}

EXTRACTION RESULT:
{json.dumps(extraction_result, indent=2)}

EVALUATION CRITERIA:
1. Consistency between detection and extraction results
2. Confidence scores alignment and reasonableness
3. Completeness of extracted information
4. Logical coherence of categorization and reasoning
5. Potential issues or inconsistencies

CONFIDENCE LEVELS:
- HIGH (80-100): Clear evidence, consistent results, complete information
- MEDIUM (60-79): Good evidence, minor inconsistencies, mostly complete
- LOW (0-59): Unclear evidence, significant issues, incomplete information

QUALITY CHECKS:
- Does the extracted amount match detection confidence?
- Is the vendor name consistent with the email sender?
- Does the category make sense for the described expense?
- Are confidence scores realistic and well-calibrated?

OUTPUT FORMAT (JSON only):
{{
    "overall_confidence": number (0-100),
    "quality_score": number (0-100),
    "issues_found": ["list of any issues or inconsistencies"],
    "recommendations": ["list of improvements or validations needed"],
    "final_decision": "ACCEPT, REVIEW, or REJECT",
    "reasoning": "detailed explanation of evaluation"
}}

Evaluate the results and respond with JSON only:"""
        )

    @staticmethod
    def get_category_classification_prompt(
        expense_description: str, vendor: str, amount: Optional[float] = None
    ) -> str:
        """
        Generate category classification prompt for expenses.

        Args:
            expense_description: Description of the expense
            vendor: Vendor/merchant name
            amount: Expense amount if available

        Returns:
            Formatted prompt for category classification
        """
        amount_info = f"Amount: ${amount:.2f}\n" if amount else ""

        return (
            f"""You are an expense categorization expert. Classify this business """
            f"""expense into the most appropriate category.

EXPENSE DETAILS:
Vendor: {vendor}
Description: {expense_description}
{amount_info}

AVAILABLE CATEGORIES:
1. Travel - Transportation, hotels, airfare, parking, mileage
2. Food - Business meals, catering, client entertainment
3. Office - Supplies, equipment, furniture, stationery
4. Software - Subscriptions, licenses, SaaS tools, applications
5. Fuel - Gas, fuel cards, vehicle expenses
6. Communications - Phone, internet, mobile services
7. Marketing - Advertising, promotional materials, events
8. Professional Services - Legal, consulting, accounting
9. Training - Courses, certifications, conferences
10. Other - Miscellaneous business expenses

CLASSIFICATION RULES:
- Choose the most specific category that fits
- Consider the vendor type and business context
- Use "Other" only when no specific category applies
- Provide reasoning for your classification choice

EXAMPLES:
Vendor: "Starbucks", Description: "Coffee meeting with client" → Food (85% confidence)
Vendor: "Microsoft", Description: "Office 365 subscription" → Software (95% confidence)
Vendor: "Shell", Description: "Fuel for business travel" → Fuel (90% confidence)

OUTPUT FORMAT (JSON only):
{{
    "category": "selected category name",
    "confidence": number (0-100),
    "reasoning": "explanation for category choice",
    "alternative_categories": ["list of other possible categories"],
    "subcategory": "more specific classification if applicable"
}}

Classify the expense and respond with JSON only:"""
        )

    @staticmethod
    def get_batch_processing_prompt(emails: List[Dict[str, Any]]) -> str:
        """
        Generate batch processing prompt for multiple emails.

        Args:
            emails: List of email data dictionaries

        Returns:
            Formatted prompt for batch expense detection
        """
        email_list = []
        for i, email in enumerate(emails[:10]):  # Limit to 10 emails
            email_list.append(
                f"""
Email {i+1}:
From: {email.get('from', 'Unknown')}
Subject: {email.get('subject', 'No Subject')}
Content: {email.get('snippet', 'No Content')[:200]}...
"""
            )

        emails_text = "\n".join(email_list)

        return (
            f"""You are an expense detection expert processing multiple emails """
            f"""efficiently. Analyze each email for potential business expenses.

EMAILS TO ANALYZE:
{emails_text}

BATCH PROCESSING INSTRUCTIONS:
1. Process each email independently for expense detection
2. Focus on speed while maintaining accuracy
3. Use consistent confidence scoring across all emails
4. Identify patterns and common expense types

OUTPUT FORMAT (JSON only):
{{
    "results": [
        {{
            "email_index": number,
            "is_reimbursable": boolean,
            "confidence": number (0-100),
            "quick_reasoning": "brief explanation",
            "category": "category if reimbursable",
            "estimated_amount": number or null
        }}
    ],
    "batch_summary": {{
        "total_emails": number,
        "potential_expenses": number,
        "high_confidence_count": number,
        "processing_notes": "any patterns or issues observed"
    }}
}}

Process all emails and respond with JSON only:"""
        )

    @staticmethod
    def get_validation_prompt(
        extracted_data: Dict[str, Any], email_content: str
    ) -> str:
        """
        Generate validation prompt for extracted expense data.

        Args:
            extracted_data: Previously extracted expense information
            email_content: Original email content for validation

        Returns:
            Formatted prompt for data validation
        """
        return (
            f"""You are an expense data validator. Verify the accuracy of extracted """
            f"""information against the original email content.

EXTRACTED DATA:
{json.dumps(extracted_data, indent=2)}

ORIGINAL EMAIL CONTENT:
{email_content}

VALIDATION CHECKS:
1. Amount accuracy - Is the extracted amount correct and complete?
2. Vendor verification - Is the vendor name accurate and properly extracted?
3. Category appropriateness - Is the category classification logical?
4. Date consistency - Is the transaction date accurate if extracted?
5. Description completeness - Does the description capture the key details?

VALIDATION CRITERIA:
- PASS: Information is accurate and complete
- WARNING: Minor issues or missing optional information
- FAIL: Significant errors or missing critical information

OUTPUT FORMAT (JSON only):
{{
    "validation_status": "PASS, WARNING, or FAIL",
    "validation_score": number (0-100),
    "field_validations": {{
        "amount": {{"status": "PASS/WARNING/FAIL", "notes": "validation notes"}},
        "vendor": {{"status": "PASS/WARNING/FAIL", "notes": "validation notes"}},
        "category": {{"status": "PASS/WARNING/FAIL", "notes": "validation notes"}},
        "description": {{"status": "PASS/WARNING/FAIL", "notes": "validation notes"}}
    }},
    "corrections": {{
        "amount": "corrected value or null",
        "vendor": "corrected value or null",
        "category": "corrected value or null",
        "description": "corrected value or null"
    }},
    "overall_notes": "summary of validation findings"
}}

Validate the extracted data and respond with JSON only:"""
        )
