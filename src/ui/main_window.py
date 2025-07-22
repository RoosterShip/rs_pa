"""
Main window for RS Personal Agent desktop application.

This module contains the MainWindow class which serves as the primary 
application window using PySide6's QMainWindow.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QMenuBar, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QAction


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
        exit_action.setShortcut(QKeySequence.Quit)
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("RS Personal Agent")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Status indicator placeholder
        status_label = QLabel("System Ready")
        status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #27ae60;
                padding: 10px;
                border: 1px solid #27ae60;
                border-radius: 5px;
                background-color: #d5f4e6;
            }
        """)
        header_layout.addWidget(status_label)
        
        main_layout.addLayout(header_layout)
        
        # Content area placeholder
        content_label = QLabel("Welcome to RS Personal Agent")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                padding: 40px;
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
        """)
        main_layout.addWidget(content_label)
        
        # Footer spacer
        main_layout.addStretch()
    
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
        refresh_action.setShortcut(QKeySequence.Refresh)
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
        # Add refresh logic here later
        QTimer.singleShot(2000, lambda: self.statusBar().showMessage("Ready"))
    
    def _show_about_dialog(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About RS Personal Agent",
            "<h3>RS Personal Agent v0.1.0</h3>"
            "<p>A privacy-first, local AI-powered personal agent platform.</p>"
            "<p>Built with PySide6 and Qt6.</p>"
            "<p>© 2024 Roostership</p>"
        )
    
    def closeEvent(self, event) -> None:
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Add any cleanup logic here
        event.accept()