"""
Premium timeline management page with calendar-like visualization.
"""
from datetime import date, datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox,
    QAbstractItemView, QDialog, QFormLayout, QLineEdit, QDateEdit,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from database import (
    get_all_projects, get_timelines_by_project, upsert_timeline,
    delete_timeline, SessionLocal,
)
from models import Timeline


class TimelineEditDialog(QDialog):
    """Edit/create a timeline entry with project selector."""

    def __init__(self, timeline: Timeline | None = None, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.setWindowTitle("📅 编辑时间节点")
        self.setMinimumWidth(450)

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet("QComboBox { font-size: 14px; padding: 8px 12px; }")
        session = SessionLocal()
        try:
            projects = get_all_projects(session)
            for p in projects:
                self.project_combo.addItem(f"{p.school} - {p.major}", p.id)
        finally:
            session.close()
        layout.addRow("所属项目:", self.project_combo)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: 报名截止、入营通知、面试日期")
        layout.addRow("节点名称:", self.name_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("日期:", self.date_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("备注")
        layout.addRow("描述:", self.desc_edit)

        if timeline:
            self.name_edit.setText(timeline.name)
            if timeline.date:
                d = timeline.date
                self.date_edit.setDate(QDate(d.year, d.month, d.day))
            self.desc_edit.setText(timeline.description)
            idx = self.project_combo.findData(timeline.project_id)
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self._save)
        btn.rejected.connect(self.reject)
        layout.addRow(btn)

    def _save(self):
        project_id = self.project_combo.currentData()
        if project_id is None:
            QMessageBox.warning(self, "提示", "请选择所属项目。")
            return
        session = SessionLocal()
        try:
            tid = self.timeline.id if self.timeline else None
            upsert_timeline(
                session, tid,
                project_id=project_id,
                name=self.name_edit.text().strip() or "未命名",
                date=self.date_edit.date().toPyDate(),
                description=self.desc_edit.text().strip(),
            )
            session.commit()
        finally:
            session.close()
        self.accept()


class TimelinePage(QWidget):
    """Premium timeline overview page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_timelines: list[tuple[Timeline, str]] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📅  时间节点总览")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #1E293B;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.add_btn = QPushButton("＋ 添加时间节点")
        self.add_btn.setProperty("cssClass", "success")
        self.add_btn.clicked.connect(self._add_timeline)
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)

        # Filter bar
        filter_layout = QHBoxLayout()
        self.project_filter = QComboBox()
        self.project_filter.addItem("全部项目", None)
        self.project_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("筛选项目:"))
        filter_layout.addWidget(self.project_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        hint = QLabel("💡 日期临近的节点会以黄色/红色高亮显示")
        hint.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 0 4px;")
        layout.addWidget(hint)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["项目", "节点名称", "日期", "剩余天数", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 100)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("📝 编辑选中")
        self.edit_btn.setProperty("cssClass", "primary")
        self.edit_btn.clicked.connect(self._edit_timeline)

        self.del_btn = QPushButton("删除选中")
        self.del_btn.setProperty("cssClass", "danger")
        self.del_btn.clicked.connect(self._delete_timeline)

        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        session = SessionLocal()
        try:
            current = self.project_filter.currentData()
            self.project_filter.blockSignals(True)
            self.project_filter.clear()
            self.project_filter.addItem("全部项目", None)
            projects = get_all_projects(session)
            for p in projects:
                self.project_filter.addItem(f"{p.school} - {p.major}", p.id)
            idx = self.project_filter.findData(current)
            if idx >= 0:
                self.project_filter.setCurrentIndex(idx)
            self.project_filter.blockSignals(False)

            filter_id = self.project_filter.currentData()
            self._all_timelines = []
            if filter_id:
                tls = get_timelines_by_project(session, filter_id)
                proj = next((p for p in projects if p.id == filter_id), None)
                label = f"{proj.school} - {proj.major}" if proj else ""
                self._all_timelines = [(tl, label) for tl in tls]
            else:
                for p in projects:
                    tls = get_timelines_by_project(session, p.id)
                    label = f"{p.school} - {p.major}"
                    self._all_timelines.extend((tl, label) for tl in tls)

            self._all_timelines.sort(key=lambda x: x[0].date or date(2099, 1, 1))
            self._populate_table()
        finally:
            session.close()

    def _populate_table(self):
        today = date.today()
        self.table.setRowCount(len(self._all_timelines))
        for row, (tl, label) in enumerate(self._all_timelines):
            self.table.setItem(row, 0, QTableWidgetItem(label))
            self.table.setItem(row, 1, QTableWidgetItem(tl.name))

            date_str = str(tl.date) if tl.date else ""
            date_item = QTableWidgetItem(date_str)
            if tl.date:
                if tl.date < today:
                    date_item.setForeground(Qt.red)
                elif (tl.date - today).days <= 3:
                    date_item.setForeground(QColor("#D97706"))
            self.table.setItem(row, 2, date_item)

            if tl.date:
                days_left = (tl.date - today).days
                if days_left < 0:
                    days_text = f"已过 {abs(days_left)} 天"
                elif days_left == 0:
                    days_text = "今天!"
                else:
                    days_text = f"还有 {days_left} 天"
                days_item = QTableWidgetItem(days_text)
                if days_left < 0:
                    days_item.setForeground(Qt.red)
                elif days_left <= 3:
                    days_item.setForeground(QColor("#D97706"))
                    days_item.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
                else:
                    days_item.setForeground(Qt.darkGreen)
                self.table.setItem(row, 3, days_item)
            else:
                self.table.setItem(row, 3, QTableWidgetItem("—"))

            self.table.setItem(row, 4, QTableWidgetItem(tl.description))

    def _selected_data(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._all_timelines):
            return None
        return self._all_timelines[row]

    def _add_timeline(self):
        dialog = TimelineEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit_timeline(self):
        data = self._selected_data()
        if not data:
            QMessageBox.information(self, "提示", "请先选择一个时间节点。")
            return
        tl, _ = data
        dialog = TimelineEditDialog(timeline=tl, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _delete_timeline(self):
        data = self._selected_data()
        if not data:
            QMessageBox.information(self, "提示", "请先选择一个时间节点。")
            return
        tl, _ = data
        reply = QMessageBox.question(self, "确认", f"删除 {tl.name}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_timeline(session, tl.id)
            session.commit()
        finally:
            session.close()
        self.refresh()
