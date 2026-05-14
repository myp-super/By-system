"""
Project list page with CRUD operations, search, and detail dialog.
"""
from datetime import date, datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QTextEdit, QDialogButtonBox, QProgressBar,
    QFrame, QGridLayout, QFileDialog, QSpinBox, QDateEdit, QListWidget,
    QListWidgetItem, QGroupBox, QAbstractItemView, QMenu, QAction,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from database import (
    get_all_projects, search_projects, create_project, update_project,
    delete_project, get_project_by_id, get_materials_by_project,
    update_material, add_material, delete_material,
    get_timelines_by_project, upsert_timeline, delete_timeline,
    get_interviews_by_project, upsert_interview, delete_interview,
    SessionLocal,
)
from models import (
    DEGREE_TYPES, BATCH_TYPES, PROJECT_STATUSES, MATERIAL_STATUSES,
    INTERVIEW_FORMATS, DEFAULT_MATERIALS,
)


class ProjectDetailDialog(QDialog):
    """Dialog for viewing/editing a project and its associated data."""

    def __init__(self, project_id: int | None = None, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("项目详情" if project_id else "添加项目")
        self.setMinimumSize(800, 650)
        self.setup_ui()
        if project_id:
            self.load_data()
        else:
            # Pre-add default materials for new project
            for name in DEFAULT_MATERIALS:
                item = QListWidgetItem(name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.material_list.addItem(item)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Tab-like sections using group boxes
        # ─── Basic Info ───────────────────────────────────────────────
        basic_group = QGroupBox("基本信息")
        form = QFormLayout(basic_group)

        self.school_edit = QLineEdit()
        self.school_edit.setPlaceholderText("例如: 清华大学")
        form.addRow("院校名称:", self.school_edit)

        self.college_edit = QLineEdit()
        self.college_edit.setPlaceholderText("例如: 计算机科学与技术学院")
        form.addRow("学院:", self.college_edit)

        self.major_edit = QLineEdit()
        self.major_edit.setPlaceholderText("例如: 计算机科学与技术")
        form.addRow("专业:", self.major_edit)

        self.degree_combo = QComboBox()
        self.degree_combo.addItems(DEGREE_TYPES)
        form.addRow("学位类型:", self.degree_combo)

        self.batch_combo = QComboBox()
        self.batch_combo.addItems(BATCH_TYPES)
        form.addRow("招生批次:", self.batch_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(PROJECT_STATUSES)
        form.addRow("当前状态:", self.status_combo)

        self.link_edit = QLineEdit()
        self.link_edit.setPlaceholderText("https://...")
        form.addRow("官网链接:", self.link_edit)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("用逗号分隔多个标签")
        form.addRow("标签:", self.tags_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlaceholderText("备注信息...")
        form.addRow("备注:", self.notes_edit)

        main_layout.addWidget(basic_group)

        # ─── Materials ────────────────────────────────────────────────
        mat_group = QGroupBox("材料清单")
        mat_layout = QVBoxLayout(mat_group)

        self.material_progress = QProgressBar()
        self.material_progress.setRange(0, 100)
        self.material_progress.setValue(0)
        self.material_progress.setTextVisible(True)
        self.material_progress.setFormat("%p% 完成")
        mat_layout.addWidget(self.material_progress)

        mat_btn_layout = QHBoxLayout()
        self.material_list = QListWidget()
        self.material_list.setAlternatingRowColors(True)
        mat_layout.addWidget(self.material_list)

        self.mat_add_btn = QPushButton("+ 添加材料")
        self.mat_add_btn.clicked.connect(self._add_material)
        self.mat_del_btn = QPushButton("删除选中")
        self.mat_del_btn.clicked.connect(self._delete_material)
        mat_btn_layout.addWidget(self.mat_add_btn)
        mat_btn_layout.addWidget(self.mat_del_btn)
        mat_btn_layout.addStretch()
        mat_layout.addLayout(mat_btn_layout)

        main_layout.addWidget(mat_group)

        # ─── Timelines ─────────────────────────────────────────────────
        tl_group = QGroupBox("时间节点")
        tl_layout = QVBoxLayout(tl_group)

        self.timeline_list = QListWidget()
        self.timeline_list.setAlternatingRowColors(True)
        self.timeline_list.setMaximumHeight(120)
        tl_layout.addWidget(self.timeline_list)

        tl_btn_layout = QHBoxLayout()
        self.tl_add_btn = QPushButton("+ 添加节点")
        self.tl_add_btn.clicked.connect(self._add_timeline)
        self.tl_del_btn = QPushButton("删除选中")
        self.tl_del_btn.clicked.connect(self._delete_timeline)
        tl_btn_layout.addWidget(self.tl_add_btn)
        tl_btn_layout.addWidget(self.tl_del_btn)
        tl_btn_layout.addStretch()
        tl_layout.addLayout(tl_btn_layout)
        main_layout.addWidget(tl_group)

        # ─── Buttons ───────────────────────────────────────────────────
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.save_and_close)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    def load_data(self):
        session = SessionLocal()
        try:
            p = get_project_by_id(session, self.project_id)
            if not p:
                return
            self.school_edit.setText(p.school)
            self.college_edit.setText(p.college)
            self.major_edit.setText(p.major)
            self.degree_combo.setCurrentText(p.degree_type)
            self.batch_combo.setCurrentText(p.batch)
            self.status_combo.setCurrentText(p.status)
            self.link_edit.setText(p.official_link)
            self.tags_edit.setText(p.tags)
            self.notes_edit.setPlainText(p.notes)

            # Materials
            self.material_list.clear()
            for mat in p.materials:
                item = QListWidgetItem(f"{mat.name} [{mat.status}]")
                item.setData(Qt.UserRole, mat.id)
                item.setData(Qt.UserRole + 1, mat.file_path)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                check = Qt.Checked if mat.status == "已完成" else Qt.Unchecked
                item.setCheckState(check)
                if mat.status == "已完成":
                    item.setForeground(Qt.gray)
                self.material_list.addItem(item)
            self._update_material_progress()

            # Timelines
            self.timeline_list.clear()
            for tl in p.timelines:
                text = f"{tl.name} — {tl.date} — {tl.description}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, tl.id)
                self.timeline_list.addItem(item)
        finally:
            session.close()

    def save_and_close(self):
        if not self.school_edit.text().strip():
            QMessageBox.warning(self, "提示", "请至少填写院校名称。")
            return

        session = SessionLocal()
        try:
            if self.project_id:
                update_project(session, self.project_id,
                    school=self.school_edit.text().strip(),
                    college=self.college_edit.text().strip(),
                    major=self.major_edit.text().strip(),
                    degree_type=self.degree_combo.currentText(),
                    batch=self.batch_combo.currentText(),
                    status=self.status_combo.currentText(),
                    official_link=self.link_edit.text().strip(),
                    tags=self.tags_edit.text().strip(),
                    notes=self.notes_edit.toPlainText(),
                )
            else:
                p = create_project(session,
                    school=self.school_edit.text().strip(),
                    college=self.college_edit.text().strip(),
                    major=self.major_edit.text().strip(),
                    degree_type=self.degree_combo.currentText(),
                    batch=self.batch_combo.currentText(),
                    status=self.status_combo.currentText(),
                    official_link=self.link_edit.text().strip(),
                    tags=self.tags_edit.text().strip(),
                    notes=self.notes_edit.toPlainText(),
                )
                self.project_id = p.id

            # Save materials
            for i in range(self.material_list.count()):
                item = self.material_list.item(i)
                mat_id = item.data(Qt.UserRole)
                checked = item.checkState() == Qt.Checked
                new_status = "已完成" if checked else "未开始"
                text = item.text().split(" [")[0]
                if mat_id:
                    update_material(session, mat_id, name=text, status=new_status)
                else:
                    m = add_material(session, self.project_id, text)
                    update_material(session, m.id, status=new_status)

            # Save timelines
            for i in range(self.timeline_list.count()):
                item = self.timeline_list.item(i)
                tl_id = item.data(Qt.UserRole)
                parts = item.text().split(" — ")
                if len(parts) >= 2:
                    name = parts[0]
                    date_str = parts[1] if len(parts) >= 2 else ""
                    desc = parts[2] if len(parts) >= 3 else ""
                    try:
                        d = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
                    except ValueError:
                        d = None
                    if tl_id:
                        upsert_timeline(session, tl_id, project_id=self.project_id,
                                        name=name, date=d, description=desc)

            session.commit()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
        finally:
            session.close()
        self.accept()

    def _update_material_progress(self):
        total = self.material_list.count()
        if total == 0:
            self.material_progress.setValue(0)
            return
        done = sum(1 for i in range(total) if self.material_list.item(i).checkState() == Qt.Checked)
        self.material_progress.setValue(int(done / total * 100))

    def _add_material(self):
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "添加材料", "材料名称:")
        if ok and name.strip():
            item = QListWidgetItem(name.strip())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.material_list.addItem(item)
            self._update_material_progress()

    def _delete_material(self):
        row = self.material_list.currentRow()
        if row < 0:
            return
        item = self.material_list.takeItem(row)
        mat_id = item.data(Qt.UserRole)
        if mat_id:
            session = SessionLocal()
            try:
                delete_material(session, mat_id)
                session.commit()
            finally:
                session.close()
        self._update_material_progress()

    def _add_timeline(self):
        dialog = TimelineEditDialog(self.project_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.name_edit.text().strip()
            d = dialog.date_edit.date().toPyDate()
            desc = dialog.desc_edit.text().strip()
            text = f"{name} — {d} — {desc}"
            item = QListWidgetItem(text)
            self.timeline_list.addItem(item)

    def _delete_timeline(self):
        row = self.timeline_list.currentRow()
        if row < 0:
            return
        item = self.timeline_list.takeItem(row)
        tl_id = item.data(Qt.UserRole)
        if tl_id:
            session = SessionLocal()
            try:
                delete_timeline(session, tl_id)
                session.commit()
            finally:
                session.close()


class TimelineEditDialog(QDialog):
    """Small dialog for editing a single timeline node."""

    def __init__(self, project_id: int, timeline_id: int | None = None, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.timeline_id = timeline_id
        self.setWindowTitle("编辑时间节点")
        self.setMinimumWidth(350)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: 报名截止")
        layout.addRow("节点名称:", self.name_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("日期:", self.date_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("备注说明")
        layout.addRow("描述:", self.desc_edit)

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self.accept)
        btn.rejected.connect(self.reject)
        layout.addRow(btn)


class ProjectListPage(QWidget):
    """院校项目库页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("院校项目库")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # Search bar
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索院校/专业/标签...")
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self.refresh)
        search_layout.addWidget(self.search_input)

        self.batch_filter = QComboBox()
        self.batch_filter.addItem("全部批次", "")
        for b in BATCH_TYPES:
            self.batch_filter.addItem(b, b)
        self.batch_filter.currentIndexChanged.connect(self.refresh)
        search_layout.addWidget(QLabel("批次:"))
        search_layout.addWidget(self.batch_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", "")
        for s in PROJECT_STATUSES:
            self.status_filter.addItem(s, s)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        search_layout.addWidget(QLabel("状态:"))
        search_layout.addWidget(self.status_filter)

        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.refresh)
        self.search_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: white; border-radius: 4px;
                          padding: 6px 16px; font-weight: bold; }
            QPushButton:hover { background: #357ABD; }
        """)
        search_layout.addWidget(self.search_btn)

        self.add_btn = QPushButton("+ 添加项目")
        self.add_btn.clicked.connect(self.add_project)
        self.add_btn.setStyleSheet("""
            QPushButton { background: #7ED321; color: white; border-radius: 4px;
                          padding: 6px 16px; font-weight: bold; }
            QPushButton:hover { background: #6CB81D; }
        """)
        search_layout.addWidget(self.add_btn)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "院校名称", "学院", "专业", "学位类型", "招生批次", "状态", "标签",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.doubleClicked.connect(self.view_detail)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.detail_btn = QPushButton("详情 / 编辑")
        self.detail_btn.clicked.connect(self.view_detail)
        self.detail_btn.setStyleSheet("""
            QPushButton { background: #4A90D9; color: white; border-radius: 4px;
                          padding: 6px 14px; }
            QPushButton:hover { background: #357ABD; }
        """)
        btn_layout.addWidget(self.detail_btn)

        self.delete_btn = QPushButton("删除项目")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setStyleSheet("""
            QPushButton { background: #E74C3C; color: white; border-radius: 4px;
                          padding: 6px 14px; }
            QPushButton:hover { background: #C0392B; }
        """)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        session = SessionLocal()
        try:
            keyword = self.search_input.text().strip()
            batch = self.batch_filter.currentData() or ""
            status = self.status_filter.currentData() or ""
            projects = search_projects(session, keyword=keyword, batch=batch, status=status)
            self._populate_table(projects)
        finally:
            session.close()

    def _populate_table(self, projects):
        self.table.setRowCount(len(projects))
        for row, p in enumerate(projects):
            self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(row, 1, QTableWidgetItem(p.school))
            self.table.setItem(row, 2, QTableWidgetItem(p.college))
            self.table.setItem(row, 3, QTableWidgetItem(p.major))
            self.table.setItem(row, 4, QTableWidgetItem(p.degree_type))
            self.table.setItem(row, 5, QTableWidgetItem(p.batch))
            status_item = QTableWidgetItem(p.status)
            if "优" in p.status or "拟" in p.status:
                status_item.setForeground(Qt.darkGreen)
            elif "未" in p.status or "放弃" in p.status:
                status_item.setForeground(Qt.red)
            self.table.setItem(row, 6, status_item)
            self.table.setItem(row, 7, QTableWidgetItem(p.tags))

    def _selected_project_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def add_project(self):
        dialog = ProjectDetailDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def view_detail(self):
        pid = self._selected_project_id()
        if not pid:
            QMessageBox.information(self, "提示", "请先选择一个项目。")
            return
        dialog = ProjectDetailDialog(pid, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh()

    def delete_selected(self):
        pid = self._selected_project_id()
        if not pid:
            QMessageBox.information(self, "提示", "请先选择一个项目。")
            return
        reply = QMessageBox.question(self, "确认删除", "确定要删除此项目及其关联的所有数据吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        session = SessionLocal()
        try:
            delete_project(session, pid)
            session.commit()
        finally:
            session.close()
        self.refresh()

    def _context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        self.table.selectRow(row)
        menu = QMenu(self)
        view_action = menu.addAction("查看/编辑详情")
        change_status_menu = menu.addMenu("更改状态")
        status_actions = []
        for s in PROJECT_STATUSES:
            act = change_status_menu.addAction(s)
            status_actions.append(act)
        menu.addSeparator()
        delete_action = menu.addAction("删除")

        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == view_action:
            self.view_detail()
        elif action == delete_action:
            self.delete_selected()
        elif action in status_actions:
            new_status = action.text()
            pid = self._selected_project_id()
            if pid:
                session = SessionLocal()
                try:
                    update_project(session, pid, status=new_status)
                    session.commit()
                finally:
                    session.close()
                self.refresh()
