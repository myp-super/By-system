"""
保研全程管理 Web v3.0 — Flask Backend
Features: 信息广场爬虫 · 硕士专业查询 · PDF/Excel解析 · 生产级部署
"""
import sys, os, io, re, threading, json, uuid, zipfile
from pathlib import Path
from datetime import date, datetime, timedelta
from werkzeug.utils import secure_filename

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, relationship
import pandas as pd

# ─── App ─────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'baoyan-v3-secret'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
CORS(app)

# ─── Database ────────────────────────────────────────────────────────────────
DB_DIR = Path.home() / "baoyan_data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "data.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass

# ─── Models ──────────────────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    school = Column(String(100), default=""); college = Column(String(100), default="")
    major = Column(String(100), default=""); degree_type = Column(String(20), default="学硕")
    batch = Column(String(20), default="夏令营"); official_link = Column(String(500), default="")
    tags = Column(String(200), default=""); status = Column(String(20), default="计划中")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now); updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    materials = relationship("Material", back_populates="project", cascade="all, delete-orphan")
    timelines = relationship("Timeline", back_populates="project", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="project", cascade="all, delete-orphan")

class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), default=""); status = Column(String(20), default="未开始")
    file_path = Column(String(500), default="")
    project = relationship("Project", back_populates="materials")

class Timeline(Base):
    __tablename__ = "timelines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), default=""); date = Column(Date, nullable=True)
    description = Column(String(200), default="")
    project = relationship("Project", back_populates="timelines")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=True); format_type = Column(String(20), default="线上")
    questions = Column(Text, default=""); self_rating = Column(Integer, default=0)
    summary = Column(Text, default=""); notes = Column(Text, default="")
    project = relationship("Project", back_populates="interviews")

class Mentor(Base):
    __tablename__ = "mentors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), default=""); school = Column(String(100), default="")
    research_direction = Column(String(200), default=""); email = Column(String(100), default="")
    first_contact_date = Column(Date, nullable=True); status = Column(String(20), default="未发")
    reply_summary = Column(Text, default=""); next_followup_date = Column(Date, nullable=True)
    notes = Column(Text, default=""); created_at = Column(DateTime, default=datetime.now)

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), default=""); category = Column(String(50), default="个人陈述")
    content = Column(Text, default="")
    file_path = Column(String(500), default="")       # stored file path on disk
    original_filename = Column(String(300), default="")  # original upload filename
    file_size = Column(Integer, default=0)            # file size in bytes
    created_at = Column(DateTime, default=datetime.now)

class SummerCamp(Base):
    """夏令营/预推免/九推信息"""
    __tablename__ = "summer_camps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    school = Column(String(100), default=""); college = Column(String(100), default="")
    title = Column(String(300), default=""); camp_type = Column(String(20), default="夏令营")
    discipline = Column(String(50), default="");  # 理工/经管/文科/医学/艺术
    apply_start = Column(Date, nullable=True); apply_end = Column(Date, nullable=True)
    camp_start = Column(Date, nullable=True); camp_end = Column(Date, nullable=True)
    official_link = Column(String(500), default=""); description = Column(Text, default="")
    requirements = Column(Text, default=""); benefits = Column(Text, default="")
    source = Column(String(200), default="");  # 信息来源
    is_pinned = Column(Integer, default=0); created_at = Column(DateTime, default=datetime.now)

class GraduateProgram(Base):
    """硕士专业信息"""
    __tablename__ = "graduate_programs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    school = Column(String(100), default=""); college = Column(String(100), default="")
    major = Column(String(200), default=""); degree_type = Column(String(20), default="学硕")
    research_directions = Column(Text, default=""); exam_subjects = Column(Text, default="")
    enrollment_count = Column(Integer, default=0); advisor = Column(String(100), default="")
    official_link = Column(String(500), default=""); tags = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(bind=engine)


# ─── Seed real data on first run ──────────────────────────────────────────
def _seed_database():
    """Pre-populate database with real graduate programs and summer camp data."""
    session = SessionLocal()
    try:
        existing_programs = session.query(GraduateProgram).count()
        existing_camps = session.query(SummerCamp).count()

        if existing_programs == 0:
            from data.seed_data import GRADUATE_PROGRAMS
            import re
            for item in GRADUATE_PROGRAMS:
                # Parse enrollment count: extract digits from strings like "约15人" -> 15
                raw_count = item[6] if len(item) > 6 else "0"
                try:
                    count = int(''.join(c for c in str(raw_count) if c.isdigit())) if raw_count else 0
                except:
                    count = 0
                p = GraduateProgram(
                    school=item[0], college=item[1], major=item[2],
                    degree_type=item[3], research_directions=item[4],
                    exam_subjects=item[5], enrollment_count=count,
                    advisor=item[7] if len(item) > 7 else "",
                    official_link="", tags="",
                )
                session.add(p)
            session.commit()
            print(f"  [Seed] Added {len(GRADUATE_PROGRAMS)} graduate programs")

        if existing_camps == 0:
            from data.seed_data import SUMMER_CAMP_DATA
            for item in SUMMER_CAMP_DATA:
                c = SummerCamp(
                    school=item[0], college=item[1], title=item[2],
                    camp_type=item[3], discipline=item[4],
                    apply_start=date.fromisoformat(item[5]) if item[5] else None,
                    apply_end=date.fromisoformat(item[6]) if item[6] else None,
                    camp_start=date.fromisoformat(item[7]) if item[7] else None,
                    camp_end=date.fromisoformat(item[8]) if item[8] else None,
                    official_link=item[9], description=item[10],
                    requirements=item[11], benefits=item[12] if len(item) > 12 else "",
                    source=item[13] if len(item) > 13 else "",
                )
                session.add(c)
            session.commit()
            print(f"  [Seed] Added {len(SUMMER_CAMP_DATA)} summer camp entries")
    except Exception as e:
        session.rollback()
        print(f"  [Seed] Error: {e}")
    finally:
        session.close()


