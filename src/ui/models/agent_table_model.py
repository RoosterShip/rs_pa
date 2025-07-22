"""
Agent table model for Qt Model-View architecture.

This module provides a QAbstractTableModel for displaying agent data
in a QTableView with proper sorting, filtering, and custom styling.
Loads data from the SQLAlchemy database instead of using mock data.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Optional, Union

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import QWidget

from ...core.database import get_db_session
from ...models.agent import Agent, AgentStatus
from ..widgets.status_indicator_widget import ServiceStatus


@dataclass
class AgentData:
    """Data class representing an agent's information for the UI."""

    name: str
    agent_type: str
    status: ServiceStatus
    last_run: Optional[datetime]
    description: str = ""
    tasks_completed: int = 0
    success_rate: float = 0.0
    id: Optional[int] = None
    enabled: bool = True


class AgentTableModel(QAbstractTableModel):
    """
    Table model for displaying agent information in a QTableView.

    This model provides data for displaying agents with columns for
    name, type, status, last run time, and other relevant information.
    """

    # Custom signals
    agent_status_changed = Signal(str, ServiceStatus)
    refresh_requested = Signal()

    # Column definitions
    COLUMN_NAME = 0
    COLUMN_TYPE = 1
    COLUMN_STATUS = 2
    COLUMN_LAST_RUN = 3
    COLUMN_TASKS = 4
    COLUMN_SUCCESS_RATE = 5

    COLUMN_COUNT = 6

    COLUMN_HEADERS = [
        "Agent Name",
        "Type",
        "Status",
        "Last Run",
        "Tasks",
        "Success Rate",
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the agent table model.

        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self._agents: List[AgentData] = []
        self._load_agents_from_database()
        self._setup_update_timer()

    def _load_agents_from_database(self) -> None:
        """Load agent data from the database."""
        try:
            with get_db_session() as session:
                db_agents = session.query(Agent).all()

                self._agents = []
                for db_agent in db_agents:
                    # Convert database status to UI status
                    ui_status = self._convert_db_status_to_ui_status(
                        db_agent.status_enum
                    )

                    # Format agent type for display
                    agent_type_display = db_agent.agent_type_enum.value.replace(
                        "_", " "
                    ).title()

                    agent_data = AgentData(
                        id=db_agent.id,
                        name=db_agent.name,
                        agent_type=agent_type_display,
                        status=ui_status,
                        last_run=db_agent.last_run,
                        description=db_agent.description or "",
                        tasks_completed=db_agent.run_count,
                        success_rate=self._calculate_success_rate(db_agent),
                        enabled=db_agent.enabled,
                    )
                    self._agents.append(agent_data)
        except Exception as e:
            print(f"Error loading agents from database: {e}")
            # Fallback to empty list
            self._agents = []

    def _convert_db_status_to_ui_status(self, db_status: AgentStatus) -> ServiceStatus:
        """Convert database agent status to UI service status."""
        status_mapping = {
            AgentStatus.RUNNING: ServiceStatus.RUNNING,
            AgentStatus.IDLE: ServiceStatus.IDLE,
            AgentStatus.ERROR: ServiceStatus.ERROR,
            AgentStatus.DISABLED: ServiceStatus.DISABLED,
        }
        return status_mapping.get(db_status, ServiceStatus.UNKNOWN)

    def _calculate_success_rate(self, db_agent: Agent) -> float:
        """Calculate a mock success rate based on agent data."""
        # This is a placeholder calculation - in a real system this would
        # be calculated from actual task success/failure records
        if db_agent.status_enum == AgentStatus.ERROR:
            return 75.0 + (db_agent.id * 3) % 25  # 75-100% range
        elif db_agent.status_enum == AgentStatus.DISABLED:
            return 85.0 + (db_agent.id * 2) % 15  # 85-100% range
        else:
            return 90.0 + (db_agent.id * 1.5) % 10  # 90-100% range

    def _setup_update_timer(self) -> None:
        """Set up timer for periodic data updates."""
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._simulate_updates)
        self._update_timer.start(10000)  # Update every 10 seconds

    def _simulate_updates(self) -> None:
        """Simulate real-time updates to agent data."""
        import random

        # Randomly update some agents
        for i, agent in enumerate(self._agents):
            if random.random() < 0.3:  # 30% chance of update
                # Update last run time for running agents
                if agent.status == ServiceStatus.RUNNING:
                    agent.last_run = datetime.now() - timedelta(
                        seconds=random.randint(30, 300)
                    )
                    agent.tasks_completed += random.randint(0, 2)

                # Emit data changed signal
                start_index = self.index(i, 0)
                end_index = self.index(i, self.COLUMN_COUNT - 1)
                self.dataChanged.emit(start_index, end_index)

    def rowCount(
        self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()
    ) -> int:
        """
        Return the number of rows in the model.

        Args:
            parent: Parent index

        Returns:
            Number of agents
        """
        return len(self._agents)

    def columnCount(
        self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()
    ) -> int:
        """
        Return the number of columns in the model.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        return self.COLUMN_COUNT

    def data(
        self,
        index: Union[QModelIndex, QPersistentModelIndex],
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """
        Return data for the given index and role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data for the index and role
        """
        if not index.isValid() or index.row() >= len(self._agents):
            return None

        agent = self._agents[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(agent, column)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self._get_background_color(agent)
        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_text_color(agent)
        elif role == Qt.ItemDataRole.FontRole:
            return self._get_font(agent, column)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._get_tooltip(agent)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return self._get_alignment(column)

        return None

    def _get_display_data(self, agent: AgentData, column: int) -> str:
        """
        Get display data for a specific column.

        Args:
            agent: Agent data
            column: Column index

        Returns:
            Display string
        """
        if column == self.COLUMN_NAME:
            return agent.name
        elif column == self.COLUMN_TYPE:
            return agent.agent_type
        elif column == self.COLUMN_STATUS:
            return self._format_status(agent.status)
        elif column == self.COLUMN_LAST_RUN:
            return self._format_datetime(agent.last_run) if agent.last_run else "Never"
        elif column == self.COLUMN_TASKS:
            return str(agent.tasks_completed)
        elif column == self.COLUMN_SUCCESS_RATE:
            return f"{agent.success_rate:.1f}%"

        return ""

    def _format_status(self, status: ServiceStatus) -> str:
        """
        Format status for display.

        Args:
            status: Service status

        Returns:
            Formatted status string
        """
        status_text = {
            ServiceStatus.RUNNING: "🟢 Running",
            ServiceStatus.IDLE: "🟡 Idle",
            ServiceStatus.ERROR: "🔴 Error",
            ServiceStatus.DISABLED: "⚫ Disabled",
            ServiceStatus.CONNECTED: "🟢 Connected",
            ServiceStatus.DISCONNECTED: "🔴 Disconnected",
            ServiceStatus.UNKNOWN: "⚪ Unknown",
        }
        return status_text.get(status, "⚪ Unknown")

    def _format_datetime(self, dt: datetime) -> str:
        """
        Format datetime for display.

        Args:
            dt: Datetime to format

        Returns:
            Formatted datetime string
        """
        now = datetime.now()
        diff = now - dt

        if diff.total_seconds() < 60:
            return "Just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"{days}d ago"

    def _get_background_color(self, agent: AgentData) -> QBrush:
        """
        Get background color based on agent status.

        Args:
            agent: Agent data

        Returns:
            Background brush
        """
        colors = {
            ServiceStatus.RUNNING: QColor(240, 253, 244),  # Light green
            ServiceStatus.IDLE: QColor(255, 251, 235),  # Light yellow
            ServiceStatus.ERROR: QColor(254, 242, 242),  # Light red
            ServiceStatus.DISABLED: QColor(249, 250, 251),  # Light gray
        }

        color = colors.get(agent.status, QColor(255, 255, 255))
        return QBrush(color)

    def _get_text_color(self, agent: AgentData) -> QBrush:
        """
        Get text color based on agent status.

        Args:
            agent: Agent data

        Returns:
            Text color brush
        """
        if agent.status == ServiceStatus.DISABLED:
            return QBrush(QColor(156, 163, 175))  # Gray
        else:
            return QBrush(QColor(17, 24, 39))  # Dark gray

    def _get_font(self, agent: AgentData, column: int) -> QFont:
        """
        Get font for a specific cell.

        Args:
            agent: Agent data
            column: Column index

        Returns:
            Font object
        """
        font = QFont()

        if column == self.COLUMN_NAME:
            font.setBold(True)

        if agent.status == ServiceStatus.DISABLED:
            font.setItalic(True)

        return font

    def _get_tooltip(self, agent: AgentData) -> str:
        """
        Get tooltip text for an agent.

        Args:
            agent: Agent data

        Returns:
            Tooltip string
        """
        status_text = (
            self._format_status(agent.status)
            .replace("🟢", "")
            .replace("🟡", "")
            .replace("🔴", "")
            .replace("⚫", "")
            .replace("⚪", "")
            .strip()
        )

        last_run_str = (
            agent.last_run.strftime("%Y-%m-%d %H:%M:%S") if agent.last_run else "Never"
        )

        return f"""<b>{agent.name}</b><br/>
