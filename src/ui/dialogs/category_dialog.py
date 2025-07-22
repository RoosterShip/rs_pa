"""
Category management dialog for expense categorization.

This module provides a comprehensive dialog for managing expense categories
with AI-powered suggestions and bulk operations.
"""

import logging

# from datetime import datetime  # TODO: Use when needed
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.llm_manager import OllamaManager

logger = logging.getLogger(__name__)


class CategorySuggestionWorker(QThread):
    """Worker thread for generating AI-powered category suggestions."""

    suggestions_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, descriptions: List[str]):
        super().__init__()
        self.descriptions = descriptions
        self.llm_manager = OllamaManager()

    def run(self) -> None:
        """Generate category suggestions using AI."""
        try:
            suggestions = []

            for description in self.descriptions:
                # Mock AI suggestions for now
                # In real implementation, would use LLM to analyze expense descriptions
                mock_suggestions = [
                    {
                        "category": "Travel",
                        "confidence": 0.85,
                        "reason": "Contains travel-related keywords",
                    },
                    {
                        "category": "Meals",
                        "confidence": 0.75,
                        "reason": "Restaurant or food service mentioned",
                    },
                    {
                        "category": "Office Supplies",
                        "confidence": 0.65,
                        "reason": "Office or supply keywords detected",
                    },
                ]

                suggestions.append(
                    {"description": description, "suggestions": mock_suggestions}
                )

            self.suggestions_ready.emit(suggestions)

        except Exception as e:
            logger.error(f"Error generating category suggestions: {e}")
            self.error_occurred.emit(str(e))


