"""
Vibrant kanban board with drag-and-drop, live column highlights, and rich colors.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QMenu, QAction, QPushButton, QSizePolicy, QMessageBox, QApplication,
)
from PyQt5.QtCore import Qt, QMimeData, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QDrag, QPixmap, QPainter, QColor, QMouseEvent

from database import get_all_projects, update_project, SessionLocal
from models import PROJECT_STATUSES

STATUS_COLORS = {
    "计划中":        "#6B7280",
    "已报名":        "#3B82F6",
    "等待通知":      "#F59E0B",
    "入营":          "#06B6D4",
    "参营中":        "#F97316",
    "优营(拟录取)":  "#8B5CF6",
    "未通过":        "#EF4444",
    "已放弃":        "#9CA3AF",
}

STATUS_BG = {
    "计划中":        "#F3F4F6",
    "已报名":        "#EFF6FF",
    "等待通知":      "#FFFBEB",
    "入营":          "#ECFEFF",
    "参营中":        "#FFF7ED",
    "优营(拟录取)":  "#F5F3FF",
    "未通过":        "#FEF2F2",
    "已放弃":        "#F9FAFB",
}

STATUS_ICONS = {
    "计划中":        "📝",
    "已报名":        "📤",
    "等待通知":      "⏳",
    "入营":          "🏕️",
    "参营中":        "🚀",
    "优营(拟录取)":  "🎉",
    "未通过":        "❌",
    "已放弃":        "🚫",
}


class DraggableCard(QFrame):
    """Draggable kanban card."""

    card_moved = pyqtSignal(int, str)

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self._drag_start_pos: QPoint | None = None
        self.setObjectName("kanbanCard")

        color = STATUS_COLORS.get(project.status, "#6B7280")
        bg = STATUS_BG.get(project.status, "#F3F4F6")

        self._base_style = f"""
            #kanbanCard {{
                background: #ffffff;
                border: 2px solid #E5E7EB;
                border-left: 6px solid {color};
                border-radius: 12px;
                padding: 14px;
                margin: 5px 0;
            }}
            #kanbanCard:hover {{
                border-color: {color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fff, stop:1 {bg});
            }}
        """
        self.setStyleSheet(self._base_style)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(88)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)

        icon = STATUS_ICONS.get(project.status, "📌")
        title = QLabel(f"{icon}  {project.school}")
        title.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        title.setStyleSheet("color: #1E293B; border: none;")
        layout.addWidget(title)

        detail = QLabel(f"{project.major} · {project.degree_type} · {project.batch}")
        detail.setFont(QFont("Microsoft YaHei", 13))
        detail.setStyleSheet("color: #6B7280; border: none;")
        layout.addWidget(detail)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self._drag_start_pos:
            dist = (event.pos() - self._drag_start_pos).manhattanLength()
            if dist < 12:
                return
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData("application/x-project-id", str(self.project.id).encode())
            drag.setMimeData(mime)

            pixmap = self.grab()
            p = QPainter(pixmap)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.fillRect(pixmap.rect(), QColor(0, 0, 0, 170))
            p.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            self.setVisible(False)
            drag.exec_(Qt.MoveAction)
            self.setVisible(True)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def _menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #fff; border: 2px solid #DDD6FE; border-radius: 12px; padding: 6px; }
            QMenu::item { padding: 10px 28px 10px 18px; border-radius: 8px; font-size: 15px; }
            QMenu::item:selected { background: #F5F3FF; color: #4F46E5; }
            QMenu::separator { height: 1px; background: #E2E8F0; margin: 4px 8px; }
        """)
        sub = menu.addMenu("移动到...")
        for s in PROJECT_STATUSES:
            if s != self.project.status:
                act = sub.addAction(f"{STATUS_ICONS.get(s, '')}  {s}")
                act.setData(s)
        action = menu.exec_(self.mapToGlobal(pos))
        if action and action.data():
            self.card_moved.emit(self.project.id, action.data())


