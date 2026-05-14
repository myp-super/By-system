"""
保研全程管理 (Graduate School Application Manager)
Main entry point — sets up the main window, sidebar navigation, and stacked pages.
"""
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QSizePolicy,
    QMessageBox, QAction, QMenuBar, QMenu, QSpacerItem,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from database import init_db, SessionLocal, get_upcoming_timelines
from scheduler import ReminderService
from utils import export_to_excel

from ui.dashboard import DashboardPage
from ui.project_list import ProjectListPage
from ui.kanban import KanbanPage
from ui.timeline import TimelinePage
from ui.materials import MaterialsPage
from ui.interviews import InterviewsPage
from ui.mentors import MentorsPage
from ui.templates import TemplatesPage


# ─── QSS Stylesheet ──────────────────────────────────────────────────────────

APP_STYLESHEET = """
/* Global */
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #333;
    background: #F5F7FA;
}

/* Main window */
QMainWindow {
    background: #F5F7FA;
}

/* Sidebar */
#sidebar {
    background: #2C3E50;
    border-right: 1px solid #1a252f;
}
#sidebar QPushButton {
    color: #BDC3C7;
    background: transparent;
    border: none;
    text-align: left;
    padding: 12px 20px;
    font-size: 13px;
    border-left: 3px solid transparent;
}
#sidebar QPushButton:hover {
    color: white;
    background: #34495E;
}
#sidebar QPushButton:checked {
    color: white;
    background: #34495E;
    border-left: 3px solid #4A90D9;
    font-weight: bold;
}
#sidebar #sidebarTitle {
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 20px 20px 10px 20px;
    background: transparent;
}

/* Main content area */
#contentArea {
    background: #F5F7FA;
}

/* QTableWidget */
QTableWidget {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    gridline-color: #f0f0f0;
    selection-background-color: #E3F2FD;
    selection-color: #333;
}
QTableWidget::item {
    padding: 6px 8px;
}
QHeaderView::section {
    background: #F4F7FC;
    color: #555;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #e0e0e0;
}

/* QScrollArea */
QScrollArea {
    background: transparent;
    border: none;
}

/* QScrollBar */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #c0c0c0;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* QComboBox */
QComboBox {
    background: white;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
}
QComboBox:hover { border-color: #4A90D9; }
QComboBox::drop-down { border: none; }

/* QLineEdit */
QLineEdit {
    background: white;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px 10px;
}
QLineEdit:focus { border-color: #4A90D9; }

/* QTextEdit */
QTextEdit {
    background: white;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 4px;
}
QTextEdit:focus { border-color: #4A90D9; }

/* QPushButton */
QPushButton {
    border-radius: 4px;
    padding: 6px 14px;
}
QPushButton:hover { opacity: 0.9; }

/* QGroupBox */
QGroupBox {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #333;
}

/* QListWidget */
QListWidget {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 4px;
}
QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #f5f5f5;
}
QListWidget::item:alternate {
    background: #F9FAFB;
}

/* QProgressBar */
QProgressBar {
    background: #e0e0e0;
    border: none;
    border-radius: 6px;
    height: 18px;
    text-align: center;
    font-weight: bold;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4A90D9, stop:1 #7ED321);
    border-radius: 6px;
}

/* QToolTip */
QToolTip {
    background: #333;
    color: white;
    border: none;
    padding: 6px;
}
"""


# ─── Navigation Items ────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("首页仪表盘", "dashboard"),
    ("院校项目库", "project_list"),
    ("申请进度看板", "kanban"),
    ("时间节点", "timeline"),
    ("材料管理", "materials"),
    ("面试记录", "interviews"),
    ("导师联系", "mentors"),
    ("文书模板库", "templates"),
]


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("保研全程管理")
        self.setMinimumSize(1200, 780)
        self.resize(1360, 860)

        self._setup_menu_bar()
        self._setup_ui()
        self._connect_nav()

        # Start reminder service
        self.reminder = ReminderService(interval_minutes=30)
        self.reminder.worker.reminders_found.connect(self._on_reminders)
        self.reminder.start()

    def _setup_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("文件(&F)")
        export_action = QAction("导出全部数据为 Excel", self)
        export_action.triggered.connect(self._export_data)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction("退出(&Q)", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("视图(&V)")
        self.view_actions = []
        for label, key in NAV_ITEMS:
            action = QAction(label, self)
            action.setData(key)
            action.triggered.connect(lambda checked, k=key: self._navigate_to(k))
            view_menu.addAction(action)
            self.view_actions.append(action)

        # Help menu
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于", self)
        about_action.triggered.connect(
            lambda: QMessageBox.about(
                self, "关于",
                "保研全程管理 v1.0\n\n"
                "帮助你高效管理保研申请全过程:\n"
                "- 院校项目追踪\n- 申请进度看板\n- 时间节点提醒\n"
                "- 材料清单管理\n- 面试/导师记录\n- 文书模板库\n\n"
                "数据存储位置: ~/baoyan_data/data.db"
            )
        )
        help_menu.addAction(about_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        title = QLabel("保研管理")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        sb_layout.addWidget(title)

        sb_layout.addSpacing(12)

        self.nav_buttons: dict[str, QPushButton] = {}
        for label, key in NAV_ITEMS:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
            self.nav_buttons[key] = btn
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        # Version label at bottom
        ver = QLabel("v1.0")
        ver.setStyleSheet("color: #7F8C8D; font-size: 11px; padding: 12px 20px; background: transparent;")
        sb_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # ── Content Area ──────────────────────────────────────────────
        content_frame = QFrame()
        content_frame.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {}

        # Create all pages
        self.pages["dashboard"] = DashboardPage()
        self.pages["project_list"] = ProjectListPage()
        self.pages["kanban"] = KanbanPage()
        self.pages["timeline"] = TimelinePage()
        self.pages["materials"] = MaterialsPage()
        self.pages["interviews"] = InterviewsPage()
        self.pages["mentors"] = MentorsPage()
        self.pages["templates"] = TemplatesPage()

        for key, page in self.pages.items():
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_frame, 1)

        # Default to dashboard
        self._navigate_to("dashboard")

    def _connect_nav(self):
        """Navigation is connected via button clicks above."""

    def _navigate_to(self, key: str):
        """Switch to the page identified by key."""
        if key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])
            # Update button checked states
            for k, btn in self.nav_buttons.items():
                btn.setChecked(k == key)
            # Refresh the page
            page = self.pages[key]
            if hasattr(page, "refresh"):
                page.refresh()

    def _export_data(self):
        """Trigger Excel export."""
        export_to_excel(SessionLocal)

    def _on_reminders(self, upcoming):
        """Handle reminder notifications from background worker."""
        # The worker already sends desktop notifications.
        # We can also refresh the dashboard if visible.
        pass

    def closeEvent(self, event):
        """Clean up on close."""
        self.reminder.stop()
        event.accept()


def main():
    """Application entry point."""
    # Initialize database
    init_db()

    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    app.setApplicationName("保研全程管理")
    app.setOrganizationName("BaoyanManager")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