_seed_database()

# ─── Constants ───────────────────────────────────────────────────────────────
PROJECT_STATUSES = ["计划中","已报名","等待通知","入营","参营中","优营(拟录取)","未通过","已放弃"]
DEFAULT_MATERIALS = ["简历","个人陈述","成绩单","排名证明","推荐信","英语成绩","证书扫描件"]
DISCIPLINES = ["理科","工科","经管","文科","医学","艺术","农学","法学","教育","全部"]

UNIVERSITIES_MAJOR = [
    "计算机科学与技术","软件工程","人工智能","数据科学","电子信息","信息与通信工程",
    "控制科学与工程","电子科学与技术","网络空间安全","集成电路","机械工程","电气工程",
    "土木工程","材料科学与工程","化学工程","环境科学与工程","生物医学工程",
    "数学","物理学","化学","生物学","统计学",
    "金融学","经济学","管理学","工商管理","会计学","法学","新闻传播学",
    "临床医学","药学","基础医学","公共卫生","护理学",
    "中国语言文学","外国语言文学","哲学","历史学","社会学","心理学",
    "设计学","美术学","音乐学","建筑学","城乡规划学","风景园林学"
]

# Load university list: prefer scraped data (520 schools), fall back to bundled
ALL_SCHOOLS = []
try:
    uni_file = Path(__file__).parent / 'data' / 'all_universities.json'
    if uni_file.exists():
        with open(uni_file, 'r', encoding='utf-8') as f:
            ALL_SCHOOLS = json.load(f)
        if ALL_SCHOOLS:
            print(f"  [Data] Loaded {len(ALL_SCHOOLS)} universities from 研招网")
except Exception:
    pass

if not ALL_SCHOOLS:
    ALL_SCHOOLS = ["北京大学","清华大学","复旦大学","浙江大学","南京大学","上海交通大学",
                   "中国科学技术大学","哈尔滨工业大学","武汉大学","华中科技大学","中山大学",
                   "四川大学","电子科技大学","西安交通大学","南开大学","天津大学","东南大学",
                   "北京航空航天大学","北京理工大学","同济大学","厦门大学","吉林大学",
                   "山东大学","中南大学","湖南大学","华南理工大学","大连理工大学",
                   "重庆大学","兰州大学","西北工业大学","中国农业大学","北京师范大学",
                   "中国人民大学","华东师范大学","东北大学","中国海洋大学"]

# ═══════════════════════════════════════════════════════════════════════════════
# University Search
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/universities/search')
def search_universities():
    q = request.args.get('q','').strip().lower()
    from data.university_details import DISCIPLINE_RATINGS

    if not q:
        # Show schools with 学科评估 data first
        with_data = [s for s in ALL_SCHOOLS if s in DISCIPLINE_RATINGS]
        without = [s for s in ALL_SCHOOLS if s not in DISCIPLINE_RATINGS]
        results = (with_data + without)[:50]
    else:
        exact = [s for s in ALL_SCHOOLS if s == q]
        starts = [s for s in ALL_SCHOOLS if s.lower().startswith(q) and s not in exact]
        contains = [s for s in ALL_SCHOOLS if q in s.lower() and s not in exact and s not in starts]
        # Prefer schools with rating data
        for lst in [exact, starts, contains]:
            lst.sort(key=lambda s: s not in DISCIPLINE_RATINGS)
        results = (exact + starts + contains)[:30]
    return jsonify(results)

@app.route('/api/university/<name>')
def university_detail(name):
    """Get university details: 学科评估 tags website city type."""
    from data.university_details import DISCIPLINE_RATINGS
    info = DISCIPLINE_RATINGS.get(name)
    if not info:
        for key in DISCIPLINE_RATINGS:
            if key in name or name in key:
                info = DISCIPLINE_RATINGS[key]; name = key
                break
    if not info:
        # Return basic info for any school
        return jsonify({"name": name, "tags": [], "website": "", "city": "",
                        "type": "", "ratings": {}, "program_count": 0,
                        "note": "暂无学科评估数据，为基础信息"})

    session = SessionLocal()
    try:
        pc = session.query(GraduateProgram).filter(GraduateProgram.school.like(f"%{name}%")).count()
    finally:
        session.close()

    return jsonify({"name": name, "tags": info.get("tags",[]),
                    "website": info.get("website",""), "city": info.get("city",""),
                    "type": info.get("type",""), "ratings": info.get("ratings",{}),
                    "program_count": pc})

@app.route('/api/majors')
def get_majors():
    q = request.args.get('q','').strip().lower()
    results = [m for m in UNIVERSITIES_MAJOR if not q or q in m.lower()]
    return jsonify(results[:30])

@app.route('/api/constants')
def get_constants():
    return jsonify(dict(project_statuses=PROJECT_STATUSES, disciplines=DISCIPLINES,
                        majors=UNIVERSITIES_MAJOR))

# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/dashboard')
def dashboard():
    session = SessionLocal()
    try:
        today = date.today()
        projects = session.query(Project).all()
        total = len(projects)
        status_counts = {}
        for p in projects: status_counts[p.status] = status_counts.get(p.status,0) + 1

        upcoming_3d = (session.query(Timeline, Project).join(Project)
                       .filter(Timeline.date >= today, Timeline.date <= today+timedelta(days=3))
                       .order_by(Timeline.date).all())

        this_month = today.month
        all_iv = session.query(Interview).all()
        monthly_iv = sum(1 for iv in all_iv if iv.date and iv.date.month==this_month)

        upcoming_30d = session.query(Timeline).filter(
            Timeline.date >= today, Timeline.date <= today+timedelta(days=30)).count()

        camps_ending = session.query(SummerCamp).filter(
            SummerCamp.apply_end >= today, SummerCamp.apply_end <= today+timedelta(days=7)).count()

        mentors_fu = (session.query(Mentor).filter(Mentor.next_followup_date <= today,
                      Mentor.status.in_(["已发","已回复"])).order_by(Mentor.next_followup_date).all())

        recent = session.query(Project).order_by(Project.created_at.desc()).limit(8).all()
        recent_camps = session.query(SummerCamp).order_by(SummerCamp.created_at.desc()).limit(5).all()

        return jsonify(dict(
            total=total, status_counts=status_counts, monthly_interviews=monthly_iv,
            upcoming_30d_count=upcoming_30d, camps_ending=camps_ending,
            upcoming_3d=[dict(timeline=dict(id=t.id,name=t.name,date=str(t.date),description=t.description),
                              project=dict(id=p.id,school=p.school,major=p.major)) for t,p in upcoming_3d],
            followup_mentors=[dict(id=m.id,name=m.name,school=m.school,status=m.status,
                                   next_followup_date=str(m.next_followup_date) if m.next_followup_date else None) for m in mentors_fu],
            recent_projects=[dict(id=p.id,school=p.school,major=p.major,degree_type=p.degree_type,
                                  status=p.status,batch=p.batch) for p in recent],
            recent_camps=[dict(id=c.id,school=c.school,title=c.title,camp_type=c.camp_type,
                               apply_end=str(c.apply_end) if c.apply_end else None,
                               discipline=c.discipline) for c in recent_camps],
        ))
    finally: session.close()

# ═══════════════════════════════════════════════════════════════════════════════
# Projects CRUD
# ═══════════════════════════════════════════════════════════════════════════════

def _proj_dict(p):
    return dict(id=p.id,school=p.school,college=p.college,major=p.major,
                degree_type=p.degree_type,batch=p.batch,status=p.status,
                official_link=p.official_link,tags=p.tags,notes=p.notes,
                created_at=str(p.created_at)[:19] if p.created_at else None,
                updated_at=str(p.updated_at)[:19] if p.updated_at else None,
                material_count=len(p.materials),
                material_done=sum(1 for m in p.materials if m.status=="已完成"),
                timeline_count=len(p.timelines), interview_count=len(p.interviews))

@app.route('/api/projects')
def get_projects():
    session = SessionLocal()
    try:
        q = session.query(Project)
        kw = request.args.get('q','').strip()
        batch = request.args.get('batch','').strip()
        status = request.args.get('status','').strip()
        if kw:
            like = f"%{kw}%"
            q = q.filter((Project.school.like(like))|(Project.major.like(like))|
                         (Project.college.like(like))|(Project.tags.like(like)))
        if batch: q = q.filter(Project.batch==batch)
        if status: q = q.filter(Project.status==status)
        return jsonify([_proj_dict(p) for p in q.order_by(Project.updated_at.desc()).all()])
    finally: session.close()

@app.route('/api/projects/<int:pid>')
def get_project(pid):
    session = SessionLocal()
    try:
        p = session.query(Project).filter_by(id=pid).first()
        if not p: return jsonify(dict(error="Not found")),404
        r = _proj_dict(p)
        r.update(materials=[dict(id=m.id,name=m.name,status=m.status,file_path=m.file_path) for m in p.materials],
                 timelines=[dict(id=t.id,name=t.name,date=str(t.date) if t.date else None,description=t.description) for t in p.timelines],
                 interviews=[dict(id=iv.id,date=str(iv.date) if iv.date else None,format_type=iv.format_type,
                                  questions=iv.questions,self_rating=iv.self_rating,
                                  summary=iv.summary,notes=iv.notes) for iv in p.interviews])
        return jsonify(r)
    finally: session.close()

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    session = SessionLocal()
    try:
        p = Project(school=data.get('school',''),college=data.get('college',''),
                    major=data.get('major',''),degree_type=data.get('degree_type','学硕'),
                    batch=data.get('batch','夏令营'),status=data.get('status','计划中'),
                    official_link=data.get('official_link',''),tags=data.get('tags',''),
                    notes=data.get('notes',''),created_at=datetime.now(),updated_at=datetime.now())
        session.add(p); session.flush()
        for name in DEFAULT_MATERIALS:
            session.add(Material(project_id=p.id,name=name,status="未开始"))
        session.commit()
        return jsonify(_proj_dict(p)),201
    except Exception as e:
        session.rollback(); return jsonify(dict(error=str(e))),400
    finally: session.close()

