# UI Design - RS Personal Agent

## 📋 Overview

This document details the user interface design and implementation guidelines for the RS Personal Agent. The UI provides a modern, native desktop interface for managing AI agents, monitoring their status, viewing outputs, and analyzing performance metrics in real-time using **PySide6 6.9.1** (Qt6 Python bindings) for professional cross-platform desktop functionality.

## 🎨 Design Philosophy

### Visual Language
- **Native Desktop Feel**: Professional Qt-based interface with OS-appropriate styling
- **Dark/Light Theme Support**: System-adaptive theming with manual override capability
- **High Contrast**: Clear visual hierarchy with proper spacing and typography
- **Responsive Layout**: Adapts to different screen sizes and window states
- **Real-time Updates**: Live data visualization using Qt Model-View architecture

### User Experience Principles
1. **Intuitive Navigation**: Clear visual cues and logical grouping with Qt layouts
2. **Minimal Clicks**: Common actions accessible within 2 clicks via Qt widgets
3. **Visual Feedback**: Immediate response to user interactions with Qt signals/slots
4. **Progressive Disclosure**: Advanced features accessed through expandable sections
5. **Consistency**: Uniform interaction patterns across all Qt components
6. **Keyboard Navigation**: Full keyboard accessibility with Qt shortcuts

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                Qt Main Application Window                   │
│                    (QMainWindow)                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌─────────────────────────────────────────┐  │
│  │          │  │                                         │  │
│  │   Side   │  │        Main Content Area                │  │
│  │   Panel  │  │         (QStackedWidget)                │  │
│  │          │  │                                         │  │
│  │ - Agents │  │  ┌─────────────┐  ┌──────────────────┐  │  │
│  │ - Stats  │  │  │   Agent     │  │     Timeline     │  │  │
│  │ - Config │  │  │   Cards     │  │     View         │  │  │
│  │          │  │  │ (QTableView)│  │  (Custom Widget) │  │  │
│  │          │  │  └─────────────┘  └──────────────────┘  │  │
│  │          │  │                                         │  │
│  │          │  │  ┌────────────────────────────────────┐ │  │
│  │          │  │  │     Log Viewer (QTextBrowser)      │ │  │
│  │          │  │  └────────────────────────────────────┘ │  │
│  └──────────┘  └─────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Status Bar (QStatusBar)                  │
└─────────────────────────────────────────────────────────────┘
```

## 🧩 PySide6 Component Library

### Base Application Architecture

#### 1. Main Application Window (`src/ui/main_window.py`)
```python
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QStackedWidget, QMenuBar, 
                             QStatusBar, QToolBar)
from PySide6.QtCore import QTimer, QThread, Signal, QSettings
from PySide6.QtGui import QAction, QIcon, QKeySequence
from src.ui.widgets.theme_manager import ThemeManager
from src.ui.views.dashboard_view import DashboardView

