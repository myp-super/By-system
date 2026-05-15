/**
 * 保研全程管理 v4 — 企业级前端 (中文版)
 */
const API = '/api';
const S = ['计划中','已报名','等待通知','入营','参营中','优营(拟录取)','未通过','已放弃'];

// ═══ 导航 ══════════════════════════════════════════════════════════════
document.getElementById('sidebarNav').addEventListener('click', function(e) {
  const item = e.target.closest('.nav-item');
  if (!item) return;
  e.preventDefault();
  navigateTo(item.dataset.page);
});
function navigateTo(page) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const t = document.getElementById(`page-${page}`);
  if (t) t.classList.add('active');
  const L = {dashboard:refreshDashboard, notices:null, programs:loadPrograms, kanban:loadKanban,
    projects:loadProjects, timeline:loadTimeline, materials:loadMaterials,
    interviews:loadInterviews, mentors:loadMentors, templates:loadTemplates};
  if (L[page]) L[page]();
}

// ═══ 提示 & 弹窗 ════════════════════════════════════════════════════════
function toast(msg, type) {
  const c = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = 'toast' + (type ? ' ' + type : ''); el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; }, 2500);
  setTimeout(() => el.remove(), 3000);
}
function openModal(title, body, footer) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = body;
  document.getElementById('modalFooter').innerHTML = footer || '';
  document.getElementById('modalOverlay').classList.add('show');
}
function closeModal() { document.getElementById('modalOverlay').classList.remove('show'); }
document.getElementById('modalOverlay').addEventListener('click', function(e) { if (e.target === this) closeModal(); });

// ═══ 院校详情 ════════════════════════════════════════════════════════════
async function showUniDetail(name) {
  document.getElementById('uniModalTitle').textContent = '加载中...';
  document.getElementById('uniModalBody').innerHTML = '<div style="text-align:center;padding:40px"><div class="spinner"></div></div>';
  document.getElementById('uniModalOverlay').classList.add('show');
  try {
    const r = await fetch(API + '/university/' + encodeURIComponent(name));
    const d = await r.json();
    document.getElementById('uniModalTitle').textContent = d.name || name;
    let rh = '';
    if (d.ratings && Object.keys(d.ratings).length > 0) {
      rh = '<div style="margin-top:14px"><h4 style="font-size:13px;font-weight:600;margin-bottom:8px">📊 第四轮学科评估</h4>';
      const gc = {'A+':'#DC2626','A':'#EA580C','A-':'#F59E0B','B+':'#7C3AED','B':'#6366F1','B-':'#3B82F6','C+':'#059669','C':'#047857','C-':'#065F46'};
      for (const [g, ss] of Object.entries(d.ratings)) {
        rh += `<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px"><span class="uni-rating-grade" style="background:${gc[g]||'#64748B'}">${g}</span><span style="flex:1;font-size:13px;line-height:1.5">${ss.join(' · ')}</span></div>`;
      }
      rh += '</div>';
    }
    document.getElementById('uniModalBody').innerHTML = `
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">${(d.tags||[]).map(t=>`<span class="badge badge-primary">${t}</span>`).join('')}${d.city?`<span class="badge badge-info">📍${d.city}</span>`:''}${d.type?`<span class="badge badge-purple">${d.type}</span>`:''}${d.program_count?`<span class="badge badge-success">📚${d.program_count}个专业</span>`:''}</div>
      ${d.website?`<div style="margin-bottom:10px"><a href="${d.website}" target="_blank" style="color:var(--primary);font-size:13px;text-decoration:none">🔗 ${d.website}</a></div>`:''}${rh}${d.note?`<div style="margin-top:10px;color:var(--text-muted);font-size:12px">${d.note}</div>`:''}`;
  } catch (e) {
    document.getElementById('uniModalBody').innerHTML = '<div style="text-align:center;padding:20px;color:var(--danger)">加载失败</div>';
  }
}
function closeUniModal() { document.getElementById('uniModalOverlay').classList.remove('show'); }
document.getElementById('uniModalOverlay').addEventListener('click', function(e) { if (e.target === this) closeUniModal(); });

// ═══ 专业详情弹窗 ════════════════════════════════════════════════════════
function showProgDetail(p) {
  document.getElementById('progDetailTitle').textContent = p.school + ' — ' + p.major;
  document.getElementById('progDetailBody').innerHTML = `
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
      <span class="badge badge-primary">${p.school}</span><span class="badge badge-info">${p.degree_type||'学硕'}</span>
      ${p.college?`<span class="badge badge-gray">${p.college}</span>`:''}
      ${p.enrollment_count?`<span class="badge badge-success">招生${p.enrollment_count}人</span>`:''}
    </div>
    <div style="margin-bottom:14px"><h4 style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">研究方向</h4><p style="font-size:14px;line-height:1.6">${p.research_directions||'未填写'}</p></div>
    <div style="margin-bottom:14px"><h4 style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">考试科目</h4><p style="font-size:14px;line-height:1.6">${p.exam_subjects||'未填写'}</p></div>
    ${p.advisor?`<div style="margin-bottom:14px"><h4 style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">导师</h4><p style="font-size:14px">${p.advisor}</p></div>`:''}
    <div style="margin-top:16px">
      <button class="btn btn-sm btn-secondary" onclick="showUniDetail('${p.school.replace(/'/g,"\\'")}')">📊 院校详情</button>
      ${p.official_link?`<a href="${p.official_link}" target="_blank" class="btn btn-sm btn-primary" style="margin-left:8px;text-decoration:none">🔗 官网链接</a>`:''}
    </div>`;
  document.getElementById('progDetailOverlay').classList.add('show');
}
function closeProgDetail() { document.getElementById('progDetailOverlay').classList.remove('show'); }
document.getElementById('progDetailOverlay').addEventListener('click', function(e) { if (e.target === this) closeProgDetail(); });

// ═══ API ════════════════════════════════════════════════════════════════
async function get(url) { return (await fetch(API+url)).json(); }
async function post(url, data) { const r = await fetch(API+url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)}); return r.json(); }
async function put(url, data) { const r = await fetch(API+url, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)}); return r.json(); }
async function del(url) { await fetch(API+url, {method:'DELETE'}); }
function setupSearch(inputId, resultsId, cb) {
  const input = document.getElementById(inputId), results = document.getElementById(resultsId);
  if (!input || !results) return;
  input.addEventListener('input', async () => {
    const q = input.value.trim();
    if (!q) { results.classList.remove('show'); return; }
    const data = await get(`/universities/search?q=${encodeURIComponent(q)}`);
    results.innerHTML = data.map(s => `<div class="search-result-item" data-name="${s.replace(/"/g,'&quot;')}">${s}</div>`).join('');
    results.querySelectorAll('.search-result-item').forEach(el => {
      el.addEventListener('click', () => { input.value = el.dataset.name; results.classList.remove('show'); if (cb) cb(el.dataset.name); });
    });
    results.classList.add('show');
  });
  input.addEventListener('focus', () => { if (input.value.trim()) results.classList.add('show'); });
  document.addEventListener('click', e => { if (!input.contains(e.target) && !results.contains(e.target)) results.classList.remove('show'); });
}
function statusBadge(s) {
  const m = {'优营(拟录取)':'badge-success','未通过':'badge-danger','已报名':'badge-primary','等待通知':'badge-warning','入营':'badge-info','参营中':'badge-purple','计划中':'badge-gray','已放弃':'badge-gray'};
  return `<span class="badge ${m[s]||'badge-gray'}">${s}</span>`;
}