@app.route('/api/projects/<int:pid>', methods=['PUT'])
def update_project(pid):
    data = request.json
    session = SessionLocal()
    try:
        p = session.query(Project).filter_by(id=pid).first()
        if not p: return jsonify(dict(error="Not found")),404
        for f in ['school','college','major','degree_type','batch','status','official_link','tags','notes']:
            if f in data: setattr(p,f,data[f])
        p.updated_at = datetime.now(); session.commit()
        return jsonify(_proj_dict(p))
    except Exception as e:
        session.rollback(); return jsonify(dict(error=str(e))),400
    finally: session.close()

@app.route('/api/projects/<int:pid>', methods=['DELETE'])
def delete_project(pid):
    session = SessionLocal()
    try:
        p = session.query(Project).filter_by(id=pid).first()
        if p: session.delete(p); session.commit()
        return jsonify(dict(ok=True))
    finally: session.close()

# ─── Materials / Timelines / Interviews / Mentors / Templates ─────────────────

@app.route('/api/projects/<int:pid>/materials', methods=['GET'])
def get_materials(pid):
    session = SessionLocal()
    mats = session.query(Material).filter_by(project_id=pid).all()
    session.close()
    return jsonify([dict(id=m.id,name=m.name,status=m.status,file_path=m.file_path) for m in mats])

@app.route('/api/materials/<int:mid>', methods=['PUT'])
def update_material(mid):
    data = request.json
    session = SessionLocal()
    m = session.query(Material).filter_by(id=mid).first()
    if m:
        for f in ['name','status','file_path']:
            if f in data: setattr(m,f,data[f])
        session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/projects/<int:pid>/materials', methods=['POST'])
def add_material(pid):
    data = request.json
    session = SessionLocal()
    m = Material(project_id=pid,name=data.get('name',''),status='未开始')
    session.add(m); session.commit()
    r = dict(id=m.id,name=m.name,status=m.status,file_path=m.file_path)
    session.close()
    return jsonify(r),201

@app.route('/api/materials/<int:mid>', methods=['DELETE'])
def delete_material(mid):
    session = SessionLocal()
    m = session.query(Material).filter_by(id=mid).first()
    if m: session.delete(m); session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/projects/<int:pid>/timelines', methods=['GET'])
def get_timelines(pid):
    session = SessionLocal()
    tls = session.query(Timeline).filter_by(project_id=pid).order_by(Timeline.date).all()
    session.close()
    return jsonify([dict(id=t.id,name=t.name,date=str(t.date) if t.date else None,
                         description=t.description) for t in tls])

@app.route('/api/projects/<int:pid>/timelines', methods=['POST'])
def create_timeline(pid):
    data = request.json
    session = SessionLocal()
    d = data.get('date')
    t = Timeline(project_id=pid,name=data.get('name',''),
                 date=date.fromisoformat(d) if d else None,
                 description=data.get('description',''))
    session.add(t); session.commit()
    r = dict(id=t.id,name=t.name,date=str(t.date) if t.date else None,description=t.description)
    session.close()
    return jsonify(r),201

@app.route('/api/timelines/<int:tid>', methods=['PUT'])
def update_timeline(tid):
    data = request.json
    session = SessionLocal()
    t = session.query(Timeline).filter_by(id=tid).first()
    if t:
        for f in ['name','description']:
            if f in data: setattr(t,f,data[f])
        if 'date' in data: t.date = date.fromisoformat(data['date']) if data['date'] else None
        session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/timelines/<int:tid>', methods=['DELETE'])
def delete_timeline(tid):
    session = SessionLocal()
    t = session.query(Timeline).filter_by(id=tid).first()
    if t: session.delete(t); session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/projects/<int:pid>/interviews', methods=['GET'])
def get_interviews(pid):
    session = SessionLocal()
    ivs = session.query(Interview).filter_by(project_id=pid).order_by(Interview.date.desc()).all()
    session.close()
    return jsonify([dict(id=iv.id,date=str(iv.date) if iv.date else None,format_type=iv.format_type,
                         questions=iv.questions,self_rating=iv.self_rating,
                         summary=iv.summary,notes=iv.notes) for iv in ivs])

@app.route('/api/projects/<int:pid>/interviews', methods=['POST'])
def create_interview(pid):
    data = request.json
    session = SessionLocal()
    d = data.get('date')
    iv = Interview(project_id=pid,date=date.fromisoformat(d) if d else None,
                   format_type=data.get('format_type','线上'),questions=data.get('questions',''),
                   self_rating=data.get('self_rating',0),summary=data.get('summary',''),
                   notes=data.get('notes',''))
    session.add(iv); session.commit()
    r = dict(id=iv.id,date=str(iv.date) if iv.date else None,format_type=iv.format_type,self_rating=iv.self_rating)
    session.close()
    return jsonify(r),201

@app.route('/api/interviews/<int:iid>', methods=['PUT'])
def update_interview(iid):
    data = request.json
    session = SessionLocal()
    iv = session.query(Interview).filter_by(id=iid).first()
    if iv:
        for f in ['questions','summary','notes','format_type','self_rating']:
            if f in data: setattr(iv,f,data[f])
        if 'date' in data: iv.date = date.fromisoformat(data['date']) if data['date'] else None
        session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/interviews/<int:iid>', methods=['DELETE'])
def delete_interview(iid):
    session = SessionLocal()
    iv = session.query(Interview).filter_by(id=iid).first()
    if iv: session.delete(iv); session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/mentors', methods=['GET'])
