"""
Premium material management page with drag-drop file upload.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox,
    QAbstractItemView, QFileDialog, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import (
    get_all_projects, get_materials_by_project, update_material, SessionLocal,
)
from ui.widgets import FileDropZone


class MaterialsPage(QWidget):
    """Premium material management page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📁  材料管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #1E293B;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Filter row
        filter_layout = QHBoxLayout()
        self.project_filter = QComboBox()
        self.project_filter.addItem("全部项目", None)
        self.project_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("筛选项目:"))
        filter_layout.addWidget(self.project_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", "")
        self.status_filter.addItems(["未开始", "进行中", "已完成"])
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("状态:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # File drop zone
        self.drop_zone = FileDropZone(
            self, accept_extensions=[".pdf", ".docx", ".doc", ".jpg", ".png", ".zip"]
        )
        self.drop_zone.fileDropped.connect(self._on_file_dropped)
        self.drop_zone.setMaximumHeight(140)
        layout.addWidget(self.drop_zone)

        drop_hint = QLabel("💡 拖拽文件到上方区域为当前选中材料设置文件路径")
        drop_hint.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 0 4px;")
        layout.addWidget(drop_hint)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["项目", "材料名称", "状态", "文件路径", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 80)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(4, 120)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Action buttons
        btn_layout = QHBoxLayout()
        self.complete_btn = QPushButton("✅ 标记已完成")
        self.complete_btn.setProperty("cssClass", "success")
        self.complete_btn.clicked.connect(lambda: self._set_status("已完成"))

        self.progress_btn = QPushButton("🔄 标记进行中")
        self.progress_btn.setProperty("cssClass", "primary")
        self.progress_btn.clicked.connect(lambda: self._set_status("进行中"))

        self.browse_btn = QPushButton("📂 浏览文件")
        self.browse_btn.clicked.connect(self._browse_file)

        btn_layout.addWidget(self.complete_btn)
        btn_layout.addWidget(self.progress_btn)
        btn_layout.addWidget(self.browse_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        session = SessionLocal()
        try:
            current_p = self.project_filter.currentData()
            self.project_filter.blockSignals(True)
            self.project_filter.clear()
            self.project_filter.addItem("全部项目", None)
            projects = get_all_projects(session)
            for p in projects:
                self.project_filter.addItem(f"{p.school} - {p.major}", p.id)
            idx = self.project_filter.findData(current_p)
            if idx >= 0:
                self.project_filter.setCurrentIndex(idx)
            self.project_filter.blockSignals(False)

            filter_id = self.project_filter.currentData()
            status_filter = self.status_filter.currentText()
            project_list = [p for p in projects if filter_id is None or p.id == filter_id]
            self._data = []
            for p in project_list:
                for mat in p.materials:
                    if status_filter and mat.status != status_filter:
                        continue
                    self._data.append((mat, f"{p.school} - {p.major}"))
            self._populate_table()
        finally:
            session.close()

    def _populate_table(self):
        self.table.setRowCount(len(self._data))
        for row, (mat, label) in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(label))
            self.table.setItem(row, 1, QTableWidgetItem(mat.name))

            status_item = QTableWidgetItem(mat.status)
            if mat.status == "已完成":
                status_item.setForeground(Qt.darkGreen)
            elif mat.status == "进行中":
                status_item.setForeground(Qt.darkYellow)
            self.table.setItem(row, 2, status_item)

            self.table.setItem(row, 3, QTableWidgetItem(mat.file_path or "未设置"))

            btn_widget = QWidget()
            btn_hbox = QHBoxLayout(btn_widget)
            btn_hbox.setContentsMargins(0, 2, 0, 2)
            btn_hbox.setSpacing(4)

            toggle_btn = QPushButton("完成" if mat.status != "已完成" else "重开")
            toggle_btn.setFixedHeight(28)
            toggle_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            toggle_btn.clicked.connect(lambda checked, r=row: self._toggle_row(r))
            btn_hbox.addWidget(toggle_btn)

            browse_btn = QPushButton("浏览")
            browse_btn.setFixedHeight(28)
            browse_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            browse_btn.clicked.connect(lambda checked, r=row: self._browse_row(r))
            btn_hbox.addWidget(browse_btn)

            self.table.setCellWidget(row, 4, btn_widget)

    def _get_selected_mat(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return None
        return self._data[row][0]

    def _set_status(self, status: str):
        mat = self._get_selected_mat()
        if not mat:
            QMessageBox.information(self, "提示", "请先选择一项材料。")
            return
        session = SessionLocal()
        try:
            update_material(session, mat.id, status=status)
            session.commit()
        finally:
            session.close()
        self.refresh()

    def _browse_file(self):
        mat = self._get_selected_mat()
        if not mat:
            QMessageBox.information(self, "提示", "请先选择一项材料。")
            return
        path, _ = QFileDialog.getOpenFileName(self, "选择材料文件", "",
                                              "所有文件 (*)")
        if path:
            session = SessionLocal()
            try:
                update_material(session, mat.id, file_path=path)
                session.commit()
            finally:
                session.close()
            self.refresh()

    def _on_file_dropped(self, path: str):
        mat = self._get_selected_mat()
        if not mat:
            QMessageBox.information(self, "提示", "请先在表格中选择一项材料，再拖拽文件。")
            self.drop_zone.reset()
            return
        session = SessionLocal()
        try:
            update_material(session, mat.id, file_path=path)
            session.commit()
        finally:
            session.close()
        self.drop_zone.reset()
        self.refresh()

    def _browse_row(self, row: int):
        mat = self._data[row][0]
        path, _ = QFileDialog.getOpenFileName(self, "选择材料文件", "", "所有文件 (*)")
        if path:
            session = SessionLocal()
            try:
                update_material(session, mat.id, file_path=path)
                session.commit()
            finally:
                session.close()
            self.refresh()

    def _toggle_row(self, row: int):
        mat = self._data[row][0]
        new_status = "未开始" if mat.status == "已完成" else "已完成"
        session = SessionLocal()
        try:
            update_material(session, mat.id, status=new_status)
            session.commit()
        finally:
            session.close()
        self.refresh()
