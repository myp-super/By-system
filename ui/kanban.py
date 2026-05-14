"""
Kanban board view showing projects organized by status columns.
Supports context-menu status changes and visual drag feedback.
"""
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QMenu, QAction, QPushButton, QSizePolicy, QMessageBox,
)
from PyQt5.QtCore import Qt, QMimeData, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QDrag, QPixmap, QPainter, QColor

from database import get_all_projects, update_project, SessionLocal
from models import PROJECT_STATUSES


STATUS_COLORS = {
    "计划中": "#B0BEC5",
    "已报名": "#64B5F6",
    "等待通知": "#FFB74D",
    "入营": "#4DD0E1",
    "参营中": "#81C784",
    "优营(拟录取)": "#4CAF50",
    "未通过": "#E57373",
    "已放弃": "#9E9E9E",
}


class KanbanCard(QFrame):
    """A single project card on the kanban board."""

    status_changed = pyqtSignal(int, str)  # project_id, new_status

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setObjectName("kanbanCard")
        self.setStyleSheet("""
            #kanbanCard {
                background: #fff; border: 1px solid #ddd; border-radius: 8px;
                padding: 10px; margin: 4px 0;
            }
            #kanbanCard:hover { border-color: #4A90D9; }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # School and degree
        title = QLabel(f"{project.school}")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        major = QLabel(f"{project.major} · {project.degree_type}")
        major.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(major)

        batch_label = QLabel(f"{project.batch}")
        batch_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(batch_label)

        # Context menu for status change
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        change_menu = menu.addMenu("移动到...")
        for s in PROJECT_STATUSES:
            if s != self.project.status:
                act = change_menu.addAction(f"→ {s}")
                act.setData(s)
        action = menu.exec_(self.mapToGlobal(pos))
        if action and action.data():
            self.status_changed.emit(self.project.id, action.data())


class KanbanColumn(QFrame):
    """A single column in the kanban board."""

    card_status_changed = pyqtSignal(int, str)

    def __init__(self, status_name: str, parent=None):
        super().__init__(parent)
        self.status_name = status_name
        self.setObjectName("kanbanColumn")
        color = STATUS_COLORS.get(status_name, "#ccc")
        self.setStyleSheet(f"""
            #kanbanColumn {{
                background: #F0F2F5; border-radius: 8px;
                border-top: 4px solid {color};
                min-width: 200px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(6)

        # Column header
        header = QLabel(f"{status_name} (0)")
        self.header_label = header
        header.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"color: {color}; padding: 4px;")
        layout.addWidget(header)

        # Cards container
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(6)
        layout.addLayout(self.cards_layout)
        layout.addStretch()

        self.setAcceptDrops(True)

    def set_cards(self, projects):
        self._clear_cards()
        self.header_label.setText(f"{self.status_name} ({len(projects)})")
        for p in projects:
            card = KanbanCard(p)
            card.status_changed.connect(self.card_status_changed.emit)
            self.cards_layout.addWidget(card)

    def _clear_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class KanbanPage(QWidget):
    """申请进度看板页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title = QLabel("申请进度看板")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        self.refresh_btn = QPushButton("刷新看板")
        self.refresh_btn.clicked.connect(self.refresh)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: white; border-radius: 4px;
                          padding: 4px 12px; }
            QPushButton:hover { background: #357ABD; }
        """)
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignLeft)

        # Scroll area for horizontal columns
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        columns_widget = QWidget()
        self.columns_layout = QHBoxLayout(columns_widget)
        self.columns_layout.setSpacing(12)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)

        self.columns: dict[str, KanbanColumn] = {}
        for status in PROJECT_STATUSES:
            col = KanbanColumn(status)
            col.card_status_changed.connect(self._change_project_status)
            self.columns[status] = col
            self.columns_layout.addWidget(col, 1)

        scroll.setWidget(columns_widget)
        layout.addWidget(scroll)

    def refresh(self):
        session = SessionLocal()
        try:
            projects = get_all_projects(session)
            # Group by status
            grouped: dict[str, list] = {s: [] for s in PROJECT_STATUSES}
            for p in projects:
                if p.status in grouped:
                    grouped[p.status].append(p)
                else:
                    grouped["计划中"].append(p)
            for status, col in self.columns.items():
                col.set_cards(grouped.get(status, []))
        finally:
            session.close()

    def _change_project_status(self, project_id: int, new_status: str):
        session = SessionLocal()
        try:
            update_project(session, project_id, status=new_status)
            session.commit()
        finally:
            session.close()
        self.refresh()
