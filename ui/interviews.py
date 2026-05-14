"""
Premium interview records page with star rating and rich text notes.
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
from ui.widgets import RatingStars, SearchableComboBox
from ui.university_data import ALL_SCHOOLS


class InterviewEditDialog(QDialog):
    """Premium interview record dialog."""

    def __init__(self, interview=None, parent=None):
        super().__init__(parent)
        self.interview = interview
        self.setWindowTitle("💬 编辑面试/考核记录")
        self.setMinimumSize(560, 520)

        layout = QFormLayout(self)
        layout.setSpacing(14)

        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet("QComboBox { font-size: 14px; padding: 8px 12px; }")
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

        # Rating stars
        rating_layout = QHBoxLayout()
        self.rating_stars = RatingStars()
        self.rating_stars.ratingChanged.connect(lambda v: None)
        rating_layout.addWidget(self.rating_stars)
        rating_layout.addStretch()
        rating_label = QLabel("自我评分:")
        layout.addRow(rating_label, rating_layout)

        self.questions_edit = QTextEdit()
        self.questions_edit.setPlaceholderText("面试中被问到的问题，每行一个...")
        self.questions_edit.setMinimumHeight(80)
        layout.addRow("问题列表:", self.questions_edit)

        self.summary_edit = QTextEdit()
        self.summary_edit.setPlaceholderText("面试经验总结...")
        self.summary_edit.setMinimumHeight(80)
        layout.addRow("经验总结:", self.summary_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("附加笔记、附件说明等...")
        self.notes_edit.setMinimumHeight(60)
        layout.addRow("附加笔记:", self.notes_edit)

        if interview:
            idx = self.project_combo.findData(interview.project_id)
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)
            if interview.date:
                d = interview.date
                self.date_edit.setDate(QDate(d.year, d.month, d.day))
            self.format_combo.setCurrentText(interview.format_type)
            self.questions_edit.setPlainText(interview.questions)
            self.rating_stars.set_rating(interview.self_rating)
            self.summary_edit.setPlainText(interview.summary)
            self.notes_edit.setPlainText(interview.notes)

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
            iid = self.interview.id if self.interview else None
            upsert_interview(
                session, iid,
                project_id=project_id,
                date=self.date_edit.date().toPyDate(),
                format_type=self.format_combo.currentText(),
                questions=self.questions_edit.toPlainText(),
                self_rating=self.rating_stars.rating(),
                summary=self.summary_edit.toPlainText(),
                notes=self.notes_edit.toPlainText(),
            )
            session.commit()
        finally:
            session.close()
        self.accept()


class InterviewsPage(QWidget):
    """Premium interview records page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("💬  面试/考核记录")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #1E293B;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.add_btn = QPushButton("＋ 添加记录")
        self.add_btn.setProperty("cssClass", "success")
        self.add_btn.clicked.connect(self._add)
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["项目", "日期", "形式", "评分", "问题", "经验总结", "笔记"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 120)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._edit)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("📝 编辑记录")
        self.edit_btn.setProperty("cssClass", "primary")
        self.edit_btn.clicked.connect(self._edit)

        self.del_btn = QPushButton("删除记录")
        self.del_btn.setProperty("cssClass", "danger")
        self.del_btn.clicked.connect(self._delete)

        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        session = SessionLocal()
        try:
            interviews = get_all_interviews(session)
            projects = get_all_projects(session)
            proj_map = {p.id: f"{p.school} - {p.major}" for p in projects}
            self._data = [(iv, proj_map.get(iv.project_id, "未知")) for iv in interviews]
            self._populate_table()
        finally:
            session.close()

    def _populate_table(self):
        self.table.setRowCount(len(self._data))
        for row, (iv, label) in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(label))
            self.table.setItem(row, 1, QTableWidgetItem(str(iv.date) if iv.date else ""))
            self.table.setItem(row, 2, QTableWidgetItem(iv.format_type))

            stars = "★" * iv.self_rating + "☆" * (5 - iv.self_rating) if iv.self_rating else "—"
            star_item = QTableWidgetItem(stars)
            star_item.setForeground(Qt.darkYellow)
            self.table.setItem(row, 3, star_item)

            self.table.setItem(row, 4, QTableWidgetItem(iv.questions[:120] if iv.questions else ""))
            self.table.setItem(row, 5, QTableWidgetItem(iv.summary[:120] if iv.summary else ""))
            self.table.setItem(row, 6, QTableWidgetItem(iv.notes[:120] if iv.notes else ""))

    def _selected_iv(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return None
        return self._data[row][0]

    def _add(self):
        dialog = InterviewEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit(self):
        iv = self._selected_iv()
        if not iv:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return
        dialog = InterviewEditDialog(interview=iv, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _delete(self):
        iv = self._selected_iv()
        if not iv:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return
        reply = QMessageBox.question(self, "确认", "删除此面试记录?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_interview(session, iv.id)
            session.commit()
        finally:
            session.close()
        self.refresh()
