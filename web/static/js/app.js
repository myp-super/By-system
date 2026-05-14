/**
 * 保研全程管理 v3.0 — Complete Frontend
 * New: 信息广场爬虫 · 硕士专业查询 · PDF/Excel解析 · 生产部署
 */
const API = '/api';
const STATUSES = ['计划中','已报名','等待通知','入营','参营中','优营(拟录取)','未通过','已放弃'];
const CAMP_TYPES = ['夏令营','预推免','九推'];
const DISCIPLINES = ['理科','工科','经管','文科','医学','艺术','农学','法学','教育','全部'];

// ═══════════════════════════════════════════════════════════════════════════
// Navigation — FIXED with proper event delegation
// ═══════════════════════════════════════════════════════════════════════════
document.getElementById('sidebarNav').addEventListener('click', function(e) {
  const item = e.target.closest('.nav-item');
  if (!item) return;
  e.preventDefault();
  const page = item.dataset.page;
  if (page) navigateTo(page);
});

function navigateTo(page) {
  // Update nav active state
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');

  // Show correct page
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.add('active');

  // Lazy-load page data
  const loaders = {
    dashboard: refreshDashboard, news: loadCamps, programs: loadPrograms,
    kanban: loadKanban, projects: loadProjects, timeline: loadTimeline,
    materials: loadMaterials, interviews: loadInterviews,
    mentors: loadMentors, templates: loadTemplates
  };
  if (loaders[page]) loaders[page]();
}

// ═══════════════════════════════════════════════════════════════════════════
// Toast
// ═══════════════════════════════════════════════════════════════════════════
function toast(msg, type='') {
  const c = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast ${type}`; el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => { el.style.opacity='0'; el.style.transition='opacity .3s'; }, 2500);
  setTimeout(() => el.remove(), 3000);
}

// ═══════════════════════════════════════════════════════════════════════════
// Modal
// ═══════════════════════════════════════════════════════════════════════════
function openModal(title, body, footer) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = body;
  document.getElementById('modalFooter').innerHTML = footer || '';
  document.getElementById('modalOverlay').classList.add('show');
}
function closeModal() { document.getElementById('modalOverlay').classList.remove('show'); }
document.getElementById('modalOverlay').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

// ═══════════════════════════════════════════════════════════════════════════
// API helpers
// ═══════════════════════════════════════════════════════════════════════════
async function get(url) { return (await fetch(API+url)).json(); }
async function post(url, data) {
  const r = await fetch(API+url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  return r.json();
}
async function put(url, data) {
  const r = await fetch(API+url, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  return r.json();
}
async function del(url) { await fetch(API+url, {method:'DELETE'}); }

// ═══════════════════════════════════════════════════════════════════════════
// Searchable dropdown
// ═══════════════════════════════════════════════════════════════════════════
function setupSearch(inputId, resultsId) {
  const input = document.getElementById(inputId);
  const results = document.getElementById(resultsId);
  if (!input || !results) return;
  input.addEventListener('input', async () => {
    const q = input.value.trim();
    if (!q) { results.classList.remove('show'); return; }
    const data = await get(`/universities/search?q=${encodeURIComponent(q)}`);
    results.innerHTML = data.map(s => `<div class="search-result-item" onclick="selectItem('${inputId}','${resultsId}','${s.replace(/'/g,"\\'")}')">${s}</div>`).join('');
    results.classList.add('show');
  });
  input.addEventListener('focus', () => { if (input.value.trim()) results.classList.add('show'); });
  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !results.contains(e.target)) results.classList.remove('show');
  });
}
function selectItem(inputId, resultsId, value) {
  document.getElementById(inputId).value = value;
  document.getElementById(resultsId).classList.remove('show');
}

// ═══════════════════════════════════════════════════════════════════════════
// Badges
// ═══════════════════════════════════════════════════════════════════════════
function statusBadge(s) {
  const m = {'优营(拟录取)':'badge-success','未通过':'badge-danger','已报名':'badge-primary',
             '等待通知':'badge-warning','入营':'badge-info','参营中':'badge-purple',
             '计划中':'badge-gray','已放弃':'badge-gray'};
  return `<span class="badge ${m[s]||'badge-gray'}">${s}</span>`;
}

// ═══════════════════════════════════════════════════════════════════════════
// 1. DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════
async function refreshDashboard() {
  const d = await get('/dashboard');
  const today = new Date();
  document.getElementById('dashboardDate').textContent = `📅 ${today.getFullYear()}年${today.getMonth()+1}月${today.getDate()}日`;

  const sc = document.getElementById('statCards');
  const colors = ['primary','success','warning','purple','info','danger','orange'];
  const items = [
    {v:d.total,l:'申请总数',i:'🎯'},{v:d.monthly_interviews,l:'本月面试',i:'💬'},
    {v:d.upcoming_3d.length,l:'3天截止',i:'⏰'},{v:d.camps_ending,l:'7天截止夏令营',i:'📡'}
  ];
  sc.innerHTML = items.map((x,i) => `<div class="stat-card ${colors[i]}">
    <div class="stat-icon">${x.i}</div><div class="stat-value">${x.v}</div><div class="stat-label">${x.l}</div>
  </div>`).join('');

  // Status counts in extra row
  for (const [s, c] of Object.entries(d.status_counts||{})) {
    sc.innerHTML += `<div class="stat-card"><div class="stat-value" style="font-size:22px">${c}</div><div class="stat-label">${s}</div></div>`;
  }

  // Deadlines
  const dl = document.getElementById('deadlineList');
  dl.innerHTML = d.upcoming_3d.length === 0
    ? '<div class="empty-state"><h3>✅ 暂无即将截止</h3></div>'
    : d.upcoming_3d.map(x => {
        const days = Math.ceil((new Date(x.timeline.date)-today)/86400000);
        const cls = days<=0?'urgent':(days<=1?'soon':'');
        const u = days<=0?'🔴 今天!':(days===1?'🟡 明天':`🔵 还有${days}天`);
        return `<div class="deadline-item ${cls}">${x.project.school} · ${x.timeline.name}<span style="margin-left:auto;font-weight:700">${x.timeline.date} ${u}</span></div>`;
      }).join('');

  // Latest camps
  const lc = document.getElementById('latestCamps');
  lc.innerHTML = !d.recent_camps||d.recent_camps.length===0
    ? '<div class="empty-state"><h3>暂无夏令营信息</h3><p>前往"保研信息广场"采集</p></div>'
    : d.recent_camps.map(c => `<div class="deadline-item">${c.school} · ${c.title||'未命名'} <span style="margin-left:auto">${c.apply_end||''}</span></div>`).join('');

  // Follow-ups
  const fu = document.getElementById('followupList');
  fu.innerHTML = d.followup_mentors.length===0
    ? '<div class="empty-state"><h3>✅ 无待跟进</h3></div>'
    : d.followup_mentors.map(m => `<div class="deadline-item">👤 ${m.name} (${m.school})<span style="margin-left:auto">📅 ${m.next_followup_date||'尽快'}</span></div>`).join('');

  // Recent projects
  const rp = document.getElementById('recentProjects');
  rp.innerHTML = d.recent_projects.length===0
    ? '<div class="empty-state"><h3>暂无项目</h3></div>'
    : d.recent_projects.map(p => `<div class="deadline-item">${p.school} · ${p.major} (${p.degree_type}) ${statusBadge(p.status)}</div>`).join('');
}

