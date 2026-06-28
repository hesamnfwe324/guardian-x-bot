/* ================================================
   GUARDIAN X — Glassmorphism Admin Panel
   Application Logic & API Integration
   ================================================ */

// ============ STATE ============
const state = {
  adminKey: '',
  serverUrl: '',
  currentPage: 'dashboard',
  stats: null,
  users: { data: [], total: 0, page: 1, limit: 20 },
  groups: { data: [], total: 0, page: 1, limit: 20 },
  leaderboard: [],
  logs: { data: [], total: 0, page: 1, limit: 30 },
};

// ============ INIT ============
document.addEventListener('DOMContentLoaded', () => {
  // Load saved settings
  const savedKey = localStorage.getItem('gx_admin_key');
  const savedUrl = localStorage.getItem('gx_server_url');

  if (savedKey && savedUrl) {
    state.adminKey = savedKey;
    state.serverUrl = savedUrl;
    verifyAndEnter();
  }

  // Broadcast preview live update
  document.getElementById('broadcastMsg').addEventListener('input', (e) => {
    const preview = document.getElementById('broadcastPreview');
    const text = e.target.value.trim();
    if (text) {
      preview.innerHTML = text;
    } else {
      preview.textContent = 'پیش‌نمایش پیام در اینجا نمایش داده می‌شود...';
    }
  });

  // Enter key on login
  document.getElementById('adminKeyInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doLogin();
  });

  // Settings page: populate fields
  if (savedUrl) document.getElementById('settingsServerUrl').value = savedUrl;
  if (savedKey) document.getElementById('settingsAdminKey').value = savedKey;
});

// ============ AUTH ============
function doLogin() {
  const keyInput = document.getElementById('adminKeyInput');
  const key = keyInput.value.trim();
  if (!key) {
    keyInput.focus();
    return;
  }

  // Determine server URL
  const currentHost = window.location.origin;
  state.serverUrl = currentHost;
  state.adminKey = key;

  // Verify
  fetchWithAuth('/admin/stats')
    .then(data => {
      localStorage.setItem('gx_admin_key', key);
      localStorage.setItem('gx_server_url', state.serverUrl);
      enterApp();
    })
    .catch(err => {
      const errorEl = document.getElementById('loginError');
      errorEl.classList.add('show');
      setTimeout(() => errorEl.classList.remove('show'), 3000);
    });
}

function verifyAndEnter() {
  fetchWithAuth('/admin/stats')
    .then(data => enterApp())
    .catch(err => {
      // Saved key invalid, show login
      localStorage.removeItem('gx_admin_key');
      localStorage.removeItem('gx_server_url');
    });
}

function enterApp() {
  document.getElementById('loginPage').classList.add('hidden');
  document.getElementById('appLayout').classList.remove('hidden');
  loadDashboard();
}

function doLogout() {
  state.adminKey = '';
  localStorage.removeItem('gx_admin_key');
  localStorage.removeItem('gx_server_url');
  document.getElementById('appLayout').classList.add('hidden');
  document.getElementById('loginPage').classList.remove('hidden');
  document.getElementById('adminKeyInput').value = '';
}

// ============ API HELPER ============
async function fetchWithAuth(endpoint, options = {}) {
  const url = `${state.serverUrl}${endpoint}`;
  const headers = {
    'X-Admin-Key': state.adminKey,
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const resp = await fetch(url, { ...options, headers });

  if (resp.status === 401) {
    throw new Error('Unauthorized');
  }

  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }

  return resp.json();
}

// ============ NAVIGATION ============
function navigateTo(page) {
  state.currentPage = page;

  // Update sidebar
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.page === page);
  });

  // Hide all pages
  document.querySelectorAll('.page-content').forEach(el => {
    el.classList.add('hidden');
  });

  // Show target page
  const targetPage = document.getElementById(`page-${page}`);
  if (targetPage) {
    targetPage.classList.remove('hidden');
  }

  // Update title
  const titles = {
    dashboard: { icon: '📊', text: 'داشبورد' },
    users: { icon: '👥', text: 'مدیریت کاربران' },
    groups: { icon: '🏠', text: 'مدیریت گروه‌ها' },
    economy: { icon: '💰', text: 'لیدربورد اقتصاد' },
    logs: { icon: '📋', text: 'لاگ فعالیت‌ها' },
    broadcast: { icon: '📢', text: 'پیام همگانی' },
    security: { icon: '🛡️', text: 'امنیت' },
    settings: { icon: '⚙️', text: 'تنظیمات' },
  };

  const titleInfo = titles[page] || titles.dashboard;
  document.getElementById('pageTitle').innerHTML = `
    <span class="title-icon">${titleInfo.icon}</span>
    <h2>${titleInfo.text}</h2>
  `;

  // Load page data
  loadPageData(page);
}

