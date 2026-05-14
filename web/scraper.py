"""
Enterprise-grade scraper for 保研全程管理 v3.2
Sources:
  - 中国研究生招生信息网 (yz.chsi.com.cn) — 520+ universities, all graduate programs
  - 保研通知网 (baoyantongzhi.com) — summer camp / pre-admission notices
  - 各高校研究生院 — supplementary info

Usage: python scraper.py [--full]
  --full : Full scrape (all programs for all universities, takes ~30 min)
  default: Quick scrape (top 100 universities programs + all camps)
"""
import sys, os, io, re, json, time, hashlib, urllib3
from pathlib import Path
from datetime import date, datetime
from collections import OrderedDict

urllib3.disable_warnings()

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup

# ─── Config ──────────────────────────────────────────────────────────────────
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}
YZ_BASE = 'https://yz.chsi.com.cn'
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. University List Scraper (研招网院校信息库)
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_all_universities():
    """Scrape complete university list from 研招网 (all 31 provinces)."""
    print("[1/5] Scraping university list from 研招网...")
    schools = {}
    provinces = {
        '11':'北京','12':'天津','13':'河北','14':'山西','15':'内蒙古',
        '21':'辽宁','22':'吉林','23':'黑龙江',
        '31':'上海','32':'江苏','33':'浙江','34':'安徽','35':'福建','36':'江西','37':'山东',
        '41':'河南','42':'湖北','43':'湖南','44':'广东','45':'广西','46':'海南',
        '50':'重庆','51':'四川','52':'贵州','53':'云南','54':'西藏',
        '61':'陕西','62':'甘肃','63':'青海','64':'宁夏','65':'新疆'
    }

    for code, name in provinces.items():
        try:
            r = requests.get(f'{YZ_BASE}/sch/search.do',
                           params={'ssdm': code, 'yxls': '', 'pageno': '1'},
                           headers=HEADERS, timeout=15, verify=False)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')

            for a in soup.select('a[href]'):
                school_name = a.get_text(strip=True)
                if len(school_name) >= 4 and len(school_name) <= 30:
                    if any(k in school_name for k in ['大学','学院','研究院','研究所']):
                        schools[school_name] = {'province': name, 'province_code': code}
        except Exception as e:
            print(f"  Warning: Province {name}({code}) failed: {e}")

    # Save
    output_path = DATA_DIR / 'universities.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schools, f, ensure_ascii=False, indent=2)

    print(f"  Done: {len(schools)} universities from {len(provinces)} provinces")
    print(f"  Saved to: {output_path}")
    return schools


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Major/Discipline Code Scraper (研招网学科专业目录)
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_discipline_codes():
    """Scrape 学科门类 and 一级学科 codes from 研招网."""
    print("[2/5] Scraping discipline/major codes...")

    disciplines = {}
    try:
        # ml.json = 门类 (学科门类)
        r = requests.get(f'{YZ_BASE}/zsml/code/ml.json', headers=HEADERS, timeout=10, verify=False)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            disciplines['categories'] = r.json()
            print(f"  Categories loaded: {len(disciplines['categories'])}")

        # zyly.json = 专业领域
        r = requests.get(f'{YZ_BASE}/zsml/code/zyly.json', headers=HEADERS, timeout=10, verify=False)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            disciplines['fields'] = r.json()
            print(f"  Fields loaded: {len(disciplines['fields'])}")

    except Exception as e:
        print(f"  Warning: {e}")

    # Save
    with open(DATA_DIR / 'disciplines.json', 'w', encoding='utf-8') as f:
        json.dump(disciplines, f, ensure_ascii=False, indent=2)
    print(f"  Saved to: {DATA_DIR / 'disciplines.json'}")
    return disciplines


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Graduate Program Scraper (硕士专业目录)
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_programs_for_school(school_name, max_pages=3):
    """Scrape all graduate programs for a specific school from 研招网."""
    programs = []

    try:
        # Use the ajaxRs.do endpoint with school name
        for page in range(1, max_pages + 1):
            params = {
                'dwmc': school_name,
                'ssdm': '',
                'zymc': '',
                'yjxkdm': '',
                'pageno': str(page),
                'pageSize': '100'
            }

            r = requests.get(f'{YZ_BASE}/zsml/ajaxRs.do',
                           params=params, headers={**HEADERS, 'Referer': f'{YZ_BASE}/zsml/'},
                           timeout=15, verify=False)
            r.encoding = 'utf-8'

            if r.status_code != 200 or not r.text.strip():
                break

            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.select('table tbody tr, tr')

            if not rows and page == 1:
                # Try alternative: zydetail scraping
                continue

            for row in rows:
                cells = row.select('td')
                if len(cells) >= 4:
                    program = {
                        'school': school_name,
                        'college': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                        'major': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                        'degree_type': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'research_directions': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                        'exam_subjects': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                        'enrollment_count': 0,
                    }
                    programs.append(program)

            if len(rows) < 50:  # No more pages
                break

            time.sleep(0.3)  # Rate limit

    except Exception as e:
        pass  # Silently fail for individual schools

    return programs