// ═══════════════════════════════════════════════════════════════════════════
// 2. SUMMER CAMP INFO HUB (信息广场)
// ═══════════════════════════════════════════════════════════════════════════
async function loadCamps() {
  const q = document.getElementById('campSearch')?.value||'';
  const camp_type = document.getElementById('campTypeFilter')?.value||'';
  const discipline = document.getElementById('campDisciplineFilter')?.value||'';
  const params = new URLSearchParams({q, camp_type, discipline});
  const data = await get(`/camps?${params}`);
  const grid = document.getElementById('campsGrid');

  if (!data.length) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📡</div><h3>暂无夏令营信息</h3><p>点击"采集信息"从网络获取最新通知，或"手动添加"</p></div>`;
    return;
  }

  grid.innerHTML = data.map(c => {
    const today = new Date();
    const end = c.apply_end ? new Date(c.apply_end) : null;
    let badge = '';
    if (end) {
      const days = Math.ceil((end-today)/86400000);
      if (days<0) badge = '<span class="badge badge-danger">已截止</span>';
      else if (days<=3) badge = `<span class="badge badge-warning">${days}天后截止!</span>`;
      else if (days<=7) badge = `<span class="badge badge-info">还有${days}天</span>`;
      else badge = `<span class="badge badge-gray">${days}天后截止</span>`;
    }

    return `<div class="camp-card card">
      <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:10px">
        <h3 style="font-size:17px;color:#1E293B">${c.title||c.school}</h3>
        ${badge}
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
        <span class="badge badge-primary">${c.school}</span>
        <span class="badge badge-info">${c.camp_type||'夏令营'}</span>
        ${c.discipline ? `<span class="badge badge-purple">${c.discipline}</span>` : ''}
        ${c.college ? `<span class="badge badge-gray">${c.college}</span>` : ''}
      </div>
      ${c.apply_start||c.apply_end ? `<div style="font-size:13px;color:#64748B;margin-bottom:8px">
        📅 报名: ${c.apply_start||'?'} ~ ${c.apply_end||'?'}
        ${c.camp_start ? ` | 参营: ${c.camp_start}` : ''}${c.camp_end ? ` ~ ${c.camp_end}` : ''}
      </div>` : ''}
      ${c.description ? `<div style="font-size:14px;color:#475569;margin-bottom:8px;line-height:1.6">${c.description.slice(0,200)}</div>` : ''}
      ${c.requirements ? `<div style="font-size:13px;color:#94A3B8;margin-bottom:8px"><strong>要求:</strong> ${c.requirements.slice(0,150)}</div>` : ''}
      <div style="display:flex;gap:8px;justify-content:flex-end">
        ${c.official_link ? `<a href="${c.official_link}" target="_blank" class="btn btn-sm btn-primary" style="text-decoration:none">🔗 官网链接</a>` : ''}
        <button class="btn btn-sm btn-primary" onclick="showCampModal(${c.id})">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="deleteCamp(${c.id})">删除</button>
      </div>
      ${c.source ? `<div style="font-size:11px;color:#CBD5E1;margin-top:8px">来源: ${c.source}</div>` : ''}
    </div>`;
  }).join('');
}

function showCampModal(cid=null) {
  const load = async () => {
    let c = {school:'',college:'',title:'',camp_type:'夏令营',discipline:'',
             apply_start:'',apply_end:'',camp_start:'',camp_end:'',
             official_link:'',description:'',requirements:'',benefits:'',source:'手动添加'};
    if (cid) {
      const camps = await get('/camps');
      const f = camps.find(x=>x.id===cid);
      if (f) c = f;
    }
    openModal(cid?'编辑夏令营':'添加夏令营', `
      <div class="form-row">
        <div class="form-group"><label class="form-label">院校</label>
          <div class="search-wrapper"><input class="form-input" id="cSchool" value="${c.school||''}" placeholder="搜索院校" autocomplete="off"><div class="search-results" id="cSchoolResults"></div></div></div>
        <div class="form-group"><label class="form-label">学院</label><input class="form-input" id="cCollege" value="${c.college||''}"></div>
      </div>
      <div class="form-group"><label class="form-label">标题</label><input class="form-input" id="cTitle" value="${c.title||''}" placeholder="如: 2026年优秀大学生夏令营"></div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">类型</label><select class="form-input" id="cType">${CAMP_TYPES.map(t=>`<option ${c.camp_type===t?'selected':''}>${t}</option>`).join('')}</select></div>
        <div class="form-group"><label class="form-label">学科</label><select class="form-input" id="cDiscipline">${DISCIPLINES.map(d=>`<option ${c.discipline===d?'selected':''}>${d}</option>`).join('')}</select></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">报名开始</label><input type="date" class="form-input" id="cApplyStart" value="${c.apply_start||''}"></div>
        <div class="form-group"><label class="form-label">报名截止</label><input type="date" class="form-input" id="cApplyEnd" value="${c.apply_end||''}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">参营开始</label><input type="date" class="form-input" id="cCampStart" value="${c.camp_start||''}"></div>
        <div class="form-group"><label class="form-label">参营结束</label><input type="date" class="form-input" id="cCampEnd" value="${c.camp_end||''}"></div>
      </div>
      <div class="form-group"><label class="form-label">官网链接</label><input class="form-input" id="cLink" value="${c.official_link||''}" placeholder="https://..."></div>
      <div class="form-group"><label class="form-label">描述</label><textarea class="form-input" id="cDesc">${c.description||''}</textarea></div>
      <div class="form-group"><label class="form-label">申请要求</label><textarea class="form-input" id="cReq">${c.requirements||''}</textarea></div>
      <div class="form-group"><label class="form-label">福利/待遇</label><textarea class="form-input" id="cBenefits">${c.benefits||''}</textarea></div>
      <div class="form-group"><label class="form-label">信息来源</label><input class="form-input" id="cSource" value="${c.source||''}"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="saveCamp(${cid||'null'})">💾 保存</button>`);
    setupSearch('cSchool', 'cSchoolResults');
  };
  load();
}

async function saveCamp(cid) {
  const data = {
    school: document.getElementById('cSchool').value.trim(),
    college: document.getElementById('cCollege').value.trim(),
    title: document.getElementById('cTitle').value.trim(),
    camp_type: document.getElementById('cType').value,
    discipline: document.getElementById('cDiscipline').value,
    apply_start: document.getElementById('cApplyStart').value||null,
    apply_end: document.getElementById('cApplyEnd').value||null,
    camp_start: document.getElementById('cCampStart').value||null,
    camp_end: document.getElementById('cCampEnd').value||null,
    official_link: document.getElementById('cLink').value.trim(),
    description: document.getElementById('cDesc').value.trim(),
    requirements: document.getElementById('cReq').value.trim(),
    benefits: document.getElementById('cBenefits').value.trim(),
    source: document.getElementById('cSource').value.trim()||'手动添加',
  };
  if (!data.school && !data.title) { toast('请至少填写院校或标题','error'); return; }
  if (cid && cid!=='null') { await put(`/camps/${cid}`, data); }
  else { await post('/camps', data); }
  closeModal(); toast('保存成功','success'); loadCamps();
}

async function deleteCamp(cid) {
  if (!confirm('删除此夏令营信息?')) return;
  await del(`/camps/${cid}`); toast('已删除','success'); loadCamps();
}

// ═══════════════════════════════════════════════════════════════════════════
// Web Scraping Modal
// ═══════════════════════════════════════════════════════════════════════════
function showScrapeModal() {
  openModal('🌐 采集保研信息', `
    <div class="tabs" id="scrapeTabs">
      <button class="tab active" onclick="switchScrapeTab('auto')">自动采集</button>
      <button class="tab" onclick="switchScrapeTab('url')">指定网址</button>
      <button class="tab" onclick="switchScrapeTab('paste')">粘贴文本</button>
    </div>
    <div id="scrapeAuto">
      <p style="margin:16px 0;color:#64748B;line-height:1.8">
        自动从公开信息源（保研通、保研论坛等）采集最新夏令营/预推免通知。<br>
        <strong>注意:</strong> 请核实信息准确性后使用。
      </p>
      <button class="btn btn-primary" onclick="doScrape()">🔍 开始采集</button>
      <div id="scrapeResult" style="margin-top:16px"></div>
    </div>
    <div id="scrapeUrl" style="display:none">
      <div class="form-group"><label class="form-label">输入目标网址</label>
        <input class="form-input" id="scrapeUrlInput" placeholder="https://...">
        <div class="form-hint">输入大学研究生院官网或其他保研信息网站URL</div>
      </div>
      <button class="btn btn-primary" onclick="doScrapeUrl()">🔍 采集该网址</button>
      <div id="scrapeUrlResult" style="margin-top:16px"></div>
    </div>
    <div id="scrapePaste" style="display:none">
      <div class="form-group"><label class="form-label">粘贴原始文本</label>
        <textarea class="form-input" id="scrapePasteText" style="min-height:180px" placeholder="粘贴夏令营通知的文本内容..."></textarea>
      </div>
      <button class="btn btn-primary" onclick="doScrapePaste()">📋 解析文本</button>
      <div id="scrapePasteResult" style="margin-top:16px"></div>
    </div>
  `, `<button class="btn btn-secondary" onclick="closeModal()">关闭</button>`);
}

function switchScrapeTab(tab) {
  document.querySelectorAll('#scrapeTabs .tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`#scrapeTabs .tab:nth-child(${tab==='auto'?1:tab==='url'?2:3})`)?.classList.add('active');
  ['auto','url','paste'].forEach(t => document.getElementById(`scrape${t.charAt(0).toUpperCase()+t.slice(1)}`).style.display = t===tab?'block':'none');
}

