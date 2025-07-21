# UI Design - RS Personal Assistant Agent Admin Panel

## 📋 Overview

This document details the user interface design and implementation guidelines for the RS Personal Assistant Agent Admin Panel. The UI provides a modern, sleek interface for managing AI agents, monitoring their status, viewing outputs, and analyzing performance metrics in real-time using Python's CustomTkinter framework.

## 🎨 Design Philosophy

### Visual Language
- **Modern & Clean**: Minimalist design with rounded corners and smooth transitions
- **Dark/Light Theme Support**: System-adaptive theming with manual override
- **High Contrast**: Clear visual hierarchy with proper spacing and typography
- **Responsive Layout**: Adapts to different screen sizes and resolutions
- **Real-time Updates**: Live data visualization without flickering or lag

### User Experience Principles
1. **Intuitive Navigation**: Clear visual cues and logical grouping
2. **Minimal Clicks**: Common actions accessible within 2 clicks
3. **Visual Feedback**: Immediate response to user interactions
4. **Progressive Disclosure**: Advanced features hidden by default
5. **Consistency**: Uniform interaction patterns across all components

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Application Window                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌─────────────────────────────────────────┐  │
│  │          │  │                                         │  │
│  │   Side   │  │           Main Content Area             │  │
│  │   Panel  │  │                                         │  │
│  │          │  │  ┌─────────────┐  ┌──────────────────┐  │  │
│  │ - Agents │  │  │   Agent     │  │     Timeline     │  │  │
│  │ - Stats  │  │  │   Cards     │  │     View         │  │  │
│  │ - Config │  │  └─────────────┘  └──────────────────┘  │  │
│  │          │  │                                         │  │
│  │          │  │  ┌────────────────────────────────────┐ │  │
│  │          │  │  │        Output/Logs Panel           │ │  │
│  │          │  │  └────────────────────────────────────┘ │  │
│  └──────────┘  └─────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Status Bar                             │
└─────────────────────────────────────────────────────────────┘
```

## 🧩 Component Library

### Base Components

#### 1. Theme Manager (`ui/components/theme_manager.py`)
```python
import customtkinter as ctk
from typing import Dict, Any, Callable, List
import json
from pathlib import Path

class ThemeManager:
    """Centralized theme management for the application"""
    
    # Default color schemes
    THEMES = {
        "dark": {
            "bg_color": "#0F0F0F",
            "fg_color": "#1A1A1A", 
            "hover_color": "#2A2A2A",
            "button_fg_color": "#2563EB",
            "button_hover_color": "#1D4ED8",
            "success_color": "#10B981",
            "warning_color": "#F59E0B",
            "error_color": "#EF4444",
            "text_color": "#FFFFFF",
            "text_secondary": "#9CA3AF",
            "border_color": "#374151",
            "card_bg": "#1F2937",
            "accent_color": "#6366F1"
        },
        "light": {
            "bg_color": "#F9FAFB",
            "fg_color": "#FFFFFF",
            "hover_color": "#F3F4F6",
            "button_fg_color": "#3B82F6",
            "button_hover_color": "#2563EB",
            "success_color": "#34D399",
            "warning_color": "#FBBF24",
            "error_color": "#F87171",
            "text_color": "#111827",
            "text_secondary": "#6B7280",
            "border_color": "#E5E7EB",
            "card_bg": "#FFFFFF",
            "accent_color": "#818CF8"
        }
    }
    
    def __init__(self):
        self.current_theme = "dark"
        self.theme_callbacks: List[Callable] = []
        self.custom_themes = self._load_custom_themes()
        
    def _load_custom_themes(self) -> Dict[str, Dict[str, str]]:
        """Load custom themes from configuration"""
        theme_file = Path("config/themes.json")
        if theme_file.exists():
            with open(theme_file) as f:
                return json.load(f)
        return {}
    
    def get_theme(self) -> Dict[str, str]:
        """Get current theme colors"""
        if self.current_theme in self.custom_themes:
            return self.custom_themes[self.current_theme]
        return self.THEMES.get(self.current_theme, self.THEMES["dark"])
    
    def set_theme(self, theme_name: str):
        """Set application theme"""
        if theme_name in self.THEMES or theme_name in self.custom_themes:
            self.current_theme = theme_name
            self._apply_theme()
            self._notify_callbacks()
    
    def _apply_theme(self):
        """Apply theme to CustomTkinter"""
        theme = self.get_theme()
        ctk.set_appearance_mode(self.current_theme)
        
        # Update default colors
        ctk.set_default_color_theme({
            "CTk": {
                "fg_color": [theme["fg_color"], theme["fg_color"]],
                "bg_color": [theme["bg_color"], theme["bg_color"]],
                "hover_color": [theme["hover_color"], theme["hover_color"]],
                "border_color": [theme["border_color"], theme["border_color"]],
                "text_color": [theme["text_color"], theme["text_color"]]
            }
        })
    
    def register_callback(self, callback: Callable):
        """Register callback for theme changes"""
        self.theme_callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of theme change"""
        for callback in self.theme_callbacks:
            callback(self.current_theme, self.get_theme())
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.set_theme("light" if self.current_theme == "dark" else "dark")

# Global theme manager instance
theme_manager = ThemeManager()
```

#### 2. Card Component (`ui/components/card.py`)
```python
import customtkinter as ctk
from typing import Optional, Callable, Tuple
from ui.components.theme_manager import theme_manager

class Card(ctk.CTkFrame):
    """Modern card component with rounded corners and shadow effect"""
    
    def __init__(
        self,
        parent,
        title: str = "",
        subtitle: str = "",
        width: int = 300,
        height: int = 200,
        corner_radius: int = 15,
        border_width: int = 1,
        clickable: bool = False,
        on_click: Optional[Callable] = None,
        **kwargs
    ):
        theme = theme_manager.get_theme()
        
        super().__init__(
            parent,
            width=width,
            height=height,
            corner_radius=corner_radius,
            border_width=border_width,
            fg_color=theme["card_bg"],
            border_color=theme["border_color"],
            **kwargs
        )
        
        self.title = title
        self.subtitle = subtitle
        self.clickable = clickable
        self.on_click = on_click
        self.theme = theme
        
        self._setup_ui()
        
        if clickable:
            self._setup_hover_effects()
            if on_click:
                self.bind("<Button-1>", lambda e: on_click())
    
    def _setup_ui(self):
        """Set up card UI elements"""
        # Title
        if self.title:
            self.title_label = ctk.CTkLabel(
                self,
                text=self.title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=self.theme["text_color"],
                anchor="w"
            )
            self.title_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        # Subtitle
        if self.subtitle:
            self.subtitle_label = ctk.CTkLabel(
                self,
                text=self.subtitle,
                font=ctk.CTkFont(size=12),
                text_color=self.theme["text_secondary"],
                anchor="w"
            )
            self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Content frame
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.content_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _setup_hover_effects(self):
        """Set up hover effects for clickable cards"""
        def on_enter(e):
            self.configure(
                fg_color=self.theme["hover_color"],
                border_color=self.theme["accent_color"]
            )
            self.configure(cursor="hand2")
        
        def on_leave(e):
            self.configure(
                fg_color=self.theme["card_bg"],
                border_color=self.theme["border_color"]
            )
            self.configure(cursor="")
        
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
    
    def add_content(self, widget):
        """Add content widget to the card"""
        widget.grid(in_=self.content_frame, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
```

#### 3. Agent Card (`ui/components/agent_card.py`)
```python
import customtkinter as ctk
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from ui.components.card import Card
from ui.components.theme_manager import theme_manager
from models.agent import AgentStatus

class AgentCard(Card):
    """Specialized card for displaying agent information"""
    
    def __init__(
        self,
        parent,
        agent_data: Dict[str, Any],
        on_launch: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_view_logs: Optional[Callable] = None,
        **kwargs
    ):
        self.agent_data = agent_data
        self.on_launch = on_launch
        self.on_stop = on_stop
        self.on_view_logs = on_view_logs
        
        super().__init__(
            parent,
            title=agent_data.get("name", "Unknown Agent"),
            subtitle=agent_data.get("description", ""),
            width=350,
            height=220,
            clickable=True,
            on_click=self._on_card_click,
            **kwargs
        )
        
        self._setup_agent_ui()
        self._update_status()
    
    def _setup_agent_ui(self):
        """Set up agent-specific UI elements"""
        theme = theme_manager.get_theme()
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )
        self.status_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            width=20
        )
        self.status_indicator.grid(row=0, column=0, padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=self.agent_data.get("status", "Unknown"),
            font=ctk.CTkFont(size=12),
            text_color=theme["text_secondary"]
        )
        self.status_label.grid(row=0, column=1, sticky="w")
        
        # Stats frame
        self.stats_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=10)
        
        # Execution count
        self.exec_count_label = ctk.CTkLabel(
            self.stats_frame,
            text=f"Executions: {self.agent_data.get('execution_count', 0)}",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"]
        )
        self.exec_count_label.grid(row=0, column=0, sticky="w")
        
        # Last execution
        last_exec = self.agent_data.get("last_execution")
        if last_exec:
            last_exec_str = self._format_time_ago(last_exec)
        else:
            last_exec_str = "Never"
        
        self.last_exec_label = ctk.CTkLabel(
            self.stats_frame,
            text=f"Last run: {last_exec_str}",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"]
        )
        self.last_exec_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        # Action buttons
        self.button_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(10, 0))
        
        self.launch_button = ctk.CTkButton(
            self.button_frame,
            text="Launch",
            width=80,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color=theme["button_fg_color"],
            hover_color=theme["button_hover_color"],
            command=self._on_launch_click
        )
        self.launch_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ctk.CTkButton(
            self.button_frame,
            text="Stop",
            width=60,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color=theme["error_color"],
            hover_color=theme["error_color"],
            command=self._on_stop_click,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(0, 5))
        
        self.logs_button = ctk.CTkButton(
            self.button_frame,
            text="Logs",
            width=60,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color=theme["fg_color"],
            hover_color=theme["hover_color"],
            text_color=theme["text_color"],
            command=self._on_logs_click
        )
        self.logs_button.grid(row=0, column=2)
    
    def _update_status(self):
        """Update status indicator and buttons based on agent status"""
        theme = theme_manager.get_theme()
        status = self.agent_data.get("status", "UNKNOWN")
        
        # Update status indicator color
        status_colors = {
            "IDLE": theme["success_color"],
            "ACTIVE": theme["warning_color"],
            "ERROR": theme["error_color"],
            "REGISTERED": theme["text_secondary"]
        }
        
        color = status_colors.get(status, theme["text_secondary"])
        self.status_indicator.configure(text_color=color)
        self.status_label.configure(text=status)
        
        # Update button states
        if status == "ACTIVE":
            self.launch_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
        else:
            self.launch_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
    
    def _format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as time ago"""
        try:
            dt = datetime.fromisoformat(timestamp)
            delta = datetime.now() - dt
            
            if delta.days > 0:
                return f"{delta.days}d ago"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600}h ago"
            elif delta.seconds > 60:
                return f"{delta.seconds // 60}m ago"
            else:
                return "Just now"
        except:
            return "Unknown"
    
    def _on_card_click(self):
        """Handle card click"""
        # Could show detailed agent view
        pass
    
    def _on_launch_click(self):
        """Handle launch button click"""
        if self.on_launch:
            self.on_launch(self.agent_data["agent_id"])
    
    def _on_stop_click(self):
        """Handle stop button click"""
        if self.on_stop:
            self.on_stop(self.agent_data["agent_id"])
    
    def _on_logs_click(self):
        """Handle logs button click"""
        if self.on_view_logs:
            self.on_view_logs(self.agent_data["agent_id"])
    
    def update_agent_data(self, agent_data: Dict[str, Any]):
        """Update agent data and refresh UI"""
        self.agent_data = agent_data
        self.title_label.configure(text=agent_data.get("name", "Unknown Agent"))
        self.subtitle_label.configure(text=agent_data.get("description", ""))
        self.exec_count_label.configure(text=f"Executions: {agent_data.get('execution_count', 0)}")
        
        last_exec = agent_data.get("last_execution")
        if last_exec:
            last_exec_str = self._format_time_ago(last_exec)
        else:
            last_exec_str = "Never"
        self.last_exec_label.configure(text=f"Last run: {last_exec_str}")
        
        self._update_status()