def get_mentors():
    session = SessionLocal()
    status = request.args.get('status','').strip()
    q = session.query(Mentor)
    if status == '__followup__':
        today = date.today()
        q = q.filter(Mentor.next_followup_date <= today, Mentor.status.in_(["已发","已回复"]))
    elif status: q = q.filter(Mentor.status==status)
    mentors = q.order_by(Mentor.created_at.desc()).all()
    session.close()
    return jsonify([dict(id=m.id,name=m.name,school=m.school,research_direction=m.research_direction,
                         email=m.email,first_contact_date=str(m.first_contact_date) if m.first_contact_date else None,
                         status=m.status,reply_summary=m.reply_summary,
                         next_followup_date=str(m.next_followup_date) if m.next_followup_date else None,
                         notes=m.notes) for m in mentors])

@app.route('/api/mentors', methods=['POST'])
def create_mentor():
    data = request.json
    session = SessionLocal()
    fc = data.get('first_contact_date'); nf = data.get('next_followup_date')
    m = Mentor(name=data.get('name',''),school=data.get('school',''),
               research_direction=data.get('research_direction',''),email=data.get('email',''),
               first_contact_date=date.fromisoformat(fc) if fc else None,
               status=data.get('status','未发'),reply_summary=data.get('reply_summary',''),
               next_followup_date=date.fromisoformat(nf) if nf else None,
               notes=data.get('notes',''))
    session.add(m); session.commit()
    r = dict(id=m.id,name=m.name); session.close()
    return jsonify(r),201

@app.route('/api/mentors/<int:mid>', methods=['PUT'])
def update_mentor(mid):
    data = request.json
    session = SessionLocal()
    m = session.query(Mentor).filter_by(id=mid).first()
    if m:
        for f in ['name','school','research_direction','email','status','reply_summary','notes']:
            if f in data: setattr(m,f,data[f])
        if 'first_contact_date' in data: m.first_contact_date = date.fromisoformat(data['first_contact_date']) if data['first_contact_date'] else None
        if 'next_followup_date' in data: m.next_followup_date = date.fromisoformat(data['next_followup_date']) if data['next_followup_date'] else None
        session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/mentors/<int:mid>', methods=['DELETE'])
def delete_mentor(mid):
    session = SessionLocal()
    m = session.query(Mentor).filter_by(id=mid).first()
    if m: session.delete(m); session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/templates', methods=['GET'])
def get_templates():
    session = SessionLocal()
    cat = request.args.get('category','').strip()
    kw = request.args.get('q','').strip().lower()
    q = session.query(Template)
    if cat: q = q.filter(Template.category==cat)
    templates = q.order_by(Template.created_at.desc()).all()
    session.close()
    result = [dict(id=t.id, title=t.title, category=t.category,
                   content=t.content[:200] if t.content else '',
                   full_content=t.content if t.content else '',
                   file_path=t.file_path, original_filename=t.original_filename,
                   file_size=t.file_size, has_file=bool(t.file_path))
              for t in templates]
    if kw: result = [t for t in result if kw in t['title'].lower() or kw in t.get('full_content','').lower()]
    return jsonify(result)

@app.route('/api/templates', methods=['POST'])
def create_template():
    data = request.json
    session = SessionLocal()
    t = Template(title=data.get('title',''),category=data.get('category','个人陈述'),content=data.get('content',''))
    session.add(t); session.commit()
    r = dict(id=t.id,title=t.title); session.close()
    return jsonify(r),201

@app.route('/api/templates/<int:tid>', methods=['PUT'])
def update_template(tid):
    data = request.json
    session = SessionLocal()
    t = session.query(Template).filter_by(id=tid).first()
    if t:
        for f in ['title','category','content']:
            if f in data: setattr(t,f,data[f])
        session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/templates/<int:tid>', methods=['DELETE'])
def delete_template(tid):
    session = SessionLocal()
    t = session.query(Template).filter_by(id=tid).first()
    if t: session.delete(t); session.commit()
    session.close()
    return jsonify(dict(ok=True))

# ═══════════════════════════════════════════════════════════════════════════════
# File Upload — now supports PDF, Excel, Word, TXT
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_pdf(file_bytes):
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: text += t + "\n"
        return text.strip()
    except Exception:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            return "\n".join(p.extract_text() or "" for p in reader.pages).strip()
        except Exception:
            return ""

def _parse_excel(file_bytes):
    try:
        dfs = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
        lines = []
        for sheet_name, df in dfs.items():
            lines.append(f"--- {sheet_name} ---")
            lines.append(df.to_string(max_rows=50))
            lines.append("")
        return "\n".join(lines)
    except Exception:
        return ""

def _parse_docx(file_bytes):
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        return ""

@app.route('/api/templates/upload', methods=['POST'])
def upload_template_file():
    """Upload one or multiple files — store on disk in original format."""
    files = request.files.getlist('files') or ([request.files['file']] if 'file' in request.files else [])
    if not files or all(not f.filename for f in files):
        return jsonify(dict(error="未选择文件")), 400

    upload_dir = DB_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    session = SessionLocal()
    results = []

    try:
        for file in files:
            if not file.filename:
                continue
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            stored_name = f"{uuid.uuid4().hex}{ext}"
            stored_path = upload_dir / stored_name
            file_bytes = file.read()
            file_size = len(file_bytes)

            with open(stored_path, 'wb') as f:
                f.write(file_bytes)

            t = Template(
                title=file.filename,
                category=request.form.get('category', '其他'),
                content='',
                file_path=str(stored_path),
                original_filename=file.filename,
                file_size=file_size,
            )
            session.add(t)
            session.flush()
            results.append(dict(id=t.id, title=file.filename, file_size=file_size, ext=ext))

        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify(dict(error=str(e))), 400
    finally:
        session.close()

    return jsonify(dict(files=results, count=len(results)))