async function doScrape() {
  const result = document.getElementById('scrapeResult');
  result.innerHTML = '<div style="text-align:center;padding:20px"><div class="spinner"></div>采集ing...</div>';
  try {
    const r = await fetch(API+'/camps/scrape', {method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    const data = await r.json();
    if (data.error) { result.innerHTML = `<div style="color:var(--danger)">${data.error}</div>`; return; }
    if (!data.results.length) { result.innerHTML = '<div style="color:#64748B">未采集到信息，请尝试其他来源</div>'; return; }
    result.innerHTML = `
      <div style="background:var(--success-bg);border-radius:10px;padding:14px;margin-bottom:12px">
        采集到 <strong>${data.count}</strong> 条信息${data.note ? `<br><small>${data.note}</small>` : ''}
      </div>
      <div style="max-height:300px;overflow-y:auto">${data.results.map((r,i) => `
        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-light)">
          <span style="font-size:12px;color:#94A3B8">${i+1}.</span>
          <div style="flex:1"><strong>${r.title.slice(0,100)}</strong>
            <div style="font-size:12px;color:#94A3B8">${r.school||''} ${r.source||''}</div></div>
          ${r.link ? `<a href="${r.link}" target="_blank" style="font-size:12px">链接</a>` : ''}
          <button class="btn btn-sm btn-success" onclick="saveOneCamp('${r.title.replace(/'/g,"\\'")}','${(r.school||'').replace(/'/g,"\\'")}','${r.source||''}','${(r.link||'').replace(/'/g,"\\'")}')">保存</button>
        </div>`).join('')}</div>
      <button class="btn btn-success" style="margin-top:12px" onclick="saveAllCamps()">💾 批量保存全部</button>
    `;
    window._scrapedData = data.results;
  } catch(e) { result.innerHTML = `<div style="color:var(--danger)">采集失败: ${e.message}</div>`; }
}

async function doScrapeUrl() {
  const url = document.getElementById('scrapeUrlInput').value.trim();
  if (!url) { toast('请输入网址','error'); return; }
  const result = document.getElementById('scrapeUrlResult');
  result.innerHTML = '采集ing...';
  const r = await fetch(API+'/camps/scrape', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
  const data = await r.json();
  if (data.error) { result.innerHTML = `<div style="color:var(--danger)">${data.error}</div>`; return; }
  result.innerHTML = `<div style="background:var(--success-bg);padding:12px;border-radius:10px">采集到 ${data.count} 条 <button class="btn btn-sm btn-primary" onclick="saveScrapedItems()">批量保存</button></div>`;
  window._scrapedData = data.results;
}

async function doScrapePaste() {
  const text = document.getElementById('scrapePasteText').value.trim();
  if (!text) { toast('请粘贴文本','error'); return; }
  const r = await fetch(API+'/camps/scrape', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({manual:text})});
  const data = await r.json();
  const result = document.getElementById('scrapePasteResult');
  result.innerHTML = `解析到 ${data.count} 条 <button class="btn btn-sm btn-primary" onclick="saveScrapedItems()">批量保存</button>`;
  window._scrapedData = data.results;
}

async function saveOneCamp(title, school, source, link) {
  await post('/camps', {title, school, source, official_link:link, camp_type:'夏令营'});
  toast('已保存','success');
}

async function saveAllCamps() {
  if (!window._scrapedData) return;
  const items = window._scrapedData.map(r => ({
    title: r.title || '', school: r.school || '',
    camp_type: r.camp_type || '夏令营', discipline: r.discipline || '工科',
    description: r.description || '', requirements: r.requirements || '',
    link: r.link || '', source: r.source || '网络采集'
  }));
  await fetch(API+'/camps/scrape/save', {method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({items})});
  toast('批量保存完成','success');
  closeModal();
  loadCamps();
}

// ═══════════════════════════════════════════════════════════════════════════
// 3. GRADUATE PROGRAMS (硕士专业查询)
// ═══════════════════════════════════════════════════════════════════════════
async function loadPrograms() {
  const school = document.getElementById('programSchoolSearch')?.value||'';
  const major = document.getElementById('programMajorSearch')?.value||'';
  const degree = document.getElementById('programDegreeFilter')?.value||'';
  const params = new URLSearchParams({school, major, degree_type:degree});
  const data = await get(`/programs?${params}`);
  const tbody = document.getElementById('programTableBody');
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><h3>暂无专业信息</h3><p>点击"+ 添加专业"开始录入</p></div></td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(p => `<tr>
    <td><strong>${p.school}</strong></td><td>${p.college||'-'}</td><td>${p.major}</td>
    <td>${p.degree_type}</td><td><small>${p.research_directions||'-'}</small></td>
    <td><small>${p.exam_subjects||'-'}</small></td>
    <td>
      <button class="btn btn-sm btn-primary" onclick="showProgramModal(${p.id})">编辑</button>
      <button class="btn btn-sm btn-danger" onclick="deleteProgram(${p.id})">删除</button>
    </td>
  </tr>`).join('');
}

function showProgramModal(gid=null) {
  const load = async () => {
    let p = {school:'',college:'',major:'',degree_type:'学硕',research_directions:'',
             exam_subjects:'',enrollment_count:0,advisor:'',official_link:'',tags:''};
    if (gid) {
      const programs = await get('/programs');
      const f = programs.find(x=>x.id===gid);
      if (f) p = f;
    }
    openModal(gid?'编辑专业':'添加专业', `
      <div class="form-row">
        <div class="form-group"><label class="form-label">院校</label>
          <div class="search-wrapper"><input class="form-input" id="pSchool" value="${p.school||''}" placeholder="搜索院校" autocomplete="off"><div class="search-results" id="pSchoolResults"></div></div></div>
        <div class="form-group"><label class="form-label">学院</label><input class="form-input" id="pCollege" value="${p.college||''}"></div>
      </div>
      <div class="form-group"><label class="form-label">专业</label><input class="form-input" id="pMajor" value="${p.major||''}" placeholder="如: 计算机科学与技术"></div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">学位类型</label><select class="form-input" id="pDegree"><option ${p.degree_type==='学硕'?'selected':''}>学硕</option><option ${p.degree_type==='专硕'?'selected':''}>专硕</option><option ${p.degree_type==='直博'?'selected':''}>直博</option></select></div>
        <div class="form-group"><label class="form-label">招生人数</label><input class="form-input" type="number" id="pEnrollment" value="${p.enrollment_count||0}"></div>
      </div>
      <div class="form-group"><label class="form-label">研究方向</label><textarea class="form-input" id="pDirections">${p.research_directions||''}</textarea></div>
      <div class="form-group"><label class="form-label">考试科目</label><textarea class="form-input" id="pExam">${p.exam_subjects||''}</textarea></div>
      <div class="form-row">
        <div class="form-group"><label class="form-label">导师</label><input class="form-input" id="pAdvisor" value="${p.advisor||''}"></div>
        <div class="form-group"><label class="form-label">官网链接</label><input class="form-input" id="pLink" value="${p.official_link||''}"></div>
      </div>
      <div class="form-group"><label class="form-label">标签</label><input class="form-input" id="pTags" value="${p.tags||''}" placeholder="985, 211, 双一流, 强基..."></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button>
        <button class="btn btn-primary" onclick="saveProgram(${gid||'null'})">💾 保存</button>`);
    setupSearch('pSchool', 'pSchoolResults');
  };
  load();
}

async function saveProgram(gid) {
  const data = {
    school: document.getElementById('pSchool').value.trim(),
    college: document.getElementById('pCollege').value.trim(),
    major: document.getElementById('pMajor').value.trim(),
    degree_type: document.getElementById('pDegree').value,
    research_directions: document.getElementById('pDirections').value.trim(),
    exam_subjects: document.getElementById('pExam').value.trim(),
    enrollment_count: parseInt(document.getElementById('pEnrollment').value)||0,
    advisor: document.getElementById('pAdvisor').value.trim(),
    official_link: document.getElementById('pLink').value.trim(),
    tags: document.getElementById('pTags').value.trim(),
  };
  if (!data.school || !data.major) { toast('请填写院校和专业','error'); return; }
  if (gid && gid!=='null') { await put(`/programs/${gid}`, data); }
  else { await post('/programs', data); }
  closeModal(); toast('保存成功','success'); loadPrograms();
}

async function deleteProgram(gid) {
  if (!confirm('删除此专业信息?')) return;
  await del(`/programs/${gid}`); toast('已删除','success'); loadPrograms();
}

// ═══════════════════════════════════════════════════════════════════════════
// 4. KANBAN (drag & drop)
// ═══════════════════════════════════════════════════════════════════════════
async function loadKanban() {
  const data = await get('/projects');
  const board = document.getElementById('kanbanBoard');
  const grouped = {}; STATUSES.forEach(s => grouped[s] = []);
  data.forEach(p => { if (grouped[p.status]) grouped[p.status].push(p); else grouped['计划中'].push(p); });

  const colors = {'计划中':'#94A3B8','已报名':'#3B82F6','等待通知':'#F59E0B','入营':'#06B6D4',
                  '参营中':'#F97316','优营(拟录取)':'#8B5CF6','未通过':'#EF4444','已放弃':'#9CA3AF'};

  board.innerHTML = STATUSES.map(s => `<div class="kanban-col" style="border-top-color:${colors[s]||'#94A3B8'}" data-status="${s}"
    ondragover="event.preventDefault();this.classList.add('drag-over')"
    ondragleave="this.classList.remove('drag-over')"
    ondrop="onKanbanDrop(event,'${s}')">
    <div class="kanban-col-header"><span>${s}</span><span class="kanban-col-count">${(grouped[s]||[]).length}项</span></div>
    <div class="kanban-cards">${(grouped[s]||[]).map(p => `
      <div class="kanban-card" data-status="${p.status}" data-id="${p.id}"
           draggable="true" ondragstart="onKanbanDragStart(event,${p.id})" ondragend="onKanbanDragEnd(event)">
        <h4>${p.school}</h4><p>${p.major} · ${p.degree_type}</p>
      </div>`).join('')}</div>
  </div>`).join('');
}

let kanbanDragId = null;
function onKanbanDragStart(e, pid) { kanbanDragId = pid; e.target.classList.add('dragging'); e.dataTransfer.effectAllowed='move'; }
function onKanbanDragEnd(e) { e.target.classList.remove('dragging'); kanbanDragId=null; }
async function onKanbanDrop(e, status) {
  e.preventDefault(); e.currentTarget.classList.remove('drag-over');
  if (kanbanDragId) { await put(`/projects/${kanbanDragId}`,{status}); loadKanban(); }
}

// ═══════════════════════════════════════════════════════════════════════════
// 5. PROJECTS
// ═══════════════════════════════════════════════════════════════════════════
async function loadProjects() {
  const q = document.getElementById('projectSearch')?.value||'';
  const batch = document.getElementById('projectBatchFilter')?.value||'';
  const status = document.getElementById('projectStatusFilter')?.value||'';
  const data = await get(`/projects?${new URLSearchParams({q,batch,status})}`);
  const tbody = document.getElementById('projectTableBody');
  if (!data.length) { tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><h3>暂无项目</h3></div></td></tr>`; return; }
  tbody.innerHTML = data.map(p => `<tr>
    <td><strong>${p.school}</strong><br><small style="color:#94A3B8">${p.college}</small></td>
    <td>${p.major}</td><td>${p.degree_type}</td><td>${p.batch}</td>
    <td>${statusBadge(p.status)}</td>
    <td><div class="progress-bar" style="width:80px"><div class="progress-fill" style="width:${p.material_count?Math.round(p.material_done/p.material_count*100):0}%"></div></div><small>${p.material_done}/${p.material_count}</small></td>
    <td><small>${p.tags||'-'}</small></td>
    <td><button class="btn btn-sm btn-primary" onclick="showProjectModal(${p.id})">详情</button>
        <button class="btn btn-sm btn-danger" onclick="deleteProject(${p.id})">删除</button></td>
  </tr>`).join('');
}

async function showProjectModal(pid=null) {
  let p = {school:'',college:'',major:'',degree_type:'学硕',batch:'夏令营',status:'计划中',official_link:'',tags:'',notes:''};
  let materials=[],timelines=[];
  if (pid) { const d = await get(`/projects/${pid}`); p=d; materials=d.materials||[]; timelines=d.timelines||[]; }

  const matHTML = materials.map(m => `<div class="form-row" style="margin-bottom:8px">
    <input class="form-input mat-name" value="${m.name}"><select class="select-input mat-status"><option ${m.status==='未开始'?'selected':''}>未开始</option><option ${m.status==='进行中'?'selected':''}>进行中</option><option ${m.status==='已完成'?'selected':''}>已完成</option></select>
    <input class="form-input mat-file" value="${m.file_path||''}" placeholder="文件路径"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>`).join('');

  const tlHTML = timelines.map(t => `<div class="form-row" style="margin-bottom:8px">
    <input class="form-input tl-name" value="${t.name||''}"><input type="date" class="form-input tl-date" value="${t.date||''}">
    <input class="form-input tl-desc" value="${t.description||''}" placeholder="描述"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>`).join('');

  openModal(pid?'编辑项目':'添加项目', `
    <div class="form-group"><label class="form-label">院校</label><div class="search-wrapper"><input class="form-input" id="pSchool" value="${p.school||''}" placeholder="搜索院校" autocomplete="off"><div class="search-results" id="pSchoolResults"></div></div></div>
    <div class="form-row"><div class="form-group"><label class="form-label">学院</label><input class="form-input" id="pCollege" value="${p.college||''}"></div>
    <div class="form-group"><label class="form-label">专业</label><input class="form-input" id="pMajor" value="${p.major||''}"></div></div>
    <div class="form-row"><div class="form-group"><label class="form-label">学位</label><select class="form-input" id="pDegree"><option>学硕</option><option ${p.degree_type==='专硕'?'selected':''}>专硕</option><option ${p.degree_type==='直博'?'selected':''}>直博</option></select></div>
    <div class="form-group"><label class="form-label">批次</label><select class="form-input" id="pBatch"><option>夏令营</option><option ${p.batch==='预推免'?'selected':''}>预推免</option><option ${p.batch==='九推'?'selected':''}>九推</option></select></div></div>
    <div class="form-group"><label class="form-label">状态</label><select class="form-input" id="pStatus">${STATUSES.map(s=>`<option ${p.status===s?'selected':''}>${s}</option>`).join('')}</select></div>
    <div class="form-group"><label class="form-label">官网链接</label><input class="form-input" id="pLink" value="${p.official_link||''}"></div>
    <div class="form-group"><label class="form-label">标签</label><input class="form-input" id="pTags" value="${p.tags||''}"></div>
    <div class="form-group"><label class="form-label">备注</label><textarea class="form-input" id="pNotes">${p.notes||''}</textarea></div>
    <h4 style="margin:20px 0 12px">📁 材料清单</h4><div id="materialsList">${matHTML}</div>
    <button class="btn btn-sm btn-secondary" onclick="addMatRow()">＋ 材料</button>
    <h4 style="margin:20px 0 12px">📅 时间节点</h4><div id="timelinesList">${tlHTML}</div>
    <button class="btn btn-sm btn-secondary" onclick="addTlRow()">＋ 节点</button>
  `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveProject(${pid||'null'})">💾 保存</button>`);
  setupSearch('pSchool','pSchoolResults');
}

function addMatRow() { document.getElementById('materialsList').insertAdjacentHTML('beforeend',
  `<div class="form-row" style="margin-bottom:8px"><input class="form-input mat-name"><select class="select-input mat-status"><option>未开始</option><option>进行中</option><option>已完成</option></select><input class="form-input mat-file" placeholder="文件路径"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>`); }
function addTlRow() { document.getElementById('timelinesList').insertAdjacentHTML('beforeend',
  `<div class="form-row" style="margin-bottom:8px"><input class="form-input tl-name"><input type="date" class="form-input tl-date"><input class="form-input tl-desc" placeholder="描述"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>`); }

async function saveProject(pid) {
  const data = {school:document.getElementById('pSchool').value.trim(),college:document.getElementById('pCollege').value.trim(),
    major:document.getElementById('pMajor').value.trim(),degree_type:document.getElementById('pDegree').value,
    batch:document.getElementById('pBatch').value,status:document.getElementById('pStatus').value,
    official_link:document.getElementById('pLink').value.trim(),tags:document.getElementById('pTags').value.trim(),
    notes:document.getElementById('pNotes').value};
  if (!data.school) { toast('请填写院校','error'); return; }
  let result;
  if (pid&&pid!=='null') result = await put(`/projects/${pid}`,data);
  else { result = await post('/projects',data); pid = result.id; }
  if (pid) {
    const existing = pid ? (await get(`/projects/${pid}`)).materials||[] : [];
    for (const m of existing) await del(`/materials/${m.id}`);
    document.querySelectorAll('#materialsList .form-row').forEach(row => {
      const name = row.querySelector('.mat-name').value.trim();
      if (name) post(`/projects/${pid}/materials`,{name,status:row.querySelector('.mat-status').value,file_path:row.querySelector('.mat-file').value.trim()});
    });
    const tlExisting = pid ? (await get(`/projects/${pid}`)).timelines||[] : [];
    for (const t of tlExisting) await del(`/timelines/${t.id}`);
    document.querySelectorAll('#timelinesList .form-row').forEach(row => {
      const name = row.querySelector('.tl-name').value.trim();
      if (name) post(`/projects/${pid}/timelines`,{name,date:row.querySelector('.tl-date').value||null,description:row.querySelector('.tl-desc').value.trim()});
    });
  }
  closeModal(); toast('保存成功','success'); loadProjects();
}

async function deleteProject(pid) { if(!confirm('删除此项目及其全部关联数据?'))return; await del(`/projects/${pid}`); toast('已删除','success'); loadProjects(); }

// ═══════════════════════════════════════════════════════════════════════════
// 6. TIMELINE
// ═══════════════════════════════════════════════════════════════════════════
async function loadTimeline() {
  const projects = await get('/projects');
  const filter = document.getElementById('timelineProjectFilter');
  const cv = filter.value;
  filter.innerHTML = '<option value="">全部项目</option>'+projects.map(p=>`<option value="${p.id}" ${cv==String(p.id)?'selected':''}>${p.school}</option>`).join('');
  let all=[]; const today=new Date();
  if (filter.value) {
    const tls = await get(`/projects/${filter.value}/timelines`);
    const proj = projects.find(p=>p.id==filter.value);
    all = tls.map(t=>({...t,school:proj?.school||'',major:proj?.major||''}));
  } else {
    for (const p of projects) {
      const tls = await get(`/projects/${p.id}/timelines`);
      all.push(...tls.map(t=>({...t,school:p.school,major:p.major})));
    }
  }
  all.sort((a,b)=>(a.date||'9999').localeCompare(b.date||'9999'));
  const tbody = document.getElementById('timelineTableBody');
  if (!all.length) { tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><h3>暂无</h3></div></td></tr>`; return; }
  tbody.innerHTML = all.map(t => {
    const d = t.date?new Date(t.date):null;
    const days = d?Math.ceil((d-today)/86400000):null;
    let dt='',rs='';
    if (days!==null) {
      if (days<0){dt=`已过${Math.abs(days)}天`;rs='background:#FFF5F5';}
      else if(days===0){dt='🔴今天!';rs='background:#FFF5F5';}
      else if(days<=3){dt=`🟡还有${days}天`;rs='background:#FFFBEB';}
      else dt=`还有${days}天`;
    }
    return `<tr style="${rs}"><td>${t.school}·${t.major}</td><td>${t.name}</td><td>${t.date||'-'}</td><td><strong>${dt}</strong></td><td>${t.description||''}</td><td><button class="btn btn-sm btn-danger" onclick="deleteTimeline(${t.id})">删除</button></td></tr>`;
  }).join('');
}

function showTimelineModal() {
  get('/projects').then(projects => {
    openModal('📅 添加节点', `
      <select class="form-input" id="tlProject" style="margin-bottom:12px">${projects.map(p=>`<option value="${p.id}">${p.school}</option>`).join('')}</select>
      <input class="form-input" id="tlName" placeholder="节点名称" style="margin-bottom:12px">
      <input type="date" class="form-input" id="tlDate" style="margin-bottom:12px">
      <input class="form-input" id="tlDesc" placeholder="描述">
    `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveTimeline()">💾 保存</button>`);
  });
}
async function saveTimeline() {
  const pid=document.getElementById('tlProject').value;
  const name=document.getElementById('tlName').value.trim();
  if(!name){toast('请输入节点名称','error');return;}
  await post(`/projects/${pid}/timelines`,{name,date:document.getElementById('tlDate').value||null,description:document.getElementById('tlDesc').value.trim()});
  closeModal(); toast('已添加','success'); loadTimeline();
}
async function deleteTimeline(tid){if(!confirm('删除?'))return;await del(`/timelines/${tid}`);loadTimeline();}