class KanbanColumn(QFrame):
    """Drop-target column with vibrant header."""

    card_dropped = pyqtSignal(int, str)

    def __init__(self, status_name: str, parent=None):
        super().__init__(parent)
        self.status_name = status_name
        self.setObjectName("kanbanColumn")
        self.setAcceptDrops(True)

        color = STATUS_COLORS.get(status_name, "#6B7280")
        bg = STATUS_BG.get(status_name, "#F3F4F6")
        icon = STATUS_ICONS.get(status_name, "📌")

        self._base_col_style = f"""
            #kanbanColumn {{
                background: {bg};
                border: 2px solid transparent;
                border-radius: 16px;
                min-width: 210px;
            }}
        """
        self.setStyleSheet(self._base_col_style)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(10)

        header = QLabel(f"{icon}  {status_name}")
        self._header = header
        header.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"""
            color: {color}; padding: 8px; border: none;
            background: rgba(255,255,255,0.6); border-radius: 10px;
        """)
        layout.addWidget(header)

        self._count_label = QLabel("0 项")
        self._count_label.setFont(QFont("Microsoft YaHei", 14))
        self._count_label.setAlignment(Qt.AlignCenter)
        self._count_label.setStyleSheet(f"color: {color}; font-weight: 600; border: none;")
        layout.addWidget(self._count_label)

        self.cards_widget = QWidget()
        self.cards_widget.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()
        layout.addWidget(self.cards_widget, 1)

    def set_cards(self, projects):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._count_label.setText(f"{len(projects)} 项")
        for p in projects:
            card = DraggableCard(p)
            card.card_moved.connect(self.card_dropped.emit)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-project-id"):
            color = STATUS_COLORS.get(self.status_name, "#6366F1")
            self.setStyleSheet(f"""
                #kanbanColumn {{
                    background: #ffffff;
                    border: 3px dashed {color};
                    border-radius: 16px;
                    min-width: 210px;
                }}
            """)
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-project-id"):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._base_col_style)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-project-id"):
            pid = int(event.mimeData().data("application/x-project-id").data().decode())
            self.card_dropped.emit(pid, self.status_name)
            event.acceptProposedAction()
        self.dragLeaveEvent(None)


class KanbanPage(QWidget):
    """Vibrant kanban board."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._changing = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("📋  申请进度看板")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #1E1B4B;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("🔄  刷新")
        refresh_btn.setProperty("cssClass", "primary")
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        hint = QLabel("💡  拖拽卡片到目标列即可更改状态  ·  右键卡片查看更多操作")
        hint.setFont(QFont("Microsoft YaHei", 14))
        hint.setStyleSheet("color: #818CF8; padding: 2px 6px;")
        layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        cw = QWidget()
        self.columns_layout = QHBoxLayout(cw)
        self.columns_layout.setSpacing(16)
        self.columns_layout.setContentsMargins(6, 6, 6, 6)

        self.columns: dict[str, KanbanColumn] = {}
        for s in PROJECT_STATUSES:
            col = KanbanColumn(s)
            col.card_dropped.connect(self._on_card_dropped)
            self.columns[s] = col
            self.columns_layout.addWidget(col, 1)

        scroll.setWidget(cw)
        layout.addWidget(scroll)

    def refresh(self):
        if self._changing:
            return
        self._changing = True
        session = SessionLocal()
        try:
            projects = get_all_projects(session)
            grouped: dict[str, list] = {s: [] for s in PROJECT_STATUSES}
            for p in projects:
                grouped.get(p.status, grouped["计划中"]).append(p)
            for s, col in self.columns.items():
                col.set_cards(grouped.get(s, []))
        finally:
            session.close()
        self._changing = False

    def _on_card_dropped(self, project_id: int, new_status: str):
        session = SessionLocal()
        try:
            update_project(session, project_id, status=new_status)
            session.commit()
        finally:
            session.close()
        self.refresh()
