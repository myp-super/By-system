"""
Reusable premium widgets: SearchableComboBox, FileDropZone, ModernCard, RatingStars.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QFrame, QPushButton, QFileDialog, QApplication,
    QCompleter, QComboBox, QSizePolicy, QSpacerItem,
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer, QPoint
from PyQt5.QtGui import QFont, QIcon, QDragEnterEvent, QDropEvent, QColor, QPainter


# ═══════════════════════════════════════════════════════════════════════════════
# Searchable ComboBox (fixed popup)
# ═══════════════════════════════════════════════════════════════════════════════

class SearchableComboBox(QWidget):
    """A clickable searchable dropdown with autocomplete.

    The popup uses Qt.Popup flag to properly receive mouse clicks on all platforms.
    """

    currentTextChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_items: list[str] = []
        self._filtered: list[str] = []
        self._popup: QListWidget | None = None
        self._popup_visible = False
        self._placeholder = "搜索或输入..."

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Input field
        self.input = QLineEdit()
        self.input.setPlaceholderText(self._placeholder)
        self.input.setClearButtonEnabled(True)
        self.input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px; font-size: 16px;
                border: 2px solid #D1D5DB; border-radius: 10px;
                background: #fff; color: #1E293B;
            }
            QLineEdit:focus { border-color: #6366F1; border-width: 2px; background: #F8FAFF; }
            QLineEdit:hover { border-color: #A5B4FC; }
        """)
        self.input.textChanged.connect(self._on_text_changed)
        self.input.returnPressed.connect(self._on_return)
        layout.addWidget(self.input)

        # Dropdown icon (clickable area)
        self._dropdown_btn = QPushButton("▼")
        self._dropdown_btn.setFixedSize(32, self.input.sizeHint().height())
        self._dropdown_btn.setCursor(Qt.PointingHandCursor)
        self._dropdown_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none; color: #6366F1;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { color: #4F46E5; }
        """)
        self._dropdown_btn.clicked.connect(self._toggle_popup)

        # Overlay dropdown button on the input
        # We place it manually
        self._dropdown_btn.setParent(self.input)
        self._dropdown_btn.raise_()

        # Debounce timer
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(120)
        self._debounce.timeout.connect(self._filter_and_show)

        # Create popup (singleton)
        self._popup = QListWidget()
        self._popup.setWindowFlags(Qt.Popup)
        self._popup.setStyleSheet("""
            QListWidget {
                border: 2px solid #6366F1;
                border-radius: 10px;
                background: #fff;
                font-size: 16px;
                padding: 6px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 16px;
                border-radius: 6px;
                margin: 1px 0;
            }
            QListWidget::item:hover {
                background: #EEF2FF;
                color: #4F46E5;
            }
            QListWidget::item:selected {
                background: #E0E7FF;
                color: #3730A3;
            }
        """)
        self._popup.itemClicked.connect(self._on_item_clicked)
        self._popup.installEventFilter(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position dropdown button
        w = self.input.width()
        h = self.input.height()
        self._dropdown_btn.move(w - 34, (h - 28) // 2)

    def set_items(self, items: list[str]):
        self._all_items = sorted(set(items))

    def set_text(self, text: str):
        self.input.setText(text)

    def text(self) -> str:
        return self.input.text().strip()

    def clear(self):
        self.input.clear()

    def _on_text_changed(self, text: str):
        if not text:
            self._filtered = self._all_items[:60]
            self.currentTextChanged.emit("")
            self._show_popup()
        else:
            self._debounce.start()

    def _filter_and_show(self):
        text = self.input.text().strip().lower()
        if text:
            self._filtered = [s for s in self._all_items if text in s.lower()]
        else:
            self._filtered = self._all_items[:60]
        self._show_popup()

    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
        else:
            self._filtered = self._all_items[:60]
            self._show_popup()

    def _show_popup(self):
        self._popup.clear()
        if self._filtered:
            self._popup.addItems(self._filtered[:40])
            self._popup.setFixedWidth(self.input.width())
            height = min(self._popup.sizeHintForRow(0) * self._popup.count() + 20, 350)
            self._popup.setFixedHeight(height)
            pos = self.input.mapToGlobal(QPoint(0, self.input.height() + 2))
            self._popup.move(pos)
            if not self._popup.isVisible():
                self._popup.show()
            self._popup.raise_()
            self._popup.setFocus()
        else:
            self._popup.hide()

    def _on_item_clicked(self, item: QListWidgetItem):
        self.input.setText(item.text())
        self._popup.hide()
        self.input.setFocus()
        self.currentTextChanged.emit(item.text())

    def _on_return(self):
        self._popup.hide()
        self.currentTextChanged.emit(self.input.text().strip())

    def eventFilter(self, obj, event):
        if obj == self._popup:
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key == Qt.Key_Escape:
                    self._popup.hide()
                    self.input.setFocus()
                    return True
                if key == Qt.Key_Return or key == Qt.Key_Enter:
                    row = self._popup.currentRow()
                    if row >= 0:
                        self._on_item_clicked(self._popup.item(row))
                    return True
                # Forward typing to input
                if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
                    return False
        return super().eventFilter(obj, event)


# ═══════════════════════════════════════════════════════════════════════════════
# File Drop Zone
# ═══════════════════════════════════════════════════════════════════════════════

class FileDropZone(QFrame):
    """Drag-and-drop zone for file upload."""

    fileDropped = pyqtSignal(str)

    def __init__(self, parent=None, accept_extensions: list[str] | None = None):
        super().__init__(parent)
        self._accept_ext = accept_extensions or [".docx", ".doc", ".txt", ".pdf", ".md"]
        self._file_path: str = ""
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")

        self._default_style = """
            #dropZone {
                background: #F8FAFC; border: 3px dashed #CBD5E1;
                border-radius: 16px; min-height: 130px;
            }
            #dropZone:hover { border-color: #818CF8; background: #EEF2FF; }
        """
        self.setStyleSheet(self._default_style)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        self.icon_label = QLabel("📂")
        self.icon_label.setFont(QFont("Microsoft YaHei", 36))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("border: none;")
        layout.addWidget(self.icon_label)

        self.hint_label = QLabel("拖拽文件到此处\n或点击选择文件")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet("color: #94A3B8; font-size: 15px; border: none;")
        layout.addWidget(self.hint_label)

        self.file_label = QLabel("")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet("color: #4F46E5; font-size: 14px; font-weight: bold; border: none; word-wrap: true;")
        layout.addWidget(self.file_label)

        self.browse_btn = QPushButton("选择文件")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.clicked.connect(self._browse)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #4F46E5);
                color: white; border: none; border-radius: 8px;
                padding: 8px 20px; font-size: 14px; font-weight: 500;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #4338CA); }
        """)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            ext = os.path.splitext(event.mimeData().urls()[0].toLocalFile())[1].lower()
            if ext in self._accept_ext:
                self.setStyleSheet("""
                    #dropZone {
                        background: #EEF2FF; border: 3px solid #6366F1;
                        border-radius: 16px; min-height: 130px;
                    }
                """)
                event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._default_style)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in self._accept_ext:
                self._file_path = path
                basename = os.path.basename(path)
                self.file_label.setText(f"✓  {basename}")
                self.icon_label.setText("✅")
                self.hint_label.hide()
                self.fileDropped.emit(path)
        self.setStyleSheet(self._default_style)
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        self._browse()

    def _browse(self):
        exts = " ".join(f"*{e}" for e in self._accept_ext)
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", f"文档文件 ({exts})")
        if path:
            self._file_path = path
            self.file_label.setText(f"✓  {os.path.basename(path)}")
            self.icon_label.setText("✅")
            self.hint_label.hide()
            self.fileDropped.emit(path)

    @property
    def file_path(self) -> str:
        return self._file_path

    def reset(self):
        self._file_path = ""
        self.file_label.setText("")
        self.icon_label.setText("📂")
        self.hint_label.show()
        self.setStyleSheet(self._default_style)