// ═══════════════════════════════════════════════════════════════════════════
// 7-10. Materials, Interviews, Mentors, Templates (compact)
// ═══════════════════════════════════════════════════════════════════════════

async function loadMaterials() {
  const projects = await get('/projects');
  const filter = document.getElementById('materialProjectFilter');
  const cv = filter.value;
  filter.innerHTML='<option value="">全部</option>'+projects.map(p=>`<option value="${p.id}" ${cv==String(p.id)?'selected':''}>${p.school}</option>`).join('');
  const sf = document.getElementById('materialStatusFilter').value;
  let all=[];
  if (filter.value) {
    const mats = await get(`/projects/${filter.value}/materials`);
    const proj = projects.find(p=>p.id==filter.value);
    all = mats.map(m=>({...m,label:`${proj?.school}`}));
  } else {
    for (const p of projects) {
      const mats = await get(`/projects/${p.id}/materials`);
      all.push(...mats.map(m=>({...m,label:`${p.school}`})));
    }
  }
  if(sf) all=all.filter(m=>m.status===sf);
  const tbody = document.getElementById('materialTableBody');
  if(!all.length){tbody.innerHTML=`<tr><td colspan="6"><div class="empty-state"><h3>暂无</h3></div></td></tr>`;return;}
  const groups={}; all.forEach(m=>{if(!groups[m.label])groups[m.label]=[];groups[m.label].push(m);});
  tbody.innerHTML=Object.entries(groups).map(([label,mats])=>{
    const done=mats.filter(m=>m.status==='已完成').length, pct=Math.round(done/mats.length*100);
    return mats.map((m,i)=>`<tr>${i===0?`<td rowspan="${mats.length}"><strong>${label}</strong></td>`:''}
      <td>${m.name}</td><td>${m.status==='已完成'?'✅':m.status==='进行中'?'🔄':'⬜'} ${m.status}</td>
      ${i===0?`<td rowspan="${mats.length}"><div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div><small>${done}/${mats.length}</small></td>`:''}
      <td><small>${m.file_path||'-'}</small></td>
      <td><button class="btn btn-sm btn-success" onclick="updateMatStatus(${m.id},'已完成')">完成</button></td></tr>`).join('');
  }).join('');
}
async function updateMatStatus(mid,status){await put(`/materials/${mid}`,{status});loadMaterials();}