function loadPageData(page) {
  switch (page) {
    case 'dashboard': loadDashboard(); break;
    case 'users': loadUsers(); break;
    case 'groups': loadGroups(); break;
    case 'economy': loadLeaderboard(); break;
    case 'logs': loadLogs(); break;
  }
}

// ============ DASHBOARD ============
async function loadDashboard() {
  try {
    const stats = await fetchWithAuth('/admin/stats');
    state.stats = stats;
    renderStats(stats);
    loadDashboardLeaderboard();
    loadDashboardRecentLogs();
    renderWeeklyChart();
  } catch (err) {
    showToast('خطا در بارگذاری آمار', 'error');
  }
}

function renderStats(stats) {
  animateValue('stat-totalUsers', stats.totalUsers || 0);
  animateValue('stat-activeToday', stats.activeToday || 0);
  animateValue('stat-totalGroups', stats.totalGroups || 0);
  animateValue('stat-totalMessages', stats.totalMessages || 0);
  animateValue('stat-bannedUsers', stats.bannedUsers || 0);
  animateValue('stat-gamesPlayed', stats.gamesPlayed || 0);

  // Update sidebar badge
  document.getElementById('usersCount').textContent = stats.totalUsers || 0;
}

function animateValue(elementId, target) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const duration = 800;
  const start = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
  const diff = target - start;
  const startTime = performance.now();

  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
    const current = Math.round(start + diff * eased);
    el.textContent = formatNumber(current);
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toLocaleString('fa-IR');
}

function renderWeeklyChart() {
  const chart = document.getElementById('weeklyChart');
  if (!chart) return;

  // Generate sample bars (we don't have real weekly data)
  const days = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'];
  const stats = state.stats || {};
  const activeFactor = Math.max((stats.activeToday || 1) / (stats.totalUsers || 1), 0.05);

  chart.innerHTML = '';
  days.forEach((day, i) => {
    const height = 15 + Math.random() * 75;
    const bar = document.createElement('div');
    bar.className = 'chart-bar';
    bar.style.height = height + '%';
    bar.title = day;
    bar.style.animationDelay = (i * 0.05) + 's';
    chart.appendChild(bar);
  });
}

async function loadDashboardLeaderboard() {
  try {
    const data = await fetchWithAuth('/admin/economy/leaderboard?limit=5');
    state.leaderboard = data;
    renderDashboardLeaderboard(data);
  } catch (err) {
    // silent
  }
}

function renderDashboardLeaderboard(data) {
  const container = document.getElementById('dashboardLeaderboard');
  if (!data || data.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">🏆</div><h3>داده‌ای یافت نشد</h3></div>';
    return;
  }

  container.innerHTML = data.map((item, i) => {
    const rankClass = i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : 'normal';
    const name = item.firstName || item.username || 'بدون نام';
    const balance = item.balance || 0;
    const level = item.level || 1;

    return `
      <div class="leaderboard-item">
        <div class="leaderboard-rank ${rankClass}">${i + 1}</div>
        <div class="leaderboard-info">
          <div class="leaderboard-name">${escapeHtml(name)}</div>
          <div class="leaderboard-detail">سطح ${level} — XP: ${formatNumber(item.xp || 0)}</div>
        </div>
        <div class="leaderboard-balance">🪙 ${formatNumber(balance)}</div>
      </div>
    `;
  }).join('');
}

async function loadDashboardRecentLogs() {
  try {
    const data = await fetchWithAuth('/admin/logs?limit=5');
    renderDashboardRecentLogs(data.logs || []);
  } catch (err) {
    // silent
  }
}

