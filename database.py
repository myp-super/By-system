"""
Database initialization, session management, and CRUD operations.
"""
import os
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import (
    Base, Project, Material, Timeline, Interview, Mentor, Template,
    DEFAULT_MATERIALS
)

DB_DIR = Path.home() / "baoyan_data"
DB_PATH = DB_DIR / "data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create database directory and tables if they don't exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Session:
    """Context manager for database sessions with automatic commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ─── Project CRUD ────────────────────────────────────────────────────────────

def get_all_projects(session: Session) -> list[Project]:
    return session.query(Project).order_by(Project.updated_at.desc()).all()


def get_project_by_id(session: Session, project_id: int) -> Project | None:
    return session.query(Project).filter_by(id=project_id).first()


def search_projects(
    session: Session,
    keyword: str = "",
    batch: str = "",
    tag: str = "",
    status: str = "",
) -> list[Project]:
    q = session.query(Project)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (Project.school.like(like))
            | (Project.college.like(like))
            | (Project.major.like(like))
            | (Project.tags.like(like))
        )
    if batch:
        q = q.filter(Project.batch == batch)
    if tag:
        q = q.filter(Project.tags.like(f"%{tag}%"))
    if status:
        q = q.filter(Project.status == status)
    return q.order_by(Project.updated_at.desc()).all()


def create_project(session: Session, **kwargs) -> Project:
    project = Project(created_at=datetime.now(), updated_at=datetime.now(), **kwargs)
    session.add(project)
    session.flush()
    # 为新项目自动创建默认材料清单
    for name in DEFAULT_MATERIALS:
        session.add(Material(project_id=project.id, name=name, status="未开始"))
    session.flush()
    return project


def update_project(session: Session, project_id: int, **kwargs) -> Project | None:
    project = session.query(Project).filter_by(id=project_id).first()
    if project:
        kwargs["updated_at"] = datetime.now()
        for k, v in kwargs.items():
            setattr(project, k, v)
    return project


def delete_project(session: Session, project_id: int) -> bool:
    project = session.query(Project).filter_by(id=project_id).first()
    if project:
        session.delete(project)
        return True
    return False


# ─── Material CRUD ───────────────────────────────────────────────────────────

def get_materials_by_project(session: Session, project_id: int) -> list[Material]:
    return session.query(Material).filter_by(project_id=project_id).all()


def update_material(session: Session, material_id: int, **kwargs) -> Material | None:
    mat = session.query(Material).filter_by(id=material_id).first()
    if mat:
        for k, v in kwargs.items():
            setattr(mat, k, v)
    return mat


def add_material(session: Session, project_id: int, name: str) -> Material:
    mat = Material(project_id=project_id, name=name, status="未开始")
    session.add(mat)
    session.flush()
    return mat


def delete_material(session: Session, material_id: int) -> bool:
    mat = session.query(Material).filter_by(id=material_id).first()
    if mat:
        session.delete(mat)
        return True
    return False


# ─── Timeline CRUD ───────────────────────────────────────────────────────────

def get_timelines_by_project(session: Session, project_id: int) -> list[Timeline]:
    return session.query(Timeline).filter_by(project_id=project_id).order_by(Timeline.date).all()


def upsert_timeline(session: Session, timeline_id: int | None, **kwargs) -> Timeline:
    if timeline_id:
        tl = session.query(Timeline).filter_by(id=timeline_id).first()
        for k, v in kwargs.items():
            setattr(tl, k, v)
    else:
        tl = Timeline(**kwargs)
        session.add(tl)
    session.flush()
    return tl


def delete_timeline(session: Session, timeline_id: int) -> bool:
    tl = session.query(Timeline).filter_by(id=timeline_id).first()
    if tl:
        session.delete(tl)
        return True
    return False


# ─── Interview CRUD ──────────────────────────────────────────────────────────

def get_interviews_by_project(session: Session, project_id: int) -> list[Interview]:
    return session.query(Interview).filter_by(project_id=project_id).order_by(Interview.date.desc()).all()


def get_all_interviews(session: Session) -> list[Interview]:
    return session.query(Interview).order_by(Interview.date.desc()).all()


def upsert_interview(session: Session, interview_id: int | None, project_id: int | None = None, **kwargs) -> Interview:
    if interview_id:
        iv = session.query(Interview).filter_by(id=interview_id).first()
        for k, v in kwargs.items():
            setattr(iv, k, v)
    else:
        iv = Interview(project_id=project_id, **kwargs)
        session.add(iv)
    session.flush()
    return iv


def delete_interview(session: Session, interview_id: int) -> bool:
    iv = session.query(Interview).filter_by(id=interview_id).first()
    if iv:
        session.delete(iv)
        return True
    return False


# ─── Mentor CRUD ────────────────────────────────────────────────────────────

def get_all_mentors(session: Session) -> list[Mentor]:
    return session.query(Mentor).order_by(Mentor.created_at.desc()).all()


def search_mentors(session: Session, status: str = "") -> list[Mentor]:
    q = session.query(Mentor)
    if status:
        q = q.filter(Mentor.status == status)
    return q.order_by(Mentor.created_at.desc()).all()


def upsert_mentor(session: Session, mentor_id: int | None, **kwargs) -> Mentor:
    if mentor_id:
        m = session.query(Mentor).filter_by(id=mentor_id).first()
        for k, v in kwargs.items():
            setattr(m, k, v)
    else:
        m = Mentor(**kwargs)
        session.add(m)
    session.flush()
    return m


def delete_mentor(session: Session, mentor_id: int) -> bool:
    m = session.query(Mentor).filter_by(id=mentor_id).first()
    if m:
        session.delete(m)
        return True
    return False


# ─── Template CRUD ───────────────────────────────────────────────────────────

def get_all_templates(session: Session, category: str = "") -> list[Template]:
    q = session.query(Template)
    if category:
        q = q.filter(Template.category == category)
    return q.order_by(Template.created_at.desc()).all()


def upsert_template(session: Session, template_id: int | None, **kwargs) -> Template:
    if template_id:
        t = session.query(Template).filter_by(id=template_id).first()
        for k, v in kwargs.items():
            setattr(t, k, v)
    else:
        t = Template(**kwargs)
        session.add(t)
    session.flush()
    return t


def delete_template(session: Session, template_id: int) -> bool:
    t = session.query(Template).filter_by(id=template_id).first()
    if t:
        session.delete(t)
        return True
    return False


# ─── Aggregation helpers ─────────────────────────────────────────────────────

def get_project_stats(session: Session) -> dict:
    projects = get_all_projects(session)
    total = len(projects)
    status_counts = {}
    for p in projects:
        status_counts[p.status] = status_counts.get(p.status, 0) + 1
    return {"total": total, "status_counts": status_counts}


def get_upcoming_timelines(session: Session, days: int = 3) -> list[tuple[Timeline, Project]]:
    from datetime import timedelta
    today = date.today()
    cutoff = today + timedelta(days=days)
    results = (
        session.query(Timeline, Project)
        .join(Project, Timeline.project_id == Project.id)
        .filter(Timeline.date >= today)
        .filter(Timeline.date <= cutoff)
        .order_by(Timeline.date)
        .all()
    )
    return [(tl, p) for tl, p in results]


def get_needing_followup_mentors(session: Session) -> list[Mentor]:
    """Return mentors where next_followup_date is today or past."""
    today = date.today()
    return (
        session.query(Mentor)
        .filter(Mentor.next_followup_date <= today)
        .filter(Mentor.status.in_(["已发", "已回复"]))
        .order_by(Mentor.next_followup_date)
        .all()
    )
