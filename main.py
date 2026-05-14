"""
保研全程管理 (Graduate School Application Manager) v2.1
Vibrant, modern UI with large fonts, searchable dropdowns, drag-and-drop kanban, and file upload.
"""
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QSizePolicy,
    QMessageBox, QAction,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import init_db, SessionLocal
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


# ═══════════════════════════════════════════════════════════════════════════════
# Vibrant Premium QSS Theme — Larger Fonts & Richer Colors
# ═══════════════════════════════════════════════════════════════════════════════

APP_STYLESHEET = """
/* ═══ Global ═══ */
* {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 16px;
    color: #1E293B;
}

QWidget {
    background: transparent;
}

/* ═══ Main Window Background ═══ */
QMainWindow {
    background: #EFF6FF;
}

/* ═══ Sidebar — Rich Dark Gradient ═══ */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1E1B4B, stop:0.4 #312E81, stop:1 #1E1B4B);
    border-right: none;
    padding: 0px;
}
#sidebar QPushButton {
    color: #C7D2FE;
    background: transparent;
    border: none;
    text-align: left;
    padding: 14px 28px;
    font-size: 16px;
    font-weight: 500;
    border-left: 4px solid transparent;
    border-radius: 0px;
    margin: 2px 0px;
}
#sidebar QPushButton:hover {
    color: #ffffff;
    background: rgba(129, 140, 248, 0.18);
    border-left: 4px solid rgba(165, 180, 252, 0.6);
}
#sidebar QPushButton:checked {
    color: #ffffff;
    background: rgba(99, 102, 241, 0.30);
    border-left: 4px solid #818CF8;
    font-weight: 700;
}
#sidebar #sidebarTitle {
    color: #ffffff;
    font-size: 24px;
    font-weight: 800;
    padding: 28px 28px 18px 28px;
    background: transparent;
}

/* ═══ Content Area ═══ */
#contentArea {
    background: #EFF6FF;
}

/* ═══ Scroll Area ═══ */
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical {
    width: 10px; background: transparent; margin: 4px 0;
}
QScrollBar::handle:vertical {
    background: #A5B4FC; border-radius: 5px; min-height: 40px;
}
QScrollBar::handle:vertical:hover { background: #818CF8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { height: 10px; background: transparent; }
QScrollBar::handle:horizontal {
    background: #A5B4FC; border-radius: 5px; min-width: 40px;
}
QScrollBar::handle:horizontal:hover { background: #818CF8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ═══ Table ═══ */
QTableWidget {
    background: #ffffff;
    border: 1px solid #DDD6FE;
    border-radius: 12px;
    gridline-color: #F1F5F9;
    selection-background-color: #EDE9FE;
    selection-color: #1E293B;
    font-size: 15px;
}
QTableWidget::item { padding: 10px 14px; }
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F5F3FF, stop:1 #EDE9FE);
    color: #3730A3;
    font-weight: 700;
    font-size: 15px;
    padding: 12px 14px;
    border: none;
    border-bottom: 2px solid #C4B5FD;
}
QTableWidget::item:alternate { background: #FAFAFE; }

/* ═══ ComboBox / LineEdit ═══ */
QComboBox {
    background: #ffffff;
    border: 2px solid #DDD6FE;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 16px;
    min-width: 100px;
}
QComboBox:hover { border-color: #818CF8; }
QComboBox:focus { border-color: #6366F1; background: #F8FAFF; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView {
    background: white; border: 2px solid #C4B5FD; border-radius: 10px;
    padding: 6px; selection-background-color: #EDE9FE;
    selection-color: #1E293B; font-size: 16px;
}
QComboBox QAbstractItemView::item { padding: 8px 14px; }

QLineEdit {
    background: #ffffff; border: 2px solid #DDD6FE;
    border-radius: 10px; padding: 10px 14px; font-size: 16px;
}
QLineEdit:focus { border-color: #6366F1; background: #F8FAFF; }

QTextEdit {
    background: #ffffff; border: 2px solid #DDD6FE;
    border-radius: 10px; padding: 10px 14px; font-size: 16px;
}
QTextEdit:focus { border-color: #6366F1; background: #F8FAFF; }

/* ═══ Buttons ═══ */
QPushButton {
    border-radius: 10px; padding: 10px 22px;
    font-size: 16px; font-weight: 500;
}

QPushButton[cssClass="primary"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #818CF8, stop:1 #6366F1);
    color: white; border: none;
}
QPushButton[cssClass="primary"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #4F46E5);
}

QPushButton[cssClass="success"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34D399, stop:1 #10B981);
    color: white; border: none;
}
QPushButton[cssClass="success"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
}

QPushButton[cssClass="danger"] {
    background: #FEE2E2; color: #DC2626;
    border: 2px solid #FECACA; font-weight: 600;
}
QPushButton[cssClass="danger"]:hover {
    background: #FECACA; color: #B91C1C; border-color: #FCA5A5;
}

QPushButton[cssClass="warning"] {
    background: #FEF3C7; color: #D97706;
    border: 2px solid #FDE68A; font-weight: 600;
}
QPushButton[cssClass="warning"]:hover {
    background: #FDE68A; color: #B45309; border-color: #FCD34D;
}

QPushButton[cssClass="secondary"] {
    background: #F1F5F9; color: #475569;
    border: 2px solid #E2E8F0; font-weight: 500;
}
QPushButton[cssClass="secondary"]:hover {
    background: #E2E8F0; color: #1E293B; border-color: #CBD5E1;
}

/* ═══ Group Box ═══ */
QGroupBox {
    background: #ffffff;
    border: 2px solid #DDD6FE;
    border-radius: 14px;
    margin-top: 16px;
    padding: 24px 18px 18px 18px;
    font-weight: 700;
    font-size: 17px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 18px;
    padding: 0 10px; color: #3730A3;
}

/* ═══ List Widget ═══ */
QListWidget {
    background: #ffffff; border: 2px solid #DDD6FE;
    border-radius: 10px; padding: 6px; font-size: 16px;
}
QListWidget::item {
    padding: 10px 14px; border-bottom: 1px solid #F1F5F9; border-radius: 6px;
}
QListWidget::item:hover { background: #EEF2FF; }
QListWidget::item:selected { background: #E0E7FF; color: #1E293B; }
QListWidget::item:alternate { background: #F8FAFC; }

/* ═══ Progress Bar ═══ */
QProgressBar {
    background: #E2E8F0; border: none; border-radius: 12px;
    height: 26px; text-align: center; font-weight: 700;
    font-size: 13px; color: #ffffff;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:0.4 #8B5CF6, stop:0.7 #A78BFA, stop:1 #10B981);
    border-radius: 12px;
}

/* ═══ Tooltips ═══ */
QToolTip {
    background: #1E1B4B; color: #E0E7FF;
    border: none; padding: 10px 14px; border-radius: 8px; font-size: 14px;
}

/* ═══ Menu Bar ═══ */
QMenuBar {
    background: #ffffff; border-bottom: 2px solid #EDE9FE;
    padding: 4px 10px; font-size: 16px;
}
QMenuBar::item { padding: 8px 16px; border-radius: 8px; }
QMenuBar::item:selected { background: #F5F3FF; color: #4F46E5; }

QMenu {
    background: #ffffff; border: 2px solid #DDD6FE;
    border-radius: 12px; padding: 8px;
}
QMenu::item {
    padding: 10px 36px 10px 20px; border-radius: 8px; font-size: 15px;
}
QMenu::item:selected { background: #F5F3FF; color: #4F46E5; }
QMenu::separator { height: 1px; background: #E2E8F0; margin: 6px 10px; }

/* ═══ Dialog ═══ */
QDialog { background: #F5F3FF; }

/* ═══ Date Edit ═══ */
QDateEdit {
    background: #ffffff; border: 2px solid #DDD6FE;
    border-radius: 10px; padding: 10px 14px; font-size: 16px;
}
QDateEdit:focus { border-color: #6366F1; }
QDateEdit::drop-down { border: none; width: 30px; }

/* ═══ SpinBox ═══ */
QSpinBox {
    background: #ffffff; border: 2px solid #DDD6FE;
    border-radius: 10px; padding: 10px 14px; font-size: 16px;
}
QSpinBox:focus { border-color: #6366F1; }

/* ═══ Message Box ═══ */
QMessageBox { background: #ffffff; }
QMessageBox QPushButton { padding: 10px 28px; border-radius: 10px; font-size: 15px; }
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Navigation
# ═══════════════════════════════════════════════════════════════════════════════

NAV_ITEMS = [
    ("🏠   首页仪表盘",   "dashboard"),
    ("🎓   院校项目库",   "project_list"),
    ("📋   申请进度看板", "kanban"),
    ("📅   时间节点",     "timeline"),
    ("📁   材料管理",     "materials"),
    ("💬   面试记录",     "interviews"),
    ("👨‍🏫   导师联系",   "mentors"),
    ("📝   文书模板库",   "templates"),
]


class MainWindow(QMainWindow):
    """Premium main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("保研全程管理")
        self.setMinimumSize(1320, 840)
        self.resize(1480, 940)

        self._setup_menu_bar()
        self._setup_ui()

        self.reminder = ReminderService(interval_minutes=30)
        self.reminder.worker.reminders_found.connect(self._on_reminders)
        self.reminder.start()

    def _setup_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")
        export_act = QAction("📊  导出全部数据为 Excel", self)
        export_act.triggered.connect(self._export_data)
        file_menu.addAction(export_act)
        file_menu.addSeparator()
        exit_act = QAction("退出(&Q)", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        view_menu = menubar.addMenu("视图(&V)")
        for label, key in NAV_ITEMS:
            action = QAction(label, self)
            action.setData(key)
            action.triggered.connect(lambda checked, k=key: self._navigate_to(k))
            view_menu.addAction(action)

        help_menu = menubar.addMenu("帮助(&H)")
        about_act = QAction("关于", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _show_about(self):
        QMessageBox.about(
            self, "关于 保研全程管理",
            "保研全程管理  v2.1\n\n"
            "帮助你高效管理保研申请全过程。\n\n"
            "功能亮点:\n"
            "  🎯  148所高校智能搜索\n"
            "  📋  拖拽式看板管理\n"
            "  📂  文件拖拽上传\n"
            "  ⏰  桌面定时提醒\n"
            "  📊  一键导出Excel\n\n"
            "数据位置: ~/baoyan_data/data.db"
        )

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(3)

        title = QLabel("  保研管理")
        title.setObjectName("sidebarTitle")
        sb_layout.addWidget(title)
        sb_layout.addSpacing(20)

        self.nav_buttons: dict[str, QPushButton] = {}
        for label, key in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
            self.nav_buttons[key] = btn
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        ver = QLabel("  v2.1")
        ver.setStyleSheet(
            "color: #818CF8; font-size: 13px; font-weight: 500; "
            "padding: 14px 28px; background: transparent;"
        )
        sb_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # ── Content ──────────────────────────────────────────────────
        content = QFrame()
        content.setObjectName("contentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {
            "dashboard":    DashboardPage(),
            "project_list": ProjectListPage(),
            "kanban":       KanbanPage(),
            "timeline":     TimelinePage(),
            "materials":    MaterialsPage(),
            "interviews":   InterviewsPage(),
            "mentors":      MentorsPage(),
            "templates":    TemplatesPage(),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        content_layout.addWidget(self.stack)
        main_layout.addWidget(content, 1)

        self._navigate_to("dashboard")

    def _navigate_to(self, key: str):
        if key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])
            for k, btn in self.nav_buttons.items():
                btn.setChecked(k == key)
            page = self.pages[key]
            if hasattr(page, "refresh"):
                page.refresh()

    def _export_data(self):
        export_to_excel(SessionLocal)

    def _on_reminders(self, upcoming):
        pass

    def closeEvent(self, event):
        self.reminder.stop()
        event.accept()


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    app.setApplicationName("保研全程管理")
    app.setOrganizationName("BaoyanManager")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