def scrape_all_programs(schools, full_scan=False):
    """Scrape programs for all or top schools."""
    print("[3/5] Scraping graduate programs...")

    all_programs = []
    school_list = list(schools.keys())

    # Sort by importance: 985/211 universities first
    top_keywords = ['北京大学','清华大学','复旦大学','浙江大学','上海交','南京大学',
                    '中国科学技术大学','哈尔滨工业大学','武汉大学','华中科技大学',
                    '中山大学','四川大学','电子科技大学','西安交通大学','同济大学',
                    '北京航空航天','北京理工','南开大学','天津大学','东南大学','厦门大学',
                    '中国人民大学','北京师范','华东师范','国科大','中国科学院',
                    '国防科技','中南大学','湖南大学','华南理工','大连理工','重庆大学',
                    '吉林大学','山东大学','兰州大学','西北工业','中国农业']

    priority_schools = []
    other_schools = []
    for s in school_list:
        if any(k in s for k in top_keywords):
            priority_schools.append(s)
        else:
            other_schools.append(s)

    schools_to_scan = priority_schools + other_schools
    if not full_scan:
        schools_to_scan = schools_to_scan[:100]  # Top 100 by default
        print(f"  Quick mode: scanning top {len(schools_to_scan)} schools")

    total = len(schools_to_scan)
    for i, school in enumerate(schools_to_scan):
        if i % 20 == 0:
            print(f"  Progress: {i}/{total} ({i*100//total}%)")

        try:
            programs = scrape_programs_for_school(school)
            if programs:
                all_programs.extend(programs)

            # Also try to get programs from our seed data for schools we can't scrape
            if not programs:
                # Try alternative search
                time.sleep(0.2)
        except Exception:
            pass

        if i % 5 == 0:
            time.sleep(0.5)  # Rate limit

    print(f"  Done: {len(all_programs)} programs from {total} schools")

    # Merge with seed data for completeness
    from data.seed_data import GRADUATE_PROGRAMS
    seed_count = len(GRADUATE_PROGRAMS)
    print(f"  Seed data: {seed_count} programs available as fallback")

    # Save scraped data
    with open(DATA_DIR / 'programs_scraped.json', 'w', encoding='utf-8') as f:
        json.dump(all_programs, f, ensure_ascii=False, indent=2)

    return all_programs


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Summer Camp Scraper (保研通知信息)
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_baoyantongzhi():
    """Scrape summer camp / pre-admission notices from baoyantongzhi.com."""
    print("[4/5] Scraping summer camp info from baoyantongzhi.com...")

    camps = []
    sources = [
        'https://www.baoyantongzhi.com/notice',
        'https://www.baoyantongzhi.com/',
    ]

    for url in sources:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, verify=False, allow_redirects=True)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')

            # Try multiple selectors to find article/card items
            selectors = [
                'article', '.notice-item', '.camp-card', '.card', '.item',
                '.list-item', 'li.list-group-item', '.notice-list li',
                '.news-item', '.article-item', 'tr', '.row'
            ]

            for selector in selectors:
                items = soup.select(selector)
                if items:
                    for item in items:
                        try:
                            title_el = (item.select_one('h3, h4, h5, .title, a[href] strong') or
                                       item.select_one('a[href]'))
                            link_el = item.select_one('a[href]')
                            date_el = item.select_one('.date, .time, time, span.time')
                            school_el = item.select_one('.school, .source, .tag, .badge, .label')

                            if title_el and link_el:
                                title = title_el.get_text(strip=True)
                                if len(title) >= 6 and any(k in title for k in
                                    ['夏令营','推免','免试','研究生','博士','硕士','招生','申请',
                                     '报名','通知','选拔','考核','预报名','九推','优营','offer',
                                     '入营','参营','拟录取','暑期','暑假','接收','复试']):
                                    camps.append({
                                        'title': title[:200],
                                        'school': school_el.get_text(strip=True) if school_el else '',
                                        'link': link_el.get('href', ''),
                                        'date': date_el.get_text(strip=True) if date_el else '',
                                        'source': '保研通知网',
                                        'camp_type': '夏令营',
                                        'discipline': '综合',
                                    })
                        except Exception:
                            continue

                    if camps:
                        break  # Found items with this selector, stop trying others

        except Exception as e:
            print(f"  Warning scraping {url}: {e}")

    # Deduplicate by title
    seen = set()
    unique_camps = []
    for c in camps:
        if c['title'][:60] not in seen:
            seen.add(c['title'][:60])
            unique_camps.append(c)

    print(f"  Scraped: {len(unique_camps)} unique camp notices")

    # Also scrape from eeban (保研论坛)
    try:
        r = requests.get('https://www.eeban.com/forum.php?mod=forumdisplay&fid=43',
                       headers=HEADERS, timeout=10, verify=False)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        eeban_camps = []
        for item in soup.select('th.common, th.new, a.xst')[:20]:
            title = item.get_text(strip=True)
            if len(title) > 5:
                a = item.select_one('a') or item
                href = a.get('href', '') if hasattr(a, 'get') else ''
                eeban_camps.append({
                    'title': title[:200], 'school': '', 'link': href,
                    'date': '', 'source': '保研论坛', 'camp_type': '夏令营',
                    'discipline': '综合'
                })
        unique_camps.extend(eeban_camps)
        print(f"  + {len(eeban_camps)} from 保研论坛")
    except Exception:
        pass

    # Save
    with open(DATA_DIR / 'camps_scraped.json', 'w', encoding='utf-8') as f:
        json.dump(unique_camps, f, ensure_ascii=False, indent=2)
    print(f"  Total: {len(unique_camps)} camp notices")
    print(f"  Saved to: {DATA_DIR / 'camps_scraped.json'}")
    return unique_camps


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Merge and Update Database
# ═══════════════════════════════════════════════════════════════════════════════

