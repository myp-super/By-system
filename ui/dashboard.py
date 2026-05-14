"""
Home dashboard page: statistics cards, upcoming deadlines, recent items.
"""
from datetime import date, datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QScrollArea, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import (
    get_project_stats, get_upcoming_timelines, get_needing_followup_mentors,
    get_all_projects, SessionLocal, get_all_interviews,
)
from models import PROJECT_STATUSES


class StatCard(QFrame):
    """A single statistic card with a number and label."""

    def __init__(self, title: str, value: str | int, color: str = "#4A90D9", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet(f"""
            #statCard {{
                background: #fff; border-radius: 10px; border: 1px solid #e0e0e0;
                padding: 16px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {color};")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei", 11))
        self.title_label.setStyleSheet("color: #888;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)


class DashboardPage(QWidget):
    """首页仪表盘"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Title
        title = QLabel("保研全程管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #333;")
        main_layout.addWidget(title)

        # Scroll area for the rest
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(18)

        # Stats row
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(14)
        inner_layout.addLayout(self.stats_grid)

        # Upcoming deadlines section
        self.deadlines_label = QLabel("即将截止的时间节点 (未来3天)")
        self.deadlines_label.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        self.deadlines_label.setStyleSheet("color: #333;")
        inner_layout.addWidget(self.deadlines_label)

        self.deadlines_container = QVBoxLayout()
        self.deadlines_container.setSpacing(8)
        inner_layout.addLayout(self.deadlines_container)

        # Recent projects & mentors row
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(14)

        # Recent projects
        self.recent_projects_label = QLabel("最近添加的项目")
        self.recent_projects_label.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        self.recent_projects_label.setStyleSheet("color: #333;")

        self.recent_projects_list = QVBoxLayout()
        self.recent_projects_list.setSpacing(6)

        recent_panel = QVBoxLayout()
        recent_panel.addWidget(self.recent_projects_label)
        recent_panel.addLayout(self.recent_projects_list)
        recent_panel.addStretch()
        bottom_layout.addLayout(recent_panel, 1)

        # Mentor follow-ups
        self.mentors_label = QLabel("待跟进导师")
        self.mentors_label.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        self.mentors_label.setStyleSheet("color: #333;")

        self.mentors_list = QVBoxLayout()
        self.mentors_list.setSpacing(6)

        mentor_panel = QVBoxLayout()
        mentor_panel.addWidget(self.mentors_label)
        mentor_panel.addLayout(self.mentors_list)
        mentor_panel.addStretch()
        bottom_layout.addLayout(mentor_panel, 1)

        inner_layout.addLayout(bottom_layout)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def refresh(self):
        """Reload all data on this page."""
        self._clear_layout(self.stats_grid)
        self._clear_layout(self.deadlines_container)
        self._clear_layout(self.recent_projects_list)
        self._clear_layout(self.mentors_list)

        session = SessionLocal()
        try:
            # Stats
            stats = get_project_stats(session)
            interviews = get_all_interviews(session)
            this_month = date.today().month
            monthly_interviews = sum(1 for iv in interviews if iv.date and iv.date.month == this_month)
            upcoming = get_upcoming_timelines(session, days=30)
            upcoming_3d = get_upcoming_timelines(session, days=3)

            stat_items = [
                ("申请总数", stats["total"], "#4A90D9"),
                ("本月面试", monthly_interviews, "#7ED321"),
                ("即将截止(3天)", len(upcoming_3d), "#F5A623"),
                ("本月关键节点", len(upcoming), "#BD10E0"),
            ]
            for i, (title, val, color) in enumerate(stat_items):
                self.stats_grid.addWidget(StatCard(title, val, color), 0, i)

            # Status breakdown
            for i, status_name in enumerate(PROJECT_STATUSES):
                count = stats["status_counts"].get(status_name, 0)
                if count > 0:
                    self.stats_grid.addWidget(
                        StatCard(status_name, count, "#666"),
                        1, i % 4,
                    )

            # Deadlines (3 days)
            if upcoming_3d:
                for tl, proj in upcoming_3d:
                    card = self._make_deadline_card(proj, tl)
                    self.deadlines_container.addWidget(card)
            else:
                empty = QLabel("  暂无即将截止的节点")
                empty.setStyleSheet("color: #aaa; font-size: 12px;")
                self.deadlines_container.addWidget(empty)

            # Recent projects (top 6)
            recent = get_all_projects(session)[:6]
            if recent:
                for proj in recent:
                    self.recent_projects_list.addWidget(self._make_project_row(proj))
            else:
                empty = QLabel("  暂无项目")
                empty.setStyleSheet("color: #aaa; font-size: 12px;")
                self.recent_projects_list.addWidget(empty)

            # Mentor follow-ups
            mentors = get_needing_followup_mentors(session)
            if mentors:
                for m in mentors:
                    self.mentors_list.addWidget(self._make_mentor_row(m))
            else:
                empty = QLabel("  暂无待跟进")
                empty.setStyleSheet("color: #aaa; font-size: 12px;")
                self.mentors_list.addWidget(empty)
        finally:
            session.close()

    def _clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _make_deadline_card(self, project, timeline):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFF8E1; border-left: 4px solid #F5A623;
                border-radius: 6px; padding: 10px;
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        days_left = (timeline.date - date.today()).days
        urgency = "今天!" if days_left == 0 else f"还有 {days_left} 天"
        text = QLabel(f"{project.school} · {timeline.name} · {timeline.date}  [{urgency}]")
        text.setStyleSheet("color: #333; font-size: 13px;")
        layout.addWidget(text)
        layout.addStretch()
        return card

    def _make_project_row(self, project):
        row = QFrame()
        row.setStyleSheet("QFrame { background: #F4F7FC; border-radius: 5px; padding: 6px; }")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 4, 10, 4)
        text = QLabel(f"{project.school} - {project.major} ({project.degree_type})")
        text.setStyleSheet("color: #333; font-size: 12px;")
        row_layout.addWidget(text)
        row_layout.addStretch()
        status_label = QLabel(project.status)
        color = "#4A90D9" if "优" in project.status else "#888"
        status_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        row_layout.addWidget(status_label)
        return row

    def _make_mentor_row(self, mentor):
        row = QFrame()
        row.setStyleSheet("QFrame { background: #F4F7FC; border-radius: 5px; padding: 6px; }")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 4, 10, 4)
        text = QLabel(f"{mentor.name} ({mentor.school})")
        text.setStyleSheet("color: #333; font-size: 12px;")
        row_layout.addWidget(text)
        row_layout.addStretch()
        fu = QLabel(f"跟进: {mentor.next_followup_date}" if mentor.next_followup_date else "待跟进")
        fu.setStyleSheet("color: #F5A623; font-size: 11px; font-weight: bold;")
        row_layout.addWidget(fu)
        return row