async function loadInterviews() {
  const projects = await get('/projects'); let all=[];
  for(const p of projects){const ivs=await get(`/projects/${p.id}/interviews`);all.push(...ivs.map(iv=>({...iv,school:p.school,major:p.major})));}
  all.sort((a,b)=>(b.date||'').localeCompare(a.date||''));
  const tbody=document.getElementById('interviewTableBody');
  if(!all.length){tbody.innerHTML=`<tr><td colspan="7"><div class="empty-state"><h3>暂无</h3></div></td></tr>`;return;}
  tbody.innerHTML=all.map(iv=>`<tr><td>${iv.school}·${iv.major}</td><td>${iv.date||'-'}</td><td>${iv.format_type||'线上'}</td>
    <td>${'★'.repeat(iv.self_rating||0)}${'☆'.repeat(5-(iv.self_rating||0))}</td>
    <td><small>${(iv.questions||'').slice(0,80)}</small></td><td><small>${(iv.summary||'').slice(0,80)}</small></td>
    <td><button class="btn btn-sm btn-primary" onclick="showInterviewModal(${iv.id})">编辑</button><button class="btn btn-sm btn-danger" onclick="deleteInterview(${iv.id})">删除</button></td></tr>`).join('');
}
async function showInterviewModal(iid=null){ /* similar to v2 - abbreviated for space */ }
async function deleteInterview(iid){if(!confirm('删除?'))return;await del(`/interviews/${iid}`);loadInterviews();}