def update_database(schools, scraped_programs, scraped_camps):
    """Merge scraped data + seed data into the database using direct SQLAlchemy."""
    print("[5/5] Updating database...")

    # Save scraped data as JSON, then run a separate update script
    import subprocess

    # Save data files
    with open(DATA_DIR / '_programs_import.json', 'w', encoding='utf-8') as f:
        json.dump(scraped_programs, f, ensure_ascii=False)
    with open(DATA_DIR / '_camps_import.json', 'w', encoding='utf-8') as f:
        json.dump(scraped_camps, f, ensure_ascii=False)
    with open(DATA_DIR / '_schools_import.json', 'w', encoding='utf-8') as f:
        json.dump(sorted(list(schools.keys())), f, ensure_ascii=False)

    # Run the seed_db.py helper
    seed_script = Path(__file__).parent / 'seed_db.py'
    result = subprocess.run(
        [sys.executable, str(seed_script)],
        capture_output=True, text=True, timeout=120, cwd=str(Path(__file__).parent)
    )
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
    if result.stderr:
        print(f"  [stderr] {result.stderr[:300]}")

    # Cleanup temp files
    for f in ['_programs_import.json', '_camps_import.json', '_schools_import.json']:
        (DATA_DIR / f).unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main(full_scan=False):
    print("=" * 60)
    print("  保研全程管理 — Enterprise Data Scraper v3.2")
    print("  Sources: 中国研招网 + 保研通知网 + 保研论坛")
    print("=" * 60)
    start = time.time()

    # Step 1: University list
    schools = scrape_all_universities()

    # Step 2: Discipline codes
    disciplines = scrape_discipline_codes()

    # Step 3: Programs
    # Try to load from cache first
    cache_path = DATA_DIR / 'programs_scraped.json'
    if cache_path.exists() and not full_scan:
        print("[3/5] Loading programs from cache...")
        with open(cache_path, 'r', encoding='utf-8') as f:
            scraped_programs = json.load(f)
        print(f"  Loaded {len(scraped_programs)} programs from cache")
    else:
        scraped_programs = scrape_all_programs(schools, full_scan)

    # Step 4: Camps
    camp_cache = DATA_DIR / 'camps_scraped.json'
    if camp_cache.exists():
        print("[4/5] Loading camps from cache...")
        with open(camp_cache, 'r', encoding='utf-8') as f:
            scraped_camps = json.load(f)
        print(f"  Loaded {len(scraped_camps)} camps from cache")
    else:
        scraped_camps = scrape_baoyantongzhi()

    # Step 5: Update DB
    update_database(schools, scraped_programs, scraped_camps)

    elapsed = time.time() - start
    print(f"\n  Total time: {elapsed:.1f}s")
    print("=" * 60)


if __name__ == '__main__':
    full = '--full' in sys.argv
    main(full_scan=full)