function renderDashboardRecentLogs(logs) {
  const container = document.getElementById('dashboardRecentLogs');
  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="empty-state" style="padding:24px;"><div class="empty-icon">📋</div><h3>لاگی یافت نشد</h3></div>';
    return;
  }

  container.innerHTML = logs.map(log => {
    const actionIcons = {
      ban: '⛔', unban: '✅', mute: '🔇', unmute: '🔊',
      warn: '⚠️', kick: '🚫', promote: '⬆️', demote: '⬇️',
      settings: '⚙️', delete: '🗑️', edit: '✏️', join: '➡️', leave: '⬅️',
    };
    const icon = actionIcons[log.action] || '📌';
    const time = log.createdAt ? timeAgo(log.createdAt) : '';

    return `
      <div class="log-item">
        <div class="log-icon">${icon}</div>
        <div class="log-content">
          <div class="log-action">${escapeHtml(log.action)}</div>
          <div class="log-detail">${escapeHtml(log.reason || log.details || '')}</div>
        </div>
        <div class="log-time">${time}</div>
      </div>
    `;
  }).join('');
}

// ============ USERS ============
async function loadUsers(page = 1) {
  try {
    const search = document.getElementById('userSearch')?.value || '';
    const banned = document.getElementById('userBannedFilter')?.value || '';
    let url = `/admin/users?page=${page}&limit=20`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (banned) url += `&banned=${banned}`;

    const data = await fetchWithAuth(url);
    state.users = { data: data.users || [], total: data.total || 0, page: data.page || 1, limit: data.limit || 20 };
    renderUsers();
  } catch (err) {
    showToast('خطا در بارگذاری کاربران', 'error');
  }
}

function renderUsers() {
  const tbody = document.getElementById('usersTableBody');
  const users = state.users.data;

  if (!users || users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-muted);">کاربری یافت نشد</td></tr>';
    return;
  }

  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#ef4444', '#3b82f6', '#10b981'];

  tbody.innerHTML = users.map(user => {
    const name = user.firstName || user.username || 'بدون نام';
    const initial = name.charAt(0).toUpperCase();
    const color = colors[Math.abs(hashCode(user.id)) % colors.length];
    const statusBadge = user.isBanned
      ? '<span class="badge badge-danger">بن‌شده</span>'
      : '<span class="badge badge-success">فعال</span>';
    const premiumBadge = user.isPremium ? ' <span class="badge badge-purple" style="font-size:0.6rem;">⭐ پریمیوم</span>' : '';
    const lastSeen = user.lastSeen ? timeAgo(user.lastSeen) : '—';
    const actionBtn = user.isBanned
      ? `<button class="btn btn-success btn-sm" onclick="unbanUser('${user.id}')">آنبن</button>`
      : `<button class="btn btn-danger btn-sm" onclick="showBanModal('${user.id}','${escapeHtml(name)}')">بن</button>`;

    return `
      <tr>
        <td>
          <div class="user-cell">
            <div class="user-avatar" style="background:${color};">${initial}</div>
            <div class="user-info">
              <div class="user-name">${escapeHtml(name)}${premiumBadge}</div>
              <div class="user-id">@${escapeHtml(user.username || '—')} · ${user.id}</div>
            </div>
          </div>
        </td>
        <td><span class="text-mono" style="color:var(--accent-primary);">🪙 ${formatNumber(user.balance)}</span></td>
        <td><span class="badge badge-info">Lv.${user.level || 1}</span></td>
        <td><span class="text-mono text-sm">${formatNumber(user.xp)}</span></td>
        <td><span class="text-sm">${user.language || '—'}</span></td>
        <td>${statusBadge}</td>
        <td><span class="text-sm">${lastSeen}</span></td>
        <td>${actionBtn}</td>
      </tr>
    `;
  }).join('');

  renderPagination('usersPagination', state.users.page, Math.ceil(state.users.total / state.users.limit), loadUsers);
}

function searchUsers() {
  clearTimeout(window._searchUsersTimer);
  window._searchUsersTimer = setTimeout(() => loadUsers(1), 300);
}

