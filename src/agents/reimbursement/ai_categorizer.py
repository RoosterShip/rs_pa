"""
AI-powered expense categorization system.

This module provides intelligent expense categorization using LLM analysis
with confidence scoring, learning from user feedback, and adaptive suggestions.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ...core.llm_manager import OllamaManager
from .models import ExpenseResult

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for categorization suggestions."""

    HIGH = "high"  # 90-100% confidence
    MEDIUM = "medium"  # 70-89% confidence
    LOW = "low"  # 50-69% confidence
    VERY_LOW = "very_low"  # Below 50%


@dataclass
class CategorySuggestion:
    """Represents a category suggestion with confidence and reasoning."""

    category: str
    confidence: float
    confidence_level: ConfidenceLevel
    reasoning: str
    keywords_matched: List[str]
    similar_transactions: List[str]
    suggested_by: str  # "ai", "rule", "pattern", "user_history"
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CategorizationResult:
    """Result of expense categorization."""

    expense_id: str
    original_description: str
    suggested_category: str
    all_suggestions: List[CategorySuggestion]
    final_confidence: float
    needs_review: bool
    processing_time_ms: float
    timestamp: datetime

    def get_top_suggestions(self, limit: int = 3) -> List[CategorySuggestion]:
        """Get top N suggestions by confidence."""
        return sorted(self.all_suggestions, key=lambda x: x.confidence, reverse=True)[
            :limit
        ]