async function loadMentors() {
  const status=document.getElementById('mentorStatusFilter').value;
  const data=await get(`/mentors?${new URLSearchParams({status})}`);
  const tbody=document.getElementById('mentorTableBody');
  if(!data.length){tbody.innerHTML=`<tr><td colspan="8"><div class="empty-state"><h3>暂无</h3></div></td></tr>`;return;}
  tbody.innerHTML=data.map(m=>`<tr><td><strong>${m.name}</strong></td><td>${m.school}</td><td><small>${m.research_direction||'-'}</small></td>
    <td><small>${m.email||'-'}</small></td><td>${m.first_contact_date||'-'}</td><td>${m.status}</td>
    <td>${m.next_followup_date||'-'}</td><td><button class="btn btn-sm btn-primary" onclick="showMentorModal(${m.id})">编辑</button>
    <button class="btn btn-sm btn-danger" onclick="deleteMentor(${m.id})">删除</button></td></tr>`).join('');
}
function showMentorModal(mid=null){ /* abbreviated */ }
async function deleteMentor(mid){if(!confirm('删除?'))return;await del(`/mentors/${mid}`);loadMentors();}

async function loadTemplates() {
  const cat=document.getElementById('templateCategoryFilter').value;
  const q=document.getElementById('templateSearch').value;
  const data=await get(`/templates?${new URLSearchParams({category:cat,q})}`);
  const tbody=document.getElementById('templateTableBody');
  if(!data.length){tbody.innerHTML=`<tr><td colspan="4"><div class="empty-state"><h3>暂无</h3></div></td></tr>`;return;}
  tbody.innerHTML=data.map(t=>`<tr style="cursor:pointer" onclick="previewTpl('${t.id}','${t.title.replace(/'/g,"\\'")}','${(t.full_content||'').replace(/'/g,"\\'").replace(/\\n/g,'\\\\n')}')">
    <td><strong>${t.title}</strong></td><td>${t.category}</td><td><small>${t.content.slice(0,100)}</small></td>
    <td><button class="btn btn-sm btn-primary" onclick="event.stopPropagation();showTemplateModal(${t.id})">编辑</button>
    <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();copyTpl(${t.id})">复制</button>
    <button class="btn btn-sm btn-danger" onclick="event.stopPropagation();deleteTemplate(${t.id})">删除</button></td></tr>`).join('');
}
function previewTpl(id,title,content){document.getElementById('templatePreview').innerHTML=`<h3>${title}</h3><div style="white-space:pre-wrap">${content}</div>`;}
async function copyTpl(tid){const t=(await get('/templates')).find(x=>x.id===tid);if(t){await navigator.clipboard.writeText(t.full_content||t.content);toast('已复制','success');}}
function showTemplateUpload() {
  openModal('📂 导入文件 (支持 Word/PDF/Excel/TXT)', `
    <div class="drop-zone" id="fileDropZone" onclick="document.getElementById('fileInput').click()"
         ondragover="event.preventDefault();this.classList.add('drag-over')"
         ondragleave="this.classList.remove('drag-over')"
         ondrop="handleFileDrop(event)">
      <div class="drop-zone-icon">📂</div>
      <div class="drop-zone-text">拖拽文件到此处 (.docx / .pdf / .xlsx / .txt)</div>
      <div class="drop-zone-hint">Word文档、PDF简历、Excel表格、文本文件均可</div>
      <input type="file" id="fileInput" accept=".docx,.doc,.pdf,.xlsx,.xls,.txt,.md" style="display:none" onchange="handleFileSelect(event)">
    </div><div id="uploadResult"></div>
  `, `<button class="btn btn-secondary" onclick="closeModal()">关闭</button>`);
  document.getElementById('fileInput').addEventListener('change',handleFileSelect);
}
async function handleFileSelect(e){const file=e.target.files[0];if(file)await uploadFile(file);}
async function handleFileDrop(e){e.preventDefault();e.currentTarget.classList.remove('drag-over');const file=e.dataTransfer.files[0];if(file)await uploadFile(file);}
async function uploadFile(file){
  const fd=new FormData();fd.append('file',file);
  const r=await fetch(API+'/templates/upload',{method:'POST',body:fd});const result=await r.json();
  const div=document.getElementById('uploadResult');
  if(result.error){div.innerHTML=`<div style="color:var(--danger);padding:16px">${result.error}</div>`;}
  else{div.innerHTML=`<div style="background:var(--success-bg);padding:16px;border-radius:10px">
    ✅ <strong>${result.filename}</strong> 导入成功 (${result.size}字)<br>
    <button class="btn btn-sm btn-primary" style="margin-top:8px" onclick="saveImpTpl('${result.title.replace(/'/g,"\\'")}','${result.content.replace(/'/g,"\\'").replace(/\\n/g,'\\\\n')}')">💾 保存到模板库</button></div>`;}
}
async function saveImpTpl(title,content){await post('/templates',{title,content,category:'其他'});closeModal();toast('已保存','success');loadTemplates();}
function showTemplateModal(tid=null){ /* abbreviated */ }
async function deleteTemplate(tid){if(!confirm('删除?'))return;await del(`/templates/${tid}`);loadTemplates();}

