"""
System tray widget for desktop notifications and quick access.

This module provides native system tray integration with notifications
for alerts and quick access to main dashboard functionality.
"""

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


class SystemTrayWidget(QObject):
    """
    System tray widget for notifications and quick access.

    Features:
    - Native desktop notifications
    - Right-click context menu
    - Status indicator icon
    - Quick access to dashboard
    """

    # Signals
    show_dashboard_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize system tray widget.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._setup_tray_icon()
        self._setup_context_menu()

    def _setup_tray_icon(self) -> None:
        """Setup the system tray icon."""
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available on this system")
            return

        self.tray_icon = QSystemTrayIcon(self)

        # Create a simple icon
        icon = self._create_app_icon()
        self.tray_icon.setIcon(icon)

        # Set tooltip
        self.tray_icon.setToolTip("RS Personal Agent")

        # Connect activation signal
        self.tray_icon.activated.connect(self._on_tray_activated)

        logger.info("System tray icon initialized")

    def _create_app_icon(self) -> QIcon:
        """Create application icon for system tray."""
        # Create a simple colored circle as app icon
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circle with gradient
        painter.setBrush(QBrush(QColor(33, 150, 243)))  # Blue
        painter.setPen(QColor(21, 101, 192))  # Darker blue border
        painter.drawEllipse(2, 2, 28, 28)

        # Add "RS" text
        painter.setPen(QColor(255, 255, 255))  # White text
        painter.drawText(8, 20, "RS")

        painter.end()

        return QIcon(pixmap)

    def _setup_context_menu(self) -> None:
        """Setup right-click context menu."""
        self.context_menu = QMenu()

        # Show Dashboard action
        show_action = QAction("Show Dashboard", self)
        show_action.triggered.connect(self.show_dashboard_requested.emit)
        self.context_menu.addAction(show_action)

        self.context_menu.addSeparator()

        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.context_menu.addAction(settings_action)

        self.context_menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.context_menu.addAction(quit_action)

        # Set the context menu
        if hasattr(self, "tray_icon"):
            self.tray_icon.setContextMenu(self.context_menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_dashboard_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - could show a quick status popup
            pass

    def show(self) -> None:
        """Show the system tray icon."""
        if hasattr(self, "tray_icon"):
            self.tray_icon.show()
            logger.info("System tray icon shown")
        else:
            logger.warning("Cannot show tray icon - not initialized")

    def hide(self) -> None:
        """Hide the system tray icon."""
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
            logger.info("System tray icon hidden")

    def show_notification(
        self,
        title: str,
        message: str,
        icon_type: QSystemTrayIcon.MessageIcon = (
            QSystemTrayIcon.MessageIcon.Information
        ),
        timeout: int = 5000,
    ) -> None:
        """
        Show desktop notification.

        Args:
            title: Notification title
            message: Notification message
            icon_type: Icon type (Information, Warning, Critical)
            timeout: Timeout in milliseconds
        """
        if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon_type, timeout)
            logger.debug(f"Notification shown: {title} - {message}")
        else:
            logger.warning("Cannot show notification - tray icon not visible")

    def show_alert_notification(
        self, alert_type: str, metric_name: str, value: float
    ) -> None:
        """
        Show alert notification.

        Args:
            alert_type: Type of alert (warning, critical)
            metric_name: Name of the metric
            value: Metric value
        """
        title = f"Performance Alert - {alert_type.title()}"
        message = f"{metric_name}: {value:.1f}%"

        if alert_type == "critical":
            icon_type = QSystemTrayIcon.MessageIcon.Critical
        else:
            icon_type = QSystemTrayIcon.MessageIcon.Warning

        self.show_notification(title, message, icon_type)

    def show_success_notification(self, message: str) -> None:
        """Show success notification."""
        self.show_notification(
            "RS Personal Agent", message, QSystemTrayIcon.MessageIcon.Information
        )

    def show_error_notification(self, message: str) -> None:
        """Show error notification."""
        self.show_notification(
            "RS Personal Agent - Error", message, QSystemTrayIcon.MessageIcon.Critical
        )

    def is_available(self) -> bool:
        """Check if system tray is available."""
        return QSystemTrayIcon.isSystemTrayAvailable()

    def is_visible(self) -> bool:
        """Check if tray icon is visible."""
        return hasattr(self, "tray_icon") and self.tray_icon.isVisible()