// ═══ 1. 仪表盘 ══════════════════════════════════════════════════════════
async function refreshDashboard() {
  const d = await get('/dashboard');
  const today = new Date();
  document.getElementById('dashboardDate').textContent = `${today.getFullYear()}年${today.getMonth()+1}月${today.getDate()}日`;
  const sc = document.getElementById('statCards');
  sc.innerHTML = [
    {v:d.total,l:'申请总数',i:'📋'},{v:d.monthly_interviews,l:'本月面试',i:'💬'},
    {v:d.upcoming_3d.length,l:'3天内截止',i:'⏰'},{v:d.upcoming_30d_count,l:'本月关键节点',i:'📅'}
  ].map((x,i) => `<div class="stat-card ${['primary','success','warning',''][i]}"><div class="stat-icon">${x.i}</div><div class="stat-value">${x.v}</div><div class="stat-label">${x.l}</div></div>`).join('');
  for (const [s, c] of Object.entries(d.status_counts||{})) {
    sc.innerHTML += `<div class="stat-card"><div class="stat-value" style="font-size:20px">${c}</div><div class="stat-label">${s}</div></div>`;
  }
  const dl = document.getElementById('deadlineList');
  dl.innerHTML = d.upcoming_3d.length === 0 ? '<div class="empty-state"><h3>✅ 暂无即将截止的节点</h3></div>' : d.upcoming_3d.map(x => {
    const days = Math.ceil((new Date(x.timeline.date)-today)/86400000);
    const cls = days<=0?'urgent':(days<=1?'soon':'');
    return `<div class="deadline-item ${cls}">${x.project.school} · ${x.timeline.name}<span style="margin-left:auto;font-weight:600">${x.timeline.date} ${days<=0?'今天!':days===1?'明天':days+'天'}</span></div>`;
  }).join('');
  const fu = document.getElementById('followupList');
  fu.innerHTML = d.followup_mentors.length===0 ? '<div class="empty-state"><h3>✅ 无待跟进</h3></div>' : d.followup_mentors.map(m => `<div class="deadline-item">👤 ${m.name} (${m.school})<span style="margin-left:auto">📅 ${m.next_followup_date||'尽快'}</span></div>`).join('');
  const rp = document.getElementById('recentProjects');
  rp.innerHTML = d.recent_projects.length===0 ? '<div class="empty-state"><h3>暂无项目</h3></div>' : d.recent_projects.map(p => `<div class="deadline-item">${p.school} · ${p.major} (${p.degree_type}) ${statusBadge(p.status)}</div>`).join('');
}

