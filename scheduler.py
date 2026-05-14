"""
Background reminder checker thread.
Checks every 30 minutes for upcoming deadlines (within 3 days) and sends
desktop notifications.
"""
import threading
from datetime import date, datetime, timedelta

from PyQt5.QtCore import QObject, pyqtSignal

from database import get_upcoming_timelines, SessionLocal
from utils import send_desktop_notification


class ReminderWorker(QObject):
    """Worker that periodically checks timelines and emits signals."""
    reminders_found = pyqtSignal(list)  # emits list of (Timeline, Project)

    def __init__(self, interval_minutes: int = 30):
        super().__init__()
        self.interval = interval_minutes * 60  # seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        # Check once immediately on start
        self._check_once()
        while not self._stop_event.wait(self.interval):
            self._check_once()

    def _check_once(self):
        try:
            session = SessionLocal()
            upcoming = get_upcoming_timelines(session, days=3)
            session.close()

            if upcoming:
                self.reminders_found.emit(upcoming)
                for tl, project in upcoming:
                    days_left = (tl.date - date.today()).days
                    send_desktop_notification(
                        f"提醒: {project.school} - {tl.name}",
                        f"日期: {tl.date} (还有 {days_left} 天)\n{tl.description}",
                    )
        except Exception:
            pass


class ReminderService:
    """Manages the background reminder thread."""

    def __init__(self, interval_minutes: int = 30):
        self.worker = ReminderWorker(interval_minutes)

    def start(self):
        self.worker.start()

    def stop(self):
        self.worker.stop()
