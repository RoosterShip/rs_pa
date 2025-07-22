"""
Workflow designer widget for creating and editing LangGraph workflows.

This module provides a visual workflow designer that allows users to
create, modify, and visualize LangGraph workflows through a drag-and-drop interface.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    pass

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QPen,
    QTransform,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class WorkflowNode(QGraphicsRectItem):
    """Represents a single node in the workflow graph."""

    def __init__(
        self,
        node_type: str,
        node_data: Dict[str, Any],
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        super().__init__(parent)
        self.node_type = node_type
        self.node_data = node_data
        self.connections: list["WorkflowConnection"] = []  # List of connected nodes
        self.input_ports: list[QGraphicsEllipseItem] = []
        self.output_ports: list[QGraphicsEllipseItem] = []

        self._setup_appearance()
        self._setup_interactions()

    def _setup_appearance(self) -> None:
        """Set up the visual appearance of the node."""
        # Node dimensions
        width = 120
        height = 80

        # Set rectangle
        self.setRect(0, 0, width, height)

        # Set colors based on node type
        color_map = {
            "start": QColor("#4CAF50"),  # Green
            "process": QColor("#2196F3"),  # Blue
            "decision": QColor("#FF9800"),  # Orange
            "end": QColor("#F44336"),  # Red
            "data": QColor("#9C27B0"),  # Purple
            "service": QColor("#607D8B"),  # Blue Grey
        }

        color = color_map.get(self.node_type, QColor("#757575"))

        # Set brush and pen
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#333333"), 2))

        # Add text
        self.text_item = QGraphicsTextItem(self.node_data.get("name", "Node"), self)
        self.text_item.setPos(10, 10)
        self.text_item.setDefaultTextColor(QColor("white"))

        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self.text_item.setFont(font)

        # Add type label
        self.type_item = QGraphicsTextItem(self.node_type.upper(), self)
        self.type_item.setPos(10, 50)
        self.type_item.setDefaultTextColor(QColor("white"))

        type_font = QFont()
        type_font.setPointSize(7)
        self.type_item.setFont(type_font)

    def _setup_interactions(self) -> None:
        """Set up node interactions."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Set cursor
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def get_connection_points(self) -> Tuple[QPointF, QPointF]:
        """Get input and output connection points."""
        rect = self.rect()
        center_y = rect.height() / 2

        input_point = QPointF(0, center_y)
        output_point = QPointF(rect.width(), center_y)

        return (self.mapToScene(input_point), self.mapToScene(output_point))

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """Handle item changes (like position changes)."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Update connections when node moves
            scene = self.scene()
            if scene and hasattr(scene, "update_connections"):
                scene.update_connections(self)

        return super().itemChange(change, value)


class WorkflowConnection(QGraphicsLineItem):
    """Represents a connection between two workflow nodes."""

    def __init__(
        self,
        start_node: WorkflowNode,
        end_node: WorkflowNode,
        parent: Optional[QGraphicsItem] = None,
    ) -> None:
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node

        # Set line appearance
        pen = QPen(QColor("#666666"), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)

        self.update_position()

    def update_position(self) -> None:
        """Update connection line position based on node positions."""
        if self.start_node and self.end_node:
            start_point, _ = self.start_node.get_connection_points()
            _, end_point = self.end_node.get_connection_points()

            self.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())


class WorkflowScene(QGraphicsScene):
    """Custom graphics scene for workflow design."""

    node_selected = Signal(WorkflowNode)
    connection_created = Signal(WorkflowNode, WorkflowNode)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.nodes: list[WorkflowNode] = []
        self.connections: list[WorkflowConnection] = []
        self.connection_mode = False
        self.temp_connection: Optional[QGraphicsLineItem] = None
        self.start_node: Optional[WorkflowNode] = None

        # Set scene properties
        self.setSceneRect(0, 0, 2000, 1500)
        self.setBackgroundBrush(QBrush(QColor("#F5F5F5")))

    def add_node(
        self, node_type: str, node_data: Dict[str, Any], position: QPointF
    ) -> WorkflowNode:
        """Add a new node to the scene."""
        node = WorkflowNode(node_type, node_data)
        node.setPos(position)

        self.addItem(node)
        self.nodes.append(node)

        return node

    def add_connection(
        self, start_node: WorkflowNode, end_node: WorkflowNode
    ) -> Optional[WorkflowConnection]:
        """Add a connection between two nodes."""
        if start_node == end_node or self._connection_exists(start_node, end_node):
            return None

        connection = WorkflowConnection(start_node, end_node)
        self.addItem(connection)
        self.connections.append(connection)

        # Update node connections
        start_node.connections.append(connection)

        self.connection_created.emit(start_node, end_node)
        return connection

    def _connection_exists(
        self, start_node: WorkflowNode, end_node: WorkflowNode
    ) -> bool:
        """Check if a connection already exists between two nodes."""
        for connection in self.connections:
            if connection.start_node == start_node and connection.end_node == end_node:
                return True
        return False

    def update_connections(self, node: WorkflowNode) -> None:
        """Update all connections related to a node."""
        for connection in self.connections:
            if connection.start_node == node or connection.end_node == node:
                connection.update_position()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse press events."""
        if self.connection_mode:
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, WorkflowNode):
                self.start_node = item
                # Start drawing temporary connection
                self.temp_connection = QGraphicsLineItem()
                pen = QPen(QColor("#FF5722"), 2)
                pen.setStyle(Qt.PenStyle.DotLine)
                self.temp_connection.setPen(pen)
                self.addItem(self.temp_connection)

                start_point, _ = item.get_connection_points()
                self.temp_connection.setLine(
                    start_point.x(), start_point.y(), start_point.x(), start_point.y()
                )

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse move events."""
        if self.connection_mode and self.temp_connection and self.start_node:
            start_point, _ = self.start_node.get_connection_points()
            self.temp_connection.setLine(
                start_point.x(),
                start_point.y(),
                event.scenePos().x(),
                event.scenePos().y(),
            )

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse release events."""
        if self.connection_mode and self.temp_connection and self.start_node:
            # Check if we're over a valid end node
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, WorkflowNode) and item != self.start_node:
                self.add_connection(self.start_node, item)

            # Clean up temporary connection
            self.removeItem(self.temp_connection)
            self.temp_connection = None
            self.start_node = None

        super().mouseReleaseEvent(event)


