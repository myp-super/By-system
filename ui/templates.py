"""
Document template library page - store and manage common document snippets.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox, QInputDialog,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import (
    get_all_templates, upsert_template, delete_template, SessionLocal,
)
from models import TEMPLATE_CATEGORIES
from utils import copy_to_clipboard


class TemplateEditDialog(QDialog):
    """Add/Edit template."""

    def __init__(self, template=None, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("编辑文书模板")
        self.setMinimumSize(500, 400)

        layout = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("模板标题")
        layout.addRow("标题:", self.title_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItems(TEMPLATE_CATEGORIES)
        layout.addRow("分类:", self.category_combo)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("文书模板内容...")
        layout.addRow("内容:", self.content_edit)

        if template:
            self.title_edit.setText(template.title)
            self.category_combo.setCurrentText(template.category)
            self.content_edit.setPlainText(template.content)

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self._save)
        btn.rejected.connect(self.reject)
        layout.addRow(btn)

    def _save(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入标题。")
            return
        session = SessionLocal()
        try:
            tid = self.template.id if self.template else None
            upsert_template(
                session, tid,
                title=self.title_edit.text().strip(),
                category=self.category_combo.currentText(),
                content=self.content_edit.toPlainText(),
            )
            session.commit()
        finally:
            session.close()
        self.accept()


class TemplatesPage(QWidget):
    """文书模板库页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("文书模板库")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # Filter
        filter_layout = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.addItem("全部分类", "")
        for c in TEMPLATE_CATEGORIES:
            self.category_filter.addItem(c, c)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("分类:"))
        filter_layout.addWidget(self.category_filter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标题或内容...")
        self.search_input.returnPressed.connect(self.refresh)
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()

        self.add_btn = QPushButton("+ 添加模板")
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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["标题", "分类", "内容预览", "操作"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
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

        self.copy_btn = QPushButton("复制内容")
        self.copy_btn.clicked.connect(self._copy)
        self.copy_btn.setStyleSheet("""
            QPushButton { background: #F5A623; color: white; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background: #E09515; }
        """)
        btn_layout.addWidget(self.copy_btn)

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
        category = self.category_filter.currentData() or ""
        keyword = self.search_input.text().strip().lower()
        session = SessionLocal()
        try:
            templates = get_all_templates(session, category=category)
            if keyword:
                templates = [t for t in templates
                             if keyword in t.title.lower() or keyword in t.content.lower()]
            self._data = templates
            self._populate_table()
        finally:
            session.close()

    def _populate_table(self):
        self.table.setRowCount(len(self._data))
        for row, t in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(t.title))
            self.table.setItem(row, 1, QTableWidgetItem(t.category))
            self.table.setItem(row, 2, QTableWidgetItem(t.content[:150].replace("\n", " ")))

            # Action buttons per row
            btn_widget = QWidget()
            btn_hbox = QHBoxLayout(btn_widget)
            btn_hbox.setContentsMargins(0, 0, 0, 0)
            btn_hbox.setSpacing(4)

            copy_btn = QPushButton("复制")
            copy_btn.clicked.connect(lambda checked, r=row: self._copy_row(r))
            btn_hbox.addWidget(copy_btn)

            self.table.setCellWidget(row, 3, btn_widget)

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return None
        return self._data[row]

    def _add(self):
        dialog = TemplateEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit(self):
        t = self._selected()
        if not t:
            QMessageBox.information(self, "提示", "请先选择一个模板。")
            return
        dialog = TemplateEditDialog(template=t, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def _copy(self):
        t = self._selected()
        if not t:
            QMessageBox.information(self, "提示", "请先选择一个模板。")
            return
        copy_to_clipboard(t.content)
        QMessageBox.information(self, "提示", "内容已复制到剪贴板。")

    def _copy_row(self, row: int):
        t = self._data[row]
        copy_to_clipboard(t.content)
        QMessageBox.information(self, "提示", "内容已复制到剪贴板。")

    def _delete(self):
        t = self._selected()
        if not t:
            QMessageBox.information(self, "提示", "请先选择一个模板。")
            return
        reply = QMessageBox.question(self, "确认", f"删除模板「{t.title}」?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_template(session, t.id)
            session.commit()
        finally:
            session.close()
        self.refresh()
