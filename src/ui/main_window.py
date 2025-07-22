"""
Main window for RS Personal Agent desktop application.

This module contains the MainWindow class which serves as the primary
application window using PySide6's QMainWindow.
"""

from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QWidget,
)

from .views.dashboard_view import DashboardView


class MainWindow(QMainWindow):
    """
    Main application window for RS Personal Agent.

    This window provides the primary interface for the desktop application,
    including menu bar, status bar, and central widget area.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the main window.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        self._setup_window()
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        self._setup_shortcuts()
        self._setup_connections()

    def _setup_window(self) -> None:
        """Set up basic window properties."""
        self.setWindowTitle("RS Personal Agent")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        # Center the window on screen
        self._center_window()

    def _center_window(self) -> None:
        """Center the window on the screen."""
        # Get screen geometry
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()

            # Calculate center position
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)

            # Move window to center
            self.move(window_geometry.topLeft())

    def _create_menu_bar(self) -> None:
        """Create and configure the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)

        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About RS Personal Agent")
        about_action.triggered.connect(self._show_about_dialog)

        help_menu.addAction(about_action)

    def _create_central_widget(self) -> None:
        """Create and configure the central widget."""
        # Create and set the dashboard view as the central widget
        self._dashboard_view = DashboardView()
        self.setCentralWidget(self._dashboard_view)

    def _create_status_bar(self) -> None:
        """Create and configure the status bar."""
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")

        # Add a timer to update status periodically
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(5000)  # Update every 5 seconds

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Refresh shortcut (F5)
        refresh_action = QAction(self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self._refresh_status)
        self.addAction(refresh_action)

    def _update_status(self) -> None:
        """Update the status bar message."""
        import datetime

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.statusBar().showMessage(f"Ready - {current_time}")

    def _refresh_status(self) -> None:
        """Refresh the application status."""
        self.statusBar().showMessage("Refreshing...", 2000)
        # Refresh the dashboard
        if hasattr(self, "_dashboard_view"):
            self._dashboard_view.refresh_dashboard()
        QTimer.singleShot(2000, lambda: self.statusBar().showMessage("Ready"))

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        if hasattr(self, "_dashboard_view"):
            # Connect dashboard signals
            self._dashboard_view.refresh_requested.connect(
                self._handle_dashboard_refresh
            )
            self._dashboard_view.settings_requested.connect(
                self._handle_settings_request
            )
            self._dashboard_view.agent_action_requested.connect(
                self._handle_agent_action
            )

    def _handle_dashboard_refresh(self) -> None:
        """Handle dashboard refresh request."""
        self.statusBar().showMessage("Dashboard refreshed", 3000)

    def _handle_settings_request(self) -> None:
        """Handle settings request."""
        QMessageBox.information(
            self,
            "Settings",
            "Settings dialog will be implemented in a future version.\n\n"
            "This is a placeholder for the settings interface.",
        )

    def _handle_agent_action(self, agent_name: str, action: str) -> None:
        """
        Handle agent action from dashboard.

        Args:
            agent_name: Name of the agent
            action: Action to perform
        """
        # Update status bar
        message = f"Agent action: {action} on {agent_name}"
        self.statusBar().showMessage(message, 3000)

    def _show_about_dialog(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About RS Personal Agent",
            "<h3>RS Personal Agent v0.1.0</h3>"
            "<p>A privacy-first, local AI-powered personal agent platform.</p>"
            "<p>Built with PySide6 and Qt6.</p>"
            "<p>© 2024 Roostership</p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.

        Args:
            event: Close event
        """
        # Add any cleanup logic here
        event.accept()