@app.route('/api/templates/download-batch', methods=['POST'])
def download_batch_templates():
    """Download selected templates as a ZIP file."""
    ids = request.json.get('ids', []) if request.json else []
    if not ids:
        return jsonify(dict(error="未选择文件")), 400

    session = SessionLocal()
    try:
        templates = session.query(Template).filter(Template.id.in_(ids)).all()

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for t in templates:
                if t.file_path and Path(t.file_path).exists():
                    zf.write(t.file_path, t.original_filename or t.title)
                elif t.content:
                    # Text-only template: write as .txt
                    zf.writestr(t.title if '.' in t.title else t.title + '.txt', t.content)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'templates_batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )
    finally:
        session.close()

@app.route('/api/templates/<int:tid>/download')
def download_template(tid):
    """Download the original file (attachment)."""
    session = SessionLocal()
    try:
        t = session.query(Template).filter_by(id=tid).first()
        if not t or not t.file_path:
            return jsonify(dict(error="文件不存在")), 404
        file_path = Path(t.file_path)
        if not file_path.exists():
            return jsonify(dict(error="文件已被删除")), 404
        return send_file(str(file_path), as_attachment=True,
                         download_name=t.original_filename or t.title,
                         mimetype='application/octet-stream')
    finally:
        session.close()

@app.route('/api/templates/<int:tid>/preview')
def preview_template(tid):
    """Preview file inline in browser (Content-Disposition: inline)."""
    session = SessionLocal()
    try:
        t = session.query(Template).filter_by(id=tid).first()
        if not t or not t.file_path:
            return jsonify(dict(error="文件不存在")), 404
        file_path = Path(t.file_path)
        if not file_path.exists():
            return jsonify(dict(error="文件已被删除")), 404

        # Determine MIME type from extension
        ext = os.path.splitext(t.original_filename or t.title)[1].lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain; charset=utf-8',
            '.md': 'text/plain; charset=utf-8',
            '.csv': 'text/csv; charset=utf-8',
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
        }
        mime = mime_map.get(ext, 'application/octet-stream')
        return send_file(str(file_path), mimetype=mime)
    finally:
        session.close()

# ═══════════════════════════════════════════════════════════════════════════════
# Summer Camp Hub (信息广场)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/camps')
def get_camps():
    session = SessionLocal()
    try:
        q = session.query(SummerCamp)
        school = request.args.get('school','').strip()
        camp_type = request.args.get('camp_type','').strip()
        discipline = request.args.get('discipline','').strip()
        kw = request.args.get('q','').strip()
        if school: q = q.filter(SummerCamp.school.like(f"%{school}%"))
        if camp_type: q = q.filter(SummerCamp.camp_type==camp_type)
        if discipline: q = q.filter(SummerCamp.discipline==discipline)
        if kw: q = q.filter((SummerCamp.title.like(f"%{kw}%"))|(SummerCamp.school.like(f"%{kw}%")))

        camps = q.order_by(SummerCamp.is_pinned.desc(), SummerCamp.apply_end.asc().nullslast(),
                           SummerCamp.created_at.desc()).all()
        return jsonify([dict(id=c.id,school=c.school,college=c.college,title=c.title,
                             camp_type=c.camp_type,discipline=c.discipline,
                             apply_start=str(c.apply_start) if c.apply_start else None,
                             apply_end=str(c.apply_end) if c.apply_end else None,
                             camp_start=str(c.camp_start) if c.camp_start else None,
                             camp_end=str(c.camp_end) if c.camp_end else None,
                             official_link=c.official_link,description=c.description,
                             requirements=c.requirements,benefits=c.benefits,
                             source=c.source,is_pinned=c.is_pinned,
                             created_at=str(c.created_at)[:19] if c.created_at else None)
                        for c in camps])
    finally: session.close()

@app.route('/api/camps', methods=['POST'])
def create_camp():
    data = request.json
    session = SessionLocal()
    try:
        c = SummerCamp(
            school=data.get('school',''),college=data.get('college',''),
            title=data.get('title',''),camp_type=data.get('camp_type','夏令营'),
            discipline=data.get('discipline',''),
            apply_start=date.fromisoformat(data['apply_start']) if data.get('apply_start') else None,
            apply_end=date.fromisoformat(data['apply_end']) if data.get('apply_end') else None,
            camp_start=date.fromisoformat(data['camp_start']) if data.get('camp_start') else None,
            camp_end=date.fromisoformat(data['camp_end']) if data.get('camp_end') else None,
            official_link=data.get('official_link',''),description=data.get('description',''),
            requirements=data.get('requirements',''),benefits=data.get('benefits',''),
            source=data.get('source','手动添加'))
        session.add(c); session.commit()
        return jsonify(dict(id=c.id,title=c.title)),201
    except Exception as e:
        session.rollback()
        return jsonify(dict(error=str(e))),400
    finally: session.close()

@app.route('/api/camps/<int:cid>', methods=['PUT'])
def update_camp(cid):
    data = request.json
    session = SessionLocal()
    try:
        c = session.query(SummerCamp).filter_by(id=cid).first()
        if c:
            for f in ['school','college','title','camp_type','discipline','official_link',
                      'description','requirements','benefits','source','is_pinned']:
                if f in data: setattr(c,f,data[f])
            for df in ['apply_start','apply_end','camp_start','camp_end']:
                if df in data:
                    setattr(c,df,date.fromisoformat(data[df]) if data[df] else None)
            session.commit()
        return jsonify(dict(ok=True))
    finally: session.close()