// ═══ 2. 硕士专业查询 ════════════════════════════════════════════════════
async function searchSchool() {
  const q = document.getElementById('programSchoolSearch').value.trim();
  if (!q) { loadPrograms(); return; }
  const data = await get(`/universities/search?q=${encodeURIComponent(q)}`);
  const rd = document.getElementById('programSchoolResults');
  rd.innerHTML = data.map(s => `<div class="search-result-item" style="display:flex;justify-content:space-between;align-items:center"><span>${s}</span><span style="font-size:11px;color:var(--primary);cursor:pointer" onclick="event.stopPropagation();showUniDetail('${s.replace(/'/g,"\\'")}')">📊 详情</span></div>`).join('');
  rd.querySelectorAll('.search-result-item').forEach(el => {
    el.addEventListener('click', () => { const name = el.querySelector('span').textContent; document.getElementById('programSchoolSearch').value = name; rd.classList.remove('show'); loadPrograms(); });
  });
  rd.classList.add('show');
}
async function loadPrograms() {
  const school = document.getElementById('programSchoolSearch')?.value||'';
  const major = document.getElementById('programMajorSearch')?.value||'';
  const degree = document.getElementById('programDegreeFilter')?.value||'';
  const data = await get(`/programs?${new URLSearchParams({school, major, degree_type:degree})}`);
  const tbody = document.getElementById('programTableBody');
  if (!data.length) { tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-state-icon">🔍</div><h3>未找到匹配的专业</h3><p>请尝试搜索"清华"、"计算机"、"金融学"等关键字</p></div></td></tr>`; return; }
  tbody.innerHTML = data.map(p => `<tr style="cursor:pointer" onclick="showProgDetail(${JSON.stringify(p).replace(/"/g,'&quot;')})">
    <td><span style="color:var(--primary);font-weight:600">${p.school}</span></td>
    <td style="font-size:12px;color:var(--text-muted)">${p.college||'-'}</td>
    <td><strong>${p.major}</strong></td><td>${p.degree_type||'学硕'}</td>
    <td><small>${(p.research_directions||'-').slice(0,50)}</small></td>
    <td><small>${(p.exam_subjects||'-').slice(0,50)}</small></td>
    <td>${p.enrollment_count||'-'}</td>
    <td><button class="btn btn-sm btn-primary" onclick="event.stopPropagation();showProgramModal(${p.id})">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation();deleteProgram(${p.id})">删除</button></td></tr>`).join('');
}
function showProgramModal(gid) {
  const load = async () => {
    let p = {school:'',college:'',major:'',degree_type:'学硕',research_directions:'',exam_subjects:'',enrollment_count:0,advisor:'',official_link:'',tags:''};
    if (gid) { const programs = await get('/programs'); const f = programs.find(x=>x.id===gid); if (f) p = f; }
    openModal(gid?'编辑专业':'添加专业', `
      <div class="form-row"><div class="form-group"><label class="form-label">院校</label><div class="search-wrapper"><input class="form-input" id="pSchool" value="${(p.school||'').replace(/"/g,'&quot;')}" placeholder="搜索院校..." autocomplete="off"><div class="search-results" id="pSchoolResults"></div></div></div><div class="form-group"><label class="form-label">学院</label><input class="form-input" id="pCollege" value="${(p.college||'').replace(/"/g,'&quot;')}"></div></div>
      <div class="form-group"><label class="form-label">专业名称</label><input class="form-input" id="pMajor" value="${(p.major||'').replace(/"/g,'&quot;')}" placeholder="如：计算机科学与技术"></div>
      <div class="form-row"><div class="form-group"><label class="form-label">学位类型</label><select class="form-input" id="pDegree"><option ${p.degree_type=='学硕'?'selected':''}>学硕</option><option ${p.degree_type=='专硕'?'selected':''}>专硕</option><option ${p.degree_type=='直博'?'selected':''}>直博</option></select></div><div class="form-group"><label class="form-label">招生人数</label><input class="form-input" type="number" id="pEnroll" value="${p.enrollment_count||0}"></div></div>
      <div class="form-group"><label class="form-label">研究方向</label><textarea class="form-input" id="pDir">${(p.research_directions||'').replace(/"/g,'&quot;')}</textarea></div>
      <div class="form-group"><label class="form-label">考试科目</label><textarea class="form-input" id="pExam">${(p.exam_subjects||'').replace(/"/g,'&quot;')}</textarea></div>
      <div class="form-row"><div class="form-group"><label class="form-label">导师</label><input class="form-input" id="pAdvisor" value="${(p.advisor||'').replace(/"/g,'&quot;')}"></div><div class="form-group"><label class="form-label">官网链接</label><input class="form-input" id="pLink" value="${(p.official_link||'').replace(/"/g,'&quot;')}"></div></div>
      <div class="form-group"><label class="form-label">标签</label><input class="form-input" id="pTags" value="${(p.tags||'').replace(/"/g,'&quot;')}"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveProgram(${gid||'null'})">💾 保存</button>`);
    setupSearch('pSchool','pSchoolResults');
  }; load();
}
async function saveProgram(gid) {
  const data = {school:document.getElementById('pSchool').value.trim(),college:document.getElementById('pCollege').value.trim(),major:document.getElementById('pMajor').value.trim(),degree_type:document.getElementById('pDegree').value,research_directions:document.getElementById('pDir').value.trim(),exam_subjects:document.getElementById('pExam').value.trim(),enrollment_count:parseInt(document.getElementById('pEnroll').value)||0,advisor:document.getElementById('pAdvisor').value.trim(),official_link:document.getElementById('pLink').value.trim(),tags:document.getElementById('pTags').value.trim()};
  if (!data.school||!data.major) { toast('请填写院校和专业','error'); return; }
  if (gid&&gid!=='null') await put(`/programs/${gid}`,data); else await post('/programs',data);
  closeModal(); toast('保存成功','success'); loadPrograms();
}
async function deleteProgram(gid) { if (!confirm('确定删除此专业信息？')) return; await del(`/programs/${gid}`); toast('已删除','success'); loadPrograms(); }

// ═══ 3. 看板 ════════════════════════════════════════════════════════════
async function loadKanban() {
  const data = await get('/projects'); const board = document.getElementById('kanbanBoard');
  const grouped = {}; S.forEach(s => grouped[s] = []);
  data.forEach(p => { if (grouped[p.status]) grouped[p.status].push(p); else grouped['计划中'].push(p); });
  const colors = {'计划中':'#94A3B8','已报名':'#3B82F6','等待通知':'#F59E0B','入营':'#06B6D4','参营中':'#F97316','优营(拟录取)':'#8B5CF6','未通过':'#EF4444','已放弃':'#9CA3AF'};
  board.innerHTML = S.map(s => `<div class="kanban-col" style="border-top-color:${colors[s]||'#94A3B8'}" data-status="${s}" ondragover="event.preventDefault();this.classList.add('drag-over')" ondragleave="this.classList.remove('drag-over')" ondrop="onKDrop(event,'${s}')"><div class="kanban-col-header"><span>${s}</span><span class="kanban-col-count">${(grouped[s]||[]).length}项</span></div><div class="kanban-cards">${(grouped[s]||[]).map(p => `<div class="kanban-card" data-id="${p.id}" draggable="true" ondragstart="onKDragStart(event,${p.id})" ondragend="onKDragEnd(event)"><h4>${p.school}</h4><p>${p.major} · ${p.degree_type}</p></div>`).join('')}</div></div>`).join('');
}
let kdId = null;
function onKDragStart(e, pid) { kdId = pid; e.target.classList.add('dragging'); e.dataTransfer.effectAllowed='move'; }
function onKDragEnd(e) { e.target.classList.remove('dragging'); kdId=null; }
async function onKDrop(e, status) { e.preventDefault(); e.currentTarget.classList.remove('drag-over'); if (kdId) { await put(`/projects/${kdId}`,{status}); loadKanban(); } }

// ═══ 4-8. 项目/时间/材料/面试/导师 ═══════════════════════════════════════
async function loadProjects() {
  const q = document.getElementById('projectSearch')?.value||'', batch = document.getElementById('projectBatchFilter')?.value||'', status = document.getElementById('projectStatusFilter')?.value||'';
  const data = await get(`/projects?${new URLSearchParams({q,batch,status})}`);
  const tbody = document.getElementById('projectTableBody');
  if (!data.length) { tbody.innerHTML = '<tr><td colspan="8"><div class="empty-state"><h3>暂无项目</h3><p>点击"+ 新建项目"开始添加</p></div></td></tr>'; return; }
  tbody.innerHTML = data.map(p => `<tr><td><strong>${p.school}</strong>${p.college?`<br><small style="color:var(--text-muted)">${p.college}</small>`:''}</td><td>${p.major}</td><td>${p.degree_type}</td><td>${p.batch}</td><td>${statusBadge(p.status)}</td><td><div class="progress-bar"><div class="progress-fill" style="width:${p.material_count?Math.round(p.material_done/p.material_count*100):0}%"></div></div><small>${p.material_done}/${p.material_count}</small></td><td><small>${p.tags||'-'}</small></td><td><button class="btn btn-sm btn-primary" onclick="showProjectModal(${p.id})">编辑</button><button class="btn btn-sm btn-danger" onclick="deleteProject(${p.id})">删除</button></td></tr>`).join('');
}
async function showProjectModal(pid) {
  let p = {school:'',college:'',major:'',degree_type:'学硕',batch:'夏令营',status:'计划中',official_link:'',tags:'',notes:''};
  let mats=[], tls=[];
  if (pid) { const d = await get(`/projects/${pid}`); p=d; mats=d.materials||[]; tls=d.timelines||[]; }
  const mHTML = mats.map(m => `<div class="form-row" style="margin-bottom:6px"><input class="form-input mn" value="${(m.name||'').replace(/"/g,'&quot;')}"><select class="select-input ms"><option ${m.status=='未开始'?'selected':''}>未开始</option><option ${m.status=='进行中'?'selected':''}>进行中</option><option ${m.status=='已完成'?'selected':''}>已完成</option></select><input class="form-input mf" value="${(m.file_path||'').replace(/"/g,'&quot;')}" placeholder="文件路径"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>`).join('');
  const tHTML = tls.map(t => `<div class="form-row" style="margin-bottom:6px"><input class="form-input tn" value="${(t.name||'').replace(/"/g,'&quot;')}"><input type="date" class="form-input td" value="${t.date||''}"><input class="form-input tx" value="${(t.description||'').replace(/"/g,'&quot;')}" placeholder="描述"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>`).join('');
  openModal(pid?'编辑项目':'新建项目', `<div class="form-group"><label class="form-label">院校名称</label><div class="search-wrapper"><input class="form-input" id="pS" value="${(p.school||'').replace(/"/g,'&quot;')}" placeholder="搜索院校..." autocomplete="off"><div class="search-results" id="pSRes"></div></div></div>
    <div class="form-row"><div class="form-group"><label class="form-label">学院</label><input class="form-input" id="pC" value="${(p.college||'').replace(/"/g,'&quot;')}"></div><div class="form-group"><label class="form-label">专业</label><input class="form-input" id="pM" value="${(p.major||'').replace(/"/g,'&quot;')}"></div></div>
    <div class="form-row"><div class="form-group"><label class="form-label">学位类型</label><select class="form-input" id="pDg"><option>学硕</option><option ${p.degree_type=='专硕'?'selected':''}>专硕</option><option ${p.degree_type=='直博'?'selected':''}>直博</option></select></div><div class="form-group"><label class="form-label">招生批次</label><select class="form-input" id="pBt"><option>夏令营</option><option ${p.batch=='预推免'?'selected':''}>预推免</option><option ${p.batch=='九推'?'selected':''}>九推</option></select></div></div>
    <div class="form-group"><label class="form-label">当前状态</label><select class="form-input" id="pSt">${S.map(s=>`<option ${p.status===s?'selected':''}>${s}</option>`).join('')}</select></div>
    <div class="form-group"><label class="form-label">官网链接</label><input class="form-input" id="pL" value="${(p.official_link||'').replace(/"/g,'&quot;')}"></div>
    <div class="form-row"><div class="form-group"><label class="form-label">标签</label><input class="form-input" id="pTg" value="${(p.tags||'').replace(/"/g,'&quot;')}"></div><div class="form-group"><label class="form-label">备注</label><textarea class="form-input" id="pNt">${(p.notes||'').replace(/"/g,'&quot;')}</textarea></div></div>
    <h4 style="font-size:13px;font-weight:600;margin:14px 0 8px">📁 材料清单</h4><div id="matsL">${mHTML}</div><button class="btn btn-sm btn-secondary" onclick="addMRow()">＋ 添加材料</button>
    <h4 style="font-size:13px;font-weight:600;margin:14px 0 8px">📅 时间节点</h4><div id="tlsL">${tHTML}</div><button class="btn btn-sm btn-secondary" onclick="addTRow()">＋ 添加节点</button>
  `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveProject(${pid||'null'})">💾 保存</button>`);
  setupSearch('pS','pSRes');
}
function addMRow() { document.getElementById('matsL').insertAdjacentHTML('beforeend','<div class="form-row" style="margin-bottom:6px"><input class="form-input mn"><select class="select-input ms"><option>未开始</option><option>进行中</option><option>已完成</option></select><input class="form-input mf" placeholder="文件路径"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>'); }
function addTRow() { document.getElementById('tlsL').insertAdjacentHTML('beforeend','<div class="form-row" style="margin-bottom:6px"><input class="form-input tn"><input type="date" class="form-input td"><input class="form-input tx" placeholder="描述"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>'); }
async function saveProject(pid) {
  const d = {school:document.getElementById('pS').value.trim(),college:document.getElementById('pC').value.trim(),major:document.getElementById('pM').value.trim(),degree_type:document.getElementById('pDg').value,batch:document.getElementById('pBt').value,status:document.getElementById('pSt').value,official_link:document.getElementById('pL').value.trim(),tags:document.getElementById('pTg').value.trim(),notes:document.getElementById('pNt').value};
  if (!d.school) { toast('请填写院校名称','error'); return; }
  let r; if (pid&&pid!=='null') r = await put(`/projects/${pid}`,d); else { r = await post('/projects',d); pid = r.id; }
  if (pid) {
    const em = pid ? (await get(`/projects/${pid}`)).materials||[] : []; for (const m of em) await del(`/materials/${m.id}`);
    document.querySelectorAll('#matsL .form-row').forEach(row => { const n = row.querySelector('.mn').value.trim(); if (n) post(`/projects/${pid}/materials`,{name:n,status:row.querySelector('.ms').value,file_path:row.querySelector('.mf').value.trim()}); });
    const et = pid ? (await get(`/projects/${pid}`)).timelines||[] : []; for (const t of et) await del(`/timelines/${t.id}`);
    document.querySelectorAll('#tlsL .form-row').forEach(row => { const n = row.querySelector('.tn').value.trim(); if (n) post(`/projects/${pid}/timelines`,{name:n,date:row.querySelector('.td').value||null,description:row.querySelector('.tx').value.trim()}); });
  }
  closeModal(); toast('保存成功','success'); loadProjects();
}
async function deleteProject(pid) { if (!confirm('确定删除此项目及其全部关联数据？')) return; await del(`/projects/${pid}`); toast('已删除','success'); loadProjects(); }

// Timeline
async function loadTimeline() {
  const projects = await get('/projects'); const filter = document.getElementById('timelineProjectFilter'); const cv = filter.value;
  filter.innerHTML = '<option value="">全部项目</option>'+projects.map(p=>`<option value="${p.id}" ${cv==String(p.id)?'selected':''}>${p.school}</option>`).join('');
  let all=[]; const today=new Date();
  if (filter.value) { const tls=await get(`/projects/${filter.value}/timelines`); const proj=projects.find(p=>p.id==filter.value); all=tls.map(t=>({...t,school:proj?.school||''})); }
  else { for(const p of projects) { const tls=await get(`/projects/${p.id}/timelines`); all.push(...tls.map(t=>({...t,school:p.school}))); } }
  all.sort((a,b)=>(a.date||'9999').localeCompare(b.date||'9999'));
  const tbody=document.getElementById('timelineTableBody');
  if(!all.length){tbody.innerHTML='<tr><td colspan="6"><div class="empty-state"><h3>暂无时间节点</h3></div></td></tr>';return;}
  tbody.innerHTML=all.map(t=>{const d=t.date?new Date(t.date):null;const days=d?Math.ceil((d-today)/86400000):null;let dt='',rs='';
    if(days!==null){if(days<0){dt=`已过${Math.abs(days)}天`;rs='background:#FFF5F5';}else if(days===0){dt='今天!';rs='background:#FFF5F5';}else if(days<=3){dt=`${days}天`;rs='background:#FFFBEB';}else dt=`${days}天`;}
    return `<tr style="${rs}"><td>${t.school||''}</td><td>${t.name}</td><td>${t.date||'-'}</td><td><strong>${dt}</strong></td><td>${t.description||''}</td><td><button class="btn btn-sm btn-danger" onclick="deleteTimeline(${t.id})">删除</button></td></tr>`;}).join('');
}
function showTimelineModal() { get('/projects').then(projects => { openModal('添加时间节点',`<select class="form-input" id="tlP" style="margin-bottom:10px">${projects.map(p=>`<option value="${p.id}">${p.school}</option>`).join('')}</select><input class="form-input" id="tlN" placeholder="节点名称" style="margin-bottom:10px"><input type="date" class="form-input" id="tlD" style="margin-bottom:10px"><input class="form-input" id="tlX" placeholder="描述">`,`<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveTimeline()">保存</button>`); }); }
async function saveTimeline() { const pid=document.getElementById('tlP').value, name=document.getElementById('tlN').value.trim(); if(!name){toast('请输入节点名称','error');return;} await post(`/projects/${pid}/timelines`,{name,date:document.getElementById('tlD').value||null,description:document.getElementById('tlX').value.trim()}); closeModal(); toast('已添加','success'); loadTimeline(); }
async function deleteTimeline(tid) { if(!confirm('确定删除？')) return; await del(`/timelines/${tid}`); loadTimeline(); }

// Materials
async function loadMaterials() {
  const projects=await get('/projects'); const filter=document.getElementById('materialProjectFilter'); const cv=filter.value;
  filter.innerHTML='<option value="">全部项目</option>'+projects.map(p=>`<option value="${p.id}" ${cv==String(p.id)?'selected':''}>${p.school}</option>`).join('');
  const sf=document.getElementById('materialStatusFilter').value; let all=[];
  if(filter.value){const mats=await get(`/projects/${filter.value}/materials`);const proj=projects.find(p=>p.id==filter.value);all=mats.map(m=>({...m,label:proj?.school||''}));}
  else{for(const p of projects){const mats=await get(`/projects/${p.id}/materials`);all.push(...mats.map(m=>({...m,label:p.school})));}}
  if(sf) all=all.filter(m=>m.status===sf);
  const tbody=document.getElementById('materialTableBody'); if(!all.length){tbody.innerHTML='<tr><td colspan="6"><div class="empty-state"><h3>暂无材料</h3></div></td></tr>';return;}
  const groups={};all.forEach(m=>{if(!groups[m.label])groups[m.label]=[];groups[m.label].push(m);});
  tbody.innerHTML=Object.entries(groups).map(([label,mats])=>{const done=mats.filter(m=>m.status=='已完成').length,pct=Math.round(done/mats.length*100);
    return mats.map((m,i)=>`<tr>${i===0?`<td rowspan="${mats.length}"><strong>${label}</strong></td>`:''}<td>${m.name}</td><td>${m.status=='已完成'?'✅':m.status=='进行中'?'🔄':'⬜'} ${m.status}</td>${i===0?`<td rowspan="${mats.length}"><div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div><small>${done}/${mats.length}</small></td>`:''}<td><small>${m.file_path||'-'}</small></td><td><button class="btn btn-sm btn-success" onclick="updateMatStatus(${m.id},'已完成')">完成</button></td></tr>`).join('');}).join('');
}
async function updateMatStatus(mid,status){await put(`/materials/${mid}`,{status});loadMaterials();}

// Interviews
async function loadInterviews(){const projects=await get('/projects');let all=[];for(const p of projects){const ivs=await get(`/projects/${p.id}/interviews`);all.push(...ivs.map(iv=>({...iv,school:p.school,major:p.major})));}all.sort((a,b)=>(b.date||'').localeCompare(a.date||''));const tbody=document.getElementById('interviewTableBody');if(!all.length){tbody.innerHTML='<tr><td colspan="7"><div class="empty-state"><h3>暂无面试记录</h3></div></td></tr>';return;}tbody.innerHTML=all.map(iv=>`<tr><td>${iv.school}·${iv.major}</td><td>${iv.date||'-'}</td><td>${iv.format_type||'线上'}</td><td>${'★'.repeat(iv.self_rating||0)}${'☆'.repeat(5-(iv.self_rating||0))}</td><td><small>${(iv.questions||'').slice(0,80)}</small></td><td><small>${(iv.summary||'').slice(0,80)}</small></td><td><button class="btn btn-sm btn-primary" onclick="showInterviewModal(${iv.id})">编辑</button><button class="btn btn-sm btn-danger" onclick="deleteInterview(${iv.id})">删除</button></td></tr>`).join('');}
async function showInterviewModal(iid){get('/projects').then(async projects=>{let iv={project_id:projects[0]?.id||'',date:'',format_type:'线上',questions:'',self_rating:0,summary:'',notes:''};if(iid){for(const p of projects){const ivs=await get(`/projects/${p.id}/interviews`);const f=ivs.find(i=>i.id===iid);if(f){iv=f;iv.project_id=p.id;break;}}}openModal(iid?'编辑面试':'添加面试',`<select class="form-input" id="ivP" style="margin-bottom:10px">${projects.map(p=>`<option value="${p.id}" ${p.id==iv.project_id?'selected':''}>${p.school}</option>`).join('')}</select><div class="form-row"><input type="date" class="form-input" id="ivD" value="${iv.date||''}"><select class="form-input" id="ivF"><option>线上</option><option ${iv.format_type=='线下'?'selected':''}>线下</option></select></div><div class="stars" id="starR" style="margin:10px 0">${[1,2,3,4,5].map(i=>`<span class="star ${i<=iv.self_rating?'active':''}" onclick="setStars(${i})">★</span>`).join('')}</div><textarea class="form-input" id="ivQ" placeholder="面试问题" style="margin-bottom:10px">${(iv.questions||'').replace(/"/g,'&quot;')}</textarea><textarea class="form-input" id="ivS" placeholder="经验总结" style="margin-bottom:10px">${(iv.summary||'').replace(/"/g,'&quot;')}</textarea><textarea class="form-input" id="ivN" placeholder="附加笔记">${(iv.notes||'').replace(/"/g,'&quot;')}</textarea>`,`<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveInterview(${iid||'null'})">保存</button>`);});}
function setStars(n){document.querySelectorAll('.star').forEach((s,i)=>s.classList.toggle('active',i<n));}
async function saveInterview(iid){const pid=document.getElementById('ivP').value,rating=document.querySelectorAll('.star.active').length;const data={date:document.getElementById('ivD').value||null,format_type:document.getElementById('ivF').value,questions:document.getElementById('ivQ').value,self_rating:rating,summary:document.getElementById('ivS').value,notes:document.getElementById('ivN').value};if(iid&&iid!=='null')await put(`/interviews/${iid}`,data);else await post(`/projects/${pid}/interviews`,data);closeModal();toast('保存成功','success');loadInterviews();}
async function deleteInterview(iid){if(!confirm('确定删除？'))return;await del(`/interviews/${iid}`);loadInterviews();}

// Mentors
async function loadMentors(){const status=document.getElementById('mentorStatusFilter').value;const data=await get(`/mentors?${new URLSearchParams({status})}`);const tbody=document.getElementById('mentorTableBody');if(!data.length){tbody.innerHTML='<tr><td colspan="8"><div class="empty-state"><h3>暂无导师记录</h3></div></td></tr>';return;}tbody.innerHTML=data.map(m=>`<tr><td><strong>${m.name}</strong></td><td>${m.school}</td><td><small>${m.research_direction||'-'}</small></td><td><small>${m.email||'-'}</small></td><td>${m.first_contact_date||'-'}</td><td>${m.status}</td><td>${m.next_followup_date||'-'}</td><td><button class="btn btn-sm btn-primary" onclick="showMentorModal(${m.id})">编辑</button><button class="btn btn-sm btn-danger" onclick="deleteMentor(${m.id})">删除</button></td></tr>`).join('');}
async function deleteMentor(mid){if(!confirm('确定删除？'))return;await del(`/mentors/${mid}`);loadMentors();}
function showMentorModal(mid){const load=async()=>{let m={name:'',school:'',research_direction:'',email:'',first_contact_date:'',status:'未发',reply_summary:'',next_followup_date:'',notes:''};if(mid){const mentors=await get('/mentors');const f=mentors.find(x=>x.id===mid);if(f)m=f;}openModal(mid?'编辑导师':'添加导师',`<div class="form-row"><input class="form-input" id="mN" value="${(m.name||'').replace(/"/g,'&quot;')}" placeholder="导师姓名"><div class="search-wrapper"><input class="form-input" id="mS" value="${(m.school||'').replace(/"/g,'&quot;')}" placeholder="所在院校" autocomplete="off"><div class="search-results" id="mSRes"></div></div></div><input class="form-input" id="mD" value="${(m.research_direction||'').replace(/"/g,'&quot;')}" placeholder="研究方向" style="margin:10px 0"><input type="email" class="form-input" id="mE" value="${(m.email||'').replace(/"/g,'&quot;')}" placeholder="邮箱" style="margin-bottom:10px"><div class="form-row"><input type="date" class="form-input" id="mFC" value="${m.first_contact_date||''}"><select class="form-input" id="mSt"><option>未发</option><option ${m.status=='已发'?'selected':''}>已发</option><option ${m.status=='已回复'?'selected':''}>已回复</option><option ${m.status=='积极回复'?'selected':''}>积极回复</option><option ${m.status=='婉拒'?'selected':''}>婉拒</option></select></div><textarea class="form-input" id="mR" placeholder="回复内容摘要" style="margin:10px 0">${(m.reply_summary||'').replace(/"/g,'&quot;')}</textarea><div class="form-row"><input type="date" class="form-input" id="mFU" value="${m.next_followup_date||''}"><input class="form-input" id="mNo" value="${(m.notes||'').replace(/"/g,'&quot;')}" placeholder="备注"></div>`,`<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveMentor(${mid||'null'})">保存</button>`);setupSearch('mS','mSRes');};load();}
async function saveMentor(mid){const d={name:document.getElementById('mN').value.trim(),school:document.getElementById('mS').value.trim(),research_direction:document.getElementById('mD').value.trim(),email:document.getElementById('mE').value.trim(),first_contact_date:document.getElementById('mFC').value||null,status:document.getElementById('mSt').value,reply_summary:document.getElementById('mR').value.trim(),next_followup_date:document.getElementById('mFU').value||null,notes:document.getElementById('mNo').value.trim()};if(!d.name){toast('请填写导师姓名','error');return;}if(mid&&mid!=='null')await put(`/mentors/${mid}`,d);else await post('/mentors',d);closeModal();toast('保存成功','success');loadMentors();}

// ═══ 9. 文书模板 — 批量上传/下载（原格式） ═══════════════════════════

function toggleAllTpl() {
  const all = document.getElementById('selectAllTpl').checked;
  document.querySelectorAll('.tpl-checkbox').forEach(cb => cb.checked = all);
}
function getSelectedTplIds() {
  return [...document.querySelectorAll('.tpl-checkbox:checked')].map(cb => parseInt(cb.value));
}

async function loadTemplates() {
  const cat = document.getElementById('templateCategoryFilter').value;
  const q = document.getElementById('templateSearch').value;
  const data = await get(`/templates?${new URLSearchParams({category:cat, q})}`);
  window._tplData = data;
  const tbody = document.getElementById('templateTableBody');
  document.getElementById('selectAllTpl').checked = false;
  if (!data.length) { tbody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><h3>暂无文件</h3><p>点击"批量上传"添加文件</p></div></td></tr>'; return; }
  tbody.innerHTML = data.map(t => {
    const title = t.title || t.original_filename || '';
    const extMatch = title.match(/\.(\w+)$/);
    const ext = extMatch ? extMatch[1].toLowerCase() : '';
    const icons = {docx:'📄', doc:'📄', pdf:'📕', xlsx:'📊', xls:'📊', txt:'📝', md:'📝', pptx:'📽️', zip:'🗜️'};
    const icon = icons[ext] || '📁';
    const sizeStr = t.file_size ? (t.file_size < 1024 ? t.file_size+' B' : t.file_size < 1048576 ? (t.file_size/1024).toFixed(1)+' KB' : (t.file_size/1048576).toFixed(1)+' MB') : (t.content ? (t.content||'').length+' 字' : '—');
    return `<tr>
      <td style="text-align:center"><input type="checkbox" class="tpl-checkbox" value="${t.id}" onchange="document.getElementById('selectAllTpl').checked = false"></td>
      <td style="font-size:22px;text-align:center">${icon}</td>
      <td><strong>${title}</strong></td>
      <td>${t.category||'其他'}</td>
      <td>${sizeStr}</td>
      <td>
        ${t.has_file ? `<button class="btn btn-sm btn-info" onclick="previewFile(${t.id})">👁 预览</button><a href="${API}/templates/${t.id}/download" class="btn btn-sm btn-success">💾 下载</a>` : `<button class="btn btn-sm btn-primary" onclick="copyTplText(${t.id})">📋 复制</button>`}
        <button class="btn btn-sm btn-primary" onclick="showTemplateModal(${t.id})">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="deleteTemplate(${t.id})">删除</button>
      </td></tr>`;
  }).join('');
}
function previewFile(tid) {
  const t = window._tplData?.find(x => x.id === tid);
  if (!t || !t.has_file) { toast('无可预览的文件','error'); return; }
  document.getElementById('previewIframe').src = API + '/templates/' + tid + '/preview';
  document.getElementById('previewOverlay').classList.add('show');
}
function closePreview() {
  document.getElementById('previewOverlay').classList.remove('show');
  document.getElementById('previewIframe').src = '';
}
document.getElementById('previewOverlay').addEventListener('click', function(e) { if (e.target === this) closePreview(); });

async function copyTplText(tid) {
  const t = window._tplData?.find(x => x.id === tid);
  if (t) { await navigator.clipboard.writeText(t.full_content || t.content || ''); toast('已复制','success'); }
}

// Batch download — ZIP
async function batchDownload() {
  const ids = getSelectedTplIds();
  if (ids.length === 0) { toast('请先勾选要下载的文件','error'); return; }
  const r = await fetch(API+'/templates/download-batch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ids})});
  if (!r.ok) { toast('下载失败','error'); return; }
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'templates_batch.zip'; document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
  toast(`已打包下载 ${ids.length} 个文件`,'success');
}

// Batch upload — multiple files
function showTemplateUpload() {
  openModal('📂 批量上传文件', `
    <div class="drop-zone" id="fileDZ" onclick="document.getElementById('fInput').click()"
         ondragover="event.preventDefault();this.classList.add('drag-over')"
         ondragleave="this.classList.remove('drag-over')"
         ondrop="onFileDrop(event)">
      <div class="drop-zone-icon">📂</div>
      <div class="drop-zone-text">拖拽文件到此处或点击选择</div>
      <div class="drop-zone-hint">支持多选 · 所有格式 · 原文件存储 · 原格式下载</div>
      <input type="file" id="fInput" multiple style="display:none">
    </div>
    <div id="upResult"></div>
  `, `<button class="btn btn-secondary" onclick="closeModal()">关闭</button>`);
  setTimeout(() => { document.getElementById('fInput').onchange = onFilesSelect; }, 100);
}
async function onFilesSelect(e) {
  const files = [...e.target.files];
  if (files.length) await doBatchUpload(files);
}
async function onFileDrop(e) {
  e.preventDefault(); e.currentTarget.classList.remove('drag-over');
  const files = [...e.dataTransfer.files];
  if (files.length) await doBatchUpload(files);
}
async function doBatchUpload(files) {
  const div = document.getElementById('upResult');
  div.innerHTML = `<div style="text-align:center;padding:20px"><div class="spinner"></div>上传 ${files.length} 个文件中...</div>`;
  const fd = new FormData();
  files.forEach(f => fd.append('files', f));
  const r = await fetch(API+'/templates/upload', {method:'POST', body:fd});
  const result = await r.json();
  if (result.error) { div.innerHTML = `<div style="color:var(--danger);padding:14px;background:var(--danger-bg);border-radius:var(--radius)">❌ ${result.error}</div>`; }
  else {
    const totalSize = result.files.reduce((s,f) => s + (f.file_size||0), 0);
    const sizeStr = totalSize < 1048576 ? (totalSize/1024).toFixed(1)+' KB' : (totalSize/1048576).toFixed(1)+' MB';
    div.innerHTML = `<div style="background:var(--success-bg);border:1px solid var(--success-border);border-radius:var(--radius-lg);padding:14px;margin-top:12px">
      ✅ 成功上传 <strong>${result.count}</strong> 个文件（${sizeStr}）<br>
      ${result.files.map(f => `<div style="font-size:12px;color:var(--text-secondary);margin-top:2px">· ${f.title} (${(f.file_size/1024).toFixed(1)} KB)</div>`).join('')}
      <button class="btn btn-sm btn-primary" style="margin-top:10px" onclick="closeModal();loadTemplates();">完成</button></div>`;
  }
}

// Template CRUD
function showTemplateModal(tid) {
  const load = async () => {
    let t = {title:'', category:'个人陈述', content:''};
    if (tid) { const tmps = await get('/templates'); const f = tmps.find(x => x.id === tid); if (f) t = f; }
    openModal(tid?'编辑模板':'新建模板', `
      <div class="form-group"><label class="form-label">标题</label><input class="form-input" id="tT" value="${(t.title||'').replace(/"/g,'&quot;')}" placeholder="模板标题"></div>
      <div class="form-group"><label class="form-label">分类</label><select class="form-input" id="tC"><option>个人陈述</option><option ${t.category=='邮件模板'?'selected':''}>邮件模板</option><option ${t.category=='感谢信'?'selected':''}>感谢信</option><option ${t.category=='其他'?'selected':''}>其他</option></select></div>
      <div class="form-group"><label class="form-label">内容</label><textarea class="form-input" id="tX" style="min-height:200px">${(t.content||'').replace(/"/g,'&quot;')}</textarea></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">取消</button><button class="btn btn-primary" onclick="saveTemplate(${tid||'null'})">保存</button>`);
  }; load();
}
async function saveTemplate(tid) {
  const d = {title:document.getElementById('tT').value.trim(),category:document.getElementById('tC').value,content:document.getElementById('tX').value};
  if (!d.title) { toast('请输入标题','error'); return; }
  if (tid&&tid!=='null') await put(`/templates/${tid}`,d); else await post('/templates',d);
  closeModal(); loadTemplates();
}
async function deleteTemplate(tid) { if (!confirm('确定删除此文件？')) return; await del(`/templates/${tid}`); toast('已删除','success'); loadTemplates(); }
function exportData() { window.open(API+'/export','_blank'); }

// ═══ Auth ══════════════════════════════════════════════════════════════
let authMode = 'login';

async function checkAuth() {
  const r = await fetch(API+'/auth/me');
  if (r.status === 200) {
    const user = await r.json();
    window._currentUser = user;
    return true;
  }
  window._currentUser = null;
  return false;
}

function toggleAuthMode() {
  authMode = authMode === 'login' ? 'register' : 'login';
  document.getElementById('authSubtitle').textContent = authMode === 'login' ? '登录你的账号' : '注册新账号';
  document.getElementById('authBtn').textContent = authMode === 'login' ? '登录' : '注册';
  document.getElementById('authToggleText').textContent = authMode === 'login' ? '没有账号？' : '已有账号？';
  document.getElementById('authToggleLink').textContent = authMode === 'login' ? '注册' : '登录';
  document.getElementById('nicknameGroup').style.display = authMode === 'register' ? 'block' : 'none';
  document.getElementById('authError').style.display = 'none';
}

async function handleAuth() {
  const email = document.getElementById('authEmail').value.trim();
  const password = document.getElementById('authPassword').value;
  const errDiv = document.getElementById('authError');

  if (authMode === 'register') {
    const nickname = document.getElementById('authNickname').value.trim();
    const r = await fetch(API+'/auth/register', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email, password, nickname})
    });
    const d = await r.json();
    if (r.ok) { authSuccess(d); }
    else { errDiv.textContent = d.error; errDiv.style.display = 'block'; }
  } else {
    const r = await fetch(API+'/auth/login', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email, password})
    });
    const d = await r.json();
    if (r.ok) { authSuccess(d); }
    else { errDiv.textContent = d.error; errDiv.style.display = 'block'; }
  }
}

