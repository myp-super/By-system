"""
Interview records page - view and manage all interview/assessment records.
"""
from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox, QDialog,
    QFormLayout, QLineEdit, QDateEdit, QTextEdit, QSpinBox, QDialogButtonBox,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from database import (
    get_all_interviews, get_all_projects, upsert_interview, delete_interview,
    SessionLocal,
)
from models import INTERVIEW_FORMATS


class InterviewEditDialog(QDialog):
    """Add/Edit interview record."""

    def __init__(self, interview=None, parent=None):
        super().__init__(parent)
        self.interview = interview
        self.setWindowTitle("编辑面试/考核记录")
        self.setMinimumSize(500, 450)

        layout = QFormLayout(self)

        self.project_combo = QComboBox()
        session = SessionLocal()
        try:
            for p in get_all_projects(session):
                self.project_combo.addItem(f"{p.school} - {p.major}", p.id)
        finally:
            session.close()
        layout.addRow("所属项目:", self.project_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("面试日期:", self.date_edit)

        self.format_combo = QComboBox()
        self.format_combo.addItems(INTERVIEW_FORMATS)
        layout.addRow("形式:", self.format_combo)

        self.questions_edit = QTextEdit()
        self.questions_edit.setPlaceholderText("记录面试中被问到的问题...")
        self.questions_edit.setMaximumHeight(100)
        layout.addRow("问题列表:", self.questions_edit)

        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(0, 5)
        self.rating_spin.setSuffix(" 星")
        layout.addRow("自我评分:", self.rating_spin)

        self.summary_edit = QTextEdit()
        self.summary_edit.setPlaceholderText("面试经验总结...")
        self.summary_edit.setMaximumHeight(80)
        layout.addRow("经验总结:", self.summary_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("附加笔记、附件路径等...")
        self.notes_edit.setMaximumHeight(80)
        layout.addRow("附加笔记:", self.notes_edit)

        if interview:
            idx = self.project_combo.findData(interview.project_id)
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)
            if interview.date:
                self.date_edit.setDate(QDate(interview.date.year, interview.date.month, interview.date.day))
            self.format_combo.setCurrentText(interview.format_type)
            self.questions_edit.setPlainText(interview.questions)
            self.rating_spin.setValue(interview.self_rating)
            self.summary_edit.setPlainText(interview.summary)
            self.notes_edit.setPlainText(interview.notes)

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
            iid = self.interview.id if self.interview else None
            upsert_interview(
                session, iid,
                project_id=project_id,
                date=self.date_edit.date().toPyDate(),
                format_type=self.format_combo.currentText(),
                questions=self.questions_edit.toPlainText(),
                self_rating=self.rating_spin.value(),
                summary=self.summary_edit.toPlainText(),
                notes=self.notes_edit.toPlainText(),
            )
            session.commit()
        finally:
            session.close()
        self.accept()


class InterviewsPage(QWidget):
    """面试/考核记录页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # list of (interview, project_label)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("面试/考核记录")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # Actions
        action_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ 添加记录")
        self.add_btn.clicked.connect(self._add)
        self.add_btn.setStyleSheet("""
            QPushButton { background: #7ED321; color: white; border-radius: 4px;
                          padding: 6px 14px; font-weight: bold; }
            QPushButton:hover { background: #6CB81D; }
        """)
        action_layout.addWidget(self.add_btn)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: white; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background: #357ABD; }
        """)
        action_layout.addWidget(self.refresh_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "项目", "日期", "形式", "评分", "问题", "经验总结", "笔记"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._edit)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("编辑记录")
        self.edit_btn.clicked.connect(self._edit)
        self.edit_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: white; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background: #357ABD; }
        """)
        btn_layout.addWidget(self.edit_btn)

        self.del_btn = QPushButton("删除记录")
        self.del_btn.clicked.connect(self._delete)
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
            interviews = get_all_interviews(session)
            projects = get_all_projects(session)
            proj_map = {p.id: f"{p.school} - {p.major}" for p in projects}
            self._data = [(iv, proj_map.get(iv.project_id, "未知项目")) for iv in interviews]
            self._populate_table()
        finally:
            session.close()

    def _populate_table(self):
        self.table.setRowCount(len(self._data))
        for row, (iv, label) in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(label))
            self.table.setItem(row, 1, QTableWidgetItem(str(iv.date) if iv.date else ""))
            self.table.setItem(row, 2, QTableWidgetItem(iv.format_type))

            stars = "★" * iv.self_rating + "☆" * (5 - iv.self_rating) if iv.self_rating else ""
            rating_item = QTableWidgetItem(stars)
            rating_item.setForeground(Qt.darkYellow)
            self.table.setItem(row, 3, rating_item)

            self.table.setItem(row, 4, QTableWidgetItem(iv.questions[:100] if iv.questions else ""))
            self.table.setItem(row, 5, QTableWidgetItem(iv.summary[:100] if iv.summary else ""))
            self.table.setItem(row, 6, QTableWidgetItem(iv.notes[:100] if iv.notes else ""))

    def _selected_data(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return None
        return self._data[row][0]

    def _add(self):
        dialog = InterviewEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit(self):
        iv = self._selected_data()
        if not iv:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return
        dialog = InterviewEditDialog(interview=iv, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _delete(self):
        iv = self._selected_data()
        if not iv:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return
        reply = QMessageBox.question(self, "确认", "删除此面试记录?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_interview(session, iv.id)
            session.commit()
        finally:
            session.close()
        self.refresh()