class MainWindow(QMainWindow):
    """Main application window with native Qt interface"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Roostership", "RSPersonalAgent")
        self.theme_manager = ThemeManager()
        
        self.setWindowTitle("RS Personal Agent")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_timers()
        self._apply_theme()
        
    def _setup_ui(self):
        """Set up the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Side panel (navigation)
        self.side_panel = SidePanel()
        self.side_panel.page_changed.connect(self._change_page)
        main_layout.addWidget(self.side_panel, 0)  # Fixed width
        
        # Main content area (stacked widget for different pages)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)  # Expandable
        
        # Add content pages
        self.dashboard_view = DashboardView()
        self.agents_view = AgentsView()
        self.logs_view = LogsView()
        self.settings_view = SettingsView()
        
        self.content_stack.addWidget(self.dashboard_view)
        self.content_stack.addWidget(self.agents_view)
        self.content_stack.addWidget(self.logs_view)
        self.content_stack.addWidget(self.settings_view)
        
    def _setup_menu_bar(self):
        """Create native menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        settings_action = QAction('&Preferences...', self)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('&Quit', self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Agents menu
        agents_menu = menubar.addMenu('&Agents')
        
        start_all_action = QAction('&Start All', self)
        start_all_action.setShortcut('Ctrl+R')
        start_all_action.triggered.connect(self._start_all_agents)
        agents_menu.addAction(start_all_action)
        
        stop_all_action = QAction('St&op All', self)
        stop_all_action.setShortcut('Ctrl+T')
        stop_all_action.triggered.connect(self._stop_all_agents)
        agents_menu.addAction(stop_all_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        toggle_theme_action = QAction('Toggle &Theme', self)
        toggle_theme_action.setShortcut('Ctrl+Shift+T')
        toggle_theme_action.triggered.connect(self.theme_manager.toggle_theme)
        view_menu.addAction(toggle_theme_action)
        
        refresh_action = QAction('&Refresh', self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self._refresh_data)
        view_menu.addAction(refresh_action)
```

#### 2. Theme Manager (`src/ui/widgets/theme_manager.py`)
```python
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QPalette, QColor
from enum import Enum
from typing import Dict

class Theme(Enum):
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"

class ThemeManager(QObject):
    """Centralized theme management for Qt application"""
    
    theme_changed = Signal(str)  # Emits theme name when changed
    
    # Modern color schemes
    THEMES = {
        "dark": {
            "window": "#1e1e1e",
            "window_text": "#ffffff", 
            "base": "#2d2d2d",
            "alternate_base": "#3a3a3a",
            "button": "#404040",
            "button_text": "#ffffff",
            "highlight": "#0078d4",
            "highlighted_text": "#ffffff",
            "link": "#4dc7ff",
            "success": "#10b981",
            "warning": "#f59e0b", 
            "error": "#ef4444",
            "text_secondary": "#9ca3af",
            "border": "#4a5568",
            "accent": "#6366f1"
        },
        "light": {
            "window": "#f9fafb",
            "window_text": "#111827",
            "base": "#ffffff", 
            "alternate_base": "#f3f4f6",
            "button": "#e5e7eb",
            "button_text": "#374151",
            "highlight": "#3b82f6",
            "highlighted_text": "#ffffff",
            "link": "#2563eb",
            "success": "#059669",
            "warning": "#d97706",
            "error": "#dc2626", 
            "text_secondary": "#6b7280",
            "border": "#d1d5db",
            "accent": "#818cf8"
        }
    }
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings()
        self.current_theme = self.settings.value("theme", Theme.AUTO.value)
        self.apply_theme(self.current_theme)
        
    def apply_theme(self, theme_name: str):
        """Apply theme to the Qt application"""
        app = QApplication.instance()
        if not app:
            return
            
        # Determine actual theme to use
        if theme_name == Theme.AUTO.value:
            # Detect system theme preference
            palette = app.palette()
            is_dark = palette.color(QPalette.Window).lightness() < 128
            actual_theme = "dark" if is_dark else "light"
        else:
            actual_theme = theme_name
            
        # Get theme colors
        colors = self.THEMES.get(actual_theme, self.THEMES["dark"])
        
        # Create and apply palette
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.Window, QColor(colors["window"]))
        palette.setColor(QPalette.WindowText, QColor(colors["window_text"]))
        
        # Input colors
        palette.setColor(QPalette.Base, QColor(colors["base"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["alternate_base"]))
        palette.setColor(QPalette.Text, QColor(colors["window_text"]))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor(colors["button"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["button_text"]))
        
        # Selection colors
        palette.setColor(QPalette.Highlight, QColor(colors["highlight"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["highlighted_text"]))
        
        # Link colors
        palette.setColor(QPalette.Link, QColor(colors["link"]))
        
        # Apply the palette
        app.setPalette(palette)
        
        # Store current theme
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        
        # Apply additional stylesheet for custom styling
        self._apply_stylesheet(actual_theme, colors)
        
        # Emit signal for custom widgets to update
        self.theme_changed.emit(actual_theme)
        
    def _apply_stylesheet(self, theme_name: str, colors: Dict[str, str]):
        """Apply custom stylesheet for enhanced styling"""
        app = QApplication.instance()
        
        stylesheet = f"""
        /* Main window styling */
        QMainWindow {{
            background-color: {colors['window']};
            color: {colors['window_text']};
        }}
        
        /* Status indicators */
        QLabel[statusIndicator="true"] {{
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QLabel[status="connected"] {{
            background-color: {colors['success']};
            color: white;
        }}
        
        QLabel[status="disconnected"] {{
            background-color: {colors['error']};
            color: white;
        }}
        
        QLabel[status="warning"] {{
            background-color: {colors['warning']};
            color: white;
        }}
        
        /* Table styling */
        QTableView {{
            gridline-color: {colors['border']};
            selection-background-color: {colors['highlight']};
            alternate-background-color: {colors['alternate_base']};
        }}
        
        QTableView::item:selected {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        /* Headers */
        QHeaderView::section {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            padding: 8px;
            border: 1px solid {colors['border']};
            font-weight: bold;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 1px solid {colors['border']};
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent']};
        }}
        
        QPushButton[primary="true"] {{
            background-color: {colors['accent']};
            color: white;
            border: none;
        }}
        
        /* Side panel */
        QFrame[role="sidePanel"] {{
            background-color: {colors['base']};
            border-right: 1px solid {colors['border']};
        }}
        """
        
        app.setStyleSheet(stylesheet)
        
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.current_theme == Theme.DARK.value:
            self.apply_theme(Theme.LIGHT.value)
        else:
            self.apply_theme(Theme.DARK.value)
            
    def get_color(self, color_name: str) -> str:
        """Get color value for current theme"""
        actual_theme = self.current_theme
        if actual_theme == Theme.AUTO.value:
            # Determine actual theme
            app = QApplication.instance()
            if app:
                palette = app.palette()
                is_dark = palette.color(QPalette.Window).lightness() < 128
                actual_theme = "dark" if is_dark else "light"
            else:
                actual_theme = "dark"
                
        return self.THEMES.get(actual_theme, self.THEMES["dark"]).get(color_name, "#000000")
```

#### 3. Side Navigation Panel (`src/ui/widgets/side_panel.py`)
```python
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QButtonGroup, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QIcon
from typing import List, Dict

class SidePanel(QFrame):
    """Collapsible side navigation panel with Qt widgets"""
    
    page_changed = Signal(int)  # Emits page index
    
    def __init__(self):
        super().__init__()
        self.setProperty("role", "sidePanel")
        self.setFixedWidth(200)
        self.setFrameStyle(QFrame.StyledPanel)
        
        self.current_page = 0
        self.nav_buttons = []
        self.button_group = QButtonGroup(self)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up side panel layout"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header with app title
        header_frame = QFrame()
        header_layout = QVBoxLayout()
        header_frame.setLayout(header_layout)
        
        title_label = QLabel("RS Assistant")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        header_layout.addWidget(title_label)
        
        layout.addWidget(header_frame)
        
        # Navigation buttons
        nav_items = [
            ("Dashboard", "📊"),
            ("Agents", "🤖"), 
            ("Logs", "📋"),
            ("Settings", "⚙️")
        ]
        
        self.nav_frame = QFrame()
        nav_layout = QVBoxLayout()
        self.nav_frame.setLayout(nav_layout)
        
        for i, (text, icon) in enumerate(nav_items):
            button = self._create_nav_button(text, icon, i)
            nav_layout.addWidget(button)
            self.nav_buttons.append(button)
            self.button_group.addButton(button, i)
            
        layout.addWidget(self.nav_frame)
        
        # Spacer to push everything to top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)
        
        # Set first button as active
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
            
        # Connect button group signal
        self.button_group.buttonToggled.connect(self._on_button_toggled)
        
    def _create_nav_button(self, text: str, icon: str, index: int) -> QPushButton:
        """Create a navigation button"""
        button = QPushButton(f"{icon}  {text}")
        button.setCheckable(True)
        button.setMinimumHeight(40)
        button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                font-weight: bold;
            }
            QPushButton:hover:!checked {
                background-color: palette(alternate-base);
            }
        """)
        return button
        
    def _on_button_toggled(self, button: QPushButton, checked: bool):
        """Handle navigation button toggle"""
        if checked:
            index = self.button_group.id(button)
            self.current_page = index
            self.page_changed.emit(index)
```

### Model-View Components

#### 4. Agent Table Model (`src/ui/models/agent_table_model.py`)
```python
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from typing import List, Any, Optional
from datetime import datetime
from src.models.agent import Agent, AgentStatus
from src.core.database import DatabaseManager

class AgentTableModel(QAbstractTableModel):
    """Qt model for displaying agent data in table views"""
    
    data_changed = Signal()
    
    def __init__(self, database_manager: DatabaseManager):
        super().__init__()
        self.database_manager = database_manager
        self.agents: List[Agent] = []
        self.headers = ["Name", "Type", "Status", "Last Run", "Tasks", "Performance"]
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
        # Initial data load
        self.refresh_data()
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.agents)
        
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
        
    def data(self, index: QModelIndex, role: int):
        if not index.isValid() or index.row() >= len(self.agents):
            return None
            
        agent = self.agents[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Name
                return agent.name
            elif column == 1:  # Type
                return agent.agent_type.replace('_', ' ').title()
            elif column == 2:  # Status
                return agent.status.value.title()
            elif column == 3:  # Last Run
                if agent.updated_at:
                    return agent.updated_at.strftime("%Y-%m-%d %H:%M")
                return "Never"
            elif column == 4:  # Tasks
                return f"{agent.completed_tasks}/{agent.total_tasks}"
            elif column == 5:  # Performance
                return f"{agent.success_rate:.1f}%"
                
        elif role == Qt.BackgroundRole:
            # Status-based row coloring
            if agent.status == AgentStatus.ACTIVE:
                return QBrush(QColor(220, 255, 220))  # Light green
            elif agent.status == AgentStatus.ERROR:
                return QBrush(QColor(255, 220, 220))  # Light red
            elif agent.status == AgentStatus.IDLE:
                return QBrush(QColor(255, 255, 220))  # Light yellow
                
        elif role == Qt.FontRole:
            if column == 2:  # Status column
                font = QFont()
                font.setBold(True)
                return font
                
        elif role == Qt.TextAlignmentRole:
            if column in [4, 5]:  # Numeric columns
                return Qt.AlignCenter
                
        return None
        
    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        elif role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            return font
        return None
        
    def refresh_data(self):
        """Refresh agent data from database"""
        try:
            with self.database_manager.get_session() as session:
                new_agents = session.query(Agent).all()
                
                if new_agents != self.agents:
                    self.beginResetModel()
                    self.agents = new_agents
                    self.endResetModel()
                    self.data_changed.emit()
                    
        except Exception as e:
            print(f"Error refreshing agent data: {e}")
            
    def get_agent_at_index(self, index: QModelIndex) -> Optional[Agent]:
        """Get agent object at given index"""
        if index.isValid() and index.row() < len(self.agents):
            return self.agents[index.row()]
        return None
```

#### 5. Agent Card Widget (`src/ui/widgets/agent_card_widget.py`)
```python
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QGridLayout)
from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QFont, QPalette
from typing import Dict, Any
from src.models.agent import Agent, AgentStatus
from datetime import datetime