# ═══════════════════════════════════════════════════════════════════════════════
# Modern Card (with shadow effect)
# ═══════════════════════════════════════════════════════════════════════════════

class ModernCard(QFrame):
    """A modern card with hover effect."""

    clicked = pyqtSignal()

    def __init__(self, parent=None, accent_color: str = "#6366F1"):
        super().__init__(parent)
        self.setObjectName("modernCard")
        self.setStyleSheet(f"""
            #modernCard {{
                background: #fff;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                padding: 18px;
                border-top: 4px solid {accent_color};
            }}
            #modernCard:hover {{
                border-color: {accent_color};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #F8FAFC);
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ═══════════════════════════════════════════════════════════════════════════════
# Rating Stars
# ═══════════════════════════════════════════════════════════════════════════════

class RatingStars(QWidget):
    """Interactive clickable star rating widget."""

    ratingChanged = pyqtSignal(int)

    def __init__(self, parent=None, max_stars: int = 5):
        super().__init__(parent)
        self._max = max_stars
        self._rating = 0
        self._hover_level = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._stars: list[QPushButton] = []
        for i in range(1, max_stars + 1):
            btn = QPushButton("☆")
            btn.setFixedSize(44, 44)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { font-size: 28px; border: none; background: transparent; color: #CBD5E1; }
                QPushButton:hover { color: #FBBF24; }
            """)
            btn.clicked.connect(lambda checked, v=i: self.set_rating(v))
            btn.enterEvent = lambda e, v=i: self._on_hover(v)
            btn.leaveEvent = lambda e: self._on_hover(0)
            layout.addWidget(btn)
            self._stars.append(btn)
        layout.addStretch()

    def set_rating(self, value: int):
        self._rating = value
        self._redraw()
        self.ratingChanged.emit(value)

    def _on_hover(self, value: int):
        self._hover_level = value
        self._redraw()

    def _redraw(self):
        val = self._hover_level or self._rating
        for i, btn in enumerate(self._stars):
            if i < val:
                btn.setText("★")
                btn.setStyleSheet("""
                    QPushButton { font-size: 28px; border: none; background: transparent; color: #F59E0B; }
                """)
            else:
                btn.setText("☆")
                btn.setStyleSheet("""
                    QPushButton { font-size: 28px; border: none; background: transparent; color: #CBD5E1; }
                    QPushButton:hover { color: #FBBF24; }
                """)

    def rating(self) -> int:
        return self._rating
