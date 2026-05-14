"""
Mentor contact records page.
"""
from datetime import date, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox, QDialog,
    QFormLayout, QLineEdit, QDateEdit, QTextEdit, QDialogButtonBox,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from database import (
    get_all_mentors, search_mentors, upsert_mentor, delete_mentor, SessionLocal,
)
from models import MENTOR_STATUSES


class MentorEditDialog(QDialog):
    """Add/Edit mentor record."""

    def __init__(self, mentor=None, parent=None):
        super().__init__(parent)
        self.mentor = mentor
        self.setWindowTitle("编辑导师联系记录")
        self.setMinimumSize(450, 400)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("导师姓名")
        layout.addRow("姓名:", self.name_edit)

        self.school_edit = QLineEdit()
        self.school_edit.setPlaceholderText("所在院校")
        layout.addRow("院校:", self.school_edit)

        self.direction_edit = QLineEdit()
        self.direction_edit.setPlaceholderText("研究方向")
        layout.addRow("研究方向:", self.direction_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("邮箱地址")
        layout.addRow("邮箱:", self.email_edit)

        self.first_contact = QDateEdit()
        self.first_contact.setCalendarPopup(True)
        self.first_contact.setDate(QDate.currentDate())
        self.first_contact.setDisplayFormat("yyyy-MM-dd")
        self.first_contact.setSpecialValueText("未设置")
        layout.addRow("首次联系日:", self.first_contact)

        self.status_combo = QComboBox()
        self.status_combo.addItems(MENTOR_STATUSES)
        layout.addRow("状态:", self.status_combo)

        self.reply_edit = QTextEdit()
        self.reply_edit.setPlaceholderText("导师回复内容摘要...")
        self.reply_edit.setMaximumHeight(70)
        layout.addRow("回复摘要:", self.reply_edit)

        self.next_followup = QDateEdit()
        self.next_followup.setCalendarPopup(True)
        self.next_followup.setDate(QDate.currentDate().addDays(7))
        self.next_followup.setDisplayFormat("yyyy-MM-dd")
        self.next_followup.setSpecialValueText("未设置")
        layout.addRow("下次跟进:", self.next_followup)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("其他备注...")
        self.notes_edit.setMaximumHeight(70)
        layout.addRow("备注:", self.notes_edit)

        if mentor:
            self.name_edit.setText(mentor.name)
            self.school_edit.setText(mentor.school)
            self.direction_edit.setText(mentor.research_direction)
            self.email_edit.setText(mentor.email)
            if mentor.first_contact_date:
                self.first_contact.setDate(QDate(mentor.first_contact_date.year,
                                                  mentor.first_contact_date.month,
                                                  mentor.first_contact_date.day))
            self.status_combo.setCurrentText(mentor.status)
            self.reply_edit.setPlainText(mentor.reply_summary)
            if mentor.next_followup_date:
                self.next_followup.setDate(QDate(mentor.next_followup_date.year,
                                                  mentor.next_followup_date.month,
                                                  mentor.next_followup_date.day))
            self.notes_edit.setPlainText(mentor.notes)

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self._save)
        btn.rejected.connect(self.reject)
        layout.addRow(btn)

    def _save(self):
        session = SessionLocal()
        try:
            mid = self.mentor.id if self.mentor else None
            upsert_mentor(
                session, mid,
                name=self.name_edit.text().strip(),
                school=self.school_edit.text().strip(),
                research_direction=self.direction_edit.text().strip(),
                email=self.email_edit.text().strip(),
                first_contact_date=self.first_contact.date().toPyDate(),
                status=self.status_combo.currentText(),
                reply_summary=self.reply_edit.toPlainText(),
                next_followup_date=self.next_followup.date().toPyDate(),
                notes=self.notes_edit.toPlainText(),
            )
            session.commit()
        finally:
            session.close()
        self.accept()


class MentorsPage(QWidget):
    """导师联系记录页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("导师联系记录")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # Filter
        filter_layout = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部", "")
        for s in MENTOR_STATUSES:
            self.status_filter.addItem(s, s)
        self.status_filter.addItem("待跟进", "__followup__")
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("筛选:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()

        self.add_btn = QPushButton("+ 添加导师")
        self.add_btn.clicked.connect(self._add)
        self.add_btn.setStyleSheet("""
            QPushButton { background: #7ED321; color: white; border-radius: 4px;
                          padding: 6px 14px; font-weight: bold; }
            QPushButton:hover { background: #6CB81D; }
        """)
        filter_layout.addWidget(self.add_btn)
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "姓名", "院校", "研究方向", "邮箱", "首次联系", "状态", "回复摘要", "下次跟进"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit)
        self.edit_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: white; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background: #357ABD; }
        """)
        btn_layout.addWidget(self.edit_btn)
        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self._delete)
        self.del_btn.setStyleSheet("""
            QPushButton { background: #E74C3C; color: white; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background: #C0392B; }
        """)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        filter_val = self.status_filter.currentData()
        session = SessionLocal()
        try:
            if filter_val == "__followup__":
                # 待跟进: next_followup_date <= today and status in (已发, 已回复)
                today = date.today()
                all_m = get_all_mentors(session)
                self._data = [m for m in all_m
                              if m.next_followup_date and m.next_followup_date <= today
                              and m.status in ("已发", "已回复")]
            elif filter_val:
                self._data = search_mentors(session, status=filter_val)
            else:
                self._data = get_all_mentors(session)
            self._populate_table()
        finally:
            session.close()

    def _populate_table(self):
        today = date.today()
        self.table.setRowCount(len(self._data))
        for row, m in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(m.name))
            self.table.setItem(row, 1, QTableWidgetItem(m.school))
            self.table.setItem(row, 2, QTableWidgetItem(m.research_direction))
            self.table.setItem(row, 3, QTableWidgetItem(m.email))
            self.table.setItem(row, 4, QTableWidgetItem(str(m.first_contact_date) if m.first_contact_date else ""))

            status_item = QTableWidgetItem(m.status)
            if m.status == "积极回复":
                status_item.setForeground(Qt.darkGreen)
            elif m.status == "婉拒":
                status_item.setForeground(Qt.red)
            elif m.status == "已回复":
                status_item.setForeground(Qt.darkCyan)
            self.table.setItem(row, 5, status_item)

            self.table.setItem(row, 6, QTableWidgetItem(m.reply_summary[:80] if m.reply_summary else ""))

            fu_item = QTableWidgetItem(str(m.next_followup_date) if m.next_followup_date else "")
            # Highlight if follow-up is due
            if m.next_followup_date and m.next_followup_date <= today and m.status in ("已发", "已回复"):
                fu_item.setBackground(QColor("#FFF3CD"))
                fu_item.setForeground(Qt.red)
            self.table.setItem(row, 7, fu_item)

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return None
        return self._data[row]

    def _add(self):
        dialog = MentorEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit(self):
        m = self._selected()
        if not m:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return
        dialog = MentorEditDialog(mentor=m, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _delete(self):
        m = self._selected()
        if not m:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return
        reply = QMessageBox.question(self, "确认", f"删除导师 {m.name} 的记录?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_mentor(session, m.id)
            session.commit()
        finally:
            session.close()
        self.refresh()
