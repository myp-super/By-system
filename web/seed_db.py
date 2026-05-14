"""
Standalone database seeder — reads JSON files and populates DB.
Called by scraper.py as a subprocess to avoid Flask stdout conflicts.
"""
import sys, json, re
from pathlib import Path
from datetime import date, datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ─── Models (must match app.py) ────────────────────────────────────────────

class Base(DeclarativeBase): pass

class GraduateProgram(Base):
    __tablename__ = "graduate_programs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    school = Column(String(100), default="")
    college = Column(String(100), default="")
    major = Column(String(200), default="")
    degree_type = Column(String(20), default="")
    research_directions = Column(Text, default="")
    exam_subjects = Column(Text, default="")
    enrollment_count = Column(Integer, default=0)
    advisor = Column(String(100), default="")
    official_link = Column(String(500), default="")
    tags = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.now)

class SummerCamp(Base):
    __tablename__ = "summer_camps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    school = Column(String(100), default="")
    college = Column(String(100), default="")
    title = Column(String(300), default="")
    camp_type = Column(String(20), default="")
    discipline = Column(String(50), default="")
    apply_start = Column(Date, nullable=True)
    apply_end = Column(Date, nullable=True)
    camp_start = Column(Date, nullable=True)
    camp_end = Column(Date, nullable=True)
    official_link = Column(String(500), default="")
    description = Column(Text, default="")
    requirements = Column(Text, default="")
    benefits = Column(Text, default="")
    source = Column(String(200), default="")
    is_pinned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

# ─── DB Connection ──────────────────────────────────────────────────────────

DB_PATH = Path.home() / "baoyan_data" / "data.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(bind=engine)

# ─── Load data ──────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / 'data'

def load_json(name):
    path = DATA_DIR / name
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

scraped_programs = load_json('_programs_import.json')
scraped_camps = load_json('_camps_import.json')
school_list = load_json('_schools_import.json')

# Also load seed data
try:
    from data.seed_data import GRADUATE_PROGRAMS, SUMMER_CAMP_DATA
except ImportError:
    GRADUATE_PROGRAMS = []
    SUMMER_CAMP_DATA = []

# ─── Seed ────────────────────────────────────────────────────────────────────

session = SessionLocal()
try:
    # Clear existing
    session.query(GraduateProgram).delete()
    session.query(SummerCamp).delete()

    # 1. Graduate Programs
    programs_added = 0
    seen = set()

    for p in scraped_programs:
        key = f"{p.get('school','')}|{p.get('major','')}|{p.get('college','')}"
        if key in seen: continue
        seen.add(key)
        try:
            session.add(GraduateProgram(
                school=p.get('school',''), college=p.get('college',''),
                major=p.get('major',''), degree_type=p.get('degree_type',''),
                research_directions=p.get('research_directions',''),
                exam_subjects=p.get('exam_subjects',''),
                enrollment_count=int(p.get('enrollment_count',0) or 0)
            ))
            programs_added += 1
        except: pass

    # Add seed data as supplement
    for item in GRADUATE_PROGRAMS:
        key = f"{item[0]}|{item[2]}|{item[1]}"
        if key in seen: continue
        seen.add(key)
        try:
            raw = item[6] if len(item)>6 else "0"
            cnt = int(''.join(c for c in str(raw) if c.isdigit())) if raw else 0
            session.add(GraduateProgram(
                school=item[0], college=item[1], major=item[2],
                degree_type=item[3], research_directions=item[4],
                exam_subjects=item[5], enrollment_count=cnt,
                advisor=item[7] if len(item)>7 else ""
            ))
            programs_added += 1
        except: pass

    print(f"Programs: {programs_added} (scraped + seed)")

    # 2. Summer Camps
    camps_added = 0
    seen_camps = set()

    for c in scraped_camps:
        key = c.get('title','')[:80]
        if key in seen_camps: continue
        seen_camps.add(key)
        try:
            session.add(SummerCamp(
                school=c.get('school',''), title=c.get('title','')[:300],
                camp_type=c.get('camp_type','夏令营'), discipline=c.get('discipline','综合'),
                official_link=c.get('link',''), source=c.get('source','')
            ))
            camps_added += 1
        except: pass

    for item in SUMMER_CAMP_DATA:
        key = item[2][:80]
        if key in seen_camps: continue
        seen_camps.add(key)
        try:
            session.add(SummerCamp(
                school=item[0], college=item[1], title=item[2],
                camp_type=item[3], discipline=item[4],
                apply_start=date.fromisoformat(item[5]) if item[5] else None,
                apply_end=date.fromisoformat(item[6]) if item[6] else None,
                camp_start=date.fromisoformat(item[7]) if item[7] else None,
                camp_end=date.fromisoformat(item[8]) if item[8] else None,
                official_link=item[9], description=item[10],
                requirements=item[11], benefits=item[12] if len(item)>12 else "",
                source=item[13] if len(item)>13 else ""
            ))
            camps_added += 1
        except: pass

    print(f"Camps: {camps_added} (scraped + seed)")

    # 3. University list
    if school_list:
        with open(DATA_DIR / 'all_universities.json', 'w', encoding='utf-8') as f:
            json.dump(school_list, f, ensure_ascii=False, indent=2)
    print(f"Universities: {len(school_list)} stored")

    session.commit()
    print("Database update complete.")
except Exception as e:
    session.rollback()
    print(f"Error: {e}")
finally:
    session.close()