```

#### 4. Real-time Chart Component (`ui/components/realtime_chart.py`)
```python
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from collections import deque
from typing import Optional, Callable, Tuple, List
import numpy as np
from ui.components.theme_manager import theme_manager

class RealtimeChart(ctk.CTkFrame):
    """Real-time updating chart component using matplotlib"""
    
    def __init__(
        self,
        parent,
        title: str = "Chart",
        xlabel: str = "Time",
        ylabel: str = "Value",
        max_points: int = 100,
        update_interval: int = 1000,  # milliseconds
        data_source: Optional[Callable[[], Tuple[float, float]]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.max_points = max_points
        self.update_interval = update_interval
        self.data_source = data_source
        
        # Data storage
        self.x_data = deque(maxlen=max_points)
        self.y_data = deque(maxlen=max_points)
        
        # Apply theme
        self.theme = theme_manager.get_theme()
        theme_manager.register_callback(self._on_theme_change)
        
        self._setup_chart()
        
        if data_source:
            self.start_animation()
    
    def _setup_chart(self):
        """Set up matplotlib chart"""
        # Configure matplotlib style for dark theme
        plt.style.use('dark_background' if theme_manager.current_theme == "dark" else 'default')
        
        # Create figure
        self.figure = Figure(figsize=(6, 4), dpi=100, tight_layout=True)
        self.figure.patch.set_facecolor(self.theme["card_bg"])
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(self.theme["card_bg"])
        
        # Set labels and title
        self.ax.set_title(self.title, color=self.theme["text_color"], fontsize=12, pad=10)
        self.ax.set_xlabel(self.xlabel, color=self.theme["text_secondary"], fontsize=10)
        self.ax.set_ylabel(self.ylabel, color=self.theme["text_secondary"], fontsize=10)
        
        # Configure grid
        self.ax.grid(True, alpha=0.2, color=self.theme["border_color"])
        
        # Configure spines
        for spine in self.ax.spines.values():
            spine.set_color(self.theme["border_color"])
            spine.set_linewidth(0.5)
        
        # Configure tick colors
        self.ax.tick_params(colors=self.theme["text_secondary"], labelsize=9)
        
        # Initialize line
        self.line, = self.ax.plot([], [], color=self.theme["accent_color"], linewidth=2)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _on_theme_change(self, theme_name: str, theme: Dict[str, str]):
        """Handle theme change"""
        self.theme = theme
        self._update_chart_style()
    
    def _update_chart_style(self):
        """Update chart colors based on theme"""
        # Update figure background
        self.figure.patch.set_facecolor(self.theme["card_bg"])
        self.ax.set_facecolor(self.theme["card_bg"])
        
        # Update text colors
        self.ax.title.set_color(self.theme["text_color"])
        self.ax.xaxis.label.set_color(self.theme["text_secondary"])
        self.ax.yaxis.label.set_color(self.theme["text_secondary"])
        
        # Update grid
        self.ax.grid(True, alpha=0.2, color=self.theme["border_color"])
        
        # Update spines
        for spine in self.ax.spines.values():
            spine.set_color(self.theme["border_color"])
        
        # Update tick colors
        self.ax.tick_params(colors=self.theme["text_secondary"])
        
        # Update line color
        self.line.set_color(self.theme["accent_color"])
        
        self.canvas.draw()
    
    def update_data(self, x: float, y: float):
        """Add new data point to the chart"""
        self.x_data.append(x)
        self.y_data.append(y)
        
        # Update line data
        self.line.set_data(list(self.x_data), list(self.y_data))
        
        # Adjust axes limits
        if self.x_data:
            self.ax.set_xlim(min(self.x_data), max(self.x_data))
            
            y_margin = 0.1 * (max(self.y_data) - min(self.y_data)) if len(self.y_data) > 1 else 1
            self.ax.set_ylim(min(self.y_data) - y_margin, max(self.y_data) + y_margin)
        
        self.canvas.draw()
    
    def _animate(self, frame):
        """Animation function for real-time updates"""
        if self.data_source:
            try:
                x, y = self.data_source()
                self.update_data(x, y)
            except Exception as e:
                print(f"Error updating chart: {e}")
    
    def start_animation(self):
        """Start real-time animation"""
        self.animation = FuncAnimation(
            self.figure,
            self._animate,
            interval=self.update_interval,
            blit=False,
            cache_frame_data=False
        )
    
    def stop_animation(self):
        """Stop real-time animation"""
        if hasattr(self, 'animation'):
            self.animation.event_source.stop()
    
    def clear_data(self):
        """Clear all data from the chart"""
        self.x_data.clear()
        self.y_data.clear()
        self.line.set_data([], [])
        self.canvas.draw()
```

#### 5. Log Viewer Component (`ui/components/log_viewer.py`)
```python
import customtkinter as ctk
from typing import List, Dict, Any, Optional
from datetime import datetime
from queue import Queue
import threading
from ui.components.theme_manager import theme_manager

class LogViewer(ctk.CTkFrame):
    """Scrollable log viewer with filtering and real-time updates"""
    
    LOG_LEVELS = {
        "DEBUG": {"color": "#6B7280", "symbol": "○"},
        "INFO": {"color": "#10B981", "symbol": "●"},
        "WARNING": {"color": "#F59E0B", "symbol": "▲"},
        "ERROR": {"color": "#EF4444", "symbol": "✗"}
    }
    
    def __init__(
        self,
        parent,
        max_lines: int = 1000,
        auto_scroll: bool = True,
        show_timestamp: bool = True,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.max_lines = max_lines
        self.auto_scroll = auto_scroll
        self.show_timestamp = show_timestamp
        self.log_queue = Queue()
        self.theme = theme_manager.get_theme()
        
        self._setup_ui()
        self._start_log_processor()
    
    def _setup_ui(self):
        """Set up log viewer UI"""
        # Header with controls
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.header_frame.grid_propagate(False)
        
        # Filter dropdown
        self.filter_var = ctk.StringVar(value="ALL")
        self.filter_dropdown = ctk.CTkOptionMenu(
            self.header_frame,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
            variable=self.filter_var,
            command=self._on_filter_change,
            width=100,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(size=12)
        )
        self.filter_dropdown.grid(row=0, column=0, padx=(0, 10))
        
        # Search entry
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="Search logs...",
            textvariable=self.search_var,
            width=200,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 10))
        self.search_var.trace("w", self._on_search_change)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.header_frame,
            text="Clear",
            width=60,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=self.clear_logs
        )
        self.clear_button.grid(row=0, column=2)
        
        # Auto-scroll toggle
        self.auto_scroll_var = ctk.BooleanVar(value=self.auto_scroll)
        self.auto_scroll_check = ctk.CTkCheckBox(
            self.header_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            onvalue=True,
            offvalue=False,
            command=self._toggle_auto_scroll,
            width=100,
            height=28,
            font=ctk.CTkFont(size=12)
        )
        self.auto_scroll_check.grid(row=0, column=3, padx=(10, 0))
        
        # Scrollable text widget
        self.text_frame = ctk.CTkFrame(self, corner_radius=10)
        self.text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        self.log_text = ctk.CTkTextbox(
            self.text_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=10,
            wrap="none"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Store log entries
        self.log_entries: List[Dict[str, Any]] = []
    
    def add_log(self, level: str, message: str, source: Optional[str] = None):
        """Add a log entry to the viewer"""
        timestamp = datetime.now()
        log_entry = {
            "timestamp": timestamp,
            "level": level.upper(),
            "message": message,
            "source": source
        }
        
        self.log_queue.put(log_entry)
    
    def _start_log_processor(self):
        """Start background thread to process log queue"""
        def process_logs():
            while True:
                try:
                    log_entry = self.log_queue.get(timeout=0.1)
                    self.after(0, self._add_log_entry, log_entry)
                except:
                    continue
        
        thread = threading.Thread(target=process_logs, daemon=True)
        thread.start()
    
    def _add_log_entry(self, log_entry: Dict[str, Any]):
        """Add log entry to the text widget"""
        # Store entry
        self.log_entries.append(log_entry)
        
        # Limit stored entries
        if len(self.log_entries) > self.max_lines:
            self.log_entries.pop(0)
            # Remove first line from text widget
            self.log_text.delete("1.0", "2.0")
        
        # Check if entry matches current filter
        if not self._matches_filter(log_entry):
            return
        
        # Format log entry
        formatted = self._format_log_entry(log_entry)
        
        # Add to text widget
        self.log_text.insert("end", formatted)
        
        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.log_text.see("end")
    
    def _format_log_entry(self, entry: Dict[str, Any]) -> str:
        """Format a log entry for display"""
        parts = []
        
        # Timestamp
        if self.show_timestamp:
            timestamp_str = entry["timestamp"].strftime("%H:%M:%S.%f")[:-3]
            parts.append(f"[{timestamp_str}]")
        
        # Level with symbol
        level = entry["level"]
        level_info = self.LOG_LEVELS.get(level, {"symbol": "●", "color": "#6B7280"})
        parts.append(f"{level_info['symbol']} {level:7}")
        
        # Source
        if entry.get("source"):
            parts.append(f"[{entry['source']}]")
        
        # Message
        parts.append(entry["message"])
        
        return " ".join(parts) + "\n"
    
    def _matches_filter(self, entry: Dict[str, Any]) -> bool:
        """Check if log entry matches current filter"""
        # Level filter
        filter_level = self.filter_var.get()
        if filter_level != "ALL" and entry["level"] != filter_level:
            return False
        
        # Search filter
        search_term = self.search_var.get().lower()
        if search_term:
            searchable = f"{entry.get('source', '')} {entry['message']}".lower()
            if search_term not in searchable:
                return False
        
        return True
    
    def _on_filter_change(self, *args):
        """Handle filter change"""
        self._refresh_display()
    
    def _on_search_change(self, *args):
        """Handle search change"""
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the log display with current filters"""
        self.log_text.delete("1.0", "end")
        
        for entry in self.log_entries:
            if self._matches_filter(entry):
                formatted = self._format_log_entry(entry)
                self.log_text.insert("end", formatted)
        
        if self.auto_scroll_var.get():
            self.log_text.see("end")
    
    def _toggle_auto_scroll(self):
        """Toggle auto-scroll behavior"""
        self.auto_scroll = self.auto_scroll_var.get()
        if self.auto_scroll:
            self.log_text.see("end")
    
    def clear_logs(self):
        """Clear all logs"""
        self.log_entries.clear()
        self.log_text.delete("1.0", "end")
    
    def save_logs(self, filepath: str):
        """Save logs to file"""
        with open(filepath, "w") as f:
            for entry in self.log_entries:
                formatted = self._format_log_entry(entry)
                f.write(formatted)
```

### Main Application Components

#### 6. Side Panel (`ui/components/side_panel.py`)
```python
import customtkinter as ctk
from typing import Dict, Any, List, Callable, Optional
from ui.components.theme_manager import theme_manager

class SidePanel(ctk.CTkFrame):
    """Collapsible side navigation panel"""
    
    def __init__(
        self,
        parent,
        width: int = 250,
        collapsed_width: int = 60,
        **kwargs
    ):
        super().__init__(parent, width=width, **kwargs)
        
        self.expanded_width = width
        self.collapsed_width = collapsed_width
        self.is_expanded = True
        self.theme = theme_manager.get_theme()
        
        self.configure(fg_color=self.theme["fg_color"])
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up side panel UI"""
        # Header with logo/title
        self.header_frame = ctk.CTkFrame(
            self,
            height=60,
            fg_color="transparent"
        )
        self.header_frame.pack(fill="x", padx=10, pady=10)
        self.header_frame.pack_propagate(False)
        
        # App title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="RS Assistant",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.theme["text_color"]
        )
        self.title_label.pack(side="left", padx=10)
        
        # Collapse button
        self.collapse_button = ctk.CTkButton(
            self.header_frame,
            text="◀",
            width=30,
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=self.theme["hover_color"],
            command=self.toggle_panel
        )
        self.collapse_button.pack(side="right")
        
        # Separator
        self.separator = ctk.CTkFrame(
            self,
            height=1,
            fg_color=self.theme["border_color"]
        )
        self.separator.pack(fill="x", padx=20, pady=(0, 10))
        
        # Navigation items container
        self.nav_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme["border_color"],
            scrollbar_button_hover_color=self.theme["accent_color"]
        )
        self.nav_frame.pack(fill="both", expand=True, padx=5)
        
        self.nav_items: List[NavigationItem] = []
    
    def add_navigation_item(
        self,
        icon: str,
        label: str,
        command: Optional[Callable] = None,
        badge_value: Optional[int] = None
    ) -> 'NavigationItem':
        """Add a navigation item to the panel"""
        nav_item = NavigationItem(
            self.nav_frame,
            icon=icon,
            label=label,
            command=command,
            badge_value=badge_value,
            is_expanded=self.is_expanded
        )
        nav_item.pack(fill="x", pady=2)
        self.nav_items.append(nav_item)
        return nav_item
    
    def add_section_header(self, title: str):
        """Add a section header"""
        if self.is_expanded:
            header = ctk.CTkLabel(
                self.nav_frame,
                text=title.upper(),
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.theme["text_secondary"],
                anchor="w"
            )
            header.pack(fill="x", padx=15, pady=(15, 5))
    
    def toggle_panel(self):
        """Toggle between expanded and collapsed states"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.configure(width=self.expanded_width)
            self.collapse_button.configure(text="◀")
            self.title_label.pack(side="left", padx=10)
        else:
            self.configure(width=self.collapsed_width)
            self.collapse_button.configure(text="▶")
            self.title_label.pack_forget()
        
        # Update navigation items
        for item in self.nav_items:
            item.set_expanded(self.is_expanded)
    
    def set_active_item(self, index: int):
        """Set the active navigation item"""
        for i, item in enumerate(self.nav_items):
            item.set_active(i == index)


class NavigationItem(ctk.CTkFrame):
    """Individual navigation item in side panel"""
    
    def __init__(
        self,
        parent,
        icon: str,
        label: str,
        command: Optional[Callable] = None,
        badge_value: Optional[int] = None,
        is_expanded: bool = True,
        **kwargs
    ):
        super().__init__(parent, height=45, corner_radius=10, **kwargs)
        
        self.icon = icon
        self.label = label
        self.command = command
        self.badge_value = badge_value
        self.is_expanded = is_expanded
        self.is_active = False
        self.theme = theme_manager.get_theme()
        
        self.configure(fg_color="transparent")
        self.pack_propagate(False)
        
        self._setup_ui()
        self._setup_hover_effects()
    
    def _setup_ui(self):
        """Set up navigation item UI"""
        # Icon
        self.icon_label = ctk.CTkLabel(
            self,
            text=self.icon,
            font=ctk.CTkFont(size=20),
            width=40
        )
        self.icon_label.pack(side="left", padx=(10, 5))
        
        if self.is_expanded:
            # Label
            self.text_label = ctk.CTkLabel(
                self,
                text=self.label,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            self.text_label.pack(side="left", fill="x", expand=True)
            
            # Badge
            if self.badge_value is not None:
                self.badge_label = ctk.CTkLabel(
                    self,
                    text=str(self.badge_value),
                    font=ctk.CTkFont(size=11),
                    width=25,
                    height=20,
                    corner_radius=10,
                    fg_color=self.theme["accent_color"],
                    text_color="white"
                )
                self.badge_label.pack(side="right", padx=10)
    
    def _setup_hover_effects(self):
        """Set up hover effects"""
        def on_enter(e):
            if not self.is_active:
                self.configure(fg_color=self.theme["hover_color"])
        
        def on_leave(e):
            if not self.is_active:
                self.configure(fg_color="transparent")
        
        def on_click(e):
            if self.command:
                self.command()
        
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
        self.bind("<Button-1>", on_click)
        
        # Bind to all child widgets
        for child in self.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", on_click)
    
    def set_expanded(self, expanded: bool):
        """Update item for expanded/collapsed state"""
        self.is_expanded = expanded
        
        # Clear current UI
        for widget in self.winfo_children():
            widget.destroy()
        
        # Rebuild UI
        self._setup_ui()
        self._setup_hover_effects()
    
    def set_active(self, active: bool):
        """Set item as active/inactive"""
        self.is_active = active
        if active:
            self.configure(fg_color=self.theme["accent_color"])
            if hasattr(self, 'text_label'):
                self.text_label.configure(text_color="white")
            self.icon_label.configure(text_color="white")
        else:
            self.configure(fg_color="transparent")
            if hasattr(self, 'text_label'):
                self.text_label.configure(text_color=self.theme["text_color"])
            self.icon_label.configure(text_color=self.theme["text_color"])
    
    def update_badge(self, value: Optional[int]):
        """Update badge value"""
        self.badge_value = value
        if hasattr(self, 'badge_label'):
            if value is not None:
                self.badge_label.configure(text=str(value))
                self.badge_label.pack(side="right", padx=10)
            else:
                self.badge_label.pack_forget()
```

#### 7. Agent Timeline View (`ui/components/timeline_view.py`)
```python
import customtkinter as ctk
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from ui.components.theme_manager import theme_manager
from ui.components.card import Card

class TimelineView(Card):
    """Timeline view showing agent execution history and schedule"""
    
    def __init__(
        self,
        parent,
        hours_to_show: int = 24,
        **kwargs
    ):
        super().__init__(
            parent,
            title="Agent Timeline",
            subtitle=f"Last {hours_to_show} hours",
            height=300,
            **kwargs
        )
        
        self.hours_to_show = hours_to_show
        self.timeline_data: Dict[str, List[Dict[str, Any]]] = {}
        self.theme = theme_manager.get_theme()
        
        self._setup_timeline_ui()
    
    def _setup_timeline_ui(self):
        """Set up timeline UI components"""
        # Timeline canvas
        self.canvas = ctk.CTkCanvas(
            self.content_frame,
            bg=self.theme["card_bg"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind resize event
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Time axis labels
        self.time_labels = []
        
        # Initial draw
        self.after(100, self._draw_timeline)
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize"""
        self._draw_timeline()
    
    def _draw_timeline(self):
        """Draw the timeline visualization"""
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width < 2 or height < 2:
            return
        
        # Calculate dimensions
        margin_left = 100
        margin_right = 20
        margin_top = 30
        margin_bottom = 40
        
        timeline_width = width - margin_left - margin_right
        timeline_height = height - margin_top - margin_bottom
        
        # Draw time axis
        self._draw_time_axis(
            margin_left, margin_top, 
            timeline_width, timeline_height
        )
        
        # Draw agent rows
        self._draw_agent_rows(
            margin_left, margin_top,
            timeline_width, timeline_height
        )
        
        # Draw events
        self._draw_events(
            margin_left, margin_top,
            timeline_width, timeline_height
        )
    
    def _draw_time_axis(self, x: int, y: int, width: int, height: int):
        """Draw time axis with labels"""
        # Horizontal axis line
        self.canvas.create_line(
            x, y + height,
            x + width, y + height,
            fill=self.theme["border_color"],
            width=1
        )
        
        # Time markers
        now = datetime.now()
        start_time = now - timedelta(hours=self.hours_to_show)
        
        # Draw hour markers
        for i in range(self.hours_to_show + 1):
            time_offset = i * (width / self.hours_to_show)
            marker_x = x + time_offset
            
            # Vertical line
            self.canvas.create_line(
                marker_x, y + height - 5,
                marker_x, y + height + 5,
                fill=self.theme["border_color"],
                width=1
            )
            
            # Time label
            marker_time = start_time + timedelta(hours=i)
            time_str = marker_time.strftime("%H:%M")
            
            self.canvas.create_text(
                marker_x, y + height + 15,
                text=time_str,
                fill=self.theme["text_secondary"],
                font=("Arial", 9),
                anchor="n"
            )
    
    def _draw_agent_rows(self, x: int, y: int, width: int, height: int):
        """Draw horizontal rows for each agent"""
        agents = list(self.timeline_data.keys())
        if not agents:
            # Show empty state
            self.canvas.create_text(
                x + width / 2, y + height / 2,
                text="No agent activity to display",
                fill=self.theme["text_secondary"],
                font=("Arial", 12),
                anchor="center"
            )
            return
        
        row_height = height / len(agents)
        
        for i, agent_name in enumerate(agents):
            row_y = y + i * row_height
            
            # Agent name label
            self.canvas.create_text(
                x - 10, row_y + row_height / 2,
                text=agent_name,
                fill=self.theme["text_color"],
                font=("Arial", 10),
                anchor="e"
            )
            
            # Horizontal separator
            if i > 0:
                self.canvas.create_line(
                    x, row_y,
                    x + width, row_y,
                    fill=self.theme["border_color"],
                    width=1,
                    dash=(2, 2)
                )
    
    def _draw_events(self, x: int, y: int, width: int, height: int):
        """Draw event blocks on the timeline"""
        now = datetime.now()
        start_time = now - timedelta(hours=self.hours_to_show)
        time_range = self.hours_to_show * 3600  # seconds
        
        agents = list(self.timeline_data.keys())
        if not agents:
            return
        
        row_height = height / len(agents)
        
        for i, agent_name in enumerate(agents):
            events = self.timeline_data.get(agent_name, [])
            row_y = y + i * row_height
            
            for event in events:
                # Calculate event position
                event_start = event["start_time"]
                event_end = event.get("end_time", now)
                
                # Skip events outside the visible range
                if event_end < start_time or event_start > now:
                    continue
                
                # Clamp to visible range
                visible_start = max(event_start, start_time)
                visible_end = min(event_end, now)
                
                # Calculate pixel positions
                start_offset = (visible_start - start_time).total_seconds()
                end_offset = (visible_end - start_time).total_seconds()
                
                start_x = x + (start_offset / time_range) * width
                end_x = x + (end_offset / time_range) * width
                
                # Draw event block
                block_height = row_height * 0.6
                block_y = row_y + (row_height - block_height) / 2
                
                # Determine color based on status
                status = event.get("status", "running")
                colors = {
                    "completed": self.theme["success_color"],
                    "running": self.theme["warning_color"],
                    "failed": self.theme["error_color"]
                }
                color = colors.get(status, self.theme["accent_color"])
                
                # Draw rectangle
                rect_id = self.canvas.create_rectangle(
                    start_x, block_y,
                    end_x, block_y + block_height,
                    fill=color,
                    outline="",
                    tags=("event",)
                )
                
                # Store event data for tooltip
                self.canvas.tag_bind(
                    rect_id,
                    "<Enter>",
                    lambda e, ev=event: self._show_event_tooltip(e, ev)
                )
                self.canvas.tag_bind(
                    rect_id,
                    "<Leave>",
                    lambda e: self._hide_event_tooltip()
                )
    
    def _show_event_tooltip(self, event, event_data: Dict[str, Any]):
        """Show tooltip for event"""
        # Implementation for tooltip display
        pass
    
    def _hide_event_tooltip(self):
        """Hide event tooltip"""
        # Implementation for tooltip hiding
        pass
    
    def update_timeline_data(self, agent_name: str, events: List[Dict[str, Any]]):
        """Update timeline data for an agent"""
        self.timeline_data[agent_name] = events
        self._draw_timeline()
    
    def add_event(self, agent_name: str, event: Dict[str, Any]):
        """Add a single event to the timeline"""
        if agent_name not in self.timeline_data:
            self.timeline_data[agent_name] = []
        
        self.timeline_data[agent_name].append(event)
        self._draw_timeline()
    
    def clear_timeline(self):
        """Clear all timeline data"""
        self.timeline_data.clear()
        self._draw_timeline()