class WorkflowDesignerWidget(QWidget):
    """
    Advanced workflow designer widget.

    Features:
    - Drag-and-drop workflow creation
    - Visual node and connection editing
    - Workflow validation and testing
    - Export to LangGraph format
    - Template library
    - Real-time workflow preview
    """

    workflow_changed = Signal()
    workflow_saved = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.current_workflow = None
        self.workflow_templates = self._load_workflow_templates()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - toolbox and properties
        self._create_left_panel()
        splitter.addWidget(self.left_panel)

        # Center panel - workflow canvas
        self._create_center_panel()
        splitter.addWidget(self.center_panel)

        # Right panel - preview and validation
        self._create_right_panel()
        splitter.addWidget(self.right_panel)

        # Set initial splitter sizes
        splitter.setSizes([250, 800, 300])

    def _create_left_panel(self) -> None:
        """Create the left toolbox and properties panel."""
        self.left_panel = QWidget()
        layout = QVBoxLayout(self.left_panel)

        # Toolbox
        toolbox_group = QGroupBox("Node Toolbox")
        toolbox_layout = QVBoxLayout(toolbox_group)

        self.node_list = QListWidget()
        self.node_list.setDragDropMode(QListWidget.DragDropMode.DragOnly)

        # Add node types
        node_types = [
            ("Start Node", "start", "Workflow entry point"),
            ("Process Node", "process", "Data processing step"),
            ("Decision Node", "decision", "Conditional branching"),
            ("Service Node", "service", "External service call"),
            ("Data Node", "data", "Data transformation"),
            ("End Node", "end", "Workflow termination"),
        ]

        for name, node_type, description in node_types:
            item = QListWidgetItem(name)
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"type": node_type, "description": description},
            )
            item.setToolTip(description)
            self.node_list.addItem(item)

        toolbox_layout.addWidget(self.node_list)
        layout.addWidget(toolbox_group)

        # Node properties
        self.properties_group = QGroupBox("Properties")
        self.properties_layout = QFormLayout(self.properties_group)

        self.node_name_edit = QLineEdit()
        self.node_name_edit.setEnabled(False)
        self.properties_layout.addRow("Name:", self.node_name_edit)

        self.node_type_label = QLabel("No selection")
        self.properties_layout.addRow("Type:", self.node_type_label)

        self.node_description_edit = QTextEdit()
        self.node_description_edit.setMaximumHeight(80)
        self.node_description_edit.setEnabled(False)
        self.properties_layout.addRow("Description:", self.node_description_edit)

        # Node-specific properties
        self.specific_properties_widget = QWidget()
        self.specific_properties_layout = QVBoxLayout(self.specific_properties_widget)
        self.properties_layout.addRow("", self.specific_properties_widget)

        self.update_properties_btn = QPushButton("Update Node")
        self.update_properties_btn.setEnabled(False)
        self.properties_layout.addRow("", self.update_properties_btn)

        layout.addWidget(self.properties_group)

        # Workflow templates
        templates_group = QGroupBox("Templates")
        templates_layout = QVBoxLayout(templates_group)

        self.template_combo = QComboBox()
        for template_name in self.workflow_templates.keys():
            self.template_combo.addItem(template_name)
        templates_layout.addWidget(self.template_combo)

        template_buttons = QHBoxLayout()

        self.load_template_btn = QPushButton("Load")
        template_buttons.addWidget(self.load_template_btn)

        self.save_template_btn = QPushButton("Save")
        template_buttons.addWidget(self.save_template_btn)

        templates_layout.addLayout(template_buttons)
        layout.addWidget(templates_group)

        layout.addStretch()

    def _create_center_panel(self) -> None:
        """Create the center workflow canvas panel."""
        self.center_panel = QWidget()
        layout = QVBoxLayout(self.center_panel)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.new_workflow_btn = QPushButton("New")
        self.new_workflow_btn.setToolTip("Create new workflow")
        toolbar_layout.addWidget(self.new_workflow_btn)

        self.open_workflow_btn = QPushButton("Open")
        self.open_workflow_btn.setToolTip("Open existing workflow")
        toolbar_layout.addWidget(self.open_workflow_btn)

        self.save_workflow_btn = QPushButton("Save")
        self.save_workflow_btn.setToolTip("Save workflow")
        toolbar_layout.addWidget(self.save_workflow_btn)

        toolbar_layout.addWidget(QLabel("|"))  # Separator

        self.connection_mode_btn = QPushButton("Connect")
        self.connection_mode_btn.setCheckable(True)
        self.connection_mode_btn.setToolTip("Enable connection mode")
        toolbar_layout.addWidget(self.connection_mode_btn)

        self.delete_selected_btn = QPushButton("Delete")
        self.delete_selected_btn.setToolTip("Delete selected items")
        toolbar_layout.addWidget(self.delete_selected_btn)

        toolbar_layout.addWidget(QLabel("|"))  # Separator

        self.zoom_in_btn = QPushButton("Zoom In")
        toolbar_layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("Zoom Out")
        toolbar_layout.addWidget(self.zoom_out_btn)

        self.fit_view_btn = QPushButton("Fit View")
        toolbar_layout.addWidget(self.fit_view_btn)

        toolbar_layout.addStretch()

        self.workflow_name_edit = QLineEdit()
        self.workflow_name_edit.setPlaceholderText("Workflow name")
        self.workflow_name_edit.setMaximumWidth(200)
        toolbar_layout.addWidget(self.workflow_name_edit)

        layout.addLayout(toolbar_layout)

        # Workflow canvas
        self.workflow_scene = WorkflowScene()
        self.workflow_view = QGraphicsView(self.workflow_scene)
        self.workflow_view.setAcceptDrops(True)
        self.workflow_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        layout.addWidget(self.workflow_view)

    def _create_right_panel(self) -> None:
        """Create the right preview and validation panel."""
        self.right_panel = QTabWidget()

        # Workflow overview tab
        self._create_overview_tab()

        # Validation tab
        self._create_validation_tab()

        # Export tab
        self._create_export_tab()

    def _create_overview_tab(self) -> None:
        """Create workflow overview tab."""
        overview_tab = QWidget()
        layout = QVBoxLayout(overview_tab)

        # Workflow statistics
        stats_group = QGroupBox("Workflow Statistics")
        stats_layout = QFormLayout(stats_group)

        self.node_count_label = QLabel("0")
        stats_layout.addRow("Nodes:", self.node_count_label)

        self.connection_count_label = QLabel("0")
        stats_layout.addRow("Connections:", self.connection_count_label)

        self.complexity_label = QLabel("Simple")
        stats_layout.addRow("Complexity:", self.complexity_label)

        layout.addWidget(stats_group)

        # Node list
        nodes_group = QGroupBox("Workflow Nodes")
        nodes_layout = QVBoxLayout(nodes_group)

        self.workflow_nodes_tree = QTreeWidget()
        self.workflow_nodes_tree.setHeaderLabels(["Node", "Type", "Connections"])
        nodes_layout.addWidget(self.workflow_nodes_tree)

        layout.addWidget(nodes_group)

        # Execution flow
        flow_group = QGroupBox("Execution Flow")
        flow_layout = QVBoxLayout(flow_group)

        self.execution_flow_text = QTextEdit()
        self.execution_flow_text.setMaximumHeight(120)
        self.execution_flow_text.setReadOnly(True)
        flow_layout.addWidget(self.execution_flow_text)

        self.trace_flow_btn = QPushButton("Trace Execution")
        flow_layout.addWidget(self.trace_flow_btn)

        layout.addWidget(flow_group)

        layout.addStretch()
        self.right_panel.addTab(overview_tab, "Overview")

    def _create_validation_tab(self) -> None:
        """Create workflow validation tab."""
        validation_tab = QWidget()
        layout = QVBoxLayout(validation_tab)

        # Validation controls
        controls_layout = QHBoxLayout()

        self.validate_btn = QPushButton("Validate Workflow")
        self.validate_btn.setToolTip("Check workflow for errors")
        controls_layout.addWidget(self.validate_btn)

        self.test_btn = QPushButton("Test Run")
        self.test_btn.setToolTip("Run workflow with test data")
        controls_layout.addWidget(self.test_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Validation results
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout(results_group)

        self.validation_results_text = QTextEdit()
        self.validation_results_text.setReadOnly(True)
        self.validation_results_text.setPlaceholderText("Run validation to see results")
        results_layout.addWidget(self.validation_results_text)

        layout.addWidget(results_group)

        # Test configuration
        test_group = QGroupBox("Test Configuration")
        test_layout = QFormLayout(test_group)

        self.test_data_edit = QTextEdit()
        self.test_data_edit.setPlaceholderText("Enter test data (JSON format)")
        self.test_data_edit.setMaximumHeight(100)
        test_layout.addRow("Test Data:", self.test_data_edit)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        test_layout.addRow("Timeout:", self.timeout_spin)

        layout.addWidget(test_group)

        self.right_panel.addTab(validation_tab, "Validation")

    def _create_export_tab(self) -> None:
        """Create workflow export tab."""
        export_tab = QWidget()
        layout = QVBoxLayout(export_tab)

        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout(options_group)

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(
            [
                "LangGraph Python",
                "JSON Configuration",
                "YAML Configuration",
                "Visual Diagram",
            ]
        )
        options_layout.addRow("Format:", self.export_format_combo)

        self.include_comments_checkbox = QCheckBox("Include comments")
        self.include_comments_checkbox.setChecked(True)
        options_layout.addRow("", self.include_comments_checkbox)

        self.include_validation_checkbox = QCheckBox("Include validation")
        options_layout.addRow("", self.include_validation_checkbox)

        layout.addWidget(options_group)

        # Export preview
        preview_group = QGroupBox("Export Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.export_preview_text = QTextEdit()
        self.export_preview_text.setReadOnly(True)
        self.export_preview_text.setFont(QFont("monospace"))
        preview_layout.addWidget(self.export_preview_text)

        layout.addWidget(preview_group)

        # Export actions
        actions_layout = QHBoxLayout()

        self.preview_export_btn = QPushButton("Preview Export")
        actions_layout.addWidget(self.preview_export_btn)

        self.export_btn = QPushButton("Export to File")
        actions_layout.addWidget(self.export_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        self.right_panel.addTab(export_tab, "Export")

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        # Left panel
        self.node_list.itemPressed.connect(self._start_node_drag)
        self.update_properties_btn.clicked.connect(self._update_node_properties)
        self.load_template_btn.clicked.connect(self._load_template)
        self.save_template_btn.clicked.connect(self._save_template)

        # Center panel
        self.new_workflow_btn.clicked.connect(self._new_workflow)
        self.open_workflow_btn.clicked.connect(self._open_workflow)
        self.save_workflow_btn.clicked.connect(self._save_workflow)
        self.connection_mode_btn.toggled.connect(self._toggle_connection_mode)
        self.delete_selected_btn.clicked.connect(self._delete_selected)
        self.zoom_in_btn.clicked.connect(lambda: self.workflow_view.scale(1.2, 1.2))
        self.zoom_out_btn.clicked.connect(lambda: self.workflow_view.scale(0.8, 0.8))
        self.fit_view_btn.clicked.connect(self._fit_view)

        # Scene signals
        self.workflow_scene.node_selected.connect(self._on_node_selected)
        self.workflow_scene.connection_created.connect(self._on_connection_created)

        # Right panel
        self.validate_btn.clicked.connect(self._validate_workflow)
        self.test_btn.clicked.connect(self._test_workflow)
        self.trace_flow_btn.clicked.connect(self._trace_execution_flow)
        self.preview_export_btn.clicked.connect(self._preview_export)
        self.export_btn.clicked.connect(self._export_workflow)

    def _load_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load workflow templates."""
        return {
            "Simple Processing": {
                "description": "Basic linear processing workflow",
                "nodes": [
                    {"type": "start", "name": "Start", "position": [100, 100]},
                    {"type": "process", "name": "Process", "position": [300, 100]},
                    {"type": "end", "name": "End", "position": [500, 100]},
                ],
                "connections": [{"from": 0, "to": 1}, {"from": 1, "to": 2}],
            },
            "Conditional Flow": {
                "description": "Workflow with conditional branching",
                "nodes": [
                    {"type": "start", "name": "Start", "position": [100, 150]},
                    {"type": "process", "name": "Check Data", "position": [300, 150]},
                    {"type": "decision", "name": "Valid?", "position": [500, 150]},
                    {
                        "type": "process",
                        "name": "Process Valid",
                        "position": [700, 100],
                    },
                    {"type": "process", "name": "Handle Error", "position": [700, 200]},
                    {"type": "end", "name": "End", "position": [900, 150]},
                ],
                "connections": [
                    {"from": 0, "to": 1},
                    {"from": 1, "to": 2},
                    {"from": 2, "to": 3},
                    {"from": 2, "to": 4},
                    {"from": 3, "to": 5},
                    {"from": 4, "to": 5},
                ],
            },
        }

    def _start_node_drag(self, item: QListWidgetItem) -> None:
        """Start dragging a node from the toolbox."""
        # This would normally implement drag start logic
        pass

    def _update_node_properties(self) -> None:
        """Update properties of the selected node."""
        QMessageBox.information(
            self, "Update", "Node properties would be updated here."
        )

    def _load_template(self) -> None:
        """Load the selected workflow template."""
        template_name = self.template_combo.currentText()
        template = self.workflow_templates.get(template_name)

        if template:
            self._clear_workflow()

            # Add nodes
            nodes = []
            for i, node_data in enumerate(template["nodes"]):
                position = QPointF(node_data["position"][0], node_data["position"][1])
                node = self.workflow_scene.add_node(
                    node_data["type"], {"name": node_data["name"], "id": i}, position
                )
                nodes.append(node)

            # Add connections
            for connection in template["connections"]:
                from_node = nodes[connection["from"]]
                to_node = nodes[connection["to"]]
                self.workflow_scene.add_connection(from_node, to_node)

            self.workflow_name_edit.setText(template_name)
            self._update_overview()

    def _save_template(self) -> None:
        """Save current workflow as a template."""
        QMessageBox.information(
            self, "Save Template", "Template saving would be implemented here."
        )

    def _new_workflow(self) -> None:
        """Create a new workflow."""
        self._clear_workflow()
        self.workflow_name_edit.setText("New Workflow")
        self._update_overview()

    def _open_workflow(self) -> None:
        """Open an existing workflow."""
        QMessageBox.information(
            self, "Open Workflow", "Workflow opening would be implemented here."
        )

    def _save_workflow(self) -> None:
        """Save the current workflow."""
        workflow_data = self._serialize_workflow()
        self.workflow_saved.emit(workflow_data)
        QMessageBox.information(
            self, "Saved", f"Workflow '{workflow_data['name']}' saved successfully."
        )

    def _toggle_connection_mode(self, enabled: bool) -> None:
        """Toggle connection mode on/off."""
        self.workflow_scene.connection_mode = enabled

        if enabled:
            self.workflow_view.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            self.connection_mode_btn.setText("Connecting...")
            self.connection_mode_btn.setStyleSheet("background-color: #FF5722;")
        else:
            self.workflow_view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.connection_mode_btn.setText("Connect")
            self.connection_mode_btn.setStyleSheet("")

    def _delete_selected(self) -> None:
        """Delete selected items from the workflow."""
        selected_items = self.workflow_scene.selectedItems()

        for item in selected_items:
            if isinstance(item, WorkflowNode):
                # Remove connections involving this node
                connections_to_remove = [
                    conn
                    for conn in self.workflow_scene.connections
                    if conn.start_node == item or conn.end_node == item
                ]

                for conn in connections_to_remove:
                    self.workflow_scene.removeItem(conn)
                    self.workflow_scene.connections.remove(conn)

                # Remove node
                self.workflow_scene.removeItem(item)
                self.workflow_scene.nodes.remove(item)

            elif isinstance(item, WorkflowConnection):
                # Remove connection
                self.workflow_scene.removeItem(item)
                self.workflow_scene.connections.remove(item)

                # Update node connections
                if item.start_node and item in item.start_node.connections:
                    item.start_node.connections.remove(item)

        self._update_overview()

    def _fit_view(self) -> None:
        """Fit the workflow view to show all items."""
        self.workflow_view.fitInView(
            self.workflow_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio
        )

    def _on_node_selected(self, node: WorkflowNode) -> None:
        """Handle node selection."""
        self.node_name_edit.setText(node.node_data.get("name", ""))
        self.node_type_label.setText(node.node_type.upper())
        self.node_description_edit.setPlainText(node.node_data.get("description", ""))

        # Enable properties editing
        self.node_name_edit.setEnabled(True)
        self.node_description_edit.setEnabled(True)
        self.update_properties_btn.setEnabled(True)

    def _on_connection_created(
        self, start_node: WorkflowNode, end_node: WorkflowNode
    ) -> None:
        """Handle connection creation."""
        self._update_overview()
        self.workflow_changed.emit()

    def _clear_workflow(self) -> None:
        """Clear the current workflow."""
        self.workflow_scene.clear()
        self.workflow_scene.nodes.clear()
        self.workflow_scene.connections.clear()

        # Reset properties
        self.node_name_edit.clear()
        self.node_name_edit.setEnabled(False)
        self.node_type_label.setText("No selection")
        self.node_description_edit.clear()
        self.node_description_edit.setEnabled(False)
        self.update_properties_btn.setEnabled(False)

        self._update_overview()

    def _update_overview(self) -> None:
        """Update the workflow overview display."""
        # Update statistics
        node_count = len(self.workflow_scene.nodes)
        connection_count = len(self.workflow_scene.connections)

        self.node_count_label.setText(str(node_count))
        self.connection_count_label.setText(str(connection_count))

        # Determine complexity
        if node_count <= 3:
            complexity = "Simple"
        elif node_count <= 10:
            complexity = "Moderate"
        else:
            complexity = "Complex"

        self.complexity_label.setText(complexity)

        # Update nodes tree
        self.workflow_nodes_tree.clear()

        for node in self.workflow_scene.nodes:
            item = QTreeWidgetItem(
                [
                    node.node_data.get("name", "Unnamed"),
                    node.node_type.upper(),
                    str(len(node.connections)),
                ]
            )
            self.workflow_nodes_tree.addTopLevelItem(item)

    def _validate_workflow(self) -> None:
        """Validate the current workflow."""
        issues = []

        # Check for start node
        start_nodes = [
            node for node in self.workflow_scene.nodes if node.node_type == "start"
        ]
        if not start_nodes:
            issues.append("⚠ No start node found")
        elif len(start_nodes) > 1:
            issues.append("⚠ Multiple start nodes found")

        # Check for end node
        end_nodes = [
            node for node in self.workflow_scene.nodes if node.node_type == "end"
        ]
        if not end_nodes:
            issues.append("⚠ No end node found")

        # Check for isolated nodes
        for node in self.workflow_scene.nodes:
            has_incoming = any(
                conn.end_node == node for conn in self.workflow_scene.connections
            )
            has_outgoing = len(node.connections) > 0

            if not has_incoming and node.node_type != "start":
                issues.append(
                    f"⚠ Node '{node.node_data.get('name', 'Unnamed')}' has no "
                    f"incoming connections"
                )

            if not has_outgoing and node.node_type != "end":
                issues.append(
                    f"⚠ Node '{node.node_data.get('name', 'Unnamed')}' has no "
                    f"outgoing connections"
                )

        # Display results
        if issues:
            result = "Validation Issues Found:\n\n" + "\n".join(issues)
        else:
            result = "✅ Workflow validation passed!\n\nNo issues found."

        self.validation_results_text.setPlainText(result)

    def _test_workflow(self) -> None:
        """Run a test of the workflow."""
        self.validation_results_text.setPlainText(
            "🧪 Test Run Results:\n\n"
            "✅ Workflow executed successfully\n"
            "⏱ Execution time: 1.2 seconds\n"
            "📊 Processed 5 test items\n"
            "✅ All nodes completed without errors\n\n"
            "Note: This is a mock test run. Real implementation would\n"
            "execute the workflow with test data."
        )

    def _trace_execution_flow(self) -> None:
        """Trace the execution flow of the workflow."""
        flow_steps = []

        # Find start node
        start_nodes = [
            node for node in self.workflow_scene.nodes if node.node_type == "start"
        ]

        if start_nodes:
            current_node = start_nodes[0]
            visited = set()
            step = 1

            while current_node and current_node not in visited:
                visited.add(current_node)
                flow_steps.append(
                    f"{step}. {current_node.node_data.get('name', 'Unnamed')} "
                    f"({current_node.node_type})"
                )

                # Find next node
                if current_node.connections:
                    next_connection = current_node.connections[0]
                    current_node = next_connection.end_node
                    step += 1
                else:
                    break

        if flow_steps:
            self.execution_flow_text.setPlainText("\n".join(flow_steps))
        else:
            self.execution_flow_text.setPlainText(
                "No execution flow found. Add nodes and connections to trace the flow."
            )

    def _preview_export(self) -> None:
        """Preview the workflow export."""
        export_format = self.export_format_combo.currentText()

        if export_format == "LangGraph Python":
            preview = self._generate_langgraph_code()
        elif export_format == "JSON Configuration":
            import json

            preview = json.dumps(self._serialize_workflow(), indent=2)
        else:
            preview = f"Export preview for {export_format} format would appear here."

        self.export_preview_text.setPlainText(preview)

    def _export_workflow(self) -> None:
        """Export the workflow to a file."""
        QMessageBox.information(
            self, "Export", "Workflow export would be implemented here."
        )

    def _serialize_workflow(self) -> Dict[str, Any]:
        """Serialize the current workflow to a dictionary."""
        nodes_data = []
        for i, node in enumerate(self.workflow_scene.nodes):
            nodes_data.append(
                {
                    "id": i,
                    "type": node.node_type,
                    "name": node.node_data.get("name", ""),
                    "position": [node.pos().x(), node.pos().y()],
                    "properties": node.node_data,
                }
            )

        connections_data = []
        for connection in self.workflow_scene.connections:
            start_idx = self.workflow_scene.nodes.index(connection.start_node)
            end_idx = self.workflow_scene.nodes.index(connection.end_node)
            connections_data.append({"from": start_idx, "to": end_idx})

        return {
            "name": self.workflow_name_edit.text() or "Untitled Workflow",
            "description": "",
            "nodes": nodes_data,
            "connections": connections_data,
            "created_at": "2024-01-01T00:00:00Z",
            "version": "1.0",
        }

    def _generate_langgraph_code(self) -> str:
        """Generate LangGraph Python code for the workflow."""
        code = '''"""
Generated LangGraph workflow.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict

class WorkflowState(TypedDict):
    """State for the workflow."""
    data: Any
    status: str
    result: Any

def create_workflow():
    """Create and return the LangGraph workflow."""
    workflow = StateGraph(WorkflowState)
'''

        # Add nodes
        for node in self.workflow_scene.nodes:
            node_name = node.node_data.get("name", "node").lower().replace(" ", "_")
            if node.node_type == "start":
                code += f'    workflow.set_entry_point("{node_name}")\n'

            code += f'    workflow.add_node("{node_name}", {node_name}_handler)\n'

        code += """
    return workflow.compile()

"""

        # Add handler functions
        for node in self.workflow_scene.nodes:
            node_name = node.node_data.get("name", "node").lower().replace(" ", "_")
            code += f'''def {node_name}_handler(state: WorkflowState) -> WorkflowState:
    """Handle {node.node_data.get("name", "node")} processing."""
    # TODO: Implement {node.node_type} logic
    return state

'''

        return code
