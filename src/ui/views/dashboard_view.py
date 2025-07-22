"""
Dashboard view for the RS Personal Agent application.

This module provides the main dashboard interface with agent management,
system status indicators, and professional Qt styling.
"""

from typing import Any, Dict, Optional

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

from ...core.gmail_service import GmailService
from ...core.llm_manager import OllamaManager
from ...core.performance_monitor import MetricReading, get_performance_monitor
from ..models.agent_table_model import (
    AgentTableModel,
    ServiceStatus,
)
from ..widgets.activity_timeline_widget import ActivityTimelineWidget, ActivityType
from ..widgets.connection_status_widget import ConnectionStatusWidget
from ..widgets.log_viewer_widget import LogViewerWidget
from ..widgets.metrics_panel_widget import MetricsPanelWidget
from ..widgets.system_tray_widget import SystemTrayWidget


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

        # Initialize services
        self._gmail_service = GmailService(self)
        self._ollama_manager = OllamaManager(parent=self)

        # Initialize system tray
        self._system_tray = SystemTrayWidget(self)

        self._setup_ui()
        self._setup_connections()
        self._setup_refresh_timer()

        # Start initial status checks
        self._check_service_status()

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

        # Main content with enhanced monitoring
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Agent management and metrics
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel: Activity timeline and logs
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter proportions (60% left, 40% right)
        main_splitter.setStretchFactor(0, 60)
        main_splitter.setStretchFactor(1, 40)

        main_layout.addWidget(main_splitter)

        # Apply styling
        self._apply_styling()

        # Setup monitoring
        self._setup_monitoring()

    def _create_left_panel(self) -> QWidget:
        """
        Create the left panel with agent management and system metrics.

        Returns:
            Left panel widget
        """
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Agent management section (top)
        agent_widget = self._create_agent_section()
        layout.addWidget(agent_widget, 2)  # Takes 2/3 of space

        # System metrics panel (bottom)
        self.metrics_panel = MetricsPanelWidget()
        layout.addWidget(self.metrics_panel, 1)  # Takes 1/3 of space

        return left_widget

    def _create_right_panel(self) -> QWidget:
        """
        Create the right panel with activity timeline and logs.

        Returns:
            Right panel widget
        """
        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create vertical splitter for activity and logs
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Activity timeline (top)
        self.activity_timeline = ActivityTimelineWidget()
        right_splitter.addWidget(self.activity_timeline)

        # Log viewer (bottom)
        self.log_viewer = LogViewerWidget()
        right_splitter.addWidget(self.log_viewer)

        # Set proportions (50/50)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)

        layout.addWidget(right_splitter)

        return right_widget

    def _setup_monitoring(self) -> None:
        """Setup monitoring connections and performance tracking."""
        # Get performance monitor
        self.performance_monitor = get_performance_monitor()

        # Connect signals
        self.performance_monitor.metric_updated.connect(self._on_metric_updated)
        self.performance_monitor.alert_triggered.connect(self._on_alert_triggered)
        self.activity_timeline.activity_selected.connect(self._on_activity_selected)

        # Start monitoring
        self.performance_monitor.start_monitoring()

        # Add initial system startup activities
        self.activity_timeline.add_activity(
            ActivityType.SYSTEM_EVENT, "Enhanced monitoring dashboard loaded"
        )

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

        # Create connection status indicators
        self._ollama_status = ConnectionStatusWidget("Ollama", "disconnected")
        self._gmail_status = ConnectionStatusWidget("Gmail", "disconnected")
        self._database_status = ConnectionStatusWidget("Database", "connected")

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

        # Service connections
        self._gmail_service.connection_status_changed.connect(self._update_gmail_status)
        self._gmail_service.error_occurred.connect(self._show_service_error)

        self._ollama_manager.connection_status_changed.connect(
            self._update_ollama_status
        )
        self._ollama_manager.error_occurred.connect(self._show_service_error)

        # Status widget connections
        self._ollama_status.status_changed.connect(
            self._handle_connection_status_change
        )
        self._gmail_status.status_changed.connect(self._handle_connection_status_change)
        self._database_status.status_changed.connect(
            self._handle_connection_status_change
        )

        # System tray connections
        self._system_tray.show_dashboard_requested.connect(self._bring_to_front)
        self._system_tray.settings_requested.connect(self._handle_settings)
        self._system_tray.quit_requested.connect(self._handle_quit_request)

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
        self._check_service_status()
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

    def _handle_connection_status_change(
        self, service_name: str, new_status: str
    ) -> None:
        """
        Handle connection status change.

        Args:
            service_name: Name of the service
            new_status: New status string
        """
        print(f"Service '{service_name}' status changed to {new_status}")

    def _auto_refresh(self) -> None:
        """Perform automatic refresh."""
        self._update_system_info()
        self._check_service_status()

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

    def _check_service_status(self) -> None:
        """Check real service connection status."""
        # Check Gmail status in a non-blocking way
        QTimer.singleShot(100, self._async_check_gmail_status)

        # Check Ollama status in a non-blocking way
        QTimer.singleShot(200, self._async_check_ollama_status)

    def _async_check_gmail_status(self) -> None:
        """Asynchronously check Gmail status."""
        if self._gmail_service.is_connected():
            self._gmail_status.set_status("connected")
        else:
            # Try to load existing credentials without triggering OAuth
            from pathlib import Path

            creds_path = Path.cwd() / "credentials.json"
            if creds_path.exists():
                self._gmail_service.set_credentials_file(str(creds_path))
                if self._gmail_service.get_connection_status() == "error":
                    self._gmail_status.set_status("error")
                else:
                    self._gmail_status.set_status("disconnected")
            else:
                self._gmail_status.set_status("disconnected")

    def _async_check_ollama_status(self) -> None:
        """Asynchronously check Ollama status."""
        # Test connection without blocking UI
        try:
            if self._ollama_manager.test_connection():
                self._ollama_status.set_status("connected")
            else:
                self._ollama_status.set_status("disconnected")
        except Exception:
            self._ollama_status.set_status("error")

    def _update_gmail_status(self, status: str) -> None:
        """Update Gmail status indicator."""
        self._gmail_status.set_status(status)

    def _update_ollama_status(self, status: str) -> None:
        """Update Ollama status indicator."""
        self._ollama_status.set_status(status)

    def _show_service_error(self, error_msg: str) -> None:
        """Show service error message."""
        print(f"Service error: {error_msg}")

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

    def get_gmail_service(self) -> GmailService:
        """Get the Gmail service instance."""
        return self._gmail_service

    def get_ollama_manager(self) -> OllamaManager:
        """Get the Ollama manager instance."""
        return self._ollama_manager

    def _on_metric_updated(self, reading: MetricReading) -> None:
        """Handle metric update from performance monitor."""
        # Update agent count display if this is an agent metric
        if reading.name == "active_agents":
            self.metrics_panel.update_agent_metrics(
                int(reading.value),
                self.metrics_panel.get_metrics_data()["success_rate"],
            )

        # Update performance metrics for LLM response times
        if reading.name == "llm_response_time":
            self.metrics_panel.update_performance_metrics(reading.value)

            # Add activity for LLM requests
            self.activity_timeline.add_activity(
                ActivityType.LLM_REQUEST, f"LLM responded in {reading.value:.2f}s"
            )

    def _on_alert_triggered(
        self, metric_name: str, alert_type: str, value: float
    ) -> None:
        """Handle performance alert."""
        alert_message = f"{metric_name} {alert_type}: {value:.1f}"

        # Add to activity timeline
        if alert_type == "critical":
            self.activity_timeline.add_activity(
                ActivityType.ERROR, f"Critical alert: {alert_message}"
            )
        else:
            self.activity_timeline.add_activity(
                ActivityType.WARNING, f"Warning alert: {alert_message}"
            )

        # Add to logs
        self.log_viewer.add_log_entry(
            alert_type.upper(),
            f"Performance alert triggered: {alert_message}",
            "PerformanceMonitor",
        )

        # Show system tray notification
        self._system_tray.show_alert_notification(alert_type, metric_name, value)

    def _on_activity_selected(self, activity: Dict[str, Any]) -> None:
        """Handle activity selection from timeline."""
        # Show details in logs when activity is selected
        details_text = f"Activity details: {activity.get('details', {})}"
        self.log_viewer.add_log_entry(
            "DEBUG",
            f"Selected activity: {activity['message']} | {details_text}",
            "ActivityTimeline",
        )

    def _bring_to_front(self) -> None:
        """Bring the dashboard window to front."""
        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_quit_request(self) -> None:
        """Handle quit request from system tray."""
        # This should be connected to the main application quit
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            app.quit()

    def show_system_tray(self) -> None:
        """Show the system tray icon."""
        if self._system_tray.is_available():
            self._system_tray.show()

            # Show initial notification
            self._system_tray.show_success_notification(
                "RS Personal Agent is running in the system tray"
            )
        else:
            print("System tray not available on this system")

    def hide_system_tray(self) -> None:
        """Hide the system tray icon."""
        self._system_tray.hide()

    def get_system_tray(self) -> SystemTrayWidget:
        """Get the system tray widget."""
        return self._system_tray
