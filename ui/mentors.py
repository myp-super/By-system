"""
Vibrant mentor contact records with school autocomplete and follow-up highlights.
"""
from datetime import date

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
from ui.widgets import SearchableComboBox
from ui.university_data import ALL_SCHOOLS


class MentorEditDialog(QDialog):
    """Premium mentor edit dialog."""

    def __init__(self, mentor=None, parent=None):
        super().__init__(parent)
        self.mentor = mentor
        self.setWindowTitle("👨‍🏫 编辑导师联系记录")
        self.setMinimumSize(540, 520)

        layout = QFormLayout(self)
        layout.setSpacing(14)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("导师姓名")
        self.name_edit.setStyleSheet("font-size: 16px;")
        layout.addRow("姓名:", self.name_edit)

        self.school_combo = SearchableComboBox()
        self.school_combo.set_items(ALL_SCHOOLS)
        layout.addRow("院校:", self.school_combo)

        self.direction_edit = QLineEdit()
        self.direction_edit.setPlaceholderText("研究方向")
        self.direction_edit.setStyleSheet("font-size: 16px;")
        layout.addRow("研究方向:", self.direction_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("邮箱地址")
        self.email_edit.setStyleSheet("font-size: 16px;")
        layout.addRow("邮箱:", self.email_edit)

        self.first_contact = QDateEdit()
        self.first_contact.setCalendarPopup(True)
        self.first_contact.setDate(QDate.currentDate())
        self.first_contact.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("首次联系日:", self.first_contact)

        self.status_combo = QComboBox()
        self.status_combo.addItems(MENTOR_STATUSES)
        layout.addRow("状态:", self.status_combo)

        self.reply_edit = QTextEdit()
        self.reply_edit.setPlaceholderText("导师回复内容摘要...")
        self.reply_edit.setMaximumHeight(60)
        layout.addRow("回复摘要:", self.reply_edit)

        self.next_followup = QDateEdit()
        self.next_followup.setCalendarPopup(True)
        self.next_followup.setDate(QDate.currentDate().addDays(7))
        self.next_followup.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("下次跟进:", self.next_followup)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("其他备注...")
        self.notes_edit.setMaximumHeight(60)
        layout.addRow("备注:", self.notes_edit)

        if mentor:
            self.name_edit.setText(mentor.name)
            self.school_combo.set_text(mentor.school)
            self.direction_edit.setText(mentor.research_direction)
            self.email_edit.setText(mentor.email)
            if mentor.first_contact_date:
                d = mentor.first_contact_date
                self.first_contact.setDate(QDate(d.year, d.month, d.day))
            self.status_combo.setCurrentText(mentor.status)
            self.reply_edit.setPlainText(mentor.reply_summary)
            if mentor.next_followup_date:
                d = mentor.next_followup_date
                self.next_followup.setDate(QDate(d.year, d.month, d.day))
            self.notes_edit.setPlainText(mentor.notes)

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self._save)
        btn.rejected.connect(self.reject)
        layout.addRow(btn)

    def _save(self):
        session = SessionLocal()
        try:
            mid = self.mentor.id if self.mentor else None
            upsert_mentor(session, mid,
                          name=self.name_edit.text().strip(),
                          school=self.school_combo.text(),
                          research_direction=self.direction_edit.text().strip(),
                          email=self.email_edit.text().strip(),
                          first_contact_date=self.first_contact.date().toPyDate(),
                          status=self.status_combo.currentText(),
                          reply_summary=self.reply_edit.toPlainText(),
                          next_followup_date=self.next_followup.date().toPyDate(),
                          notes=self.notes_edit.toPlainText())
            session.commit()
        finally:
            session.close()
        self.accept()


class MentorsPage(QWidget):
    """Premium mentor records page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("👨‍🏫  导师联系记录")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #1E1B4B;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.add_btn = QPushButton("＋ 添加导师")
        self.add_btn.setProperty("cssClass", "success")
        self.add_btn.clicked.connect(self._add)
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)

        filter_layout = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部", "")
        for s in MENTOR_STATUSES:
            self.status_filter.addItem(s, s)
        self.status_filter.addItem("⚠️ 待跟进", "__followup__")
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("筛选:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["姓名", "院校", "研究方向", "邮箱", "首次联系", "状态", "回复摘要", "下次跟进"])
        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 90)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setColumnWidth(7, 110)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("📝 编辑")
        self.edit_btn.setProperty("cssClass", "primary")
        self.edit_btn.clicked.connect(self._edit)
        self.del_btn = QPushButton("删除")
        self.del_btn.setProperty("cssClass", "danger")
        self.del_btn.clicked.connect(self._delete)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        fv = self.status_filter.currentData()
        session = SessionLocal()
        try:
            if fv == "__followup__":
                today = date.today()
                self._data = [m for m in get_all_mentors(session)
                              if m.next_followup_date and m.next_followup_date <= today
                              and m.status in ("已发", "已回复")]
            elif fv:
                self._data = search_mentors(session, status=fv)
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

            si = QTableWidgetItem(m.status)
            if m.status == "积极回复":
                si.setForeground(Qt.darkGreen)
            elif m.status == "婉拒":
                si.setForeground(Qt.red)
            self.table.setItem(row, 5, si)
            self.table.setItem(row, 6, QTableWidgetItem(m.reply_summary[:100] if m.reply_summary else ""))

            ft = str(m.next_followup_date) if m.next_followup_date else ""
            fi = QTableWidgetItem(ft)
            if m.next_followup_date and m.next_followup_date <= today and m.status in ("已发", "已回复"):
                fi.setBackground(QColor("#FFF3CD"))
                fi.setForeground(Qt.red)
            self.table.setItem(row, 7, fi)

    def _selected(self):
        row = self.table.currentRow()
        return self._data[row] if 0 <= row < len(self._data) else None

    def _add(self):
        d = MentorEditDialog(parent=self)
        if d.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit(self):
        m = self._selected()
        if not m:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return
        d = MentorEditDialog(mentor=m, parent=self)
        if d.exec_() == QDialog.Accepted:
            self.refresh()

    def _delete(self):
        m = self._selected()
        if not m:
            return
        if QMessageBox.question(self, "确认", f"删除导师 {m.name} 的记录?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_mentor(session, m.id)
            session.commit()
        finally:
            session.close()
        self.refresh()
