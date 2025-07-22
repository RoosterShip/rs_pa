"""
Settings dialog for Gmail OAuth2 and Ollama configuration.

This module provides a native Qt dialog for configuring Gmail
authentication and Ollama server settings.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.gmail_service import GmailService
from ...core.llm_manager import OllamaManager
from ..widgets.connection_status_widget import ConnectionStatusWidget


class SettingsDialog(QDialog):
    """
    Settings dialog for Gmail and Ollama configuration.

    This dialog provides interfaces for Gmail OAuth2 authentication
    and Ollama server configuration with connection testing.
    """

    # Signals
    settings_changed = Signal()
    gmail_authenticated = Signal()
    ollama_connected = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the settings dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Services
        self._gmail_service = GmailService(self)
        self._ollama_manager = OllamaManager(parent=self)

        self._setup_dialog()
        self._setup_ui()
        self._setup_connections()
        self._load_current_settings()

    def _setup_dialog(self) -> None:
        """Set up basic dialog properties."""
        self.setWindowTitle("Settings - RS Personal Agent")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.resize(800, 600)

        # Center on parent
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, "geometry"):
            parent_geo = parent_widget.geometry()
            dialog_geo = self.geometry()
            x = parent_geo.center().x() - dialog_geo.width() // 2
            y = parent_geo.center().y() - dialog_geo.height() // 2
            self.move(x, y)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Tab widget for different settings categories
        self._tab_widget = QTabWidget()

        # Gmail settings tab
        gmail_tab = self._create_gmail_tab()
        self._tab_widget.addTab(gmail_tab, "Gmail Authentication")

        # Ollama settings tab
        ollama_tab = self._create_ollama_tab()
        self._tab_widget.addTab(ollama_tab, "Ollama Configuration")

        main_layout.addWidget(self._tab_widget)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Apply styling
        self._apply_styling()

    def _create_gmail_tab(self) -> QWidget:
        """
        Create the Gmail authentication tab.

        Returns:
            Gmail settings widget
        """
        gmail_widget = QWidget()
        layout = QVBoxLayout(gmail_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Gmail connection status
        status_group = QGroupBox("Connection Status")
        status_layout = QHBoxLayout(status_group)

        self._gmail_status = ConnectionStatusWidget("Gmail", "disconnected")
        status_layout.addWidget(self._gmail_status)
        status_layout.addStretch()

        layout.addWidget(status_group)

        # Gmail configuration
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)

        # Credentials file path
        creds_layout = QHBoxLayout()
        self._creds_path_edit = QLineEdit()
        self._creds_path_edit.setPlaceholderText("Path to credentials.json file...")
        self._creds_path_edit.setReadOnly(True)
        creds_layout.addWidget(self._creds_path_edit)

        self._browse_creds_button = QPushButton("Browse...")
        self._browse_creds_button.clicked.connect(self._browse_credentials_file)
        creds_layout.addWidget(self._browse_creds_button)

        config_layout.addRow("Credentials File:", creds_layout)

        # User email (readonly, filled after auth)
        self._user_email_edit = QLineEdit()
        self._user_email_edit.setReadOnly(True)
        self._user_email_edit.setPlaceholderText("Not authenticated")
        config_layout.addRow("User Email:", self._user_email_edit)

        layout.addWidget(config_group)

        # Gmail actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        # Authenticate button
        auth_layout = QHBoxLayout()
        self._authenticate_button = QPushButton("🔐 Authenticate with Gmail")
        self._authenticate_button.setObjectName("authButton")
        auth_layout.addWidget(self._authenticate_button)
        auth_layout.addStretch()

        actions_layout.addLayout(auth_layout)

        # Test connection
        test_layout = QHBoxLayout()
        self._test_gmail_button = QPushButton("🔍 Test Connection")
        self._test_gmail_button.setObjectName("testButton")
        self._test_gmail_button.setEnabled(False)
        test_layout.addWidget(self._test_gmail_button)

        self._gmail_test_progress = QProgressBar()
        self._gmail_test_progress.setVisible(False)
        test_layout.addWidget(self._gmail_test_progress)

        test_layout.addStretch()
        actions_layout.addLayout(test_layout)

        layout.addWidget(actions_group)

        # Add stretch
        layout.addStretch()

        return gmail_widget

    def _create_ollama_tab(self) -> QWidget:
        """
        Create the Ollama configuration tab.

        Returns:
            Ollama settings widget
        """
        ollama_widget = QWidget()
        layout = QVBoxLayout(ollama_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Ollama connection status
        status_group = QGroupBox("Connection Status")
        status_layout = QHBoxLayout(status_group)

        self._ollama_status = ConnectionStatusWidget("Ollama", "disconnected")
        status_layout.addWidget(self._ollama_status)
        status_layout.addStretch()

        layout.addWidget(status_group)

        # Ollama server configuration
        config_group = QGroupBox("Server Configuration")
        config_layout = QFormLayout(config_group)

        # Host
        self._ollama_host_edit = QLineEdit("localhost")
        config_layout.addRow("Host:", self._ollama_host_edit)

        # Port
        self._ollama_port_spin = QSpinBox()
        self._ollama_port_spin.setRange(1, 65535)
        self._ollama_port_spin.setValue(11434)
        config_layout.addRow("Port:", self._ollama_port_spin)

        # Default model
        self._default_model_edit = QLineEdit("llama3.2")
        config_layout.addRow("Default Model:", self._default_model_edit)

        layout.addWidget(config_group)

        # Ollama actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        # Test connection
        test_layout = QHBoxLayout()
        self._test_ollama_button = QPushButton("🔍 Test Connection")
        self._test_ollama_button.setObjectName("testButton")
        test_layout.addWidget(self._test_ollama_button)

        self._ollama_test_progress = QProgressBar()
        self._ollama_test_progress.setVisible(False)
        test_layout.addWidget(self._ollama_test_progress)

        test_layout.addStretch()
        actions_layout.addLayout(test_layout)

        # Model management
        model_layout = QHBoxLayout()
        self._pull_model_button = QPushButton("📥 Pull Default Model")
        self._pull_model_button.setObjectName("pullButton")
        self._pull_model_button.setEnabled(False)
        model_layout.addWidget(self._pull_model_button)
        model_layout.addStretch()

        actions_layout.addLayout(model_layout)

        layout.addWidget(actions_group)

        # Server info
        info_group = QGroupBox("Server Information")
        info_layout = QFormLayout(info_group)

        self._server_url_label = QLabel("Not connected")
        info_layout.addRow("Server URL:", self._server_url_label)

        self._available_models_label = QLabel("Unknown")
        info_layout.addRow("Available Models:", self._available_models_label)

        layout.addWidget(info_group)

        # Add stretch
        layout.addStretch()

        return ollama_widget

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Gmail connections
        self._authenticate_button.clicked.connect(self._authenticate_gmail)
        self._test_gmail_button.clicked.connect(self._test_gmail_connection)
        self._gmail_service.connection_status_changed.connect(self._update_gmail_status)
        self._gmail_service.error_occurred.connect(self._show_gmail_error)

        # Ollama connections
        self._test_ollama_button.clicked.connect(self._test_ollama_connection)
        self._pull_model_button.clicked.connect(self._pull_default_model)
        self._ollama_manager.connection_status_changed.connect(
            self._update_ollama_status
        )
        self._ollama_manager.error_occurred.connect(self._show_ollama_error)

        # Settings change connections
        self._ollama_host_edit.textChanged.connect(self._on_ollama_settings_changed)
        self._ollama_port_spin.valueChanged.connect(self._on_ollama_settings_changed)

    def _load_current_settings(self) -> None:
        """Load current settings from configuration."""
        # Look for existing credentials file
        creds_path = Path.cwd() / "credentials.json"
        if creds_path.exists():
            self._creds_path_edit.setText(str(creds_path))
            self._gmail_service.set_credentials_file(str(creds_path))

        # Update status indicators
        self._update_gmail_status(self._gmail_service.get_connection_status())
        self._update_ollama_status(self._ollama_manager.get_connection_status())

    def _browse_credentials_file(self) -> None:
        """Browse for Gmail credentials file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Gmail Credentials File",
            str(Path.cwd()),
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            self._creds_path_edit.setText(file_path)
            self._gmail_service.set_credentials_file(file_path)

    def _authenticate_gmail(self) -> None:
        """Authenticate with Gmail."""
        if not self._creds_path_edit.text():
            QMessageBox.warning(
                self,
                "Missing Credentials",
                "Please select a Gmail credentials file first.",
            )
            return

        self._authenticate_button.setEnabled(False)
        self._authenticate_button.setText("🔐 Authenticating...")

        # Run authentication in a timer to avoid blocking UI
        QTimer.singleShot(100, self._run_gmail_auth)

    def _run_gmail_auth(self) -> None:
        """Run Gmail authentication process."""
        success = self._gmail_service.authenticate()

        self._authenticate_button.setEnabled(True)
        self._authenticate_button.setText("🔐 Authenticate with Gmail")

        if success:
            # Get user email
            user_email = self._gmail_service.get_user_email()
            self._user_email_edit.setText(user_email)
            self._test_gmail_button.setEnabled(True)

            QMessageBox.information(
                self,
                "Authentication Successful",
                f"Successfully authenticated with Gmail!\nUser: {user_email}",
            )
            self.gmail_authenticated.emit()
        else:
            QMessageBox.critical(
                self,
                "Authentication Failed",
                "Gmail authentication failed. Please check your credentials "
                "file and try again.",
            )

    def _test_gmail_connection(self) -> None:
        """Test Gmail connection."""
        self._test_gmail_button.setEnabled(False)
        self._gmail_test_progress.setVisible(True)
        self._gmail_test_progress.setRange(0, 0)  # Indeterminate

        # Run test in timer
        QTimer.singleShot(100, self._run_gmail_test)

    def _run_gmail_test(self) -> None:
        """Run Gmail connection test."""
        success = self._gmail_service.test_connection()

        self._test_gmail_button.setEnabled(True)
        self._gmail_test_progress.setVisible(False)

        if success:
            QMessageBox.information(
                self, "Connection Test", "Gmail connection test successful!"
            )
        else:
            QMessageBox.warning(
                self,
                "Connection Test",
                "Gmail connection test failed. Please check your authentication.",
            )

    def _test_ollama_connection(self) -> None:
        """Test Ollama connection."""
        self._test_ollama_button.setEnabled(False)
        self._ollama_test_progress.setVisible(True)
        self._ollama_test_progress.setRange(0, 0)  # Indeterminate

        # Update Ollama configuration
        self._update_ollama_config()

        # Run test in timer
        QTimer.singleShot(100, self._run_ollama_test)

    def _run_ollama_test(self) -> None:
        """Run Ollama connection test."""
        success = self._ollama_manager.test_connection()

        self._test_ollama_button.setEnabled(True)
        self._ollama_test_progress.setVisible(False)

        if success:
            # Update server info
            self._update_ollama_info()
            self._pull_model_button.setEnabled(True)

            QMessageBox.information(
                self, "Connection Test", "Ollama connection test successful!"
            )
            self.ollama_connected.emit()
        else:
            QMessageBox.warning(
                self,
                "Connection Test",
                "Ollama connection test failed. Please check your server "
                "configuration.",
            )

    def _pull_default_model(self) -> None:
        """Pull the default model."""
        model = self._default_model_edit.text().strip()
        if not model:
            QMessageBox.warning(
                self, "No Model Specified", "Please specify a default model name."
            )
            return

        self._pull_model_button.setEnabled(False)
        self._pull_model_button.setText("📥 Pulling Model...")

        # This could take a while, show progress
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate

        reply = QMessageBox.question(
            self,
            "Pull Model",
            f"Pull model '{model}' from Ollama?\nThis may take several "
            "minutes for large models.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            QTimer.singleShot(100, lambda: self._run_model_pull(model))
        else:
            self._pull_model_button.setEnabled(True)
            self._pull_model_button.setText("📥 Pull Default Model")

    def _run_model_pull(self, model: str) -> None:
        """Run model pull operation."""
        success = self._ollama_manager.pull_model(model)

        self._pull_model_button.setEnabled(True)
        self._pull_model_button.setText("📥 Pull Default Model")

        if success:
            self._update_ollama_info()
            QMessageBox.information(
                self, "Model Pull Complete", f"Successfully pulled model '{model}'!"
            )
        else:
            QMessageBox.critical(
                self,
                "Model Pull Failed",
                f"Failed to pull model '{model}'. Please check the model name "
                "and try again.",
            )

    def _update_ollama_config(self) -> None:
        """Update Ollama manager configuration."""
        host = self._ollama_host_edit.text().strip() or "localhost"
        port = self._ollama_port_spin.value()
        model = self._default_model_edit.text().strip() or "llama3.2"

        self._ollama_manager.set_server_config(host, port)
        self._ollama_manager.set_default_model(model)

        # Update server URL display
        self._server_url_label.setText(f"http://{host}:{port}")

    def _update_ollama_info(self) -> None:
        """Update Ollama server information display."""
        if self._ollama_manager.is_connected():
            models = self._ollama_manager.get_available_models()
            if models:
                model_text = ", ".join(models[:3])  # Show first 3
                if len(models) > 3:
                    model_text += f" (+{len(models) - 3} more)"
                self._available_models_label.setText(model_text)
            else:
                self._available_models_label.setText("No models found")
        else:
            self._available_models_label.setText("Not connected")

    def _on_ollama_settings_changed(self) -> None:
        """Handle Ollama settings changes."""
        self._update_ollama_config()
        # Reset connection status when settings change
        if self._ollama_manager.is_connected():
            self._ollama_manager.disconnect_service()

    def _update_gmail_status(self, status: str) -> None:
        """Update Gmail connection status display."""
        self._gmail_status.set_status(status)

    def _update_ollama_status(self, status: str) -> None:
        """Update Ollama connection status display."""
        self._ollama_status.set_status(status)

    def _show_gmail_error(self, error_msg: str) -> None:
        """Show Gmail error message."""
        QMessageBox.critical(self, "Gmail Error", error_msg)

    def _show_ollama_error(self, error_msg: str) -> None:
        """Show Ollama error message."""
        QMessageBox.critical(self, "Ollama Error", error_msg)

    def _save_and_accept(self) -> None:
        """Save settings and accept dialog."""
        # Update final Ollama configuration
        self._update_ollama_config()

        self.settings_changed.emit()
        self.accept()

    def _apply_styling(self) -> None:
        """Apply custom styling to the dialog."""
        self.setStyleSheet(
            """
            /* Main dialog styling */
            SettingsDialog {
                background-color: #f8fafc;
            }

            /* Group boxes */
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #374151;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8fafc;
            }

            /* Button styling */
            #authButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                min-width: 200px;
            }

            #authButton:hover {
                background-color: #059669;
            }

            #authButton:pressed {
                background-color: #047857;
            }

            #authButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
            }

            #testButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 150px;
            }

            #testButton:hover {
                background-color: #2563eb;
            }

            #testButton:pressed {
                background-color: #1d4ed8;
            }

            #testButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
            }

            #pullButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 150px;
            }

            #pullButton:hover {
                background-color: #d97706;
            }

            #pullButton:pressed {
                background-color: #b45309;
            }

            #pullButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
            }

            /* Input styling */
            QLineEdit, QSpinBox {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px 10px;
                background-color: white;
                font-size: 12px;
            }

            QLineEdit:focus, QSpinBox:focus {
                border-color: #3b82f6;
                outline: none;
            }

            QLineEdit:read-only {
                background-color: #f3f4f6;
                color: #6b7280;
            }

            /* Tab widget styling */
            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }

            QTabBar::tab {
                background-color: #f3f4f6;
                color: #6b7280;
                border: 1px solid #d1d5db;
                padding: 8px 16px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: white;
                color: #374151;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #e5e7eb;
            }

            /* Progress bar styling */
            QProgressBar {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: #f3f4f6;
                height: 8px;
                text-align: center;
            }

            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3b82f6, stop: 1 #1d4ed8);
                border-radius: 3px;
            }
        """
        )

    def get_gmail_service(self) -> GmailService:
        """Get the Gmail service instance."""
        return self._gmail_service

    def get_ollama_manager(self) -> OllamaManager:
        """Get the Ollama manager instance."""
        return self._ollama_manager