```

### Main Application Window

#### 8. Agent Admin Dashboard (`ui/agent_admin_dashboard.py`)
```python
import customtkinter as ctk
from typing import Dict, Any, List, Optional
import threading
import time
from datetime import datetime
from queue import Queue

from ui.components.theme_manager import theme_manager
from ui.components.side_panel import SidePanel
from ui.components.agent_card import AgentCard
from ui.components.realtime_chart import RealtimeChart
from ui.components.log_viewer import LogViewer
from ui.components.timeline_view import TimelineView
from ui.components.card import Card

from core.agent_manager import AgentManager
from core.database import DatabaseManager
from core.llm_manager import LLMManager
from core.config_manager import ConfigManager

class AgentAdminDashboard(ctk.CTk):
    """Main application window for Agent Admin Panel"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("RS Personal Assistant - Agent Admin Panel")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
        # Initialize core components
        self._init_core_components()
        
        # Apply theme
        theme_manager.set_theme("dark")
        
        # Set up UI
        self._setup_ui()
        
        # Start background tasks
        self._start_background_tasks()
        
        # Load initial data
        self._load_initial_data()
    
    def _init_core_components(self):
        """Initialize core system components"""
        self.db_manager = DatabaseManager()
        self.llm_manager = LLMManager()
        self.config_manager = ConfigManager()
        self.agent_manager = AgentManager(
            self.db_manager,
            self.llm_manager,
            self.config_manager
        )
        
        # Data storage
        self.agent_cards: Dict[str, AgentCard] = {}
        self.update_queue = Queue()
    
    def _setup_ui(self):
        """Set up the main UI layout"""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Side panel
        self.side_panel = SidePanel(self)
        self.side_panel.grid(row=0, column=0, sticky="ns")
        
        self._setup_navigation()
        
        # Main content area
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=theme_manager.get_theme()["bg_color"]
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        
        # Content pages
        self.content_frames = {}
        self._setup_content_pages()
        
        # Status bar
        self._setup_status_bar()
        
        # Show default page
        self._show_page("agents")
    
    def _setup_navigation(self):
        """Set up navigation items in side panel"""
        # Main navigation
        self.side_panel.add_navigation_item(
            icon="🤖",
            label="Agents",
            command=lambda: self._show_page("agents"),
            badge_value=None
        )
        
        self.side_panel.add_navigation_item(
            icon="📊",
            label="Dashboard",
            command=lambda: self._show_page("dashboard")
        )
        
        self.side_panel.add_navigation_item(
            icon="📋",
            label="Logs",
            command=lambda: self._show_page("logs")
        )
        
        self.side_panel.add_navigation_item(
            icon="⏱️",
            label="Timeline",
            command=lambda: self._show_page("timeline")
        )
        
        # Settings section
        self.side_panel.add_section_header("Settings")
        
        self.side_panel.add_navigation_item(
            icon="⚙️",
            label="Configuration",
            command=lambda: self._show_page("config")
        )
        
        self.side_panel.add_navigation_item(
            icon="🎨",
            label="Theme",
            command=self._toggle_theme
        )
        
        # Set first item as active
        self.side_panel.set_active_item(0)
    
    def _setup_content_pages(self):
        """Set up different content pages"""
        # Agents page
        self.content_frames["agents"] = self._create_agents_page()
        
        # Dashboard page
        self.content_frames["dashboard"] = self._create_dashboard_page()
        
        # Logs page
        self.content_frames["logs"] = self._create_logs_page()
        
        # Timeline page
        self.content_frames["timeline"] = self._create_timeline_page()
        
        # Config page
        self.content_frames["config"] = self._create_config_page()
    
    def _create_agents_page(self) -> ctk.CTkFrame:
        """Create agents management page"""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header_frame = ctk.CTkFrame(page, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Agent Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        # Launch all button
        launch_all_btn = ctk.CTkButton(
            header_frame,
            text="Launch All",
            width=100,
            height=35,
            corner_radius=8,
            command=self._launch_all_agents
        )
        launch_all_btn.pack(side="right", padx=(10, 0))
        
        # Stop all button
        stop_all_btn = ctk.CTkButton(
            header_frame,
            text="Stop All",
            width=100,
            height=35,
            corner_radius=8,
            fg_color=theme_manager.get_theme()["error_color"],
            command=self._stop_all_agents
        )
        stop_all_btn.pack(side="right")
        
        # Scrollable frame for agent cards
        self.agents_scroll = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent"
        )
        self.agents_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Grid configuration for cards
        self.agents_grid_frame = ctk.CTkFrame(
            self.agents_scroll,
            fg_color="transparent"
        )
        self.agents_grid_frame.pack(fill="both", expand=True)
        
        return page
    
    def _create_dashboard_page(self) -> ctk.CTkFrame:
        """Create dashboard overview page"""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header_frame = ctk.CTkFrame(page, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="System Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        # Stats cards row
        stats_frame = ctk.CTkFrame(page, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Create stat cards
        self._create_stat_card(stats_frame, "Total Agents", "0", "🤖").pack(side="left", padx=(0, 10))
        self._create_stat_card(stats_frame, "Active Agents", "0", "🟢").pack(side="left", padx=(0, 10))
        self._create_stat_card(stats_frame, "Tasks Today", "0", "📊").pack(side="left", padx=(0, 10))
        self._create_stat_card(stats_frame, "Success Rate", "0%", "✅").pack(side="left")
        
        # Charts row
        charts_frame = ctk.CTkFrame(page, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # CPU usage chart
        self.cpu_chart = RealtimeChart(
            charts_frame,
            title="System CPU Usage",
            ylabel="Usage %",
            max_points=60,
            update_interval=1000,
            data_source=self._get_cpu_usage
        )
        self.cpu_chart.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Memory usage chart
        self.memory_chart = RealtimeChart(
            charts_frame,
            title="Memory Usage",
            ylabel="MB",
            max_points=60,
            update_interval=1000,
            data_source=self._get_memory_usage
        )
        self.memory_chart.pack(side="left", fill="both", expand=True)
        
        return page
    
    def _create_logs_page(self) -> ctk.CTkFrame:
        """Create logs viewer page"""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header_frame = ctk.CTkFrame(page, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="System Logs",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        # Log viewer
        self.log_viewer = LogViewer(page)
        self.log_viewer.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        return page
    
    def _create_timeline_page(self) -> ctk.CTkFrame:
        """Create timeline view page"""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header_frame = ctk.CTkFrame(page, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Agent Timeline",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        # Timeline view
        self.timeline_view = TimelineView(page, hours_to_show=24)
        self.timeline_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        return page
    
    def _create_config_page(self) -> ctk.CTkFrame:
        """Create configuration page"""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header
        header_frame = ctk.CTkFrame(page, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Configuration",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        # Config sections
        config_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        config_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Add configuration sections here
        
        return page
    
    def _create_stat_card(self, parent, title: str, value: str, icon: str) -> Card:
        """Create a statistics card"""
        card = Card(parent, width=200, height=100)
        
        # Icon and value row
        content_frame = ctk.CTkFrame(card.content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icon,
            font=ctk.CTkFont(size=30)
        )
        icon_label.pack(side="left", padx=(10, 20))
        
        value_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        value_frame.pack(side="left", fill="both", expand=True)
        
        value_label = ctk.CTkLabel(
            value_frame,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(anchor="w")
        
        title_label = ctk.CTkLabel(
            value_frame,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=theme_manager.get_theme()["text_secondary"]
        )
        title_label.pack(anchor="w")
        
        return card
    
    def _setup_status_bar(self):
        """Set up status bar at bottom of window"""
        self.status_bar = ctk.CTkFrame(
            self,
            height=30,
            fg_color=theme_manager.get_theme()["fg_color"]
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_propagate(False)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=theme_manager.get_theme()["text_secondary"]
        )
        self.status_label.pack(side="left", padx=10)
        
        # Connection status
        self.connection_label = ctk.CTkLabel(
            self.status_bar,
            text="● Connected to Ollama",
            font=ctk.CTkFont(size=11),
            text_color=theme_manager.get_theme()["success_color"]
        )
        self.connection_label.pack(side="right", padx=10)
    
    def _show_page(self, page_name: str):
        """Show specific content page"""
        # Hide all pages
        for frame in self.content_frames.values():
            frame.pack_forget()
        
        # Show selected page
        if page_name in self.content_frames:
            self.content_frames[page_name].pack(fill="both", expand=True)
        
        # Update navigation
        page_indices = {
            "agents": 0,
            "dashboard": 1,
            "logs": 2,
            "timeline": 3,
            "config": 4
        }
        if page_name in page_indices:
            self.side_panel.set_active_item(page_indices[page_name])
    
    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        theme_manager.toggle_theme()
        
        # Update status
        self.status_label.configure(text=f"Theme changed to {theme_manager.current_theme}")
    
    def _load_initial_data(self):
        """Load initial agent data"""
        agents = self.agent_manager.list_agents()
        
        # Clear existing cards
        for card in self.agent_cards.values():
            card.destroy()
        self.agent_cards.clear()
        
        # Create agent cards
        for i, agent_data in enumerate(agents):
            agent_id = agent_data["agent_id"]
            card = AgentCard(
                self.agents_grid_frame,
                agent_data,
                on_launch=self._launch_agent,
                on_stop=self._stop_agent,
                on_view_logs=self._view_agent_logs
            )
            
            # Grid layout
            row = i // 3
            col = i % 3
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            self.agent_cards[agent_id] = card
        
        # Configure grid weights
        for i in range(3):
            self.agents_grid_frame.grid_columnconfigure(i, weight=1)
    
    def _launch_agent(self, agent_id: str):
        """Launch specific agent"""
        self.agent_manager.start_agent(agent_id)
        self.log_viewer.add_log("INFO", f"Launching agent: {agent_id}", "System")
        
        # Update UI will happen through background task
    
    def _stop_agent(self, agent_id: str):
        """Stop specific agent"""
        self.agent_manager.stop_agent(agent_id)
        self.log_viewer.add_log("INFO", f"Stopping agent: {agent_id}", "System")
    
    def _launch_all_agents(self):
        """Launch all registered agents"""
        for agent_id in self.agent_cards:
            self._launch_agent(agent_id)
    
    def _stop_all_agents(self):
        """Stop all running agents"""
        for agent_id in self.agent_cards:
            self._stop_agent(agent_id)
    
    def _view_agent_logs(self, agent_id: str):
        """View logs for specific agent"""
        self._show_page("logs")
        # Could filter logs by agent
    
    def _start_background_tasks(self):
        """Start background update tasks"""
        # Agent status updater
        def update_agent_status():
            while True:
                try:
                    # Get latest agent statuses
                    agents = self.agent_manager.list_agents()
                    self.update_queue.put(("agents", agents))
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    print(f"Error updating agent status: {e}")
        
        # Timeline updater
        def update_timeline():
            while True:
                try:
                    # Get agent execution history
                    timeline_data = self.agent_manager.get_timeline_data()
                    self.update_queue.put(("timeline", timeline_data))
                    time.sleep(5)  # Update every 5 seconds
                except Exception as e:
                    print(f"Error updating timeline: {e}")
        
        # Start threads
        threading.Thread(target=update_agent_status, daemon=True).start()
        threading.Thread(target=update_timeline, daemon=True).start()
        
        # Process updates in main thread
        self._process_updates()
    
    def _process_updates(self):
        """Process updates from background tasks"""
        try:
            while not self.update_queue.empty():
                update_type, data = self.update_queue.get_nowait()
                
                if update_type == "agents":
                    # Update agent cards
                    for agent_data in data:
                        agent_id = agent_data["agent_id"]
                        if agent_id in self.agent_cards:
                            self.agent_cards[agent_id].update_agent_data(agent_data)
                
                elif update_type == "timeline":
                    # Update timeline
                    for agent_name, events in data.items():
                        self.timeline_view.update_timeline_data(agent_name, events)
        
        except:
            pass
        
        # Schedule next update
        self.after(100, self._process_updates)
    
    def _get_cpu_usage(self) -> Tuple[float, float]:
        """Get current CPU usage for chart"""
        import psutil
        return time.time(), psutil.cpu_percent(interval=0.1)
    
    def _get_memory_usage(self) -> Tuple[float, float]:
        """Get current memory usage for chart"""
        import psutil
        return time.time(), psutil.Process().memory_info().rss / 1024 / 1024  # MB

# Application entry point
def main():
    """Run the Agent Admin Dashboard"""
    app = AgentAdminDashboard()
    app.mainloop()

if __name__ == "__main__":
    main()
```

## 🎯 Implementation Guidelines

### Development Workflow

1. **Component Development**
   - Start with base components (Theme Manager, Card)
   - Build specialized components (AgentCard, LogViewer)
   - Integrate with core system (AgentManager, DatabaseManager)
   - Add real-time updates and animations

2. **Testing Strategy**
   - Unit tests for individual components
   - Integration tests for component interactions
   - Performance tests for real-time updates
   - UI/UX testing with different themes and screen sizes

3. **Performance Optimization**
   - Use threading for background updates
   - Implement efficient canvas rendering for timeline
   - Cache theme colors to avoid repeated lookups
   - Batch UI updates to prevent flickering

### Best Practices

1. **Code Organization**
   - One component per file
   - Clear separation of concerns
   - Consistent naming conventions
   - Comprehensive docstrings

2. **UI/UX Guidelines**
   - Maintain 8px grid system
   - Use consistent spacing (5, 10, 15, 20px)
   - Apply hover effects for interactive elements
   - Provide visual feedback for all actions

3. **Real-time Updates**
   - Use queues for thread-safe communication
   - Batch updates when possible
   - Implement graceful degradation
   - Show loading states during long operations

## 🔧 Configuration

### Theme Configuration (`config/ui_settings.json`)
```json
{
  "default_theme": "dark",
  "enable_animations": true,
  "update_intervals": {
    "agent_status": 2000,
    "timeline": 5000,
    "charts": 1000,
    "logs": 100
  },
  "layout": {
    "side_panel_width": 250,
    "side_panel_collapsed_width": 60,
    "default_card_corner_radius": 15,
    "default_button_corner_radius": 8
  },
  "performance": {
    "max_log_lines": 1000,
    "chart_max_points": 100,
    "timeline_hours_default": 24
  }
}
```

## 📦 Dependencies

```python
# requirements.txt additions
customtkinter>=5.2.0
matplotlib>=3.7.0
psutil>=5.9.0
Pillow>=10.0.0  # For image support in CustomTkinter
```

## 🔧 Ollama Setup Check

### Ollama Setup Manager (`ui/components/ollama_setup.py`)

The UI includes an automatic Ollama setup check that runs on startup and can be triggered manually from the UI.

```python
import customtkinter as ctk
import subprocess
import threading
import platform
import requests
from typing import Optional, Callable
from ui.components.theme_manager import theme_manager
from ui.components.card import Card

class OllamaSetupDialog(ctk.CTkToplevel):
    """Dialog for Ollama setup and configuration"""
    
    def __init__(self, parent, on_complete: Optional[Callable] = None):
        super().__init__(parent)
        
        self.title("Ollama Setup")
        self.geometry("600x400")
        self.resizable(False, False)
        self.transient(parent)
        
        self.on_complete = on_complete
        self.theme = theme_manager.get_theme()
        self.configure(fg_color=self.theme["bg_color"])
        
        self._setup_ui()
        self._check_ollama_status()
    
    def _setup_ui(self):
        """Set up the dialog UI"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Ollama Setup & Configuration",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(pady=(20, 10))
        
        # Status card
        self.status_card = Card(
            self,
            title="Ollama Status",
            width=550,
            height=100
        )
        self.status_card.pack(pady=10)
        
        # Status elements
        self.status_frame = ctk.CTkFrame(
            self.status_card.content_frame,
            fg_color="transparent"
        )
        self.status_frame.pack(fill="both", expand=True)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Checking Ollama status...",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(pady=5)
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="⚪",
            font=ctk.CTkFont(size=20)
        )
        self.status_indicator.pack()
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=150
        )
        self.progress_frame.pack(fill="x", pady=20)
        self.progress_frame.pack_propagate(False)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=500,
            height=20,
            corner_radius=10
        )
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.theme["text_secondary"]
        )
        self.progress_label.pack()
        
        # Action buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)
        
        self.action_button = ctk.CTkButton(
            button_frame,
            text="Start Ollama",
            width=150,
            height=40,
            corner_radius=8,
            command=self._start_ollama,
            state="disabled"
        )
        self.action_button.pack(side="left", padx=5)
        
        self.close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            width=100,
            height=40,
            corner_radius=8,
            fg_color=self.theme["fg_color"],
            hover_color=self.theme["hover_color"],
            text_color=self.theme["text_color"],
            command=self.destroy
        )
        self.close_button.pack(side="left", padx=5)
    
    def _check_ollama_status(self):
        """Check Ollama installation and running status"""
        def check():
            try:
                # Check if Ollama is installed
                result = subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self._update_status("Not Installed", "error")
                    self._show_install_instructions()
                    return
                
                # Check if Ollama service is running
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if response.status_code == 200:
                        self._update_status("Running", "success")
                        self._check_model_status()
                    else:
                        self._update_status("Not Running", "warning")
                        self.action_button.configure(
                            text="Start Ollama",
                            state="normal",
                            command=self._start_ollama
                        )
                except requests.RequestException:
                    self._update_status("Not Running", "warning")
                    self.action_button.configure(
                        text="Start Ollama",
                        state="normal",
                        command=self._start_ollama
                    )
                    
            except FileNotFoundError:
                self._update_status("Not Installed", "error")
                self._show_install_instructions()
        
        threading.Thread(target=check, daemon=True).start()
    
    def _update_status(self, status: str, level: str):
        """Update status display"""
        colors = {
            "success": self.theme["success_color"],
            "warning": self.theme["warning_color"],
            "error": self.theme["error_color"],
            "info": self.theme["accent_color"]
        }
        
        symbols = {
            "success": "🟢",
            "warning": "🟡", 
            "error": "🔴",
            "info": "🔵"
        }
        
        self.status_label.configure(text=f"Ollama Status: {status}")
        self.status_indicator.configure(
            text=symbols.get(level, "⚪"),
            text_color=colors.get(level, self.theme["text_color"])
        )
    
    def _show_install_instructions(self):
        """Show installation instructions"""
        self.progress_label.configure(
            text="Ollama is not installed. Please install from https://ollama.com/download"
        )
        
        self.action_button.configure(
            text="Open Download Page",
            state="normal",
            command=lambda: self._open_url("https://ollama.com/download")
        )
    
    def _start_ollama(self):
        """Start Ollama service"""
        self.action_button.configure(state="disabled")
        self.progress_label.configure(text="Starting Ollama service...")
        
        def start():
            try:
                if platform.system() == "Windows":
                    subprocess.Popen(["ollama", "serve"], shell=True)
                else:
                    subprocess.Popen(["ollama", "serve"])
                
                # Wait for service to start
                import time
                time.sleep(3)
                
                self._check_ollama_status()
                
            except Exception as e:
                self.progress_label.configure(
                    text=f"Failed to start Ollama: {str(e)}"
                )
                self.action_button.configure(state="normal")
        
        threading.Thread(target=start, daemon=True).start()
    
    def _check_model_status(self):
        """Check if llama4:maverick model is installed"""
        self.progress_label.configure(text="Checking model status...")
        
        def check():
            try:
                # Get list of installed models
                response = requests.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    
                    if "llama4:maverick" in model_names:
                        self._update_status("Ready", "success")
                        self.progress_label.configure(
                            text="Llama 4 Maverick model is installed and ready"
                        )
                        self.action_button.configure(
                            text="Complete",
                            state="normal",
                            command=self._complete_setup
                        )
                    else:
                        self.progress_label.configure(
                            text="Llama 4 Maverick model not found"
                        )
                        self.action_button.configure(
                            text="Install Model",
                            state="normal",
                            command=self._install_model
                        )
                        
            except Exception as e:
                self.progress_label.configure(
                    text=f"Error checking models: {str(e)}"
                )
        
        threading.Thread(target=check, daemon=True).start()
    
    def _install_model(self):
        """Install llama4:maverick model"""
        self.action_button.configure(state="disabled")
        self.progress_label.configure(text="Installing Llama 4 Maverick model...")
        self.progress_bar.set(0)
        
        def install():
            try:
                process = subprocess.Popen(
                    ["ollama", "pull", "llama4:maverick"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Parse progress from output
                for line in process.stdout:
                    if "pulling" in line.lower():
                        # Extract progress percentage if available
                        if "%" in line:
                            try:
                                percent_str = line.split("%")[0].split()[-1]
                                percent = float(percent_str) / 100
                                self.progress_bar.set(percent)
                                self.progress_label.configure(
                                    text=f"Downloading: {percent_str}%"
                                )
                            except:
                                pass
                    elif "success" in line.lower():
                        self.progress_bar.set(1.0)
                        self.progress_label.configure(text="Model installed successfully!")
                
                process.wait()
                
                if process.returncode == 0:
                    self._update_status("Ready", "success")
                    self.action_button.configure(
                        text="Complete",
                        state="normal",
                        command=self._complete_setup
                    )
                else:
                    self.progress_label.configure(
                        text="Failed to install model. Please try again."
                    )
                    self.action_button.configure(state="normal")
                    
            except Exception as e:
                self.progress_label.configure(
                    text=f"Error installing model: {str(e)}"
                )
                self.action_button.configure(state="normal")
        
        threading.Thread(target=install, daemon=True).start()
    
    def _complete_setup(self):
        """Complete setup and close dialog"""
        if self.on_complete:
            self.on_complete()
        self.destroy()
    
    def _open_url(self, url: str):
        """Open URL in default browser"""
        import webbrowser
        webbrowser.open(url)

class OllamaStatusWidget(ctk.CTkFrame):
    """Widget to show Ollama connection status in the main UI"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.theme = theme_manager.get_theme()
        self.configure(fg_color="transparent")
        
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self):
        """Set up status widget UI"""
        self.status_label = ctk.CTkLabel(
            self,
            text="● Ollama: Checking...",
            font=ctk.CTkFont(size=11),
            text_color=self.theme["text_secondary"]
        )
        self.status_label.pack(side="left", padx=5)
        
        self.check_button = ctk.CTkButton(
            self,
            text="Setup",
            width=60,
            height=24,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            command=self._open_setup_dialog
        )
        self.check_button.pack(side="left", padx=5)
    
    def _start_monitoring(self):
        """Start monitoring Ollama status"""
        def monitor():
            while True:
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=1)
                    if response.status_code == 200:
                        models = response.json().get("models", [])
                        model_names = [m.get("name", "") for m in models]
                        
                        if "llama4:maverick" in model_names:
                            self._update_status("Ready", "success")
                        else:
                            self._update_status("Model Missing", "warning")
                    else:
                        self._update_status("Error", "error")
                except requests.RequestException:
                    self._update_status("Not Running", "error")
                
                import time
                time.sleep(10)  # Check every 10 seconds
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def _update_status(self, status: str, level: str):
        """Update status display"""
        colors = {
            "success": self.theme["success_color"],
            "warning": self.theme["warning_color"],
            "error": self.theme["error_color"]
        }
        
        self.status_label.configure(
            text=f"● Ollama: {status}",
            text_color=colors.get(level, self.theme["text_secondary"])
        )
        
        # Show/hide setup button based on status
        if level != "success":
            self.check_button.pack(side="left", padx=5)
        else:
            self.check_button.pack_forget()
    
    def _open_setup_dialog(self):
        """Open Ollama setup dialog"""
        dialog = OllamaSetupDialog(
            self.winfo_toplevel(),
            on_complete=lambda: self._start_monitoring()
        )
        dialog.grab_set()

# Integration in main dashboard
def integrate_ollama_check(status_bar: ctk.CTkFrame):
    """Add Ollama status widget to the status bar"""
    ollama_widget = OllamaStatusWidget(status_bar)
    ollama_widget.pack(side="right", padx=10)
```

### Usage in Main Application

To integrate the Ollama setup check into the main application:

1. **Automatic Check on Startup**: The application automatically checks Ollama status when launched
2. **Manual Check**: Users can click the "Setup" button in the status bar to open the setup dialog
3. **Visual Indicators**: Color-coded status indicators show the current state
4. **Progress Tracking**: When downloading models, a progress bar shows download status
5. **Cross-Platform Support**: Works on Windows, macOS, and Linux

The setup dialog handles:
- Checking if Ollama is installed
- Starting the Ollama service if not running
- Verifying the llama4:maverick model is installed
- Downloading the model with progress tracking
- Providing clear status updates throughout the process

## 🚀 Next Steps

1. **Extended Features**
   - Agent scheduling interface
   - Drag-and-drop agent configuration
   - Export functionality for logs and reports
   - Advanced filtering and search
   - Keyboard shortcuts

2. **Integration Points**
   - WebSocket support for real-time updates
   - REST API for external monitoring
   - Plugin system for custom visualizations
   - Integration with notification systems

3. **Advanced Visualizations**
   - Agent dependency graphs
   - Resource allocation heatmaps
   - Performance trend analysis
   - Predictive scheduling suggestions

This comprehensive UI design provides a modern, efficient, and user-friendly interface for managing AI agents in the RS Personal Assistant system, with a focus on real-time monitoring, intuitive controls, and visual appeal.