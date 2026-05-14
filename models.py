"""
SQLAlchemy ORM models for 保研全程管理 (Graduate School Application Manager).
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    """院校项目"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    school = Column(String(100), nullable=False, default="")
    college = Column(String(100), nullable=False, default="")
    major = Column(String(100), nullable=False, default="")
    degree_type = Column(String(20), nullable=False, default="学硕")  # 学硕/专硕/直博
    batch = Column(String(20), nullable=False, default="夏令营")      # 夏令营/预推免/九推
    official_link = Column(String(500), nullable=False, default="")
    tags = Column(String(200), nullable=False, default="")
    status = Column(
        String(20), nullable=False, default="计划中"
    )  # 计划中/已报名/等待通知/入营/参营中/优营(拟录取)/未通过/已放弃
    notes = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    materials = relationship("Material", back_populates="project", cascade="all, delete-orphan")
    timelines = relationship("Timeline", back_populates="project", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, school='{self.school}', major='{self.major}')>"


class Material(Base):
    """材料清单"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, default="")
    status = Column(String(20), nullable=False, default="未开始")  # 未开始/进行中/已完成
    file_path = Column(String(500), nullable=False, default="")

    project = relationship("Project", back_populates="materials")

    def __repr__(self):
        return f"<Material(id={self.id}, name='{self.name}', status='{self.status}')>"


class Timeline(Base):
    """时间节点"""
    __tablename__ = "timelines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, default="")
    date = Column(Date, nullable=True)
    description = Column(String(200), nullable=False, default="")

    project = relationship("Project", back_populates="timelines")

    def __repr__(self):
        return f"<Timeline(id={self.id}, name='{self.name}', date={self.date})>"


class Interview(Base):
    """面试/考核记录"""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=True)
    format_type = Column(String(20), nullable=False, default="线上")  # 线上/线下
    questions = Column(Text, nullable=False, default="")
    self_rating = Column(Integer, nullable=False, default=0)  # 1-5星
    summary = Column(Text, nullable=False, default="")
    notes = Column(Text, nullable=False, default="")

    project = relationship("Project", back_populates="interviews")

    def __repr__(self):
        return f"<Interview(id={self.id}, date={self.date}, rating={self.self_rating})>"


class Mentor(Base):
    """导师联系记录"""
    __tablename__ = "mentors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, default="")
    school = Column(String(100), nullable=False, default="")
    research_direction = Column(String(200), nullable=False, default="")
    email = Column(String(100), nullable=False, default="")
    first_contact_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="未发")  # 未发/已发/已回复/积极回复/婉拒
    reply_summary = Column(Text, nullable=False, default="")
    next_followup_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Mentor(id={self.id}, name='{self.name}', school='{self.school}')>"


class Template(Base):
    """文书模板"""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, default="")
    category = Column(String(50), nullable=False, default="个人陈述")  # 个人陈述/邮件模板/感谢信/其他
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Template(id={self.id}, title='{self.title}', category='{self.category}')>"


# 常量定义
DEGREE_TYPES = ["学硕", "专硕", "直博"]
BATCH_TYPES = ["夏令营", "预推免", "九推"]
PROJECT_STATUSES = ["计划中", "已报名", "等待通知", "入营", "参营中", "优营(拟录取)", "未通过", "已放弃"]
MATERIAL_STATUSES = ["未开始", "进行中", "已完成"]
INTERVIEW_FORMATS = ["线上", "线下"]
MENTOR_STATUSES = ["未发", "已发", "已回复", "积极回复", "婉拒"]
TEMPLATE_CATEGORIES = ["个人陈述", "邮件模板", "感谢信", "其他"]
DEFAULT_MATERIALS = ["简历", "个人陈述", "成绩单", "排名证明", "推荐信", "英语成绩", "证书扫描件"]