Type: {agent.agent_type}<br/>
Status: {status_text}<br/>
Description: {agent.description}<br/>
Tasks Completed: {agent.tasks_completed}<br/>
Success Rate: {agent.success_rate:.1f}%<br/>
Last Run: {last_run_str}"""

    def _get_alignment(self, column: int) -> int:
        """
        Get text alignment for a column.

        Args:
            column: Column index

        Returns:
            Alignment flag
        """
        if column in [self.COLUMN_TASKS, self.COLUMN_SUCCESS_RATE]:
            return Qt.AlignmentFlag.AlignCenter
        else:
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """
        Return header data.

        Args:
            section: Section index
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if 0 <= section < len(self.COLUMN_HEADERS):
                return self.COLUMN_HEADERS[section]
        elif (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.FontRole
        ):
            font = QFont()
            font.setBold(True)
            return font

        return None

    def get_agent_at_row(self, row: int) -> Optional[AgentData]:
        """
        Get agent data for a specific row.

        Args:
            row: Row index

        Returns:
            Agent data or None if invalid row
        """
        if 0 <= row < len(self._agents):
            return self._agents[row]
        return None

    def update_agent_status(self, row: int, new_status: ServiceStatus) -> bool:
        """
        Update the status of an agent.

        Args:
            row: Row index
            new_status: New status

        Returns:
            True if updated successfully
        """
        if 0 <= row < len(self._agents):
            old_status = self._agents[row].status
            self._agents[row].status = new_status

            # Update last run time if changing to running
            if new_status == ServiceStatus.RUNNING:
                self._agents[row].last_run = datetime.now()

            # Emit signals
            start_index = self.index(row, 0)
            end_index = self.index(row, self.COLUMN_COUNT - 1)
            self.dataChanged.emit(start_index, end_index)

            if old_status != new_status:
                agent_name = self._agents[row].name
                self.agent_status_changed.emit(agent_name, new_status)

            return True

        return False

    def refresh_data(self) -> None:
        """Refresh all data from database and emit signals."""
        self.beginResetModel()
        self._load_agents_from_database()
        self.endResetModel()
        self.refresh_requested.emit()

    def add_agent(self, agent: AgentData) -> None:
        """
        Add a new agent to the model.

        Args:
            agent: Agent data to add
        """
        row_count = len(self._agents)
        self.beginInsertRows(QModelIndex(), row_count, row_count)
        self._agents.append(agent)
        self.endInsertRows()

    def remove_agent(self, row: int) -> bool:
        """
        Remove an agent from the model.

        Args:
            row: Row index to remove

        Returns:
            True if removed successfully
        """
        if 0 <= row < len(self._agents):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._agents[row]
            self.endRemoveRows()
            return True

        return False