async function banUser(userId, reason) {
  try {
    await fetchWithAuth(`/admin/users/${userId}/ban`, {
      method: 'POST',
      body: JSON.stringify({ reason: reason || 'Admin action' }),
    });
    showToast('کاربر با موفقیت بن شد', 'success');
    loadUsers(state.users.page);
    closeModal();
  } catch (err) {
    showToast('خطا در بن کردن کاربر', 'error');
  }
}

async function unbanUser(userId) {
  try {
    await fetchWithAuth(`/admin/users/${userId}/unban`, {
      method: 'POST',
    });
    showToast('کاربر آنبن شد', 'success');
    loadUsers(state.users.page);
  } catch (err) {
    showToast('خطا در آنبن کردن کاربر', 'error');
  }
}

function showBanModal(userId, userName) {
  const html = `
    <div class="modal-backdrop" onclick="closeModal()">
      <div class="modal glass-strong" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3>⛔ بن کردن کاربر</h3>
          <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div class="modal-body">
          <p style="margin-bottom:16px;color:var(--text-secondary);">
            آیا از بن کردن <strong style="color:var(--text-primary);">${escapeHtml(userName)}</strong> مطمئن هستید؟
          </p>
          <div class="form-group">
            <label class="form-label">دلیل بن</label>
            <input type="text" class="form-input" id="banReasonInput" placeholder="دلیل بن را وارد کنید...">
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
          <button class="btn btn-danger" onclick="banUser('${userId}', document.getElementById('banReasonInput').value)">⛔ بن کردن</button>
        </div>
      </div>
    </div>
  `;
  document.getElementById('modalContainer').innerHTML = html;
}

// ============ GROUPS ============
async function loadGroups(page = 1) {
  try {
    const search = document.getElementById('groupSearch')?.value || '';
    let url = `/admin/groups?page=${page}&limit=20`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const data = await fetchWithAuth(url);
    state.groups = { data: data.groups || [], total: data.total || 0, page: data.page || 1, limit: data.limit || 20 };
    renderGroups();
  } catch (err) {
    showToast('خطا در بارگذاری گروه‌ها', 'error');
  }
}

function renderGroups() {
  const tbody = document.getElementById('groupsTableBody');
  const groups = state.groups.data;

  if (!groups || groups.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted);">گروه‌ای یافت نشد</td></tr>';
    return;
  }

  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#ef4444', '#3b82f6', '#10b981'];

  tbody.innerHTML = groups.map(group => {
    const name = group.title || 'بدون عنوان';
    const initial = name.charAt(0).toUpperCase();
    const color = colors[Math.abs(hashCode(group.id)) % colors.length];
    const statusBadge = group.isActive
      ? '<span class="badge badge-success">فعال</span>'
      : '<span class="badge badge-danger">غیرفعال</span>';
    const typeLabels = { group: 'گروه', supergroup: 'سوپرگروه', channel: 'کانال' };
    const createdAt = group.createdAt ? formatDate(group.createdAt) : '—';

    return `
      <tr>
        <td>
          <div class="user-cell">
            <div class="user-avatar" style="background:${color};">${initial}</div>
            <div class="user-info">
              <div class="user-name">${escapeHtml(name)}</div>
              <div class="user-id">@${escapeHtml(group.username || '—')} · ${group.id}</div>
            </div>
          </div>
        </td>
        <td><span class="text-sm">${typeLabels[group.type] || group.type}</span></td>
        <td><span class="text-mono">${formatNumber(group.memberCount || 0)}</span></td>
        <td><span class="text-sm">${group.language || '—'}</span></td>
        <td>${statusBadge}</td>
        <td><span class="text-sm">${createdAt}</span></td>
      </tr>
    `;
  }).join('');

  renderPagination('groupsPagination', state.groups.page, Math.ceil(state.groups.total / state.groups.limit), loadGroups);
}

function searchGroups() {
  clearTimeout(window._searchGroupsTimer);
  window._searchGroupsTimer = setTimeout(() => loadGroups(1), 300);
}

// ============ ECONOMY ============
async function loadLeaderboard() {
  try {
    const data = await fetchWithAuth('/admin/economy/leaderboard?limit=50');
    state.leaderboard = data;
    renderLeaderboard(data);
  } catch (err) {
    showToast('خطا در بارگذاری لیدربورد', 'error');
  }
}