// Interview edit
async function showInterviewModal(iid=null) {
  get('/projects').then(async projects => {
    let iv = {project_id:projects[0]?.id||'',date:'',format_type:'线上',questions:'',self_rating:0,summary:'',notes:''};
    if (iid) { for(const p of projects) { const ivs=await get(`/projects/${p.id}/interviews`); const f=ivs.find(i=>i.id===iid); if(f){iv=f;iv.project_id=p.id;break;} } }
    openModal(iid?'编辑面试':'添加面试', `
      <select class="form-input" id="ivProject" style="margin-bottom:12px">${projects.map(p=>`<option value="${p.id}" ${p.id==iv.project_id?'selected':''}>${p.school}</option>`).join('')}</select>
      <div class="form-row"><input type="date" class="form-input" id="ivDate" value="${iv.date||''}"><select class="form-input" id="ivFormat"><option>线上</option><option ${iv.format_type==='线下'?'selected':''}>线下</option></select></div>
      <div class="stars" id="starRating" style="margin:12px 0">${[1,2,3,4,5].map(i=>`<span class="star ${i<=iv.self_rating?'active':''}" onclick="setStars(${i})">★</span>`).join('')}</div>
      <textarea class="form-input" id="ivQuestions" placeholder="问题列表" style="margin-bottom:12px">${iv.questions||''}</textarea>
      <textarea class="form-input" id="ivSummary" placeholder="经验总结" style="margin-bottom:12px">${iv.summary||''}</textarea>
      <textarea class="form-input" id="ivNotes" placeholder="附加笔记">${iv.notes||''}</textarea>
    `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveInterview(${iid||'null'})">💾 保存</button>`);
  });
}
function setStars(n){document.querySelectorAll('.star').forEach((s,i)=>s.classList.toggle('active',i<n));}
async function saveInterview(iid) {
  const pid=document.getElementById('ivProject').value;
  const rating=document.querySelectorAll('.star.active').length;
  const data={date:document.getElementById('ivDate').value||null,format_type:document.getElementById('ivFormat').value,
    questions:document.getElementById('ivQuestions').value,self_rating:rating,
    summary:document.getElementById('ivSummary').value,notes:document.getElementById('ivNotes').value};
  if(iid&&iid!=='null'){await put(`/interviews/${iid}`,data);}else{await post(`/projects/${pid}/interviews`,data);}
  closeModal();toast('已保存','success');loadInterviews();
}

// Mentor modal
function showMentorModal(mid=null) {
  const load = async () => {
    let m={name:'',school:'',research_direction:'',email:'',first_contact_date:'',status:'未发',reply_summary:'',next_followup_date:'',notes:''};
    if(mid){const mentors=await get('/mentors');const f=mentors.find(x=>x.id===mid);if(f)m=f;}
    openModal(mid?'编辑导师':'添加导师', `
      <div class="form-row"><input class="form-input" id="mName" value="${m.name||''}" placeholder="姓名">
      <div class="search-wrapper"><input class="form-input" id="mSchool" value="${m.school||''}" placeholder="搜索院校" autocomplete="off"><div class="search-results" id="mSchoolResults"></div></div></div>
      <input class="form-input" id="mDir" value="${m.research_direction||''}" placeholder="研究方向" style="margin:12px 0">
      <input class="form-input" type="email" id="mEmail" value="${m.email||''}" placeholder="邮箱" style="margin-bottom:12px">
      <div class="form-row"><input type="date" class="form-input" id="mFirstContact" value="${m.first_contact_date||''}">
      <select class="form-input" id="mStatus"><option>未发</option><option ${m.status==='已发'?'selected':''}>已发</option><option ${m.status==='已回复'?'selected':''}>已回复</option><option ${m.status==='积极回复'?'selected':''}>积极回复</option><option ${m.status==='婉拒'?'selected':''}>婉拒</option></select></div>
      <textarea class="form-input" id="mReply" placeholder="回复摘要" style="margin:12px 0">${m.reply_summary||''}</textarea>
      <div class="form-row"><input type="date" class="form-input" id="mFollowup" value="${m.next_followup_date||''}"><input class="form-input" id="mNotes" value="${m.notes||''}" placeholder="备注"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveMentor(${mid||'null'})">💾 保存</button>`);
    setupSearch('mSchool','mSchoolResults');
  };
  load();
}
async function saveMentor(mid) {
  const data={name:document.getElementById('mName').value.trim(),school:document.getElementById('mSchool').value.trim(),
    research_direction:document.getElementById('mDir').value.trim(),email:document.getElementById('mEmail').value.trim(),
    first_contact_date:document.getElementById('mFirstContact').value||null,status:document.getElementById('mStatus').value,
    reply_summary:document.getElementById('mReply').value.trim(),
    next_followup_date:document.getElementById('mFollowup').value||null,notes:document.getElementById('mNotes').value.trim()};
  if(!data.name){toast('请填写姓名','error');return;}
  if(mid&&mid!=='null')await put(`/mentors/${mid}`,data);else await post('/mentors',data);
  closeModal();toast('已保存','success');loadMentors();
}

// Template save
function showTemplateModal(tid=null) {
  const load=async()=>{let t={title:'',category:'个人陈述',content:''};
    if(tid){const tmps=await get('/templates');const f=tmps.find(x=>x.id===tid);if(f)t=f;}
    openModal(tid?'编辑模板':'添加模板',`
      <input class="form-input" id="tTitle" value="${t.title||''}" placeholder="标题" style="margin-bottom:12px">
      <select class="form-input" id="tCategory" style="margin-bottom:12px"><option>个人陈述</option><option ${t.category==='邮件模板'?'selected':''}>邮件模板</option><option ${t.category==='感谢信'?'selected':''}>感谢信</option><option ${t.category==='其他'?'selected':''}>其他</option></select>
      <textarea class="form-input" id="tContent" style="min-height:200px" placeholder="内容">${t.content||''}</textarea>
    `,`<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveTemplate(${tid||'null'})">💾 保存</button>`);};
  load();
}
async function saveTemplate(tid){const d={title:document.getElementById('tTitle').value.trim(),category:document.getElementById('tCategory').value,content:document.getElementById('tContent').value};if(!d.title){toast('请输入标题','error');return;}if(tid&&tid!=='null')await put(`/templates/${tid}`,d);else await post('/templates',d);closeModal();toast('已保存','success');loadTemplates();}

function exportData(){window.open(API+'/export','_blank');}

// Init
refreshDashboard();
