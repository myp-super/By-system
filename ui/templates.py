"""
Vibrant template library with drag-drop file upload and live preview.
"""
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox, QAbstractItemView,
    QSplitter, QFrame, QTextBrowser,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import (
    get_all_templates, upsert_template, delete_template, SessionLocal,
)
from models import TEMPLATE_CATEGORIES
from utils import copy_to_clipboard
from ui.widgets import FileDropZone


def _extract_text_from_file(path: str) -> str:
    """Extract text from .docx or .txt files."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""
    elif ext in (".docx", ".doc"):
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except (ImportError, Exception):
            return ""
    return ""


class TemplateEditDialog(QDialog):
    """Add/Edit template with file upload."""

    def __init__(self, template=None, file_path: str = "", parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("📝 编辑文书模板")
        self.setMinimumSize(640, 560)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        if not template:
            self.drop_zone = FileDropZone(
                self, accept_extensions=[".docx", ".doc", ".txt", ".md"]
            )
            self.drop_zone.fileDropped.connect(self._on_file_dropped)
            layout.addWidget(self.drop_zone)

        form = QFormLayout()
        form.setSpacing(14)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("模板标题")
        self.title_edit.setStyleSheet("QLineEdit { font-size: 17px; padding: 12px 16px; }")
        form.addRow("标题:", self.title_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItems(TEMPLATE_CATEGORIES)
        self.category_combo.setStyleSheet("QComboBox { font-size: 16px; padding: 10px 14px; }")
        form.addRow("分类:", self.category_combo)
        layout.addLayout(form)

        cl = QLabel("内容:")
        cl.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        cl.setStyleSheet("color: #1E293B;")
        layout.addWidget(cl)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("文书模板内容...（也可拖拽 Word 文件到上方区域自动提取）")
        self.content_edit.setMinimumHeight(200)
        self.content_edit.setStyleSheet("QTextEdit { font-size: 16px; }")
        layout.addWidget(self.content_edit)

        if template:
            self.title_edit.setText(template.title)
            self.category_combo.setCurrentText(template.category)
            self.content_edit.setPlainText(template.content)

        if file_path:
            text = _extract_text_from_file(file_path)
            if text:
                self.content_edit.setPlainText(text)
                basename = os.path.splitext(os.path.basename(file_path))[0]
                if not self.title_edit.text():
                    self.title_edit.setText(basename)

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.setStyleSheet("QPushButton { font-size: 16px; padding: 10px 24px; }")
        btn.accepted.connect(self._save)
        btn.rejected.connect(self.reject)
        layout.addWidget(btn)

    def _on_file_dropped(self, path: str):
        text = _extract_text_from_file(path)
        if text:
            self.content_edit.setPlainText(text)
            basename = os.path.splitext(os.path.basename(path))[0]
            if not self.title_edit.text():
                self.title_edit.setText(basename)
            QMessageBox.information(self, "导入成功", f"已从文件提取文本内容（{len(text)} 字）")
        else:
            QMessageBox.warning(self, "提示", "无法从该文件提取文本，请手动粘贴内容。")

    def _save(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入标题。")
            return
        session = SessionLocal()
        try:
            tid = self.template.id if self.template else None
            upsert_template(session, tid,
                            title=self.title_edit.text().strip(),
                            category=self.category_combo.currentText(),
                            content=self.content_edit.toPlainText())
            session.commit()
        finally:
            session.close()
        self.accept()


class TemplatesPage(QWidget):
    """Premium template library."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("📝  文书模板库")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #1E1B4B;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.add_btn = QPushButton("＋ 添加模板")
        self.add_btn.setProperty("cssClass", "success")
        self.add_btn.clicked.connect(self._add)
        header_layout.addWidget(self.add_btn)

        self.import_btn = QPushButton("📂 导入Word")
        self.import_btn.setProperty("cssClass", "primary")
        self.import_btn.clicked.connect(self._import_file)
        header_layout.addWidget(self.import_btn)
        layout.addLayout(header_layout)

        filter_layout = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.addItem("全部分类", "")
        for c in TEMPLATE_CATEGORIES:
            self.category_filter.addItem(c, c)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("分类筛选:"))
        filter_layout.addWidget(self.category_filter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  搜索标题或内容...")
        self.search_input.returnPressed.connect(self.refresh)
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        splitter = QSplitter(Qt.Horizontal)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["标题", "分类", "内容预览", "操作"])
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 100)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(3, 110)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._edit)
        self.table.setMinimumWidth(520)
        splitter.addWidget(self.table)

        preview_frame = QFrame()
        preview_frame.setStyleSheet("QFrame { background: #fff; border: 2px solid #DDD6FE; border-radius: 16px; }")
        pv_layout = QVBoxLayout(preview_frame)
        pv_layout.setContentsMargins(20, 16, 20, 16)
        pv_layout.setSpacing(10)

        pt = QLabel("内容预览")
        pt.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        pt.setStyleSheet("border: none; color: #1E293B;")
        pv_layout.addWidget(pt)

        self.preview_browser = QTextBrowser()
        self.preview_browser.setStyleSheet("""
            QTextBrowser {
                background: #F8FAFC; border: 1px solid #DDD6FE;
                border-radius: 10px; padding: 14px; font-size: 16px;
            }
        """)
        self.preview_browser.setPlaceholderText("选择左侧模板查看内容")
        pv_layout.addWidget(self.preview_browser)

        copy_btn = QPushButton("📋 复制到剪贴板")
        copy_btn.clicked.connect(self._copy_selected)
        pv_layout.addWidget(copy_btn)

        splitter.addWidget(preview_frame)
        splitter.setSizes([620, 380])
        layout.addWidget(splitter)

    def _on_selection_changed(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._data):
            self.preview_browser.setPlainText(self._data[row].content)

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
            self.table.setItem(row, 2, QTableWidgetItem(t.content[:120].replace("\n", " ")))

            bw = QWidget()
            bh = QHBoxLayout(bw)
            bh.setContentsMargins(2, 2, 2, 2)
            bh.setSpacing(4)

            cb = QPushButton("复制")
            cb.setFixedHeight(32)
            cb.clicked.connect(lambda checked, r=row: self._copy_row(r))
            bh.addWidget(cb)
            eb = QPushButton("编辑")
            eb.setFixedHeight(32)
            eb.clicked.connect(lambda checked, r=row: self._edit_row(r))
            bh.addWidget(eb)
            self.table.setCellWidget(row, 3, bw)

    def _add(self):
        d = TemplateEditDialog(parent=self)
        if d.exec_() == QDialog.Accepted:
            self.refresh()

    def _import_file(self):
        d = TemplateEditDialog(parent=self)
        if d.exec_() == QDialog.Accepted:
            self.refresh()

    def _edit(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._data):
            self._edit_row(row)

    def _edit_row(self, row: int):
        d = TemplateEditDialog(template=self._data[row], parent=self)
        if d.exec_() == QDialog.Accepted:
            self.refresh()

    def _copy_selected(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._data):
            copy_to_clipboard(self._data[row].content)
            QMessageBox.information(self, "提示", "内容已复制到剪贴板。")

    def _copy_row(self, row: int):
        copy_to_clipboard(self._data[row].content)
        QMessageBox.information(self, "提示", "内容已复制到剪贴板。")

    def _delete(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return
        t = self._data[row]
        r = QMessageBox.question(self, "确认", f"删除「{t.title}」?", QMessageBox.Yes | QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_template(session, t.id)
            session.commit()
        finally:
            session.close()
        self.refresh()
