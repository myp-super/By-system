"""
Timeline management page - view all project timelines across the application.
"""
from datetime import date, datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox,
    QAbstractItemView, QDialog, QFormLayout, QLineEdit, QDateEdit,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from database import (
    get_all_projects, get_timelines_by_project, upsert_timeline,
    delete_timeline, SessionLocal,
)
from models import Timeline


class TimelinePage(QWidget):
    """时间节点总览页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_timelines: list[tuple[Timeline, str]] = []  # (timeline, project_label)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("时间节点总览")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # Filter bar
        filter_layout = QHBoxLayout()
        self.project_filter = QComboBox()
        self.project_filter.addItem("全部项目", None)
        self.project_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("筛选项目:"))
        filter_layout.addWidget(self.project_filter)
        filter_layout.addStretch()

        self.add_btn = QPushButton("+ 添加时间节点")
        self.add_btn.clicked.connect(self._add_timeline)
        self.add_btn.setStyleSheet("""
            QPushButton { background: #7ED321; color: white; border-radius: 4px;
                          padding: 6px 14px; font-weight: bold; }
            QPushButton:hover { background: #6CB81D; }
        """)
        filter_layout.addWidget(self.add_btn)
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["项目", "节点名称", "日期", "剩余天数", "描述"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("编辑选中")
        self.edit_btn.clicked.connect(self._edit_timeline)
        self.edit_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: white; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background: #357ABD; }
        """)
        btn_layout.addWidget(self.edit_btn)

        self.del_btn = QPushButton("删除选中")
        self.del_btn.clicked.connect(self._delete_timeline)
        self.del_btn.setStyleSheet("""
            QPushButton { background: #E74C3C; color: white; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background: #C0392B; }
        """)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        session = SessionLocal()
        try:
            # Update project filter
            current = self.project_filter.currentData()
            self.project_filter.blockSignals(True)
            self.project_filter.clear()
            self.project_filter.addItem("全部项目", None)
            projects = get_all_projects(session)
            for p in projects:
                label = f"{p.school} - {p.major}"
                self.project_filter.addItem(label, p.id)
            # Restore selection
            idx = self.project_filter.findData(current)
            if idx >= 0:
                self.project_filter.setCurrentIndex(idx)
            self.project_filter.blockSignals(False)

            # Load timelines
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
            if tl.date and tl.date < today:
                date_item.setForeground(Qt.red)
            elif tl.date and tl.date <= today + timedelta(days=3):
                date_item.setForeground(Qt.darkYellow)
            self.table.setItem(row, 2, date_item)

            if tl.date:
                days_left = (tl.date - today).days
                days_text = f"{days_left} 天" if days_left >= 0 else f"已过 {abs(days_left)} 天"
                days_item = QTableWidgetItem(days_text)
                if days_left < 0:
                    days_item.setForeground(Qt.red)
                elif days_left <= 3:
                    days_item.setForeground(Qt.darkYellow)
                else:
                    days_item.setForeground(Qt.darkGreen)
                self.table.setItem(row, 3, days_item)
            else:
                self.table.setItem(row, 3, QTableWidgetItem(""))

            self.table.setItem(row, 4, QTableWidgetItem(tl.description))

    def _selected_timeline_data(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._all_timelines):
            return None
        return self._all_timelines[row]

    def _add_timeline(self):
        dialog = TimelineEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit_timeline(self):
        data = self._selected_timeline_data()
        if not data:
            QMessageBox.information(self, "提示", "请先选择一个时间节点。")
            return
        tl, label = data
        dialog = TimelineEditDialog(timeline=tl, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _delete_timeline(self):
        data = self._selected_timeline_data()
        if not data:
            QMessageBox.information(self, "提示", "请先选择一个时间节点。")
            return
        tl, label = data
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


class TimelineEditDialog(QDialog):
    """Edit/create a timeline entry."""

    def __init__(self, timeline: Timeline | None = None, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.setWindowTitle("编辑时间节点")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        # Project selector
        self.project_combo = QComboBox()
        session = SessionLocal()
        try:
            projects = get_all_projects(session)
            for p in projects:
                self.project_combo.addItem(f"{p.school} - {p.major}", p.id)
        finally:
            session.close()
        layout.addRow("所属项目:", self.project_combo)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: 报名截止")
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
                self.date_edit.setDate(QDate(timeline.date.year, timeline.date.month, timeline.date.day))
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
        if not project_id:
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