@app.route('/api/camps/<int:cid>', methods=['DELETE'])
def delete_camp(cid):
    session = SessionLocal()
    c = session.query(SummerCamp).filter_by(id=cid).first()
    if c: session.delete(c); session.commit()
    session.close()
    return jsonify(dict(ok=True))

# ─── Web Scraping for 保研信息 ────────────────────────────────────────────────

SCRAPER_CACHE = {"data": [], "timestamp": None}

def _fetch_url(url, timeout=8):
    """Fetch a URL with proper headers, return soup or None."""
    import requests
    from bs4 import BeautifulSoup
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception:
        return None

def _scrape_baoyantong():
    """Fetch the latest 保研通知 from multiple public sources."""
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings()

    results = []

    # Source 1: 各高校研究生招生信息网 — common summer camp announcement URLs
    university_urls = [
        ("清华大学", "https://yz.tsinghua.edu.cn"),
        ("北京大学", "https://admission.pku.edu.cn"),
        ("浙江大学", "http://www.grs.zju.edu.cn"),
    ]

    for school, url in university_urls:
        soup = _fetch_url(url, timeout=6)
        if soup:
            try:
                for item in soup.select('a[href]')[:15]:
                    title = item.get_text(strip=True)
                    href = item.get('href', '')
                    if title and len(title) > 5 and any(k in title for k in ['夏令营','推免','研究生','招生','硕士','博士','保研','申请','选拔']):
                        link = href if href.startswith('http') else url + href
                        results.append(dict(title=title[:200], link=link, school=school, source=f'{school}研招网'))
            except Exception:
                pass

    # Source 2: 保研论坛 RSS-style scrape
    try:
        soup = _fetch_url('https://www.eeban.com/forum.php?mod=forumdisplay&fid=43', timeout=8)
        if soup:
            for item in soup.select('th.common, th.new, .xst, a.xst')[:15]:
                a = item.select_one('a[href]') or (item if item.name == 'a' else None)
                if a:
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    if title and len(title) > 5:
                        results.append(dict(title=title[:200], link=href if href.startswith('http') else f'https://www.eeban.com/{href}', school='', source='保研论坛'))
    except Exception:
        pass

    # Source 3: 中国研究生招生信息网
    try:
        soup = _fetch_url('https://yz.chsi.com.cn', timeout=6)
        if soup:
            for item in soup.select('a[href]')[:10]:
                title = item.get_text(strip=True)
                if title and len(title) > 5:
                    href = item.get('href', '')
                    results.append(dict(title=title[:200], link=href if href.startswith('http') else f'https://yz.chsi.com.cn{href}', school='', source='研招网'))
    except Exception:
        pass

    # If all online sources fail, return data from our seed database
    if not results:
        session = SessionLocal()
        try:
            camps = session.query(SummerCamp).order_by(SummerCamp.created_at.desc()).limit(15).all()
            results = [dict(title=c.title or f'{c.school} {c.college} {c.camp_type}',
                           link=c.official_link or '', school=c.school,
                           source='本地数据库',
                           description=c.description[:150] if c.description else '',
                           requirements=c.requirements[:150] if c.requirements else '',
                           camp_type=c.camp_type, discipline=c.discipline)
                       for c in camps]
        finally:
            session.close()

    return results

@app.route('/api/camps/scrape', methods=['POST'])
def trigger_scrape():
    """Trigger web scraping to fetch latest camp info."""
    global SCRAPER_CACHE
    data = request.json or {}
    url = data.get('url','').strip()
    manual = data.get('manual','').strip()

    if manual:
        # User pasted raw text — parse it
        results = [dict(title=line.strip()[:200], link='', school='',
                        source='手动粘贴') for line in manual.split('\n') if line.strip()]
        return jsonify(dict(results=results, count=len(results)))

    if url:
        # Scrape a specific URL provided by user
        try:
            import requests
            from bs4 import BeautifulSoup
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            for item in soup.select('tr, li, .item, .notice-item, article, .card, .list-item')[:20]:
                title_el = item.select_one('a, h3, h4, .title')
                if title_el:
                    results.append(dict(
                        title=title_el.get_text(strip=True)[:200],
                        link='',
                        school='',
                        source=url[:50],
                    ))
            if not results:
                # Try plain text extraction
                text = soup.get_text(separator='\n')
                lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10][:20]
                results = [dict(title=l[:200], link='', school='', source=url[:50]) for l in lines]
            return jsonify(dict(results=results[:20], count=len(results[:20])))
        except Exception as e:
            return jsonify(dict(error=str(e))), 400

    # Default: scrape known sources
    results = _scrape_baoyantong()
    SCRAPER_CACHE = {"data": results, "timestamp": datetime.now().isoformat()}
    return jsonify(dict(results=results, count=len(results),
                        note="来自公开信息源。请核实信息准确性后使用。"))