class AgentCardWidget(QFrame):
    """Individual agent status card with controls"""
    
    start_requested = Signal(str)  # agent_id
    stop_requested = Signal(str)   # agent_id
    logs_requested = Signal(str)   # agent_id
    
    def __init__(self, agent: Agent):
        super().__init__()
        self.agent = agent
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setMinimumSize(300, 200)
        self.setMaximumSize(350, 250)
        
        self._setup_ui()
        self._update_display()
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def _setup_ui(self):
        """Set up the card layout"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header with agent name and type
        header_frame = QFrame()
        header_layout = QVBoxLayout()
        header_frame.setLayout(header_layout)
        
        self.name_label = QLabel(self.agent.name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        header_layout.addWidget(self.name_label)
        
        self.type_label = QLabel(self.agent.agent_type.replace('_', ' ').title())
        self.type_label.setStyleSheet("color: palette(text); font-size: 12px;")
        header_layout.addWidget(self.type_label)
        
        layout.addWidget(header_frame)
        
        # Status section
        status_frame = QFrame()
        status_layout = QHBoxLayout()
        status_frame.setLayout(status_layout)
        
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel()
        self.status_label.setProperty("statusIndicator", True)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addWidget(status_frame)
        
        # Metrics section
        metrics_frame = QFrame()
        metrics_layout = QGridLayout()
        metrics_frame.setLayout(metrics_layout)
        
        metrics_layout.addWidget(QLabel("Tasks:"), 0, 0)
        self.tasks_label = QLabel("0/0")
        metrics_layout.addWidget(self.tasks_label, 0, 1)
        
        metrics_layout.addWidget(QLabel("Success:"), 1, 0)
        self.success_label = QLabel("0%")
        metrics_layout.addWidget(self.success_label, 1, 1)
        
        metrics_layout.addWidget(QLabel("Last Run:"), 2, 0)
        self.last_run_label = QLabel("Never")
        metrics_layout.addWidget(self.last_run_label, 2, 1)
        
        layout.addWidget(metrics_frame)
        
        # Progress bar for active tasks
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Control buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout()
        button_frame.setLayout(button_layout)
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(lambda: self.start_requested.emit(self.agent.id))
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(lambda: self.stop_requested.emit(self.agent.id))
        button_layout.addWidget(self.stop_button)
        
        self.logs_button = QPushButton("Logs")
        self.logs_button.clicked.connect(lambda: self.logs_requested.emit(self.agent.id))
        button_layout.addWidget(self.logs_button)
        
        layout.addWidget(button_frame)
        
    def _update_display(self):
        """Update the card display based on current agent state"""
        # Status indicator
        status_text = self.agent.status.value.title()
        self.status_label.setText(status_text)
        self.status_label.setProperty("status", self._get_status_class())
        
        # Update button states
        if self.agent.status == AgentStatus.ACTIVE:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)
            
        # Update metrics
        self.tasks_label.setText(f"{self.agent.completed_tasks}/{self.agent.total_tasks}")
        self.success_label.setText(f"{self.agent.success_rate:.1f}%")
        
        if self.agent.updated_at:
            last_run = self.agent.updated_at.strftime("%H:%M")
            self.last_run_label.setText(last_run)
        else:
            self.last_run_label.setText("Never")
            
        # Force style update
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
    def _get_status_class(self) -> str:
        """Get CSS class name for status"""
        status_map = {
            AgentStatus.ACTIVE: "connected",
            AgentStatus.IDLE: "warning", 
            AgentStatus.ERROR: "disconnected",
            AgentStatus.DISABLED: "disconnected"
        }
        return status_map.get(self.agent.status, "warning")
        
    def update_agent(self, agent: Agent):
        """Update the agent data and refresh display"""
        self.agent = agent
        self._update_display()
```

### View Components

#### 6. Dashboard View (`src/ui/views/dashboard_view.py`)
```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QScrollArea, QGridLayout, QPushButton,
                             QTableView, QSplitter, QTabWidget)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from src.ui.models.agent_table_model import AgentTableModel
from src.ui.widgets.agent_card_widget import AgentCardWidget
from src.ui.widgets.status_indicator_widget import StatusIndicatorWidget
from src.ui.widgets.performance_chart_widget import PerformanceChartWidget
from typing import List, Dict

class DashboardView(QWidget):
    """Main dashboard view with agent overview and system status"""
    
    refresh_requested = Signal()
    
    def __init__(self, database_manager, agent_manager):
        super().__init__()
        self.database_manager = database_manager
        self.agent_manager = agent_manager
        self.agent_cards = {}
        
        self._setup_ui()
        self._setup_timers()
        
    def _setup_ui(self):
        """Set up the dashboard layout"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header section
        header_frame = self._create_header_section()
        layout.addWidget(header_frame)
        
        # Main content splitter (horizontal)
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left side: Agent cards and table
        left_widget = self._create_agent_section()
        main_splitter.addWidget(left_widget)
        
        # Right side: System metrics and charts  
        right_widget = self._create_metrics_section()
        main_splitter.addWidget(right_widget)
        
        # Set initial splitter proportions
        main_splitter.setSizes([700, 500])
        
    def _create_header_section(self):
        """Create dashboard header with title and controls"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout()
        frame.setLayout(layout)
        
        # Title
        title_label = QLabel("Agent Dashboard")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Spacer
        layout.addStretch()
        
        # System status indicators
        self.ollama_status = StatusIndicatorWidget("Ollama", "🔴 Disconnected")
        layout.addWidget(self.ollama_status)
        
        self.gmail_status = StatusIndicatorWidget("Gmail", "🔴 Disconnected")
        layout.addWidget(self.gmail_status)
        
        self.db_status = StatusIndicatorWidget("Database", "🟢 Connected")
        layout.addWidget(self.db_status)
        
        # Control buttons
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self._refresh_all)
        layout.addWidget(refresh_button)
        
        start_all_button = QPushButton("▶️ Start All")
        start_all_button.setProperty("primary", True)
        start_all_button.clicked.connect(self._start_all_agents)
        layout.addWidget(start_all_button)
        
        return frame
        
    def _create_agent_section(self):
        """Create agent management section"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Section header
        header_label = QLabel("Agent Status")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Tab widget for different views
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Cards view (grid of agent cards)
        cards_scroll = QScrollArea()
        cards_widget = QWidget()
        self.cards_layout = QGridLayout()
        cards_widget.setLayout(self.cards_layout)
        cards_scroll.setWidget(cards_widget)
        cards_scroll.setWidgetResizable(True)
        tab_widget.addTab(cards_scroll, "Cards")
        
        # Table view (compact table)
        self.agent_table_model = AgentTableModel(self.database_manager)
        self.agent_table = QTableView()
        self.agent_table.setModel(self.agent_table_model)
        self.agent_table.setSelectionBehavior(QTableView.SelectRows)
        self.agent_table.setAlternatingRowColors(True)
        self.agent_table.resizeColumnsToContents()
        tab_widget.addTab(self.agent_table, "Table")
        
        return widget
        
    def _create_metrics_section(self):
        """Create system metrics and performance section"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Section header
        header_label = QLabel("System Metrics")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Performance charts
        self.cpu_chart = PerformanceChartWidget("CPU Usage", "Time", "Percent")
        layout.addWidget(self.cpu_chart)
        
        self.memory_chart = PerformanceChartWidget("Memory Usage", "Time", "MB")
        layout.addWidget(self.memory_chart)
        
        # Agent performance summary
        summary_frame = QFrame()
        summary_frame.setFrameStyle(QFrame.StyledPanel)
        summary_layout = QGridLayout()
        summary_frame.setLayout(summary_layout)
        
        summary_layout.addWidget(QLabel("Total Agents:"), 0, 0)
        self.total_agents_label = QLabel("0")
        summary_layout.addWidget(self.total_agents_label, 0, 1)
        
        summary_layout.addWidget(QLabel("Active Agents:"), 1, 0)
        self.active_agents_label = QLabel("0")
        summary_layout.addWidget(self.active_agents_label, 1, 1)
        
        summary_layout.addWidget(QLabel("Tasks Today:"), 2, 0)
        self.tasks_today_label = QLabel("0")
        summary_layout.addWidget(self.tasks_today_label, 2, 1)
        
        layout.addWidget(summary_frame)
        
        return widget
        
    def _setup_timers(self):
        """Set up periodic update timers"""
        # Agent status refresh
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_indicators)
        self.status_timer.start(10000)  # Every 10 seconds
        
        # Performance metrics refresh
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self._update_performance_metrics)
        self.metrics_timer.start(5000)  # Every 5 seconds
        
    def _refresh_all(self):
        """Refresh all dashboard data"""
        self._update_agent_cards()
        self._update_status_indicators()
        self._update_performance_metrics()
        self.refresh_requested.emit()
        
    def _update_agent_cards(self):
        """Update agent card widgets"""
        try:
            with self.database_manager.get_session() as session:
                agents = session.query(Agent).all()
                
                # Remove old cards
                for agent_id, card in list(self.agent_cards.items()):
                    if agent_id not in [a.id for a in agents]:
                        card.setParent(None)
                        del self.agent_cards[agent_id]
                        
                # Add/update cards
                row, col = 0, 0
                for agent in agents:
                    if agent.id not in self.agent_cards:
                        card = AgentCardWidget(agent)
                        card.start_requested.connect(self._start_agent)
                        card.stop_requested.connect(self._stop_agent)
                        card.logs_requested.connect(self._view_agent_logs)
                        self.agent_cards[agent.id] = card
                        self.cards_layout.addWidget(card, row, col)
                        
                        col += 1
                        if col >= 2:  # 2 cards per row
                            col = 0
                            row += 1
                    else:
                        self.agent_cards[agent.id].update_agent(agent)
                        
        except Exception as e:
            print(f"Error updating agent cards: {e}")
            
    def _start_agent(self, agent_id: str):
        """Start specific agent"""
        try:
            self.agent_manager.start_agent(agent_id)
            self._update_agent_cards()
        except Exception as e:
            print(f"Error starting agent {agent_id}: {e}")
            
    def _stop_agent(self, agent_id: str):
        """Stop specific agent"""
        try:
            self.agent_manager.stop_agent(agent_id)
            self._update_agent_cards()
        except Exception as e:
            print(f"Error stopping agent {agent_id}: {e}")
            
    def _start_all_agents(self):
        """Start all available agents"""
        try:
            self.agent_manager.start_all_agents()
            self._update_agent_cards()
        except Exception as e:
            print(f"Error starting all agents: {e}")
```

### Advanced UI Components

#### 7. Performance Chart Widget (`src/ui/widgets/performance_chart_widget.py`)
```python
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, QPropertyAnimation, QRect
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from typing import List, Tuple
from collections import deque
import time
import psutil

class PerformanceChartWidget(QWidget):
    """Real-time performance chart using native Qt painting"""
    
    def __init__(self, title: str, x_label: str, y_label: str, max_points: int = 100):
        super().__init__()
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.max_points = max_points
        
        # Data storage
        self.data_points = deque(maxlen=max_points)
        self.time_points = deque(maxlen=max_points)
        
        self.setMinimumSize(400, 200)
        self.setMaximumHeight(250)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(1000)  # Update every second
        
        # Initialize with some data points
        self._initialize_data()
        
    def _initialize_data(self):
        """Initialize with some sample data"""
        current_time = time.time()
        for i in range(10):
            self.time_points.append(current_time - (10 - i))
            if self.title == "CPU Usage":
                self.data_points.append(psutil.cpu_percent(interval=None))
            else:  # Memory usage
                memory = psutil.virtual_memory()
                self.data_points.append(memory.used / 1024 / 1024)  # MB
                
    def _update_data(self):
        """Update chart with new data point"""
        current_time = time.time()
        self.time_points.append(current_time)
        
        if self.title == "CPU Usage":
            self.data_points.append(psutil.cpu_percent(interval=None))
        else:  # Memory usage
            memory = psutil.virtual_memory()
            self.data_points.append(memory.used / 1024 / 1024)  # MB
            
        self.update()  # Trigger repaint
        
    def paintEvent(self, event):
        """Custom paint event for drawing the chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Margins
        margin_left = 60
        margin_right = 20
        margin_top = 40
        margin_bottom = 40
        
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        
        # Background
        painter.fillRect(rect, QColor(240, 240, 240, 50))
        
        # Chart area background
        chart_rect = QRect(margin_left, margin_top, chart_width, chart_height)
        painter.fillRect(chart_rect, QColor(255, 255, 255, 100))
        
        # Draw title
        painter.setPen(QPen(QColor(0, 0, 0)))
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(width // 2 - 50, 25, self.title)
        
        # Draw axes
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        # Y-axis
        painter.drawLine(margin_left, margin_top, margin_left, height - margin_bottom)
        # X-axis  
        painter.drawLine(margin_left, height - margin_bottom, width - margin_right, height - margin_bottom)
        
        if len(self.data_points) < 2:
            return
            
        # Calculate value range
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        if max_val == min_val:
            max_val = min_val + 1
            
        # Draw grid lines
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(5):
            y = margin_top + i * (chart_height // 4)
            painter.drawLine(margin_left, y, width - margin_right, y)
            
        # Draw data line
        painter.setPen(QPen(QColor(50, 150, 250), 3))
        
        points = []
        for i, (time_val, data_val) in enumerate(zip(self.time_points, self.data_points)):
            x = margin_left + (i / (len(self.data_points) - 1)) * chart_width
            y_ratio = (data_val - min_val) / (max_val - min_val)
            y = margin_top + chart_height - (y_ratio * chart_height)
            points.append((x, y))
            
        # Draw line segments
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
        # Draw data points
        painter.setBrush(QBrush(QColor(50, 150, 250)))
        for x, y in points:
            painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)
            
        # Draw labels
        painter.setPen(QPen(QColor(0, 0, 0)))
        label_font = QFont()
        label_font.setPointSize(9)
        painter.setFont(label_font)
        
        # Y-axis labels
        for i in range(5):
            y = margin_top + i * (chart_height // 4)
            value = max_val - i * (max_val - min_val) / 4
            if self.title == "CPU Usage":
                label = f"{value:.0f}%"
            else:
                label = f"{value:.0f}MB"
            painter.drawText(5, y + 5, label)
            
        # Current value display
        if self.data_points:
            current_value = self.data_points[-1]
            if self.title == "CPU Usage":
                value_text = f"Current: {current_value:.1f}%"
            else:
                value_text = f"Current: {current_value:.0f}MB"
            painter.drawText(width - 150, height - 10, value_text)
```

#### 8. Log Viewer Component (`src/ui/widgets/log_viewer_widget.py`)
```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextBrowser, QLineEdit, QComboBox, 
                             QPushButton, QLabel, QFrame)
from PySide6.QtCore import QTimer, Signal, QThread
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from typing import List, Dict
from src.core.logging_manager import LoggingManager, LogEntry, LogLevel

class LogViewerWidget(QWidget):
    """Real-time log viewer with filtering and search"""
    
    def __init__(self, logging_manager: LoggingManager):
        super().__init__()
        self.logging_manager = logging_manager
        self.current_logs: List[LogEntry] = []
        
        self._setup_ui()
        self._setup_timers()
        self._load_recent_logs()
        
    def _setup_ui(self):
        """Set up log viewer layout"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls header
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.StyledPanel)
        controls_layout = QHBoxLayout()
        controls_frame.setLayout(controls_layout)
        
        # Log level filter
        controls_layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self._apply_filters)
        controls_layout.addWidget(self.level_combo)
        
        # Search box
        controls_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter logs...")
        self.search_input.textChanged.connect(self._apply_filters)
        controls_layout.addWidget(self.search_input)
        
        # Auto-scroll toggle
        self.auto_scroll_button = QPushButton("🔒 Auto-scroll")
        self.auto_scroll_button.setCheckable(True)
        self.auto_scroll_button.setChecked(True)
        controls_layout.addWidget(self.auto_scroll_button)
        
        # Clear button
        clear_button = QPushButton("🗑️ Clear")
        clear_button.clicked.connect(self._clear_logs)
        controls_layout.addWidget(clear_button)
        
        layout.addWidget(controls_frame)
        
        # Log text display
        self.log_display = QTextBrowser()
        self.log_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_display)
        
    def _setup_timers(self):
        """Set up periodic log refresh"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_logs)
        self.refresh_timer.start(1000)  # Refresh every second
        
    def _load_recent_logs(self):
        """Load recent logs from database"""
        try:
            self.current_logs = self.logging_manager.query_logs(limit=1000)
            self._display_logs()
        except Exception as e:
            self.log_display.append(f"Error loading logs: {e}")
            
    def _refresh_logs(self):
        """Refresh logs if new entries available"""
        try:
            latest_logs = self.logging_manager.query_logs(limit=50)  # Get latest 50
            
            if latest_logs and (not self.current_logs or 
                              latest_logs[0].timestamp > self.current_logs[0].timestamp):
                # Add new logs to beginning
                new_entries = [log for log in latest_logs 
                             if not self.current_logs or log.timestamp > self.current_logs[0].timestamp]
                self.current_logs = new_entries + self.current_logs
                
                # Limit total logs in memory
                self.current_logs = self.current_logs[:1000]
                self._display_logs()
                
        except Exception as e:
            pass  # Silently fail to avoid spam
            
    def _display_logs(self):
        """Display logs in the text browser"""
        self.log_display.clear()
        
        level_filter = self.level_combo.currentText()
        search_text = self.search_input.text().lower()
        
        for log_entry in reversed(self.current_logs):  # Show newest first
            # Apply filters
            if level_filter != "ALL" and log_entry.level != level_filter:
                continue
                
            if search_text and search_text not in log_entry.message.lower():
                continue
                
            # Format log entry
            timestamp_str = log_entry.timestamp.strftime("%H:%M:%S")
            formatted_entry = f"[{timestamp_str}] {log_entry.level:8} {log_entry.logger_name}: {log_entry.message}"
            
            # Add color based on level
            if log_entry.level == "ERROR" or log_entry.level == "CRITICAL":
                color = "red"
            elif log_entry.level == "WARNING":
                color = "orange" 
            elif log_entry.level == "INFO":
                color = "blue"
            else:
                color = "gray"
                
            self.log_display.append(f'<span style="color: {color};">{formatted_entry}</span>')
            
        # Auto-scroll to bottom if enabled
        if self.auto_scroll_button.isChecked():
            self.log_display.moveCursor(self.log_display.textCursor().End)
            
    def _apply_filters(self):
        """Apply current filters to log display"""
        self._display_logs()
        
    def _clear_logs(self):
        """Clear the log display"""
        self.log_display.clear()
        self.current_logs.clear()
```

## 🎯 Implementation Guidelines

### Development Workflow for PySide6

1. **Component Development**
   - Start with base application structure (QMainWindow, layouts)
   - Build specialized widgets (AgentCardWidget, StatusIndicator, etc.)  
   - Integrate with core system using Qt Model-View architecture
   - Add real-time updates using QTimer and Qt signals/slots

2. **Testing Strategy**
   - Unit tests for individual Qt widgets using pytest-qt
   - Integration tests for model-view interactions
   - Performance tests for real-time updates and large data sets
   - UI/UX testing with different themes and screen sizes

3. **Performance Optimization**
   - Use Qt threading (QThread) for background updates
   - Implement efficient model updates with proper signals
   - Cache Qt resources (icons, stylesheets) to avoid repeated loading
   - Batch UI updates to prevent excessive repainting

### Best Practices for Qt Development

1. **Code Organization**
   - Follow Qt naming conventions (camelCase for methods, PascalCase for classes)
   - Separate UI logic from business logic using MVC pattern
   - Use Qt resource system for assets and stylesheets
   - Implement proper signal/slot connections for communication

2. **UI/UX Guidelines**
   - Follow platform-specific design guidelines (Windows, macOS, Linux)
   - Use native Qt styling and respect system themes
   - Implement proper keyboard navigation with tab order
   - Provide visual feedback for all interactive elements
   - Support high-DPI displays with proper scaling

3. **Real-time Updates**
   - Use Qt Model-View architecture for efficient data updates
   - Implement proper thread safety with QMutex when needed
   - Use QTimer for periodic updates with appropriate intervals
   - Emit signals for data changes to update multiple views

## 🔧 Configuration for PySide6

### Theme Configuration (`src/ui/styles/themes.yaml`)
```yaml
themes:
  dark:
    primary: "#6366f1"
    primary_hover: "#5855eb"
    success: "#10b981"
    warning: "#f59e0b"
    error: "#ef4444"
    background: "#1e1e1e"
    surface: "#2d2d2d"
    surface_variant: "#3a3a3a"
    text: "#ffffff"
    text_secondary: "#9ca3af"
    border: "#4a5568"
  light:
    primary: "#3b82f6"
    primary_hover: "#2563eb"
    success: "#059669"
    warning: "#d97706"
    error: "#dc2626"
    background: "#f9fafb"
    surface: "#ffffff"
    surface_variant: "#f3f4f6"
    text: "#111827"
    text_secondary: "#6b7280"
    border: "#d1d5db"

layout:
  side_panel_width: 200
  card_min_width: 300
  card_max_width: 350
  spacing_small: 8
  spacing_medium: 16
  spacing_large: 24
  border_radius: 8

performance:
  refresh_interval_ms: 5000
  chart_update_interval_ms: 1000
  max_log_entries: 1000
  chart_max_points: 100
```

## 📦 Dependencies for PySide6

```python
# requirements.txt additions for PySide6 UI
PySide6>=6.9.1
PySide6-Essentials>=6.9.1
PySide6-Addons>=6.9.1
```

## 🔧 Qt Standard Paths Integration for Native Desktop Applications

The RS Personal Agent uses Qt's QStandardPaths for proper cross-platform database and configuration storage, following desktop application best practices.

### Qt Standard Paths Implementation

**Production Storage Locations (using QStandardPaths.AppLocalDataLocation):**
- **Windows**: `%LOCALAPPDATA%\Roostership\RSPersonalAgent\`
- **macOS**: `~/Library/Application Support/RSPersonalAgent/`  
- **Linux**: `~/.local/share/RSPersonalAgent/`

**Development Mode**: Uses `./data/` when `RSPA_DATABASE_DEV_MODE=true`

**Qt-Native Implementation:**
```python
from PySide6.QtCore import QStandardPaths, QDir
from pathlib import Path

class DatabaseManager:
    def __init__(self):
        # Use Qt's platform-appropriate app data location
        app_data_location = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        
        # Create directory using Qt's directory management
        app_dir = QDir(app_data_location)
        if not app_dir.exists():
            app_dir.mkpath(".")
            
        # Set database path
        self.db_path = Path(app_data_location) / "main.db"
        self.cache_path = Path(app_data_location) / "cache.db"
        self.backup_dir = Path(app_data_location) / "backups"
        
    def get_database_url(self) -> str:
        """Get SQLAlchemy database URL"""
        return f"sqlite:///{self.db_path}"
```

**Cross-Platform Storage Locations with Qt Application Setup:**
Requires proper Qt application configuration:
```python
QCoreApplication.setOrganizationName("Roostership")
QCoreApplication.setApplicationName("RSPersonalAgent")
```

This produces:
- **Windows**: `%LOCALAPPDATA%\Roostership\RSPersonalAgent\`
- **macOS**: `~/Library/Application Support/RSPersonalAgent/`  
- **Linux**: `~/.local/share/RSPersonalAgent/`

**Benefits of Qt Standard Paths:**
1. **Platform Compliance**: Follows OS-specific conventions (Registry on Windows, plist on macOS)
2. **User Separation**: Proper isolation between user accounts
3. **Professional Integration**: Works with system backup tools and OS-specific behaviors
4. **Permissions**: Guarantees write permissions in returned locations
5. **Future Compatibility**: Handles OS changes automatically
6. **Deployment Independence**: Database location independent of executable location

**Native Desktop Application Benefits:**
- System tray integration capabilities
- Native theming and OS integration  
- Professional desktop packaging and distribution
- Qt Model-View architecture for responsive UI updates
- Cross-platform keyboard shortcuts and accessibility support

This implementation follows Qt documentation recommendations and ensures professional desktop application behavior across Windows, macOS, and Linux platforms.

## 🚀 Next Steps for PySide6 Implementation

1. **Core Qt Infrastructure**
   - Implement QApplication setup and main window
   - Create base widget classes and theme management
   - Set up Model-View architecture for agent data
   - Implement Qt-based configuration system

2. **Agent Management Interface**
   - Build agent card widgets and table views
   - Create agent control dialogs and forms
   - Implement real-time status updates using Qt signals
   - Add agent configuration and editing capabilities

3. **Advanced Features**
   - Performance monitoring with native Qt charts
   - Log viewer with filtering and search capabilities
   - System tray integration for background operation
   - Export functionality using Qt file dialogs

This comprehensive PySide6-based UI design provides a professional, native desktop interface that fully integrates with the existing core infrastructure while following Qt best practices and modern desktop application standards.