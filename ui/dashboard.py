"""
Premium home dashboard with vibrant stat cards, timelines, and follow-ups.
"""
from datetime import date, datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import (
    get_project_stats, get_upcoming_timelines, get_needing_followup_mentors,
    get_all_projects, SessionLocal, get_all_interviews,
)
from models import PROJECT_STATUSES

# Vibrant card color palette
CARD_PALETTE = [
    ("#6366F1", "linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%)"),
    ("#10B981", "linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%)"),
    ("#F59E0B", "linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)"),
    ("#8B5CF6", "linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)"),
    ("#EC4899", "linear-gradient(135deg, #FDF2F8 0%, #FCE7F3 100%)"),
    ("#06B6D4", "linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%)"),
    ("#F97316", "linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%)"),
    ("#14B8A6", "linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 100%)"),
]


class StatCard(QFrame):
    """Vibrant statistic card with gradient background."""

    def __init__(self, title: str, value: str | int, icon: str = "",
                 color: str = "#6366F1", bg: str = "#EEF2FF", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet(f"""
            #statCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fff, stop:1 {bg});
                border: 2px solid {color}33;
                border-radius: 16px; padding: 22px;
                border-top: 5px solid {color};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Microsoft YaHei", 28))
            icon_label.setStyleSheet("border: none;")
            header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 14))
        title_label.setStyleSheet(f"color: #6B7280; border: none; font-weight: 500;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont("Microsoft YaHei", 38, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {color}; border: none;")
        layout.addWidget(self.value_label)


class DashboardPage(QWidget):
    """Premium dashboard with vibrant cards and timelines."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 26, 30, 26)
        main_layout.setSpacing(22)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("👋  保研全程管理")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title.setStyleSheet("color: #1E1B4B;")
        title_row.addWidget(title)
        title_row.addStretch()

        today_str = date.today().strftime('%Y年%m月%d日')
        today_label = QLabel(f"📅  {today_str}")
        today_label.setFont(QFont("Microsoft YaHei", 16))
        today_label.setStyleSheet("color: #6B7280;")
        title_row.addWidget(today_label)
        main_layout.addLayout(title_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(22)

        # Stats grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(16)
        inner_layout.addLayout(self.stats_grid)

        # Upcoming deadlines
        dl_header = QLabel("⏰  即将截止的时间节点（未来 3 天）")
        dl_header.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        dl_header.setStyleSheet("color: #1E293B; padding: 6px 0;")
        inner_layout.addWidget(dl_header)

        self.deadlines_container = QVBoxLayout()
        self.deadlines_container.setSpacing(10)
        inner_layout.addLayout(self.deadlines_container)

        # Bottom: recent projects + mentors
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)

        # Recent projects
        recent_frame = QFrame()
        recent_frame.setStyleSheet("""
            QFrame { background: #fff; border: 2px solid #DDD6FE;
                     border-radius: 16px; }
        """)
        recent_l = QVBoxLayout(recent_frame)
        recent_l.setContentsMargins(22, 18, 22, 18)
        recent_l.setSpacing(10)

        rlabel = QLabel("📌  最近项目")
        rlabel.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        rlabel.setStyleSheet("border: none; color: #1E293B;")
        recent_l.addWidget(rlabel)
        self.recent_projects_list = QVBoxLayout()
        self.recent_projects_list.setSpacing(8)
        recent_l.addLayout(self.recent_projects_list)
        recent_l.addStretch()
        bottom_layout.addWidget(recent_frame, 1)

        # Mentor follow-ups
        mentor_frame = QFrame()
        mentor_frame.setStyleSheet("""
            QFrame { background: #fff; border: 2px solid #FDE68A;
                     border-radius: 16px; }
        """)
        mentor_l = QVBoxLayout(mentor_frame)
        mentor_l.setContentsMargins(22, 18, 22, 18)
        mentor_l.setSpacing(10)

        mlabel = QLabel("✉️  待跟进导师")
        mlabel.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        mlabel.setStyleSheet("border: none; color: #1E293B;")
        mentor_l.addWidget(mlabel)
        self.mentors_list = QVBoxLayout()
        self.mentors_list.setSpacing(8)
        mentor_l.addLayout(self.mentors_list)
        mentor_l.addStretch()
        bottom_layout.addWidget(mentor_frame, 1)

        inner_layout.addLayout(bottom_layout)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

    def refresh(self):
        self._clear_layout(self.stats_grid)
        self._clear_layout(self.deadlines_container)
        self._clear_layout(self.recent_projects_list)
        self._clear_layout(self.mentors_list)

        session = SessionLocal()
        try:
            stats = get_project_stats(session)
            interviews = get_all_interviews(session)
            tm = date.today().month
            monthly_iv = sum(1 for iv in interviews if iv.date and iv.date.month == tm)
            up3 = get_upcoming_timelines(session, days=3)
            up30 = get_upcoming_timelines(session, days=30)

            # Top stats — each card a different color
            cards_data = [
                ("申请总数", stats["total"], "🎯", *CARD_PALETTE[0]),
                ("本月面试", monthly_iv, "💬", *CARD_PALETTE[1]),
                ("即将截止(3天)", len(up3), "⏰", *CARD_PALETTE[2]),
                ("本月关键节点", len(up30), "📅", *CARD_PALETTE[3]),
            ]
            for i, (t, v, icon, color, bg) in enumerate(cards_data):
                self.stats_grid.addWidget(StatCard(t, v, icon, color, bg), 0, i)

            # Status distribution row
            status_colors = {
                "计划中": CARD_PALETTE[4], "已报名": CARD_PALETTE[0],
                "等待通知": CARD_PALETTE[2], "入营": CARD_PALETTE[5],
                "参营中": CARD_PALETTE[6], "优营(拟录取)": CARD_PALETTE[1],
                "未通过": ("#EF4444", "#FEF2F2"), "已放弃": ("#9CA3AF", "#F9FAFB"),
            }
            col = 0
            for s in PROJECT_STATUSES:
                cnt = stats["status_counts"].get(s, 0)
                if cnt > 0:
                    sc = status_colors.get(s, CARD_PALETTE[7])
                    self.stats_grid.addWidget(StatCard(s, cnt, "", *sc), 1, col % 4)
                    col += 1

            # Deadlines (3-day)
            if up3:
                for tl, proj in up3:
                    self.deadlines_container.addWidget(self._deadline_card(proj, tl))
            else:
                empty = QLabel("  ✅  暂无即将截止的时间节点，继续保持！")
                empty.setFont(QFont("Microsoft YaHei", 15))
                empty.setStyleSheet("color: #10B981; padding: 10px;")
                self.deadlines_container.addWidget(empty)

            # Recent projects
            recent = get_all_projects(session)[:8]
            if recent:
                for proj in recent:
                    self.recent_projects_list.addWidget(self._project_row(proj))
            else:
                empty = QLabel("  暂无项目")
                empty.setFont(QFont("Microsoft YaHei", 15))
                empty.setStyleSheet("color: #9CA3AF; padding: 10px; border: none;")
                self.recent_projects_list.addWidget(empty)

            # Mentors needing follow-up
            mentors = get_needing_followup_mentors(session)
            if mentors:
                for m in mentors:
                    self.mentors_list.addWidget(self._mentor_row(m))
            else:
                empty = QLabel("  ✅  暂无需要跟进的导师")
                empty.setFont(QFont("Microsoft YaHei", 15))
                empty.setStyleSheet("color: #10B981; padding: 10px; border: none;")
                self.mentors_list.addWidget(empty)
        finally:
            session.close()

    def _clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _deadline_card(self, project, timeline):
        card = QFrame()
        days_left = (timeline.date - date.today()).days
        if days_left == 0:
            color, bg, urgency = "#EF4444", "#FEF2F2", "🔴  今天截止!"
            border_style = f"border: 2px solid {color}44; border-left: 6px solid {color};"
        elif days_left == 1:
            color, bg, urgency = "#F59E0B", "#FFFBEB", "🟡  明天"
            border_style = f"border: 2px solid {color}44; border-left: 6px solid {color};"
        else:
            color, bg, urgency = "#6366F1", "#EEF2FF", f"🔵  还有 {days_left} 天"
            border_style = f"border: 2px solid {color}44; border-left: 6px solid {color};"

        card.setStyleSheet(f"QFrame {{ background: {bg}; {border_style} border-radius: 12px; padding: 14px; }}")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)

        info = QLabel(
            f"<b style='font-size:16px;'>{project.school}</b>"
            f"<span style='font-size:15px;'> · {timeline.name}</span><br>"
            f"<span style='color:#6B7280; font-size:14px;'>{timeline.date}</span>  "
            f"<span style='color:{color}; font-weight:700; font-size:15px;'>{urgency}</span>")
        info.setStyleSheet("border: none;")
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)
        layout.addStretch()
        return card

    def _project_row(self, project):
        row = QFrame()
        icons = {"优营(拟录取)": "🎉", "未通过": "❌", "已报名": "📤",
                 "等待通知": "⏳", "入营": "🏕️", "参营中": "🚀",
                 "计划中": "📝", "已放弃": "🚫"}
        icon = icons.get(project.status, "📌")
        sc = "#10B981" if "优" in project.status else ("#EF4444" if "未" in project.status else "#6366F1")

        row.setStyleSheet("QFrame { background: transparent; border: none; padding: 6px 0; }")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 4, 0, 4)

        text = QLabel(f"{icon}  {project.school}  ·  {project.major}")
        text.setFont(QFont("Microsoft YaHei", 15))
        text.setStyleSheet(f"color: #1E293B; border: none;")
        rl.addWidget(text)
        rl.addStretch()

        status = QLabel(project.status)
        status.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        status.setStyleSheet(f"color: {sc}; border: none;")
        rl.addWidget(status)
        return row

    def _mentor_row(self, mentor):
        row = QFrame()
        row.setStyleSheet("QFrame { background: transparent; border: none; padding: 6px 0; }")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 4, 0, 4)

        text = QLabel(f"👤  {mentor.name}  ({mentor.school})")
        text.setFont(QFont("Microsoft YaHei", 15))
        text.setStyleSheet("color: #1E293B; border: none;")
        rl.addWidget(text)
        rl.addStretch()

        fu = str(mentor.next_followup_date) if mentor.next_followup_date else "尽快"
        fu_label = QLabel(f"📅 跟进: {fu}")
        fu_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        fu_label.setStyleSheet("color: #D97706; border: none;")
        rl.addWidget(fu_label)
        return row