@app.route('/api/camps/scrape/save', methods=['POST'])
def save_scraped():
    """Batch save scraped items as summer camp entries."""
    items = request.json.get('items', [])
    session = SessionLocal()
    saved = 0
    try:
        for item in items:
            c = SummerCamp(
                school=item.get('school',''), title=item.get('title',''),
                camp_type=item.get('camp_type','夏令营'),
                discipline=item.get('discipline',''),
                official_link=item.get('link',''),
                description=item.get('description',''),
                source=item.get('source','网络采集'),
            )
            session.add(c)
            saved += 1
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify(dict(error=str(e))), 400
    finally: session.close()
    return jsonify(dict(saved=saved))

# ═══════════════════════════════════════════════════════════════════════════════
# Graduate Program Search (硕士专业查询)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/programs')
def get_programs():
    session = SessionLocal()
    try:
        q = session.query(GraduateProgram)
        school = request.args.get('school','').strip()
        major = request.args.get('major','').strip()
        degree = request.args.get('degree_type','').strip()
        kw = request.args.get('q','').strip()
        if school: q = q.filter(GraduateProgram.school.like(f"%{school}%"))
        if major: q = q.filter(GraduateProgram.major.like(f"%{major}%"))
        if degree: q = q.filter(GraduateProgram.degree_type==degree)
        if kw: q = q.filter((GraduateProgram.school.like(f"%{kw}%"))|
                            (GraduateProgram.major.like(f"%{kw}%"))|
                            (GraduateProgram.research_directions.like(f"%{kw}%")))
        programs = q.order_by(GraduateProgram.created_at.desc()).all()
        return jsonify([dict(id=p.id,school=p.school,college=p.college,major=p.major,
                             degree_type=p.degree_type,
                             research_directions=p.research_directions,
                             exam_subjects=p.exam_subjects,
                             enrollment_count=p.enrollment_count,
                             advisor=p.advisor,official_link=p.official_link,
                             tags=p.tags) for p in programs])
    finally: session.close()

@app.route('/api/programs', methods=['POST'])
def create_program():
    data = request.json
    session = SessionLocal()
    try:
        p = GraduateProgram(
            school=data.get('school',''),college=data.get('college',''),
            major=data.get('major',''),degree_type=data.get('degree_type','学硕'),
            research_directions=data.get('research_directions',''),
            exam_subjects=data.get('exam_subjects',''),
            enrollment_count=data.get('enrollment_count',0),
            advisor=data.get('advisor',''),
            official_link=data.get('official_link',''),
            tags=data.get('tags',''))
        session.add(p); session.commit()
        return jsonify(dict(id=p.id,major=p.major)),201
    except Exception as e:
        session.rollback()
        return jsonify(dict(error=str(e))),400
    finally: session.close()

@app.route('/api/programs/<int:gid>', methods=['PUT'])
def update_program(gid):
    data = request.json
    session = SessionLocal()
    p = session.query(GraduateProgram).filter_by(id=gid).first()
    if p:
        for f in ['school','college','major','degree_type','research_directions',
                  'exam_subjects','enrollment_count','advisor','official_link','tags']:
            if f in data: setattr(p,f,data[f])
        session.commit()
    session.close()
    return jsonify(dict(ok=True))

@app.route('/api/programs/<int:gid>', methods=['DELETE'])
def delete_program(gid):
    session = SessionLocal()
    p = session.query(GraduateProgram).filter_by(id=gid).first()
    if p: session.delete(p); session.commit()
    session.close()
    return jsonify(dict(ok=True))


# ═══════════════════════════════════════════════════════════════════════════════
# Export
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/export')
def export_excel():
    session = SessionLocal()
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            projs = session.query(Project).all()
            if projs:
                pd.DataFrame([_proj_dict(p) for p in projs]).to_excel(writer, sheet_name='项目', index=False)

            camps = session.query(SummerCamp).all()
            if camps:
                pd.DataFrame([dict(id=c.id,school=c.school,college=c.college,title=c.title,
                                   camp_type=c.camp_type,apply_start=str(c.apply_start),
                                   apply_end=str(c.apply_end),official_link=c.official_link)
                              for c in camps]).to_excel(writer, sheet_name='夏令营信息', index=False)

            programs = session.query(GraduateProgram).all()
            if programs:
                pd.DataFrame([dict(id=p.id,school=p.school,college=p.college,major=p.major,
                                   degree_type=p.degree_type,research_directions=p.research_directions)
                              for p in programs]).to_excel(writer, sheet_name='硕士专业', index=False)

            mentors = session.query(Mentor).all()
            if mentors:
                pd.DataFrame([dict(id=m.id,name=m.name,school=m.school,status=m.status,
                                   email=m.email) for m in mentors]).to_excel(writer, sheet_name='导师', index=False)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True,
                         download_name=f'baoyan_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    finally: session.close()

# ─── HTML ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ═══════════════════════════════════════════════════════════════════════════════
# Entry Point — supports both dev (Flask) and production (waitress)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--prod', action='store_true', help='Run with waitress (production)')
    ap.add_argument('--port', type=int, default=5000, help='Port (default: 5000)')
    args = ap.parse_args()

    print("=" * 50)
    print("  保研全程管理 Web v3.0")
    print(f"  Database: {DB_PATH}")
    print(f"  URL:      http://localhost:{args.port}")
    print("=" * 50)

    if args.prod:
        try:
            from waitress import serve
            print("  [Production mode — Waitress WSGI server]")
            serve(app, host='0.0.0.0', port=args.port)
        except ImportError:
            print("  waitress not installed, falling back to Flask dev server")
            app.run(debug=False, host='0.0.0.0', port=args.port)
    else:
        app.run(debug=True, host='0.0.0.0', port=args.port)