function authSuccess(user) {
  window._currentUser = user;
  document.getElementById('page-auth').classList.remove('active');
  document.getElementById('sidebarNav').style.display = '';
  document.querySelector('.sidebar-footer').textContent = user.nickname || user.email;
  navigateTo('dashboard');
}

async function logout() {
  await fetch(API+'/auth/logout', {method:'POST'});
  window._currentUser = null;
  showLoginPage();
}

function showLoginPage() {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-auth').classList.add('active');
  document.getElementById('sidebarNav').style.display = 'none';
  document.querySelector('.sidebar-footer').textContent = 'v5 · Enterprise';
  document.getElementById('authEmail').value = '';
  document.getElementById('authPassword').value = '';
  document.getElementById('authError').style.display = 'none';
}

// Wrapper for authenticated navigation
const _origNavigateTo = navigateTo;
navigateTo = async function(page) {
  if (page === 'auth') return;
  const ok = await checkAuth();
  if (!ok) { showLoginPage(); return; }
  _origNavigateTo(page);
};

// Init: check auth on load
(async function init() {
  const ok = await checkAuth();
  if (!ok) {
    showLoginPage();
    return;
  }
  document.querySelector('.sidebar-footer').textContent = window._currentUser.nickname || window._currentUser.email;
  refreshDashboard();
})();