function renderLeaderboard(data) {
  const container = document.getElementById('leaderboardList');

  if (!data || data.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">💰</div><h3>داده‌ای یافت نشد</h3></div>';
    return;
  }

  // Update total label
  const totalLabel = document.getElementById('economyTotalLabel');
  if (state.stats) {
    totalLabel.textContent = `💰 کل اقتصاد: ${formatNumber(state.stats.economyTotal || 0)} سکه`;
  }

  container.innerHTML = data.map((item, i) => {
    const rankClass = i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : 'normal';
    const name = item.firstName || item.username || 'بدون نام';
    const balance = item.balance || 0;
    const level = item.level || 1;
    const xp = item.xp || item.totalXp || 0;

    return `
      <div class="leaderboard-item">
        <div class="leaderboard-rank ${rankClass}">${i + 1}</div>
        <div class="leaderboard-info">
          <div class="leaderboard-name">
            ${escapeHtml(name)}
            ${item.isPremium ? '<span class="badge badge-purple" style="font-size:0.6rem;margin-right:6px;">⭐</span>' : ''}
          </div>
          <div class="leaderboard-detail">سطح ${level} — XP: ${formatNumber(xp)} — @${escapeHtml(item.username || '—')}</div>
        </div>
        <div class="leaderboard-balance">🪙 ${formatNumber(balance)}</div>
      </div>
    `;
  }).join('');
}

// ============ LOGS ============
async function loadLogs(page = 1) {
  try {
    const action = document.getElementById('logActionFilter')?.value || '';
    let url = `/admin/logs?page=${page}&limit=30`;
    if (action) url += `&action=${encodeURIComponent(action)}`;

    const data = await fetchWithAuth(url);
    state.logs = { data: data.logs || [], total: data.total || 0, page: data.page || 1, limit: data.limit || 30 };
    renderLogs();
  } catch (err) {
    showToast('خطا در بارگذاری لاگ‌ها', 'error');
  }
}

function renderLogs() {
  const container = document.getElementById('logsList');
  const logs = state.logs.data;

  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><h3>لاگی یافت نشد</h3></div>';
    return;
  }

  const actionIcons = {
    ban: '⛔', unban: '✅', mute: '🔇', unmute: '🔊',
    warn: '⚠️', kick: '🚫', promote: '⬆️', demote: '⬇️',
    settings: '⚙️', delete: '🗑️', edit: '✏️', join: '➡️',
    leave: '⬅️', game_dice: '🎲', game_rps: '✊', game_quiz: '❓',
  };

  container.innerHTML = logs.map(log => {
    const icon = actionIcons[log.action] || '📌';
    const time = log.createdAt ? formatDate(log.createdAt) : '';
    const detail = log.reason || log.details || '';
    const performedBy = log.performedBy !== 'system' ? `توسط: ${log.performedBy}` : 'سیستم';
    const target = log.targetId ? `هدف: ${log.targetId}` : '';

    return `
      <div class="log-item">
        <div class="log-icon">${icon}</div>
        <div class="log-content">
          <div class="log-action">${escapeHtml(log.action)}</div>
          <div class="log-detail">${performedBy} ${target} ${escapeHtml(detail)}</div>
        </div>
        <div class="log-time">${time}</div>
      </div>
    `;
  }).join('');

  renderPagination('logsPagination', state.logs.page, Math.ceil(state.logs.total / state.logs.limit), loadLogs);
}

function searchLogs() {
  clearTimeout(window._searchLogsTimer);
  window._searchLogsTimer = setTimeout(() => loadLogs(1), 300);
}