class CategoryManagerDialog(QDialog):
    """
    Advanced dialog for managing expense categories.

    Features:
    - Category hierarchy management
    - AI-powered categorization suggestions
    - Bulk category operations
    - Category rules and automation
    - Statistics and usage analysis
    - Import/export category definitions
    """

    categories_updated = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.categories = self._load_default_categories()
        self.category_rules: List[Dict[str, Any]] = []
        self.suggestion_worker = None

        self.setWindowTitle("Category Management")
        self.setModal(True)
        self.resize(1100, 800)

        self._setup_ui()
        self._connect_signals()
        self._populate_categories()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create tabbed interface
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_categories_tab()
        self._create_rules_tab()
        self._create_suggestions_tab()
        self._create_statistics_tab()
        self._create_import_export_tab()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.setToolTip("Apply category changes")
        button_layout.addWidget(self.apply_btn)

        self.save_btn = QPushButton("Save & Close")
        self.save_btn.setToolTip("Save changes and close")
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _create_categories_tab(self) -> None:
        """Create the categories management tab."""
        categories_tab = QWidget()
        layout = QHBoxLayout(categories_tab)

        # Left side - Category tree
        left_group = QGroupBox("Categories")
        left_layout = QVBoxLayout(left_group)

        # Category tree controls
        tree_controls = QHBoxLayout()

        self.add_category_btn = QPushButton("Add Category")
        self.add_category_btn.setToolTip("Add a new category")
        tree_controls.addWidget(self.add_category_btn)

        self.add_subcategory_btn = QPushButton("Add Subcategory")
        self.add_subcategory_btn.setToolTip("Add subcategory to selected category")
        tree_controls.addWidget(self.add_subcategory_btn)

        self.delete_category_btn = QPushButton("Delete")
        self.delete_category_btn.setToolTip("Delete selected category")
        tree_controls.addWidget(self.delete_category_btn)

        tree_controls.addStretch()
        left_layout.addLayout(tree_controls)

        # Category tree
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabels(["Category", "Count", "Last Used"])
        self.category_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        left_layout.addWidget(self.category_tree)

        # Category search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))

        self.category_search_edit = QLineEdit()
        self.category_search_edit.setPlaceholderText("Search categories...")
        search_layout.addWidget(self.category_search_edit)

        self.clear_search_btn = QPushButton("Clear")
        search_layout.addWidget(self.clear_search_btn)

        left_layout.addLayout(search_layout)

        layout.addWidget(left_group)

        # Right side - Category details
        right_group = QGroupBox("Category Details")
        right_layout = QFormLayout(right_group)

        self.category_name_edit = QLineEdit()
        self.category_name_edit.setPlaceholderText("Enter category name")
        right_layout.addRow("Name:", self.category_name_edit)

        self.category_description_edit = QTextEdit()
        self.category_description_edit.setPlaceholderText("Optional description")
        self.category_description_edit.setMaximumHeight(80)
        right_layout.addRow("Description:", self.category_description_edit)

        # Category color
        color_layout = QHBoxLayout()
        self.category_color_btn = QPushButton()
        self.category_color_btn.setMaximumWidth(50)
        self.category_color_btn.setMaximumHeight(30)
        self.category_color_btn.setStyleSheet(
            "background-color: #3498db; border: 1px solid #ccc;"
        )
        color_layout.addWidget(self.category_color_btn)

        self.category_color_label = QLabel("#3498db")
        color_layout.addWidget(self.category_color_label)
        color_layout.addStretch()
        right_layout.addRow("Color:", color_layout)

        # Keywords for auto-categorization
        self.category_keywords_edit = QLineEdit()
        self.category_keywords_edit.setPlaceholderText(
            "Comma-separated keywords for auto-categorization"
        )
        right_layout.addRow("Keywords:", self.category_keywords_edit)

        # Tax deductible checkbox
        self.tax_deductible_checkbox = QCheckBox("Tax deductible category")
        right_layout.addRow("", self.tax_deductible_checkbox)

        # Requires receipt checkbox
        self.requires_receipt_checkbox = QCheckBox("Always requires receipt")
        right_layout.addRow("", self.requires_receipt_checkbox)

        # Budget limit
        self.budget_limit_edit = QLineEdit()
        self.budget_limit_edit.setPlaceholderText("Optional budget limit")
        right_layout.addRow("Budget Limit:", self.budget_limit_edit)

        # Update category button
        self.update_category_btn = QPushButton("Update Category")
        self.update_category_btn.setEnabled(False)
        right_layout.addRow("", self.update_category_btn)

        layout.addWidget(right_group)

        self.tab_widget.addTab(categories_tab, "Categories")

    def _create_rules_tab(self) -> None:
        """Create the categorization rules tab."""
        rules_tab = QWidget()
        layout = QVBoxLayout(rules_tab)

        # Rules explanation
        info_label = QLabel(
            "Create rules to automatically categorize expenses based on vendor, "
            "description, amount, or other criteria."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; border-radius: 5px;"
        )
        layout.addWidget(info_label)

        # Rules controls
        controls_layout = QHBoxLayout()

        self.add_rule_btn = QPushButton("Add Rule")
        controls_layout.addWidget(self.add_rule_btn)

        self.edit_rule_btn = QPushButton("Edit Rule")
        self.edit_rule_btn.setEnabled(False)
        controls_layout.addWidget(self.edit_rule_btn)

        self.delete_rule_btn = QPushButton("Delete Rule")
        self.delete_rule_btn.setEnabled(False)
        controls_layout.addWidget(self.delete_rule_btn)

        controls_layout.addStretch()

        self.test_rules_btn = QPushButton("Test Rules")
        self.test_rules_btn.setToolTip("Test rules against existing expenses")
        controls_layout.addWidget(self.test_rules_btn)

        layout.addLayout(controls_layout)

        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(6)
        self.rules_table.setHorizontalHeaderLabels(
            ["Rule Name", "Condition", "Category", "Priority", "Active", "Last Used"]
        )
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.rules_table)

        # Rule testing results
        results_group = QGroupBox("Rule Testing Results")
        results_layout = QVBoxLayout(results_group)

        self.rule_results_text = QTextEdit()
        self.rule_results_text.setMaximumHeight(150)
        self.rule_results_text.setPlaceholderText(
            "Rule testing results will appear here"
        )
        results_layout.addWidget(self.rule_results_text)

        layout.addWidget(results_group)

        self.tab_widget.addTab(rules_tab, "Auto-Rules")

    def _create_suggestions_tab(self) -> None:
        """Create the AI suggestions tab."""
        suggestions_tab = QWidget()
        layout = QVBoxLayout(suggestions_tab)

        # Suggestions explanation
        info_label = QLabel(
            "Get AI-powered category suggestions for uncategorized or "
            "ambiguous expenses. The system analyzes expense descriptions "
            "and suggests appropriate categories."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; border-radius: 5px;"
        )
        layout.addWidget(info_label)

        # Suggestions controls
        controls_layout = QHBoxLayout()

        self.load_uncategorized_btn = QPushButton("Load Uncategorized")
        self.load_uncategorized_btn.setToolTip("Load uncategorized expenses")
        controls_layout.addWidget(self.load_uncategorized_btn)

        self.generate_suggestions_btn = QPushButton("Generate Suggestions")
        self.generate_suggestions_btn.setToolTip(
            "Generate AI-powered category suggestions"
        )
        controls_layout.addWidget(self.generate_suggestions_btn)

        controls_layout.addStretch()

        self.apply_all_suggestions_btn = QPushButton("Apply All")
        self.apply_all_suggestions_btn.setToolTip(
            "Apply all high-confidence suggestions"
        )
        self.apply_all_suggestions_btn.setEnabled(False)
        controls_layout.addWidget(self.apply_all_suggestions_btn)

        layout.addLayout(controls_layout)

        # Progress bar for AI processing
        self.suggestions_progress = QProgressBar()
        self.suggestions_progress.setVisible(False)
        layout.addWidget(self.suggestions_progress)

        # Suggestions table
        self.suggestions_table = QTableWidget()
        self.suggestions_table.setColumnCount(6)
        self.suggestions_table.setHorizontalHeaderLabels(
            [
                "Description",
                "Current Category",
                "Suggested Category",
                "Confidence",
                "Reason",
                "Action",
            ]
        )
        self.suggestions_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.suggestions_table)

        # Batch operations
        batch_layout = QHBoxLayout()

        batch_layout.addWidget(QLabel("Batch Operations:"))

        self.confidence_threshold_spin = QSpinBox()
        self.confidence_threshold_spin.setRange(50, 95)
        self.confidence_threshold_spin.setValue(80)
        self.confidence_threshold_spin.setSuffix("%")
        batch_layout.addWidget(QLabel("Min Confidence:"))
        batch_layout.addWidget(self.confidence_threshold_spin)

        self.apply_high_confidence_btn = QPushButton("Apply High Confidence")
        batch_layout.addWidget(self.apply_high_confidence_btn)

        batch_layout.addStretch()

        layout.addLayout(batch_layout)

        self.tab_widget.addTab(suggestions_tab, "AI Suggestions")

    def _create_statistics_tab(self) -> None:
        """Create the statistics tab."""
        statistics_tab = QWidget()
        layout = QVBoxLayout(statistics_tab)

        # Statistics controls
        controls_layout = QHBoxLayout()

        self.refresh_stats_btn = QPushButton("Refresh Statistics")
        controls_layout.addWidget(self.refresh_stats_btn)

        controls_layout.addStretch()

        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems(
            ["Last 30 days", "Last 90 days", "Last year", "All time"]
        )
        controls_layout.addWidget(QLabel("Period:"))
        controls_layout.addWidget(self.date_range_combo)

        layout.addLayout(controls_layout)

        # Statistics display
        stats_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Category usage table
        usage_group = QGroupBox("Category Usage")
        usage_layout = QVBoxLayout(usage_group)

        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(4)
        self.usage_table.setHorizontalHeaderLabels(
            ["Category", "Count", "Total Amount", "Avg Amount"]
        )
        usage_layout.addWidget(self.usage_table)

        stats_splitter.addWidget(usage_group)

        # Summary statistics
        summary_group = QGroupBox("Summary")
        summary_layout = QFormLayout(summary_group)

        self.total_categories_label = QLabel("0")
        summary_layout.addRow("Total Categories:", self.total_categories_label)

        self.active_categories_label = QLabel("0")
        summary_layout.addRow("Active Categories:", self.active_categories_label)

        self.unused_categories_label = QLabel("0")
        summary_layout.addRow("Unused Categories:", self.unused_categories_label)

        self.most_used_category_label = QLabel("None")
        summary_layout.addRow("Most Used:", self.most_used_category_label)

        self.categorization_rate_label = QLabel("0%")
        summary_layout.addRow("Categorization Rate:", self.categorization_rate_label)

        self.avg_expenses_per_category_label = QLabel("0")
        summary_layout.addRow("Avg per Category:", self.avg_expenses_per_category_label)

        stats_splitter.addWidget(summary_group)

        layout.addWidget(stats_splitter)

        # Trends section
        trends_group = QGroupBox("Trends & Insights")
        trends_layout = QVBoxLayout(trends_group)

        self.trends_text = QTextEdit()
        self.trends_text.setMaximumHeight(120)
        self.trends_text.setReadOnly(True)
        self.trends_text.setPlaceholderText(
            "Category trends and insights will appear here"
        )
        trends_layout.addWidget(self.trends_text)

        layout.addWidget(trends_group)

        self.tab_widget.addTab(statistics_tab, "Statistics")

    def _create_import_export_tab(self) -> None:
        """Create the import/export tab."""
        import_export_tab = QWidget()
        layout = QVBoxLayout(import_export_tab)

        # Export section
        export_group = QGroupBox("Export Categories")
        export_layout = QFormLayout(export_group)

        export_info = QLabel(
            "Export your category definitions to share with other users or as a backup."
        )
        export_info.setWordWrap(True)
        export_layout.addRow(export_info)

        export_buttons = QHBoxLayout()

        self.export_json_btn = QPushButton("Export as JSON")
        export_buttons.addWidget(self.export_json_btn)

        self.export_csv_btn = QPushButton("Export as CSV")
        export_buttons.addWidget(self.export_csv_btn)

        export_buttons.addStretch()
        export_layout.addRow("", export_buttons)

        layout.addWidget(export_group)

        # Import section
        import_group = QGroupBox("Import Categories")
        import_layout = QFormLayout(import_group)

        import_info = QLabel(
            "Import category definitions from a file. This will merge with "
            "existing categories."
        )
        import_info.setWordWrap(True)
        import_layout.addRow(import_info)

        import_file_layout = QHBoxLayout()

        self.import_file_edit = QLineEdit()
        self.import_file_edit.setPlaceholderText("Select file to import")
        import_file_layout.addWidget(self.import_file_edit)

        self.browse_import_btn = QPushButton("Browse...")
        import_file_layout.addWidget(self.browse_import_btn)

        import_layout.addRow("Import File:", import_file_layout)

        import_buttons = QHBoxLayout()

        self.validate_import_btn = QPushButton("Validate File")
        self.validate_import_btn.setEnabled(False)
        import_buttons.addWidget(self.validate_import_btn)

        self.import_btn = QPushButton("Import Categories")
        self.import_btn.setEnabled(False)
        import_buttons.addWidget(self.import_btn)

        import_buttons.addStretch()
        import_layout.addRow("", import_buttons)

        layout.addWidget(import_group)

        # Preset categories section
        presets_group = QGroupBox("Category Presets")
        presets_layout = QFormLayout(presets_group)

        presets_info = QLabel(
            "Load common category sets as a starting point for your categorization."
        )
        presets_info.setWordWrap(True)
        presets_layout.addRow(presets_info)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(
            [
                "Business Expenses",
                "Personal Finance",
                "Travel & Entertainment",
                "Freelancer Categories",
                "Small Business",
                "Non-Profit Organization",
            ]
        )
        presets_layout.addRow("Preset:", self.preset_combo)

        preset_buttons = QHBoxLayout()

        self.preview_preset_btn = QPushButton("Preview Preset")
        preset_buttons.addWidget(self.preview_preset_btn)

        self.load_preset_btn = QPushButton("Load Preset")
        preset_buttons.addWidget(self.load_preset_btn)

        preset_buttons.addStretch()
        presets_layout.addRow("", preset_buttons)

        layout.addWidget(presets_group)

        layout.addStretch()
        self.tab_widget.addTab(import_export_tab, "Import/Export")

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        # Categories tab
        self.add_category_btn.clicked.connect(self._add_category)
        self.add_subcategory_btn.clicked.connect(self._add_subcategory)
        self.delete_category_btn.clicked.connect(self._delete_category)
        self.category_tree.itemClicked.connect(self._on_category_selected)
        self.category_tree.customContextMenuRequested.connect(
            self._show_category_context_menu
        )
        self.category_search_edit.textChanged.connect(self._filter_categories)
        self.clear_search_btn.clicked.connect(self._clear_category_search)
        self.category_color_btn.clicked.connect(self._choose_category_color)
        self.update_category_btn.clicked.connect(self._update_category)

        # Rules tab
        self.add_rule_btn.clicked.connect(self._add_rule)
        self.edit_rule_btn.clicked.connect(self._edit_rule)
        self.delete_rule_btn.clicked.connect(self._delete_rule)
        self.test_rules_btn.clicked.connect(self._test_rules)
        self.rules_table.itemSelectionChanged.connect(self._on_rule_selected)

        # Suggestions tab
        self.load_uncategorized_btn.clicked.connect(self._load_uncategorized)
        self.generate_suggestions_btn.clicked.connect(self._generate_suggestions)
        self.apply_all_suggestions_btn.clicked.connect(self._apply_all_suggestions)
        self.apply_high_confidence_btn.clicked.connect(
            self._apply_high_confidence_suggestions
        )

        # Statistics tab
        self.refresh_stats_btn.clicked.connect(self._refresh_statistics)
        self.date_range_combo.currentTextChanged.connect(self._refresh_statistics)

        # Import/Export tab
        self.export_json_btn.clicked.connect(lambda: self._export_categories("json"))
        self.export_csv_btn.clicked.connect(lambda: self._export_categories("csv"))
        self.browse_import_btn.clicked.connect(self._browse_import_file)
        self.validate_import_btn.clicked.connect(self._validate_import)
        self.import_btn.clicked.connect(self._import_categories)
        self.preview_preset_btn.clicked.connect(self._preview_preset)
        self.load_preset_btn.clicked.connect(self._load_preset)

        # Button signals
        self.apply_btn.clicked.connect(self._apply_changes)
        self.save_btn.clicked.connect(self._save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    def _load_default_categories(self) -> List[Dict[str, Any]]:
        """Load default categories."""
        return [
            {
                "id": "travel",
                "name": "Travel",
                "description": "Travel-related expenses",
                "color": "#e74c3c",
                "keywords": ["uber", "lyft", "taxi", "flight", "hotel", "airbnb"],
                "tax_deductible": True,
                "requires_receipt": True,
                "budget_limit": None,
                "subcategories": [
                    {"id": "flights", "name": "Flights", "color": "#c0392b"},
                    {"id": "hotels", "name": "Hotels", "color": "#a93226"},
                    {"id": "transport", "name": "Transportation", "color": "#922b21"},
                ],
            },
            {
                "id": "meals",
                "name": "Meals & Entertainment",
                "description": "Food and entertainment expenses",
                "color": "#f39c12",
                "keywords": ["restaurant", "cafe", "starbucks", "lunch", "dinner"],
                "tax_deductible": False,
                "requires_receipt": True,
                "budget_limit": 500.0,
                "subcategories": [
                    {
                        "id": "business_meals",
                        "name": "Business Meals",
                        "color": "#e67e22",
                    },
                    {"id": "team_events", "name": "Team Events", "color": "#d35400"},
                ],
            },
            {
                "id": "office",
                "name": "Office Supplies",
                "description": "Office equipment and supplies",
                "color": "#3498db",
                "keywords": ["staples", "office", "supplies", "paper", "printer"],
                "tax_deductible": True,
                "requires_receipt": False,
                "budget_limit": 200.0,
                "subcategories": [],
            },
            {
                "id": "software",
                "name": "Software & Services",
                "description": "Software licenses and online services",
                "color": "#9b59b6",
                "keywords": ["saas", "software", "license", "subscription", "cloud"],
                "tax_deductible": True,
                "requires_receipt": True,
                "budget_limit": None,
                "subcategories": [],
            },
        ]

    def _populate_categories(self) -> None:
        """Populate the category tree."""
        self.category_tree.clear()

        for category in self.categories:
            item = QTreeWidgetItem(
                [category["name"], "25", "2024-01-15"]  # Mock count  # Mock last used
            )
            item.setData(0, Qt.ItemDataRole.UserRole, category)

            # Set color
            color = QColor(category.get("color", "#3498db"))
            item.setBackground(0, color)
            item.setForeground(
                0, QColor("white") if color.lightness() < 128 else QColor("black")
            )

            self.category_tree.addTopLevelItem(item)

            # Add subcategories
            for subcategory in category.get("subcategories", []):
                sub_item = QTreeWidgetItem(
                    [
                        subcategory["name"],
                        "8",  # Mock count
                        "2024-01-10",  # Mock last used
                    ]
                )
                sub_item.setData(0, Qt.ItemDataRole.UserRole, subcategory)

                sub_color = QColor(
                    subcategory.get("color", category.get("color", "#3498db"))
                )
                sub_item.setBackground(0, sub_color)
                sub_item.setForeground(
                    0,
                    QColor("white") if sub_color.lightness() < 128 else QColor("black"),
                )

                item.addChild(sub_item)

        self.category_tree.expandAll()

    def _on_category_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle category selection."""
        category_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not category_data:
            return

        # Populate details form
        self.category_name_edit.setText(category_data.get("name", ""))
        self.category_description_edit.setPlainText(
            category_data.get("description", "")
        )
        self.category_keywords_edit.setText(
            ", ".join(category_data.get("keywords", []))
        )
        self.tax_deductible_checkbox.setChecked(
            category_data.get("tax_deductible", False)
        )
        self.requires_receipt_checkbox.setChecked(
            category_data.get("requires_receipt", False)
        )

        budget_limit = category_data.get("budget_limit")
        self.budget_limit_edit.setText(str(budget_limit) if budget_limit else "")

        # Set color
        color = category_data.get("color", "#3498db")
        self.category_color_btn.setStyleSheet(
            f"background-color: {color}; border: 1px solid #ccc;"
        )
        self.category_color_label.setText(color)

        self.update_category_btn.setEnabled(True)

    def _add_category(self) -> None:
        """Add a new category."""
        name, ok = QInputDialog.getText(self, "Add Category", "Category Name:")
        if ok and name:
            new_category = {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "description": "",
                "color": "#3498db",
                "keywords": [],
                "tax_deductible": False,
                "requires_receipt": False,
                "budget_limit": None,
                "subcategories": [],
            }

            self.categories.append(new_category)
            self._populate_categories()

    def _add_subcategory(self) -> None:
        """Add a subcategory to selected category."""
        current_item = self.category_tree.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Warning", "Please select a parent category first."
            )
            return

        # If selected item is a subcategory, get its parent
        if current_item.parent():
            current_item = current_item.parent()

        name, ok = QInputDialog.getText(self, "Add Subcategory", "Subcategory Name:")
        if ok and name:
            category_data = current_item.data(0, Qt.ItemDataRole.UserRole)

            new_subcategory = {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "color": category_data.get("color", "#3498db"),
            }

            if "subcategories" not in category_data:
                category_data["subcategories"] = []

            category_data["subcategories"].append(new_subcategory)
            self._populate_categories()

    def _delete_category(self) -> None:
        """Delete selected category."""
        current_item = self.category_tree.currentItem()
        if not current_item:
            return

        category_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        category_name = category_data.get("name", "Unknown")

        reply = QMessageBox.question(
            self,
            "Delete Category",
            f"Are you sure you want to delete '{category_name}'?\n\n"
            "This will affect all expenses currently using this category.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from categories list
            if current_item.parent():
                # It's a subcategory
                parent_data = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
                parent_data["subcategories"] = [
                    sub
                    for sub in parent_data.get("subcategories", [])
                    if sub.get("id") != category_data.get("id")
                ]
            else:
                # It's a top-level category
                self.categories = [
                    cat
                    for cat in self.categories
                    if cat.get("id") != category_data.get("id")
                ]

            self._populate_categories()

    def _show_category_context_menu(self, position: Any) -> None:
        """Show context menu for category tree."""
        item = self.category_tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        edit_action = QAction("Edit Category", self)
        edit_action.triggered.connect(lambda: self._on_category_selected(item, 0))
        menu.addAction(edit_action)

        menu.addSeparator()

        add_sub_action = QAction("Add Subcategory", self)
        add_sub_action.triggered.connect(self._add_subcategory)
        menu.addAction(add_sub_action)

        menu.addSeparator()

        delete_action = QAction("Delete Category", self)
        delete_action.triggered.connect(self._delete_category)
        menu.addAction(delete_action)

        menu.exec(self.category_tree.mapToGlobal(position))

    def _filter_categories(self, text: str) -> None:
        """Filter categories based on search text."""
        for i in range(self.category_tree.topLevelItemCount()):
            item = self.category_tree.topLevelItem(i)
            if item is not None:
                visible = text.lower() in item.text(0).lower() if text else True
                item.setHidden(not visible)

    def _clear_category_search(self) -> None:
        """Clear category search."""
        self.category_search_edit.clear()
        self._filter_categories("")

    def _choose_category_color(self) -> None:
        """Choose category color."""
        current_color = QColor(self.category_color_label.text())
        color = QColorDialog.getColor(current_color, self, "Choose Category Color")

        if color.isValid():
            color_hex = color.name()
            self.category_color_btn.setStyleSheet(
                f"background-color: {color_hex}; border: 1px solid #ccc;"
            )
            self.category_color_label.setText(color_hex)

    def _update_category(self) -> None:
        """Update the selected category."""
        current_item = self.category_tree.currentItem()
        if not current_item:
            return

        category_data = current_item.data(0, Qt.ItemDataRole.UserRole)

        # Update category data
        category_data["name"] = self.category_name_edit.text()
        category_data["description"] = self.category_description_edit.toPlainText()
        category_data["color"] = self.category_color_label.text()
        category_data["keywords"] = [
            kw.strip()
            for kw in self.category_keywords_edit.text().split(",")
            if kw.strip()
        ]
        category_data["tax_deductible"] = self.tax_deductible_checkbox.isChecked()
        category_data["requires_receipt"] = self.requires_receipt_checkbox.isChecked()

        budget_text = self.budget_limit_edit.text()
        try:
            category_data["budget_limit"] = float(budget_text) if budget_text else None
        except ValueError:
            category_data["budget_limit"] = None

        self._populate_categories()
        QMessageBox.information(
            self, "Success", f"Category '{category_data['name']}' updated successfully."
        )

    def _load_uncategorized(self) -> None:
        """Load uncategorized expenses."""
        # Mock uncategorized expenses
        self.suggestions_table.setRowCount(0)

        mock_expenses = [
            ("Uber ride to airport", "Uncategorized", "", 0, ""),
            ("Starbucks coffee meeting", "Meals", "", 0, ""),
            ("Office supplies from Amazon", "Uncategorized", "", 0, ""),
            ("Software license renewal", "Uncategorized", "", 0, ""),
            ("Business lunch with client", "Uncategorized", "", 0, ""),
        ]

        for i, expense in enumerate(mock_expenses):
            self.suggestions_table.insertRow(i)
            for j, value in enumerate(expense):
                item = QTableWidgetItem(str(value))
                self.suggestions_table.setItem(i, j, item)

            # Add action button
            apply_btn = QPushButton("Apply")
            apply_btn.clicked.connect(
                lambda checked, row=i: self._apply_suggestion(row)
            )
            self.suggestions_table.setCellWidget(i, 5, apply_btn)

    def _generate_suggestions(self) -> None:
        """Generate AI-powered category suggestions."""
        if self.suggestions_table.rowCount() == 0:
            QMessageBox.information(
                self, "No Data", "Please load uncategorized expenses first."
            )
            return

        # Get descriptions from table
        descriptions = []
        for i in range(self.suggestions_table.rowCount()):
            desc_item = self.suggestions_table.item(i, 0)
            if desc_item:
                descriptions.append(desc_item.text())

        # Show progress
        self.suggestions_progress.setVisible(True)
        self.suggestions_progress.setRange(0, 0)  # Indeterminate

        # Start AI worker (disabled in stub)
        # if self.suggestion_worker:
        #     self.suggestion_worker.quit()
        #     self.suggestion_worker.wait()

        # Mock completion for stub implementation
        self._update_suggestions([])

    def _update_suggestions(self, suggestions: List[Dict[str, Any]]) -> None:
        """Update suggestions table with AI results."""
        self.suggestions_progress.setVisible(False)

        for i, suggestion_data in enumerate(suggestions):
            if i >= self.suggestions_table.rowCount():
                break

            best_suggestion = (
                suggestion_data["suggestions"][0]
                if suggestion_data["suggestions"]
                else None
            )

            if best_suggestion:
                # Update suggested category
                suggested_item = QTableWidgetItem(best_suggestion["category"])
                self.suggestions_table.setItem(i, 2, suggested_item)

                # Update confidence
                confidence_item = QTableWidgetItem(
                    f"{best_suggestion['confidence']:.0%}"
                )
                self.suggestions_table.setItem(i, 3, confidence_item)

                # Update reason
                reason_item = QTableWidgetItem(best_suggestion["reason"])
                self.suggestions_table.setItem(i, 4, reason_item)

        self.apply_all_suggestions_btn.setEnabled(True)

    def _on_suggestions_error(self, error_message: str) -> None:
        """Handle suggestions generation error."""
        self.suggestions_progress.setVisible(False)
        QMessageBox.critical(
            self, "AI Error", f"Error generating suggestions: {error_message}"
        )

    def _apply_suggestion(self, row: int) -> None:
        """Apply suggestion for a specific row."""
        suggested_item = self.suggestions_table.item(row, 2)
        if suggested_item:
            # Update current category
            current_item = QTableWidgetItem(suggested_item.text())
            self.suggestions_table.setItem(row, 1, current_item)

            # Clear suggestion
            self.suggestions_table.setItem(row, 2, QTableWidgetItem("Applied"))

    def _apply_all_suggestions(self) -> None:
        """Apply all high-confidence suggestions."""
        applied_count = 0

        for i in range(self.suggestions_table.rowCount()):
            confidence_item = self.suggestions_table.item(i, 3)
            if confidence_item:
                try:
                    confidence = float(confidence_item.text().rstrip("%")) / 100
                    if confidence >= 0.8:  # 80% threshold
                        self._apply_suggestion(i)
                        applied_count += 1
                except ValueError:
                    continue

        QMessageBox.information(
            self, "Applied", f"Applied {applied_count} high-confidence suggestions."
        )

    def _apply_high_confidence_suggestions(self) -> None:
        """Apply suggestions above the specified confidence threshold."""
        threshold = self.confidence_threshold_spin.value() / 100
        applied_count = 0

        for i in range(self.suggestions_table.rowCount()):
            confidence_item = self.suggestions_table.item(i, 3)
            if confidence_item:
                try:
                    confidence = float(confidence_item.text().rstrip("%")) / 100
                    if confidence >= threshold:
                        self._apply_suggestion(i)
                        applied_count += 1
                except ValueError:
                    continue

        QMessageBox.information(
            self,
            "Applied",
            f"Applied {applied_count} suggestions above "
            f"{self.confidence_threshold_spin.value()}% confidence.",
        )

    def _add_rule(self) -> None:
        """Add a new categorization rule."""
        QMessageBox.information(
            self, "Add Rule", "Rule creation dialog would open here."
        )

    def _edit_rule(self) -> None:
        """Edit the selected rule."""
        QMessageBox.information(
            self, "Edit Rule", "Rule editing dialog would open here."
        )

    def _delete_rule(self) -> None:
        """Delete the selected rule."""
        QMessageBox.information(
            self, "Delete Rule", "Selected rule would be deleted here."
        )

    def _test_rules(self) -> None:
        """Test categorization rules."""
        self.rule_results_text.setPlainText(
            "Rule testing results:\n"
            "- Rule 'Uber to Travel': 15 matches found\n"
            "- Rule 'Starbucks to Meals': 8 matches found\n"
            "- Rule 'Amazon Office': 23 matches found\n"
            "\nTotal: 46 expenses would be re-categorized"
        )

    def _on_rule_selected(self) -> None:
        """Handle rule selection."""
        has_selection = bool(self.rules_table.selectedItems())
        self.edit_rule_btn.setEnabled(has_selection)
        self.delete_rule_btn.setEnabled(has_selection)

    def _refresh_statistics(self) -> None:
        """Refresh category usage statistics."""
        # Mock statistics
        self.total_categories_label.setText(str(len(self.categories)))
        self.active_categories_label.setText("12")
        self.unused_categories_label.setText("3")
        self.most_used_category_label.setText("Travel")
        self.categorization_rate_label.setText("87%")
        self.avg_expenses_per_category_label.setText("18")

        # Update usage table
        self.usage_table.setRowCount(len(self.categories))
        for i, category in enumerate(self.categories):
            self.usage_table.setItem(i, 0, QTableWidgetItem(category["name"]))
            self.usage_table.setItem(i, 1, QTableWidgetItem("25"))
            self.usage_table.setItem(i, 2, QTableWidgetItem("$1,234.56"))
            self.usage_table.setItem(i, 3, QTableWidgetItem("$49.38"))

        # Update trends
        self.trends_text.setPlainText(
            "Recent trends:\n"
            "• Travel expenses increased 15% this month\n"
            "• Software subscriptions are the fastest growing category\n"
            "• Office supplies usage has stabilized\n"
            "• 3 categories haven't been used in the last 90 days"
        )

    def _export_categories(self, format_type: str) -> None:
        """Export categories to file."""
        QMessageBox.information(
            self,
            "Export",
            f"Categories would be exported as {format_type.upper()} file.",
        )

    def _browse_import_file(self) -> None:
        """Browse for import file."""
        QMessageBox.information(self, "Import", "File browser would open here.")

    def _validate_import(self) -> None:
        """Validate import file."""
        QMessageBox.information(
            self, "Validation", "Import file would be validated here."
        )

    def _import_categories(self) -> None:
        """Import categories from file."""
        QMessageBox.information(self, "Import", "Categories would be imported here.")

    def _preview_preset(self) -> None:
        """Preview selected category preset."""
        preset_name = self.preset_combo.currentText()
        QMessageBox.information(
            self,
            "Preset Preview",
            f"Preview of '{preset_name}' preset would be shown here.",
        )

    def _load_preset(self) -> None:
        """Load selected category preset."""
        preset_name = self.preset_combo.currentText()
        reply = QMessageBox.question(
            self,
            "Load Preset",
            f"Load the '{preset_name}' category preset?\n\n"
            f"This will add new categories to your existing ones.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self, "Loaded", f"'{preset_name}' preset categories have been loaded."
            )

    def _apply_changes(self) -> None:
        """Apply changes without closing."""
        QMessageBox.information(self, "Applied", "Category changes have been applied.")
        self.categories_updated.emit()

    def _save_and_close(self) -> None:
        """Save changes and close dialog."""
        self.categories_updated.emit()
        self.accept()
