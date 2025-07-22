"""
Main entry point for RS Personal Agent desktop application.

This module provides the entry point for launching the native PySide6 desktop application.
It initializes the QApplication and main window.
"""

import sys
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon

from src.ui.main_window import MainWindow


def main() -> int:
    """
    Main entry point for the RS Personal Agent desktop application.
    
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Set application metadata
    QCoreApplication.setApplicationName("RS Personal Agent")
    QCoreApplication.setApplicationVersion("0.1.0")
    QCoreApplication.setOrganizationName("Roostership")
    QCoreApplication.setOrganizationDomain("roostership.com")
    
    # Create the QApplication
    app = QApplication(sys.argv)
    
    # Set application icon (if available)
    try:
        app.setWindowIcon(QIcon("src/ui/resources/icon.png"))
    except Exception:
        # Icon file doesn't exist yet, continue without it
        pass
    
    # Enable high DPI support (Qt 6.0+ handles this automatically)
    # Note: AA_EnableHighDpiScaling and AA_UseHighDpiPixmaps are deprecated in Qt 6
    # Qt 6 automatically enables high DPI scaling by default
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())