// ============ BROADCAST ============
async function sendBroadcast() {
  const message = document.getElementById('broadcastMsg').value.trim();
  const parseMode = document.getElementById('broadcastParseMode').value;

  if (!message) {
    showToast('لطفاً متن پیام را وارد کنید', 'error');
    return;
  }

  try {
    const result = await fetchWithAuth('/admin/broadcast', {
      method: 'POST',
      body: JSON.stringify({ message, parseMode }),
    });

    const resultDiv = document.getElementById('broadcastResult');
    resultDiv.style.display = 'block';
    resultDiv.style.padding = '16px';
    resultDiv.style.borderRadius = 'var(--radius-md)';
    resultDiv.style.background = 'var(--glass-bg)';
    resultDiv.style.border = '1px solid var(--glass-border)';

    resultDiv.innerHTML = `
      <div style="margin-bottom:8px;font-weight:700;">📊 نتیجه ارسال</div>
      <div style="display:flex;gap:16px;font-size:0.85rem;">
        <span style="color:var(--accent-success);">✅ ارسال شده: ${result.sent}</span>
        <span style="color:var(--accent-danger);">❌ ناموفق: ${result.failed}</span>
        <span style="color:var(--accent-info);">📌 کل: ${result.total}</span>
      </div>
    `;

    showToast(`پیام به ${result.sent} گروه ارسال شد`, 'success');
  } catch (err) {
    showToast('خطا در ارسال پیام همگانی', 'error');
  }
}

// ============ SETTINGS ============
function saveSettings() {
  const key = document.getElementById('settingsAdminKey').value.trim();
  const url = document.getElementById('settingsServerUrl').value.trim();

  if (key) {
    state.adminKey = key;
    localStorage.setItem('gx_admin_key', key);
  }
  if (url) {
    state.serverUrl = url;
    localStorage.setItem('gx_server_url', url);
  }

  showToast('تنظیمات ذخیره شد', 'success');
}

// ============ PAGINATION ============
function renderPagination(containerId, currentPage, totalPages, loadFn) {
  const container = document.getElementById(containerId);
  if (!container || totalPages <= 1) {
    if (container) container.innerHTML = '';
    return;
  }

  let html = '';

  // Previous
  html += `<button class="pagination-btn" ${currentPage <= 1 ? 'disabled' : ''} onclick="${currentPage > 1 ? loadFn.name + '(' + (currentPage - 1) + ')' : ''}">‹</button>`;

  // Page numbers
  const start = Math.max(1, currentPage - 2);
  const end = Math.min(totalPages, currentPage + 2);

  for (let i = start; i <= end; i++) {
    html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="${loadFn.name}(${i})">${i}</button>`;
  }

  // Info
  html += `<span class="pagination-info">صفحه ${currentPage} از ${totalPages}</span>`;

  // Next
  html += `<button class="pagination-btn" ${currentPage >= totalPages ? 'disabled' : ''} onclick="${currentPage < totalPages ? loadFn.name + '(' + (currentPage + 1) + ')' : ''}">›</button>`;

  container.innerHTML = html;
}

// ============ TOAST ============
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const icon = icons[type] || icons.info;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============ MODAL ============
function closeModal() {
  document.getElementById('modalContainer').innerHTML = '';
}

// ============ UTILITIES ============
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

function timeAgo(dateStr) {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return `${diffSec} ثانیه پیش`;
  if (diffMin < 60) return `${diffMin} دقیقه پیش`;
  if (diffHour < 24) return `${diffHour} ساعت پیش`;
  if (diffDay < 30) return `${diffDay} روز پیش`;
  return formatDate(dateStr);
}

function formatDate(dateStr) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fa-IR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

function refreshData() {
  loadPageData(state.currentPage);
  showToast('داده‌ها به‌روزرسانی شدند', 'info');
}

function handleSearch(event) {
  if (event.key === 'Enter') {
    const query = event.target.value.trim();
    if (query && state.currentPage === 'users') {
      document.getElementById('userSearch').value = query;
      loadUsers(1);
    } else if (query && state.currentPage === 'groups') {
      document.getElementById('groupSearch').value = query;
      loadGroups(1);
    }
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
}

// ============ KEYBOARD SHORTCUTS ============
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case '1': e.preventDefault(); navigateTo('dashboard'); break;
      case '2': e.preventDefault(); navigateTo('users'); break;
      case '3': e.preventDefault(); navigateTo('groups'); break;
      case '4': e.preventDefault(); navigateTo('economy'); break;
      case '5': e.preventDefault(); navigateTo('logs'); break;
      case 'r': e.preventDefault(); refreshData(); break;
    }
  }
  if (e.key === 'Escape') {
    closeModal();
  }
});
