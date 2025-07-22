"""
Dashboard view for the RS Personal Agent application.

This module provides the main dashboard interface with agent management,
system status indicators, and professional Qt styling.
"""

from typing import Optional

from PySide6.QtCore import QModelIndex, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..models.agent_table_model import (
    AgentTableModel,
    ServiceStatus,
)
from ..widgets.status_indicator_widget import StatusIndicatorWidget


class DashboardView(QWidget):
    """
    Main dashboard view for the RS Personal Agent application.

    This widget provides a comprehensive dashboard with agent management,
    system status monitoring, and professional Qt styling.
    """

    # Signals
    agent_action_requested = Signal(str, str)  # agent_name, action
    refresh_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the dashboard view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._setup_connections()
        self._setup_refresh_timer()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header section
        header_widget = self._create_header_section()
        main_layout.addWidget(header_widget)

        # System status section
        status_widget = self._create_status_section()
        main_layout.addWidget(status_widget)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Agent management section
        agent_widget = self._create_agent_section()
        splitter.addWidget(agent_widget)

        # Set splitter proportions
        splitter.setStretchFactor(0, 1)

        main_layout.addWidget(splitter)

        # Apply styling
        self._apply_styling()

    def _create_header_section(self) -> QWidget:
        """
        Create the header section with title and controls.

        Returns:
            Header widget
        """
        header_widget = QFrame()
        header_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        header_widget.setObjectName("headerFrame")

        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(20, 15, 20, 15)

        # Title and subtitle
        title_layout = QVBoxLayout()

        title_label = QLabel("RS Personal Agent Dashboard")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Monitor and manage your AI agents")
        subtitle_label.setObjectName("subtitleLabel")
        title_layout.addWidget(subtitle_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Control buttons
        self._refresh_button = QPushButton("🔄 Refresh")
        self._refresh_button.setObjectName("refreshButton")
        self._refresh_button.setToolTip("Refresh dashboard data")
        layout.addWidget(self._refresh_button)

        self._settings_button = QPushButton("⚙️ Settings")
        self._settings_button.setObjectName("settingsButton")
        self._settings_button.setToolTip("Open application settings")
        layout.addWidget(self._settings_button)

        return header_widget

    def _create_status_section(self) -> QWidget:
        """
        Create the system status section.

        Returns:
            Status widget
        """
        status_group = QGroupBox("System Status")
        status_group.setObjectName("statusGroup")

        layout = QHBoxLayout(status_group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(30)

        # Create status indicators
        self._ollama_status = StatusIndicatorWidget(
            "Ollama", ServiceStatus.DISCONNECTED
        )
        self._gmail_status = StatusIndicatorWidget(
            "Gmail",
            ServiceStatus.DISCONNECTED,
        )
        self._database_status = StatusIndicatorWidget(
            "Database", ServiceStatus.CONNECTED
        )

        layout.addWidget(self._ollama_status)
        layout.addWidget(self._gmail_status)
        layout.addWidget(self._database_status)
        layout.addStretch()

        # System info
        info_layout = QVBoxLayout()

        self._agent_count_label = QLabel("Agents: 5")
        self._agent_count_label.setObjectName("infoLabel")
        info_layout.addWidget(self._agent_count_label)

        self._running_count_label = QLabel("Running: 2")
        self._running_count_label.setObjectName("infoLabel")
        info_layout.addWidget(self._running_count_label)

        layout.addLayout(info_layout)

        return status_group

    def _create_agent_section(self) -> QWidget:
        """
        Create the agent management section.

        Returns:
            Agent widget
        """
        agent_group = QGroupBox("Agent Management")
        agent_group.setObjectName("agentGroup")

        layout = QVBoxLayout(agent_group)
        layout.setContentsMargins(15, 15, 15, 15)

        # Agent table
        self._agent_model = AgentTableModel()
        self._agent_table = QTableView()
        self._agent_table.setModel(self._agent_model)

        # Configure table
        self._setup_agent_table()

        layout.addWidget(self._agent_table)

        return agent_group

    def _setup_agent_table(self) -> None:
        """Set up the agent table view."""
        # Table properties
        table = self._agent_table
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setSortingEnabled(True)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Header configuration
        header = self._agent_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)

        # Column widths
        header.resizeSection(0, 200)  # Name
        header.resizeSection(1, 150)  # Type
        header.resizeSection(2, 120)  # Status
        header.resizeSection(3, 100)  # Last Run
        header.resizeSection(4, 80)  # Tasks
        header.resizeSection(5, 100)  # Success Rate

        # Row height
        self._agent_table.verticalHeader().setDefaultSectionSize(35)
        self._agent_table.verticalHeader().hide()

        # Context menu
        table = self._agent_table
        table.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Button connections
        self._refresh_button.clicked.connect(self._handle_refresh)
        self._settings_button.clicked.connect(self._handle_settings)

        # Model connections
        self._agent_model.agent_status_changed.connect(
            self._handle_agent_status_changed
        )
        model = self._agent_model
        model.refresh_requested.connect(self._update_system_info)

        # Table connections
        table = self._agent_table
        table.doubleClicked.connect(self._handle_agent_double_click)

        # Status indicator connections
        ollama = self._ollama_status
        ollama.status_changed.connect(self._handle_status_change)
        gmail = self._gmail_status
        gmail.status_changed.connect(self._handle_status_change)
        database = self._database_status
        database.status_changed.connect(self._handle_status_change)

    def _setup_refresh_timer(self) -> None:
        """Set up automatic refresh timer."""
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(30000)  # Refresh every 30 seconds

    def _show_context_menu(self, position: QPoint) -> None:
        """
        Show context menu for agent actions.

        Args:
            position: Menu position
        """
        index = self._agent_table.indexAt(position)
        if not index.isValid():
            return

        agent = self._agent_model.get_agent_at_row(index.row())
        if not agent:
            return

        menu = QMenu(self)

        # Agent actions based on current status
        if agent.status == ServiceStatus.RUNNING:
            stop_action = QAction("⏹️ Stop Agent", self)
            stop_action.triggered.connect(
                lambda: self._handle_agent_action(agent.name, "stop")
            )
            menu.addAction(stop_action)

            pause_action = QAction("⏸️ Pause Agent", self)
            pause_action.triggered.connect(
                lambda: self._handle_agent_action(agent.name, "pause")
            )
            menu.addAction(pause_action)

        elif agent.status in [
            ServiceStatus.IDLE,
            ServiceStatus.ERROR,
            ServiceStatus.DISABLED,
        ]:
            start_action = QAction("▶️ Start Agent", self)
            start_action.triggered.connect(
                lambda: self._handle_agent_action(agent.name, "start")
            )
            menu.addAction(start_action)

        menu.addSeparator()

        # Common actions
        configure_action = QAction("⚙️ Configure Agent", self)
        configure_action.triggered.connect(
            lambda: self._handle_agent_action(agent.name, "configure")
        )
        menu.addAction(configure_action)

        view_logs_action = QAction("📄 View Logs", self)
        view_logs_action.triggered.connect(
            lambda: self._handle_agent_action(agent.name, "view_logs")
        )
        menu.addAction(view_logs_action)

        menu.addSeparator()

        restart_action = QAction("🔄 Restart Agent", self)
        restart_action.triggered.connect(
            lambda: self._handle_agent_action(agent.name, "restart")
        )
        menu.addAction(restart_action)

        # Show menu
        menu.exec(self._agent_table.mapToGlobal(position))

    def _handle_refresh(self) -> None:
        """Handle refresh button click."""
        self._agent_model.refresh_data()
        self._update_system_info()
        self._simulate_status_checks()
        self.refresh_requested.emit()

        # Show feedback
        self._refresh_button.setText("🔄 Refreshing...")

        def reset_button_text() -> None:
            self._refresh_button.setText("🔄 Refresh")

        QTimer.singleShot(1000, reset_button_text)

    def _handle_settings(self) -> None:
        """Handle settings button click."""
        self.settings_requested.emit()

    def _handle_agent_status_changed(
        self, agent_name: str, new_status: ServiceStatus
    ) -> None:
        """
        Handle agent status change.

        Args:
            agent_name: Name of the agent
            new_status: New status
        """
        self._update_system_info()

        # Show status message
        status_text = {
            ServiceStatus.RUNNING: "started",
            ServiceStatus.IDLE: "stopped",
            ServiceStatus.ERROR: "encountered an error",
            ServiceStatus.DISABLED: "disabled",
        }.get(new_status, "status changed")

        print(f"Agent '{agent_name}' {status_text}")

    def _handle_agent_double_click(self, index: QModelIndex) -> None:
        """
        Handle agent table double-click.

        Args:
            index: Clicked index
        """
        agent = self._agent_model.get_agent_at_row(index.row())
        if agent:
            self._handle_agent_action(agent.name, "configure")

    def _handle_agent_action(self, agent_name: str, action: str) -> None:
        """
        Handle agent action request.

        Args:
            agent_name: Name of the agent
            action: Action to perform
        """
        # Emit signal for external handling
        self.agent_action_requested.emit(agent_name, action)

        # Simulate action feedback
        action_text = {
            "start": "Starting",
            "stop": "Stopping",
            "pause": "Pausing",
            "restart": "Restarting",
            "configure": "Opening configuration for",
            "view_logs": "Opening logs for",
        }.get(action, "Processing")

        # Show message box for demonstration
        QMessageBox.information(
            self,
            "Agent Action",
            f"{action_text} agent '{agent_name}'...\n\n"
            f"This is a mock action for demonstration purposes.",
        )

        # Simulate status changes for some actions
        if action == "start":
            self._simulate_agent_start(agent_name)
        elif action in ["stop", "pause"]:
            self._simulate_agent_stop(agent_name)

    def _simulate_agent_start(self, agent_name: str) -> None:
        """
        Simulate starting an agent.

        Args:
            agent_name: Name of the agent to start
        """
        for row in range(self._agent_model.rowCount()):
            agent = self._agent_model.get_agent_at_row(row)
            if agent and agent.name == agent_name:
                model = self._agent_model
                model.update_agent_status(row, ServiceStatus.RUNNING)
                break

    def _simulate_agent_stop(self, agent_name: str) -> None:
        """
        Simulate stopping an agent.

        Args:
            agent_name: Name of the agent to stop
        """
        for row in range(self._agent_model.rowCount()):
            agent = self._agent_model.get_agent_at_row(row)
            if agent and agent.name == agent_name:
                self._agent_model.update_agent_status(row, ServiceStatus.IDLE)
                break

    def _handle_status_change(
        self, service_name: str, new_status: ServiceStatus
    ) -> None:
        """
        Handle system status change.

        Args:
            service_name: Name of the service
            new_status: New status
        """
        print(f"Service '{service_name}' status changed to {new_status.value}")

    def _auto_refresh(self) -> None:
        """Perform automatic refresh."""
        self._update_system_info()
        self._simulate_status_checks()

    def _update_system_info(self) -> None:
        """Update system information display."""
        # Count agents by status
        total_agents = self._agent_model.rowCount()
        running_count = 0

        for row in range(total_agents):
            agent = self._agent_model.get_agent_at_row(row)
            if agent and agent.status == ServiceStatus.RUNNING:
                running_count += 1

        self._agent_count_label.setText(f"Agents: {total_agents}")
        self._running_count_label.setText(f"Running: {running_count}")

    def _simulate_status_checks(self) -> None:
        """Simulate checking system status."""
        import random

        # Randomly update service statuses for demonstration
        services = [self._ollama_status, self._gmail_status]

        for service in services:
            if random.random() < 0.2:  # 20% chance of status change
                current_status = service.get_status()
                if current_status == ServiceStatus.CONNECTED:
                    service.set_status(ServiceStatus.DISCONNECTED)
                else:
                    service.set_status(ServiceStatus.CONNECTED)

    def _apply_styling(self) -> None:
        """Apply custom styling to the dashboard."""
        self.setStyleSheet(
            """
            /* Main dashboard styling */
            DashboardView {
                background-color: #f8fafc;
            }

            /* Header frame */
            #headerFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f1f5f9);
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }

            /* Title styling */
            #titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1e293b;
                margin: 0;
            }

            #subtitleLabel {
                font-size: 14px;
                color: #64748b;
                margin: 0;
            }

            /* Button styling */
            #refreshButton, #settingsButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 100px;
            }

            #refreshButton:hover, #settingsButton:hover {
                background-color: #2563eb;
            }

            #refreshButton:pressed, #settingsButton:pressed {
                background-color: #1d4ed8;
            }

            /* Group box styling */
            #statusGroup, #agentGroup {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            #statusGroup::title, #agentGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8fafc;
            }

            /* Info labels */
            #infoLabel {
                font-size: 14px;
                color: #4b5563;
                font-weight: 500;
            }

            /* Table styling */
            QTableView {
                gridline-color: #e5e7eb;
                background-color: white;
                alternate-background-color: #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                selection-background-color: #3b82f6;
            }

            QTableView::item {
                padding: 8px;
                border: none;
            }

            QTableView::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                color: #374151;
                border: none;
                border-right: 1px solid #d1d5db;
                border-bottom: 1px solid #d1d5db;
                padding: 8px;
                font-weight: bold;
            }
        """
        )

    def get_agent_model(self) -> AgentTableModel:
        """
        Get the agent table model.

        Returns:
            Agent table model
        """
        return self._agent_model

    def refresh_dashboard(self) -> None:
        """Refresh the entire dashboard."""
        self._handle_refresh()