class ExpenseCategorizer:
    """
    AI-powered expense categorization system.

    Features:
    - LLM-based intelligent categorization
    - Confidence scoring and uncertainty detection
    - Learning from user feedback
    - Pattern recognition from historical data
    - Rule-based categorization for known patterns
    - Adaptive suggestions based on user preferences
    """

    def __init__(
        self,
        llm_manager: Optional[OllamaManager] = None,
        model_name: str = "llama4:maverick",
    ):
        """
        Initialize the expense categorizer.

        Args:
            llm_manager: LLM manager instance
            model_name: Name of the LLM model to use
        """
        self.llm_manager = llm_manager or OllamaManager()
        self.model_name = model_name

        # Category definitions and rules
        self.categories = self._load_default_categories()
        self.categorization_rules = self._load_categorization_rules()
        self.user_feedback_history: Dict[str, Dict[str, Any]] = {}
        self.pattern_cache: Dict[str, Any] = {}

        # Performance tracking
        self.stats = {
            "total_categorizations": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "user_corrections": 0,
            "accuracy_rate": 0.0,
        }

    def _load_default_categories(self) -> Dict[str, Dict[str, Any]]:
        """Load default expense categories with their definitions."""
        return {
            "travel": {
                "name": "Travel",
                "description": "Transportation, lodging, and travel-related expenses",
                "keywords": [
                    "uber",
                    "lyft",
                    "taxi",
                    "flight",
                    "airline",
                    "hotel",
                    "airbnb",
                    "rental car",
                    "gas",
                    "mileage",
                    "parking",
                    "tolls",
                    "train",
                    "bus",
                    "airport",
                    "baggage",
                    "visa",
                    "passport",
                ],
                "common_vendors": [
                    "Uber",
                    "Lyft",
                    "Delta",
                    "American Airlines",
                    "United",
                    "Southwest",
                    "Marriott",
                    "Hilton",
                    "Airbnb",
                    "Hertz",
                    "Enterprise",
                ],
                "typical_amount_range": (10, 2000),
                "tax_deductible": True,
                "requires_receipt": True,
            },
            "meals": {
                "name": "Meals & Entertainment",
                "description": "Food, beverages, and business entertainment",
                "keywords": [
                    "restaurant",
                    "cafe",
                    "coffee",
                    "lunch",
                    "dinner",
                    "breakfast",
                    "catering",
                    "food",
                    "beverage",
                    "bar",
                    "pub",
                    "starbucks",
                    "mcdonald",
                    "subway",
                    "pizza",
                    "delivery",
                    "takeout",
                ],
                "common_vendors": [
                    "Starbucks",
                    "McDonald's",
                    "Subway",
                    "Chipotle",
                    "Panera",
                    "Olive Garden",
                    "Applebee's",
                    "DoorDash",
                    "Uber Eats",
                    "Grubhub",
                ],
                "typical_amount_range": (5, 200),
                "tax_deductible": False,
                "requires_receipt": True,
            },
            "office_supplies": {
                "name": "Office Supplies",
                "description": "Office equipment, supplies, and materials",
                "keywords": [
                    "staples",
                    "office",
                    "supplies",
                    "paper",
                    "printer",
                    "ink",
                    "pen",
                    "pencil",
                    "notebook",
                    "folder",
                    "desk",
                    "chair",
                    "computer",
                    "keyboard",
                    "mouse",
                    "monitor",
                    "software",
                ],
                "common_vendors": [
                    "Staples",
                    "Office Depot",
                    "Amazon",
                    "Best Buy",
                    "Costco",
                    "Target",
                    "Walmart",
                    "OfficeMax",
                    "Quill",
                ],
                "typical_amount_range": (5, 500),
                "tax_deductible": True,
                "requires_receipt": False,
            },
            "software": {
                "name": "Software & Services",
                "description": "Software licenses, subscriptions, and digital services",
                "keywords": [
                    "software",
                    "license",
                    "subscription",
                    "saas",
                    "cloud",
                    "microsoft",
                    "google",
                    "adobe",
                    "zoom",
                    "slack",
                    "dropbox",
                    "github",
                    "aws",
                    "azure",
                    "api",
                    "hosting",
                    "domain",
                ],
                "common_vendors": [
                    "Microsoft",
                    "Google",
                    "Adobe",
                    "Zoom",
                    "Slack",
                    "Dropbox",
                    "GitHub",
                    "AWS",
                    "Azure",
                    "Salesforce",
                    "HubSpot",
                ],
                "typical_amount_range": (10, 1000),
                "tax_deductible": True,
                "requires_receipt": True,
            },
            "training": {
                "name": "Training & Education",
                "description": "Professional development, courses, and training",
                "keywords": [
                    "course",
                    "training",
                    "conference",
                    "seminar",
                    "workshop",
                    "certification",
                    "education",
                    "udemy",
                    "coursera",
                    "linkedin",
                    "pluralsight",
                    "book",
                    "ebook",
                    "tutorial",
                    "learning",
                ],
                "common_vendors": [
                    "Udemy",
                    "Coursera",
                    "LinkedIn Learning",
                    "Pluralsight",
                    "Amazon",
                    "O'Reilly",
                    "Safari Books",
                    "MasterClass",
                ],
                "typical_amount_range": (20, 500),
                "tax_deductible": True,
                "requires_receipt": True,
            },
            "marketing": {
                "name": "Marketing & Advertising",
                "description": "Marketing, advertising, and promotional expenses",
                "keywords": [
                    "marketing",
                    "advertising",
                    "ads",
                    "promotion",
                    "campaign",
                    "social media",
                    "facebook",
                    "google ads",
                    "linkedin",
                    "twitter",
                    "instagram",
                    "youtube",
                    "website",
                    "seo",
                    "ppc",
                ],
                "common_vendors": [
                    "Google",
                    "Facebook",
                    "LinkedIn",
                    "Twitter",
                    "Instagram",
                    "YouTube",
                    "Mailchimp",
                    "Constant Contact",
                    "Hootsuite",
                ],
                "typical_amount_range": (50, 5000),
                "tax_deductible": True,
                "requires_receipt": True,
            },
            "utilities": {
                "name": "Utilities",
                "description": "Internet, phone, electricity, and utility services",
                "keywords": [
                    "internet",
                    "phone",
                    "mobile",
                    "cell",
                    "electricity",
                    "gas",
                    "water",
                    "utility",
                    "broadband",
                    "wifi",
                    "verizon",
                    "att",
                    "comcast",
                    "spectrum",
                    "tmobile",
                ],
                "common_vendors": [
                    "Verizon",
                    "AT&T",
                    "T-Mobile",
                    "Comcast",
                    "Spectrum",
                    "Cox",
                    "Charter",
                    "CenturyLink",
                    "Optimum",
                ],
                "typical_amount_range": (30, 300),
                "tax_deductible": True,
                "requires_receipt": False,
            },
            "equipment": {
                "name": "Equipment & Hardware",
                "description": "Business equipment, hardware, and tools",
                "keywords": [
                    "equipment",
                    "hardware",
                    "tool",
                    "laptop",
                    "computer",
                    "tablet",
                    "phone",
                    "camera",
                    "printer",
                    "scanner",
                    "router",
                    "switch",
                    "server",
                    "backup",
                    "storage",
                ],
                "common_vendors": [
                    "Apple",
                    "Dell",
                    "HP",
                    "Lenovo",
                    "Amazon",
                    "Best Buy",
                    "Newegg",
                    "B&H",
                    "Micro Center",
                    "CDW",
                ],
                "typical_amount_range": (100, 5000),
                "tax_deductible": True,
                "requires_receipt": True,
            },
        }

    def _load_categorization_rules(self) -> List[Dict[str, Any]]:
        """Load rule-based categorization patterns."""
        return [
            {
                "name": "Uber/Lyft Transportation",
                "condition": {"vendor_contains": ["uber", "lyft"]},
                "category": "travel",
                "confidence": 0.95,
                "reasoning": "Rideshare service",
            },
            {
                "name": "Coffee Shops",
                "condition": {"vendor_contains": ["starbucks", "dunkin", "coffee"]},
                "category": "meals",
                "confidence": 0.90,
                "reasoning": "Coffee shop purchase",
            },
            {
                "name": "Airlines",
                "condition": {
                    "vendor_contains": [
                        "airlines",
                        "delta",
                        "united",
                        "american",
                        "southwest",
                    ]
                },
                "category": "travel",
                "confidence": 0.98,
                "reasoning": "Airline ticket purchase",
            },
            {
                "name": "Hotels",
                "condition": {
                    "vendor_contains": [
                        "hotel",
                        "marriott",
                        "hilton",
                        "hyatt",
                        "airbnb",
                    ]
                },
                "category": "travel",
                "confidence": 0.95,
                "reasoning": "Hotel or accommodation booking",
            },
            {
                "name": "Office Stores",
                "condition": {
                    "vendor_contains": ["staples", "office depot", "officemax"]
                },
                "category": "office_supplies",
                "confidence": 0.90,
                "reasoning": "Office supply store purchase",
            },
            {
                "name": "Software Subscriptions",
                "condition": {
                    "description_contains": ["subscription", "saas", "monthly"],
                    "vendor_contains": [
                        "microsoft",
                        "adobe",
                        "google",
                        "zoom",
                        "slack",
                    ],
                },
                "category": "software",
                "confidence": 0.92,
                "reasoning": "Software subscription service",
            },
            {
                "name": "High-value Equipment",
                "condition": {"amount_range": (1000, float("inf"))},
                "category": "equipment",
                "confidence": 0.70,
                "reasoning": "High-value purchase likely equipment",
            },
            {
                "name": "Small Food Purchases",
                "condition": {
                    "amount_range": (5, 50),
                    "description_contains": [
                        "restaurant",
                        "food",
                        "cafe",
                        "lunch",
                        "dinner",
                    ],
                },
                "category": "meals",
                "confidence": 0.85,
                "reasoning": "Small food-related purchase",
            },
        ]

    async def categorize_expense(
        self,
        expense: ExpenseResult,
        use_ai: bool = True,
        include_reasoning: bool = True,
    ) -> CategorizationResult:
        """
        Categorize a single expense with AI assistance.

        Args:
            expense: Expense data to categorize
            use_ai: Whether to use AI for categorization
            include_reasoning: Whether to include detailed reasoning

        Returns:
            Categorization result with suggestions
        """
        start_time = datetime.now()

        try:
            # Generate all possible suggestions
            all_suggestions = []

            # 1. Rule-based suggestions
            rule_suggestions = self._apply_categorization_rules(expense)
            all_suggestions.extend(rule_suggestions)

            # 2. Pattern-based suggestions
            pattern_suggestions = self._find_pattern_matches(expense)
            all_suggestions.extend(pattern_suggestions)

            # 3. AI-based suggestions (if enabled)
            if use_ai:
                ai_suggestions = self._get_ai_suggestions(expense, include_reasoning)
                all_suggestions.extend(ai_suggestions)

            # 4. Historical user feedback
            feedback_suggestions = self._get_feedback_suggestions(expense)
            all_suggestions.extend(feedback_suggestions)

            # Consolidate and rank suggestions
            final_suggestions = self._consolidate_suggestions(all_suggestions)

            # Determine best suggestion
            best_suggestion = final_suggestions[0] if final_suggestions else None
            suggested_category = (
                best_suggestion.category if best_suggestion else "Uncategorized"
            )
            final_confidence = best_suggestion.confidence if best_suggestion else 0.0

            # Determine if manual review is needed
            needs_review = (
                final_confidence < 0.7
                or len(final_suggestions) == 0
                or (
                    len(final_suggestions) > 1
                    and final_suggestions[0].confidence
                    - final_suggestions[1].confidence
                    < 0.2
                )
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            result = CategorizationResult(
                expense_id=expense.email_id or "unknown",
                original_description=str(expense.description or ""),
                suggested_category=suggested_category,
                all_suggestions=final_suggestions,
                final_confidence=final_confidence,
                needs_review=needs_review,
                processing_time_ms=processing_time,
                timestamp=datetime.now(),
            )

            # Update statistics
            self._update_stats(result)

            logger.info(
                f"Categorized expense as '{suggested_category}' with "
                f"{final_confidence:.2f} confidence"
            )
            return result

        except Exception as e:
            logger.error(f"Error categorizing expense: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return CategorizationResult(
                expense_id=expense.email_id or "unknown",
                original_description=str(expense.description or ""),
                suggested_category="Uncategorized",
                all_suggestions=[],
                final_confidence=0.0,
                needs_review=True,
                processing_time_ms=processing_time,
                timestamp=datetime.now(),
            )

    def _apply_categorization_rules(
        self, expense: ExpenseResult
    ) -> List[CategorySuggestion]:
        """Apply rule-based categorization."""
        suggestions = []

        description = (expense.description or "").lower()
        vendor = (expense.vendor or "").lower()
        amount = expense.amount or 0

        for rule in self.categorization_rules:
            matches = True
            keywords_matched = []

            # Check conditions
            condition = rule["condition"]

            if "vendor_contains" in condition:
                vendor_keywords = condition["vendor_contains"]
                vendor_matches = [kw for kw in vendor_keywords if kw.lower() in vendor]
                if not vendor_matches:
                    matches = False
                else:
                    keywords_matched.extend(vendor_matches)

            if "description_contains" in condition and matches:
                desc_keywords = condition["description_contains"]
                desc_matches = [kw for kw in desc_keywords if kw.lower() in description]
                if not desc_matches:
                    matches = False
                else:
                    keywords_matched.extend(desc_matches)

            if "amount_range" in condition and matches:
                min_amount, max_amount = condition["amount_range"]
                if not (min_amount <= amount <= max_amount):
                    matches = False

            if matches:
                confidence = rule["confidence"]
                confidence_level = self._get_confidence_level(confidence)

                suggestion = CategorySuggestion(
                    category=self.categories[rule["category"]]["name"],
                    confidence=confidence,
                    confidence_level=confidence_level,
                    reasoning=rule["reasoning"],
                    keywords_matched=keywords_matched,
                    similar_transactions=[],
                    suggested_by="rule",
                    metadata={"rule_name": rule["name"]},
                )

                suggestions.append(suggestion)

        return suggestions

    def _find_pattern_matches(self, expense: ExpenseResult) -> List[CategorySuggestion]:
        """Find pattern matches from historical data."""
        suggestions = []

        # This would analyze historical patterns in a real implementation
        # For now, return basic keyword-based suggestions

        description = (expense.description or "").lower()
        vendor = (expense.vendor or "").lower()

        for category_key, category_info in self.categories.items():
            score = 0.0
            matched_keywords = []

            # Check keywords
            for keyword in category_info["keywords"]:
                if keyword.lower() in description or keyword.lower() in vendor:
                    score += 0.1
                    matched_keywords.append(keyword)

            # Check common vendors
            for common_vendor in category_info["common_vendors"]:
                if common_vendor.lower() in vendor:
                    score += 0.2
                    matched_keywords.append(common_vendor)

            # Check amount range
            min_amount, max_amount = category_info["typical_amount_range"]
            amount = expense.amount or 0
            if min_amount <= amount <= max_amount:
                score += 0.1

            if score > 0.2:  # Minimum threshold
                confidence = min(score, 0.8)  # Cap at 80% for pattern matching
                confidence_level = self._get_confidence_level(confidence)

                suggestion = CategorySuggestion(
                    category=category_info["name"],
                    confidence=confidence,
                    confidence_level=confidence_level,
                    reasoning=(
                        f"Pattern match based on {len(matched_keywords)} indicators"
                    ),
                    keywords_matched=matched_keywords,
                    similar_transactions=[],
                    suggested_by="pattern",
                    metadata={"pattern_score": score},
                )

                suggestions.append(suggestion)

        return suggestions

    def _get_ai_suggestions(
        self, expense: ExpenseResult, include_reasoning: bool = True
    ) -> List[CategorySuggestion]:
        """Get AI-powered categorization suggestions."""
        try:
            # Prepare context for the LLM
            categories_list = [info["name"] for info in self.categories.values()]

            prompt = self._build_categorization_prompt(
                expense, categories_list, include_reasoning
            )

            # Query the LLM
            response_content = self.llm_manager.generate_response(
                prompt=prompt,
                model=self.model_name,
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=500,
            )

            if not response_content:
                logger.warning("Empty response from LLM")
                return []

            # Parse the response
            ai_suggestions = self._parse_ai_response(response_content)

            return ai_suggestions

        except Exception as e:
            logger.error(f"Error getting AI suggestions: {e}")
            return []

    def _build_categorization_prompt(
        self, expense: ExpenseResult, categories: List[str], include_reasoning: bool
    ) -> str:
        """Build the prompt for AI categorization."""

        prompt = (
            f"You are an expert expense categorization system. "
            f"Analyze the following expense and suggest the most appropriate "
            f"category.\n\n"
            f"EXPENSE DETAILS:\n"
            f"- Description: {expense.description or 'Not provided'}\n"
            f"- Vendor: {expense.vendor or 'Not provided'}\n"
            f"- Amount: ${expense.amount or 0:.2f}\n"
            f"- Date: "
            f"{expense.date.strftime('%Y-%m-%d') if expense.date else 'Not provided'}"
            f"\n\n"
            f"AVAILABLE CATEGORIES:\n"
            f"{', '.join(categories)}\n\n"
            f"CATEGORY DEFINITIONS:\n"
        )

        # Add category definitions
        for category_info in self.categories.values():
            prompt += f"- {category_info['name']}: {category_info['description']}\n"

        if include_reasoning:
            prompt += """
Please respond with a JSON object containing:
1. "primary_category": The most likely category
2. "confidence": Confidence score (0.0 to 1.0)
3. "reasoning": Brief explanation of why this category was chosen
4. "alternative_categories": Up to 2 other possible categories with "
"their confidence scores
5. "keywords_found": Any relevant keywords you identified

Example response:
{
  "primary_category": "Travel",
  "confidence": 0.95,
  "reasoning": "Uber ride expense clearly indicates transportation/travel",
  "alternative_categories": [
    {"category": "Meals", "confidence": 0.05}
  ],
  "keywords_found": ["uber", "ride", "transportation"]
}
"""
        else:
            prompt += """
Please respond with just the most appropriate category name from the list above.
"""

        return prompt

    def _parse_ai_response(self, response_content: str) -> List[CategorySuggestion]:
        """Parse AI response into category suggestions."""
        suggestions: List[CategorySuggestion] = []

        try:
            # Try to parse as JSON first
            if response_content.strip().startswith("{"):
                data = json.loads(response_content)

                # Primary suggestion
                primary_category = data.get("primary_category", "Uncategorized")
                confidence = float(data.get("confidence", 0.5))
                reasoning = data.get("reasoning", "AI categorization")
                keywords = data.get("keywords_found", [])

                confidence_level = self._get_confidence_level(confidence)

                primary_suggestion = CategorySuggestion(
                    category=primary_category,
                    confidence=confidence,
                    confidence_level=confidence_level,
                    reasoning=reasoning,
                    keywords_matched=keywords,
                    similar_transactions=[],
                    suggested_by="ai",
                    metadata={"model": self.model_name},
                )

                suggestions.append(primary_suggestion)

                # Alternative suggestions
                alternatives = data.get("alternative_categories", [])
                for alt in alternatives:
                    alt_category = alt.get("category", "Uncategorized")
                    alt_confidence = float(alt.get("confidence", 0.1))
                    alt_confidence_level = self._get_confidence_level(alt_confidence)

                    alt_suggestion = CategorySuggestion(
                        category=alt_category,
                        confidence=alt_confidence,
                        confidence_level=alt_confidence_level,
                        reasoning="Alternative AI suggestion",
                        keywords_matched=keywords,
                        similar_transactions=[],
                        suggested_by="ai",
                        metadata={"model": self.model_name, "type": "alternative"},
                    )

                    suggestions.append(alt_suggestion)

            else:
                # Simple category name response
                category = response_content.strip()
                if category in [info["name"] for info in self.categories.values()]:
                    suggestion = CategorySuggestion(
                        category=category,
                        confidence=0.75,  # Default confidence for simple responses
                        confidence_level=ConfidenceLevel.MEDIUM,
                        reasoning="AI categorization",
                        keywords_matched=[],
                        similar_transactions=[],
                        suggested_by="ai",
                        metadata={"model": self.model_name},
                    )

                    suggestions.append(suggestion)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")

        return suggestions

    def _get_feedback_suggestions(
        self, expense: ExpenseResult
    ) -> List[CategorySuggestion]:
        """Get suggestions based on historical user feedback."""
        suggestions: List[CategorySuggestion] = []

        # This would analyze user feedback patterns in a real implementation
        # For now, return empty list

        return suggestions

    def _consolidate_suggestions(
        self, suggestions: List[CategorySuggestion]
    ) -> List[CategorySuggestion]:
        """Consolidate and rank suggestions by category and confidence."""
        if not suggestions:
            return []

        # Group suggestions by category
        category_groups: Dict[str, List[CategorySuggestion]] = {}
        for suggestion in suggestions:
            category = suggestion.category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(suggestion)

        # Consolidate each group
        consolidated = []
        for category, group in category_groups.items():
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                # Combine multiple suggestions for the same category
                best_suggestion = max(group, key=lambda x: x.confidence)

                # Calculate weighted confidence
                total_confidence = sum(s.confidence for s in group)
                avg_confidence = total_confidence / len(group)

                # Use the higher of max or weighted average
                final_confidence = max(best_suggestion.confidence, avg_confidence * 0.9)

                # Combine keywords and reasoning
                all_keywords = []
                all_reasoning = []
                suggested_by_sources = set()

                for s in group:
                    all_keywords.extend(s.keywords_matched)
                    all_reasoning.append(s.reasoning)
                    suggested_by_sources.add(s.suggested_by)

                consolidated_suggestion = CategorySuggestion(
                    category=category,
                    confidence=min(final_confidence, 1.0),  # Cap at 1.0
                    confidence_level=self._get_confidence_level(final_confidence),
                    reasoning="; ".join(set(all_reasoning)),
                    keywords_matched=list(set(all_keywords)),
                    similar_transactions=[],
                    suggested_by="+".join(sorted(suggested_by_sources)),
                    metadata={"source_count": len(group)},
                )

                consolidated.append(consolidated_suggestion)

        # Sort by confidence (highest first)
        consolidated.sort(key=lambda x: x.confidence, reverse=True)

        return consolidated

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level."""
        if confidence >= 0.9:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _update_stats(self, result: CategorizationResult) -> None:
        """Update performance statistics."""
        self.stats["total_categorizations"] += 1

        if result.final_confidence >= 0.9:
            self.stats["high_confidence"] += 1
        elif result.final_confidence >= 0.7:
            self.stats["medium_confidence"] += 1
        else:
            self.stats["low_confidence"] += 1

    async def categorize_batch(
        self,
        expenses: List[ExpenseResult],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[CategorizationResult]:
        """
        Categorize a batch of expenses.

        Args:
            expenses: List of expenses to categorize
            progress_callback: Optional progress callback function

        Returns:
            List of categorization results
        """
        results = []
        total = len(expenses)

        for i, expense in enumerate(expenses):
            try:
                result = await self.categorize_expense(expense)
                results.append(result)

                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(
                        {
                            "progress": progress,
                            "processed": i + 1,
                            "total": total,
                            "current_expense": expense.description,
                        }
                    )

            except Exception as e:
                logger.error(f"Error categorizing expense {i}: {e}")
                continue

        logger.info(f"Categorized {len(results)} out of {total} expenses")
        return results

    def learn_from_feedback(
        self,
        expense_id: str,
        correct_category: str,
        original_suggestion: str,
        user_reasoning: Optional[str] = None,
    ) -> None:
        """
        Learn from user feedback to improve future suggestions.

        Args:
            expense_id: ID of the expense
            correct_category: User-provided correct category
            original_suggestion: Originally suggested category
            user_reasoning: Optional user reasoning
        """
        feedback_entry = {
            "expense_id": expense_id,
            "correct_category": correct_category,
            "original_suggestion": original_suggestion,
            "user_reasoning": user_reasoning,
            "timestamp": datetime.now().isoformat(),
        }

        self.user_feedback_history[expense_id] = feedback_entry

        if correct_category != original_suggestion:
            self.stats["user_corrections"] += 1

        # Update accuracy rate
        total_feedback = len(self.user_feedback_history)
        if total_feedback > 0:
            correct_predictions = total_feedback - self.stats["user_corrections"]
            self.stats["accuracy_rate"] = correct_predictions / total_feedback

        logger.info(
            f"Learned from user feedback: {correct_category} for expense {expense_id}"
        )

    def get_categorization_stats(self) -> Dict[str, Any]:
        """Get categorization performance statistics."""
        return self.stats.copy()

    def get_category_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all category definitions."""
        return self.categories.copy()

    def add_custom_category(
        self, category_key: str, category_info: Dict[str, Any]
    ) -> bool:
        """
        Add a custom category definition.

        Args:
            category_key: Unique key for the category
            category_info: Category information dictionary

        Returns:
            True if successfully added
        """
        try:
            # Validate required fields
            required_fields = ["name", "description", "keywords"]
            for field in required_fields:
                if field not in category_info:
                    logger.error(f"Missing required field '{field}' in category info")
                    return False

            self.categories[category_key] = category_info
            logger.info(f"Added custom category: {category_info['name']}")
            return True

        except Exception as e:
            logger.error(f"Error adding custom category: {e}")
            return False
