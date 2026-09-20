
const NAV = [
    { label: "Dashboard", icon: "bi-grid-1x2-fill", href: "/" },
    { label: "WhatsApp", icon: "bi-whatsapp", href: "/pages/whatsapp/" },
    { label: "SMS", icon: "bi-chat-square-text", href: "/pages/sms/" },
    { label: "Calls", icon: "bi-telephone", href: "/pages/calls/" },
    { label: "Recordings", icon: "bi-mic", href: "/pages/recordings/" },
    { label: "Live Screen", icon: "bi-display", href: "/pages/live-screen/" },
    { label: "Devices", icon: "bi-phone", href: "/pages/devices/" },
    { label: "Notifications", icon: "bi-bell", href: "/pages/notifications/" },
    { label: "Settings", icon: "bi-gear", href: "/pages/settings/" }
];

let DEVICES = [];

function currentFile() { return location.pathname.split("/").pop() || "index.html" }
function getCsrfToken() {
    const cookie = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}
function safeJsonFetch(url, options = {}) {
    const init = { credentials: 'same-origin', ...options };
    init.headers = {
        'X-CSRFToken': getCsrfToken(),
        ...(options.headers || {})
    };
    return fetch(url, init);
}
function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return;
    navigator.serviceWorker.register('/sw.js').catch(() => {});
}
function syncResponsiveShell() {
  document.body.classList.toggle('mobile-shell', window.matchMedia('(max-width: 900px)').matches);
}
function injectShell() {
    const file = currentFile(), inPages = file !== "index.html";
    document.body.insertAdjacentHTML("afterbegin", `
 <header class="app-top">
  <div class="back-zone"><button class="back-arrow" id="backArrow" title="Back"><i class="bi bi-arrow-left-short"></i></button></div>
  <div class="device-selector position-relative" id="deviceSelector">
   <button class="btn p-0 border-0 d-flex align-items-center gap-2" id="deviceButton">
    <div class="android"><i class="bi bi-android2"></i></div><div class="text-start device-text">
     <div class="device-name" id="selectedDevice">Loading device... <i class="bi bi-chevron-down"></i></div>
     <div class="device-meta"><i class="bi bi-battery-half"></i> <span id="battery">--%</span> &nbsp; <i class="bi bi-wifi"></i> <span id="connection">Connecting</span></div>
    </div>
   </button>
   <div class="device-menu" id="deviceMenu"></div>
  </div>
  <div class="top-center"><button class="try-btn install-btn" id="installAppBtn"><i class="bi bi-download me-2"></i><span>Install App</span></button></div>
  <button class="mobile-menu-toggle" id="mobileMenuToggle" type="button" aria-expanded="false" aria-controls="mobileMenu" title="Open menu"><i class="bi bi-list"></i><span>Menu</span></button>
  <div class="top-actions">
    <button class="bell" id="bellButton" title="Notifications"><i class="bi bi-bell"></i><span class="bell-dot"></span></button>
    <div class="user-widget" id="userWidget">
      <div class="user-avatar" id="userAvatar">👩🏻</div>
      <div class="user-display">
        <span class="user-name" id="userName">Loading...</span>
        <span class="user-role">Admin</span>
      </div>
    </div>
    <div class="lang-wrap">
      <button class="lang" id="langButton">EN <i class="bi bi-caret-down-fill"></i></button>
      <div class="lang-menu" id="langMenu">
        <button class="lang-option active" data-lang="EN">English</button>
        <button class="lang-option" data-lang="ES">Spanish</button>
        <button class="lang-option" data-lang="FR">French</button>
      </div>
    </div>
    <a class="logout-btn" href="/logout/" title="Logout admin">
      <i class="bi bi-box-arrow-right"></i><span>Logout</span>
    </a>
  </div>
  <div class="mobile-menu" id="mobileMenu">
   <nav class="mobile-nav">${NAV.map(n => `<a class="nav-link ${((inPages && file === n.href) || (file === "index.html" && n.label === "Dashboard")) ? "active" : ""}" href="${n.href}"><i class="bi ${n.icon}"></i><span>${n.label}</span></a>`).join("")}</nav>
   <div class="mobile-menu-actions">
    <button class="mobile-menu-action" id="mobileProfile" type="button"><i class="bi bi-person-circle"></i><span>Profile</span></button>
    <button class="mobile-menu-action" id="mobileNotifications" type="button"><i class="bi bi-bell"></i><span>Notifications</span></button>
    <button class="mobile-menu-action" id="mobileLanguage" type="button"><i class="bi bi-translate"></i><span>Language: EN</span></button>
    <button class="mobile-menu-action" id="mobileInstall" type="button"><i class="bi bi-download"></i><span>Install App</span></button>
    <a class="mobile-menu-action danger" href="/logout/"><i class="bi bi-box-arrow-right"></i><span>Logout</span></a>
   </div>
  </div>
 </header>
 <div class="app-shell">
  <aside class="sidebar">
   <div class="sidebar-head">
    <span class="brand-mark"><i class="bi bi-shield-check"></i>Family Guard</span>
    <button class="sidebar-toggle" id="sidebarToggle" title="Toggle menu"><i class="bi bi-list"></i></button>
   </div>
   <div class="nav-label">Monitoring</div>
   <nav class="nav-list">${NAV.map(n => `<a class="nav-link ${((inPages && file === n.href) || (file === "index.html" && n.label === "Dashboard")) ? "active" : ""}" href="${n.href}"><i class="bi ${n.icon}"></i><span>${n.label}</span></a>`).join("")}</nav>
  </aside>
  <div class="main-wrap"></div>
 </div>`);
    const main = document.querySelector(".main-wrap");
    while (document.body.children.length > 2) { /* content is moved below */ break; }
    const existing = [...document.body.children].filter(x => !x.classList.contains("app-top") && !x.classList.contains("app-shell"));
    const shellMain = document.querySelector(".main-wrap");
    existing.forEach(x => { if (x !== document.querySelector(".app-top") && x !== document.querySelector(".app-shell")) shellMain.appendChild(x) });
    shellMain.insertAdjacentHTML("afterbegin", `<div class="pagebar">${document.title.replace(" — Device Monitor", "").replace("Device Monitor", "Dashboard")} <i class="bi bi-chevron-down"></i></div>`);
    const oldNotice = document.querySelector(".legacy-notice"); if (oldNotice) oldNotice.remove();
    setupDeviceMenu();
    setupBackArrow();
    setupProfileWidget();
    setupLanguageWidget();
    setupSearchFilters();
    setupClickWorkflows();
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.onclick = () => {
            document.querySelector('.app-shell').classList.toggle('sidebar-collapsed');
        };
    }
      setupMobileMenu();
      syncResponsiveShell();
      window.addEventListener('resize', syncResponsiveShell);
}

    function setupMobileMenu() {
      const toggle = document.getElementById('mobileMenuToggle');
      const menu = document.getElementById('mobileMenu');
      if (!toggle || !menu) return;
      toggle.addEventListener('click', event => {
        event.stopPropagation();
        const open = menu.classList.toggle('show');
        toggle.setAttribute('aria-expanded', String(open));
        toggle.innerHTML = open ? '<i class="bi bi-x-lg"></i><span>Close</span>' : '<i class="bi bi-list"></i><span>Menu</span>';
      });
      const profileName = document.getElementById('userName');
      const mobileProfile = document.querySelector('#mobileProfile span');
      if (profileName && mobileProfile) {
        const observer = new MutationObserver(() => { mobileProfile.textContent = profileName.textContent || 'Profile'; });
        observer.observe(profileName, { childList: true, characterData: true, subtree: true });
      }
      document.getElementById('mobileProfile')?.addEventListener('click', () => { window.location.href = '/pages/settings/'; });
      document.getElementById('mobileNotifications')?.addEventListener('click', () => { window.location.href = '/pages/notifications/'; });
      document.getElementById('mobileInstall')?.addEventListener('click', () => { document.getElementById('installAppBtn')?.click(); });
      document.addEventListener('click', event => {
        if (!menu.contains(event.target) && !toggle.contains(event.target)) {
          menu.classList.remove('show');
          toggle.setAttribute('aria-expanded', 'false');
          toggle.innerHTML = '<i class="bi bi-list"></i><span>Menu</span>';
        }
      });
    }

function setupBackArrow() {
    const backArrow = document.getElementById('backArrow');
    if (!backArrow) return;
    backArrow.onclick = () => {
        if (document.referrer && document.referrer.startsWith(location.origin)) {
            history.back();
        } else {
            window.location.href = '/';
        }
    };
}

function setupProfileWidget() {
    const profileName = document.getElementById('userName');
    if (!profileName) return;
    safeJsonFetch('/api/profile/', { method: 'GET' }).then(r => {
        if (!r.ok) throw new Error('Profile not available');
        return r.json();
    }).then(payload => {
        const name = payload.full_name || payload.username || 'Admin';
        if (profileName) profileName.textContent = name;
        const avatar = document.getElementById('userAvatar');
        if (avatar && payload.full_name) {
            avatar.textContent = payload.full_name.split(/\s+/).map(s => s[0]).slice(0, 2).join('').toUpperCase() || 'A';
        }
    }).catch(() => {
        if (profileName) profileName.textContent = 'Admin';
    });
}

function setupLanguageWidget() {
    const langButton = document.getElementById('langButton');
    const langMenu = document.getElementById('langMenu');
    const langOptions = Array.from(document.querySelectorAll('#langMenu .lang-option'));
    if (langButton && langMenu) {
        langButton.addEventListener('click', () => {
            langMenu.classList.toggle('show');
        });
    }
    langOptions.forEach(option => option.addEventListener('click', () => {
        langOptions.forEach(o => o.classList.toggle('active', o === option));
        const lang = option.dataset.lang || 'EN';
        if (langButton) {
            langButton.innerHTML = `${lang} <i class="bi bi-caret-down-fill"></i>`;
        }
        if (langMenu) langMenu.classList.remove('show');
    }));
}

function setupSearchFilters() {
    const searches = Array.from(document.querySelectorAll('[data-search]'));
    searches.forEach(input => {
        const target = input.getAttribute('data-target') || '[data-search-row]';
        const context = input.closest('.panel') || input.closest('main') || document.body;
        const rows = () => Array.from(context.querySelectorAll(target));
        const applySearch = () => {
            const txt = (input.value || '').trim().toLowerCase();
            rows().forEach(row => {
                const hay = (row.textContent || '').trim().toLowerCase();
                row.style.display = hay.includes(txt) ? '' : 'none';
            });
        };
        input.addEventListener('input', applySearch);
        input.dataset.filterReady = 'true';
        applySearch();
    });
}

function setupClickWorkflows() {
    const bellButton = document.getElementById('bellButton');
    if (bellButton) {
        bellButton.addEventListener('click', () => {
            window.location.href = '/pages/notifications/';
        });
    }
    const userWidget = document.getElementById('userWidget');
    if (userWidget) {
        userWidget.addEventListener('click', () => {
            window.location.href = '/pages/settings/';
        });
    }
}
function setupDeviceMenu() {
    const menu = document.getElementById("deviceMenu");
    menu.innerHTML = '';
    fetch('/api/devices/')
      .then(r => r.json())
      .then(payload => {
        DEVICES = payload.devices || [];
        if (!DEVICES.length) {
          document.getElementById('selectedDevice').innerHTML = 'No device <i class="bi bi-chevron-down"></i>';
          return;
        }
        menu.innerHTML = DEVICES.map((d, i) => `<div class="device-option ${i === 0 ? "active" : ""}" data-index="${i}"><div class="fw-semibold small">${d.name}</div><div class="text-muted" style="font-size:10px">${d.os} • ${d.connection}</div></div>`).join("");
        const first = DEVICES[0];
        document.getElementById('selectedDevice').innerHTML = `${first.name} <i class="bi bi-chevron-down"></i>`;
        document.getElementById('battery').textContent = `${first.battery || '—'}%`;
        document.getElementById('connection').textContent = first.connection_status === 'Online' ? 'Connected' : 'Offline';
        menu.querySelectorAll(".device-option").forEach(o => o.onclick = () => { const d = DEVICES[o.dataset.index]; document.getElementById("selectedDevice").innerHTML = `${d.name} <i class="bi bi-chevron-down"></i>`; document.getElementById("battery").textContent = `${d.battery || '—'}%`; document.getElementById("connection").textContent = d.connection_status === 'Online' ? 'Connected' : 'Offline'; menu.classList.remove("show") });
      })
      .catch(() => {
        document.getElementById('selectedDevice').innerHTML = 'No device <i class="bi bi-chevron-down"></i>';
      });
    document.getElementById("deviceButton").onclick = e => { e.stopPropagation(); menu.classList.toggle("show") };
    document.addEventListener("click", () => menu.classList.remove("show"));
}
function bindDeviceModal() {
    if (!document.getElementById("bindModal")) {
        document.body.insertAdjacentHTML("beforeend", `<div class="modal fade" id="bindModal" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content"><div class="modal-header"><h5 class="modal-title">Bind Authorized Device</h5><button class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><p class="text-muted small">Enter the child device details. After creation, the server generates a pairing code and secure consent link. Send both to the child; the code is entered on the child consent page.</p><label class="form-label">Device name</label><input id="deviceName" class="form-control mb-3" placeholder="e.g. Child's Galaxy"><label class="form-label">Device ID</label><input id="deviceId" class="form-control mb-3" placeholder="device-01"><label class="form-label">OS</label><input id="deviceOs" class="form-control mb-3" value="Android" placeholder="Android"><label class="form-label">Battery</label><input id="deviceBattery" class="form-control mb-3" placeholder="78"><label class="form-label">Risk level</label><input id="deviceRisk" class="form-control mb-3" value="Low" placeholder="Low"><div class="pairing-help small text-muted"><i class="bi bi-info-circle me-1"></i>The pairing code is generated after you click Create Pairing. It is not entered in this form. The device stays inactive until the child accepts consent.</div></div><div class="modal-footer"><button class="btn btn-light" data-bs-dismiss="modal">Cancel</button><button class="try-btn" id="submitBinding">Create Pairing</button></div></div></div></div>`);
    }
    document.querySelectorAll("[data-action='bind']").forEach(b => b.onclick = () => {
        new bootstrap.Modal(document.getElementById("bindModal")).show();
    });
    const createPairingButton = document.getElementById('submitBinding');
    if (createPairingButton) {
        createPairingButton.onclick = event => {
            event.preventDefault();
            const formData = new FormData();
            const name = document.getElementById('deviceName').value || 'New Authorized Device';
            const deviceId = document.getElementById('deviceId').value || `device-${Date.now()}`;
            const os = document.getElementById('deviceOs').value || 'Android';
            const battery = document.getElementById('deviceBattery').value || '0';
            const risk = document.getElementById('deviceRisk').value || 'Low';
            formData.append('name', name);
            formData.append('device_id', deviceId);
            formData.append('os', os);
            formData.append('battery', battery);
            formData.append('risk_level', risk);
            formData.append('connection_status', 'Online');
            safeJsonFetch('/api/bind-device/', {
                method: 'POST',
                body: formData,
            }).then(r => {
                if (!r.ok) return r.json().then(payload => Promise.reject(payload));
                return r.json();
            }).then(payload => {
                const msg = payload.detail || 'Device paired successfully.';
                 if (payload.device && payload.device.pairing_token) {
                   const childUrl = `${location.origin}${payload.consent_url || `/child/consent/${payload.device.pairing_token}/`}`;
                   const devicePage = '/pages/devices/';
                   alert(`${msg}\n\nPairing code: ${payload.device.pairing_code || 'Unavailable'}\nChild consent link: ${childUrl}\n\nThe device remains inactive until the child accepts consent.`);
                   window.location.href = devicePage;
                } else {
                   alert(msg);
                   window.location.href = '/pages/devices/';
                }
              }).catch(err => {
                console.error(err);
                alert(err.detail || 'Pairing failed.');
              });
        };
    }

}
function wireInstallButton() {
    const installBtn = document.getElementById('installAppBtn');
    if (!installBtn) return;
    registerServiceWorker();
    let deferredPrompt = null;
    window.addEventListener('beforeinstallprompt', event => {
        event.preventDefault();
        deferredPrompt = event;
        installBtn.classList.add('ready');
        installBtn.innerHTML = '<i class="bi bi-download me-2"></i><span>Install App</span>';
    });
    installBtn.addEventListener('click', () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            return;
        }
        const isChrome = /Chrome/.test(navigator.userAgent) && !/Edg/.test(navigator.userAgent);
        const isEdge = /Edg/.test(navigator.userAgent);
        if (isChrome || isEdge) {
            alert('The Family Guard PWA install prompt is available through your browser menu. Open the page with HTTPS or localhost, then use the browser install option.');
        } else {
            alert('Install the Family Guard PWA from the browser or device menu.');
        }
    });
}

function renderDashboardFromApi() {
    safeJsonFetch('/api/dashboard/', { method: 'GET' })
      .then(r => r.json())
      .then(payload => {
        const stats = payload.stats || {};
        const statPairs = {
          'Monitored Devices': 'monitored_devices',
          'WhatsApp Messages': 'whatsapp_messages',
          'SMS Messages': 'sms_messages',
          'Call Recordings': 'call_recordings',
        };
        const statLabels = Array.from(document.querySelectorAll('.stat small'));
        statLabels.forEach(label => {
          const text = label.textContent.trim();
          const key = statPairs[text];
          const valueTag = label.nextElementSibling;
          if (key && valueTag) valueTag.textContent = stats[key] ?? 0;
        });
        const activityList = document.getElementById('recentActivityList');
        if (activityList) {
            activityList.innerHTML = (payload.timeline || []).length
                ? payload.timeline.map(item => `<div class="py-3 border-bottom"><b class="small">${item.title || 'Device activity'}</b><div class="text-muted small">${item.device || 'Device'} &bull; ${item.time || ''}</div><div class="text-muted small">${item.summary || ''}</div></div>`).join('')
                : '<div class="py-3 text-muted small">No authorized device activity yet.</div>';
        }
        const deviceList = document.getElementById('dashboardDeviceList');
        if (deviceList) {
            deviceList.innerHTML = (payload.devices || []).length
                ? payload.devices.map(device => `<div class="py-3 border-bottom"><b class="small">${device.name || device.device_id}</b><div class="${device.is_active && device.connection_status === 'Online' ? 'text-success' : 'text-secondary'} small">&bull; ${device.is_active ? device.connection_status : (device.consent_accepted ? 'Disconnected' : 'Awaiting consent')}</div></div>`).join('')
                : '<div class="py-3 text-muted small">No bound devices yet.</div>';
        }
          const online = (payload.devices || []).filter(device => device.is_active && device.connection_status === 'Online').length;
          document.querySelectorAll('[data-live-device-count]').forEach(node => { node.textContent = online; });
      })
      .catch(() => {});
}

      function startAdminRealtimeRefresh() {
        if (!document.body.classList.contains('admin-dashboard') && window.location.pathname !== '/pages/devices/') return;
        setInterval(() => {
          if (!document.hidden) {
            renderDashboardFromApi();
            if (window.location.pathname === '/pages/devices/') renderDevicesPage();
          }
        }, 10000);
      }

function renderWhatsAppPage() {
    safeJsonFetch('/api/whatsapp/', { method: 'GET' })
      .then(r => r.json())
      .then(payload => {
        const messages = payload.messages || [];
        const list = document.getElementById('waList');
        if (!list) return;
        list.innerHTML = messages.slice(0, 30).map((m, idx) => `
          <div class="p-3 border-top d-flex gap-3 wa-row" data-name="${m.sender || 'Unknown'}">
            <div class="avatar a${(idx % 5) + 1}">${(m.sender || 'U').charAt(0)}</div>
            <div>
              <b>${m.sender || 'Unknown'}</b>
              <div class="small text-muted">${m.content || ''}</div>
              <small>${m.time || ''}</small>
            </div>
          </div>
        `).join('');
      }).catch(() => {});
}

function renderSmsPage() {
    safeJsonFetch('/api/sms/', { method: 'GET' })
      .then(r => r.json())
      .then(payload => {
        const rows = payload.messages || [];
        const table = document.getElementById('smsRows');
        if (!table) return;
        table.innerHTML = rows.map(m => `
          <tr>
            <td>${m.sender || 'Unknown'}</td>
            <td>${m.content || ''}</td>
            <td>${m.time || ''}</td>
            <td><span class="badge text-bg-success">Received</span></td>
          </tr>
        `).join('');
      }).catch(() => {});
}

function renderCallsPage() {
    safeJsonFetch('/api/calls/', { method: 'GET' })
      .then(r => r.json())
      .then(payload => {
        const rows = payload.calls || [];
        const table = document.getElementById('callRows');
        if (!table) return;
        table.innerHTML = rows.map(c => `
          <tr>
            <td>${c.caller || 'Unknown'}<br /><small class="text-muted">${c.device || 'Device'}</small></td>
            <td><span class="badge text-bg-success">Incoming</span></td>
            <td>${c.time || ''}</td>
            <td>${c.duration || '00:00'}</td>
            <td><a href="/pages/recordings/"><i class="bi bi-play-circle-fill text-success fs-5"></i></a></td>
          </tr>
        `).join('');
      }).catch(() => {});
}

function renderRecordingsPage() {
    safeJsonFetch('/api/recordings/', { method: 'GET' })
      .then(r => r.json())
      .then(payload => {
        const rows = payload.recordings || [];
        const box = document.getElementById('recRows');
        if (!box) return;
        box.innerHTML = rows.map((r, idx) => `
          <div class="p-3 border-bottom d-flex align-items-center gap-3 rec-row" data-name="${r.source || 'Device'}">
            <div class="avatar" style="background: #ee5d67"><i class="bi bi-mic"></i></div>
            <div class="flex-grow-1">
              <b>${r.source || 'Device'}</b>
              <div class="small text-muted">${r.status || 'Ready'} • ${r.date || ''} • ${r.duration || '00:00'}</div>
            </div>
            <button class="btn btn-sm btn-light"><i class="bi bi-play-fill"></i></button>
            <button class="btn btn-sm btn-light"><i class="bi bi-download"></i></button>
          </div>
        `).join('');
      }).catch(() => {});
}

function renderNotificationsPage() {
    safeJsonFetch('/api/notifications/', { method: 'GET' })
      .then(r => r.json())
      .then(payload => {
        const notes = payload.notifications || [];
        const root = document.querySelector('.page-content .panel') || document.body;
        const panel = document.querySelector('#notifyRows');
        if (!panel) return;
        panel.innerHTML = notes.map(n => `
          <div class="n p-3 border-bottom bg-light d-flex gap-3">
            <div class="avatar" style="background: #25c95b"><i class="bi bi-whatsapp"></i></div>
            <div>
              <b class="small">${n.title || 'Device update'}</b>
              <div class="small text-muted">${n.source || 'Family Guard'} • ${n.time || ''}</div>
            </div>
          </div>
        `).join('');
      }).catch(() => {});
}

function renderDevicesPage() {
    safeJsonFetch('/api/devices/', { method: 'GET' })
      .then(r => r.json())
      .then(payload => {
        const devices = payload.devices || [];
        const cards = document.querySelector('.page-content .p-3.row.g-3');
        if (!cards) return;
        cards.innerHTML = devices.map(d => `
          <div class="col-md-6">
            <div class="border rounded-4 p-3">
              <div class="d-flex gap-3">
                <div class="avatar" style="background: #20b7a5"><i class="bi bi-phone"></i></div>
                <div>
                  <b>${d.name || d.device_id || 'Family Device'}</b>
                  <div class="${d.is_active && d.connection_status === 'Online' ? 'text-success' : 'text-secondary'} small">● ${d.is_active ? (d.connection_status || 'Online') : (d.consent_accepted ? 'Disconnected' : 'Awaiting consent')}</div>
                </div>
              </div>
              <hr />
              <div class="small text-muted">${d.os || 'Android'} • Battery ${d.battery || 0}% • ${d.last_seen ? `Last seen ${new Date(d.last_seen).toLocaleString()}` : 'Not connected'}</div>
              <a href="/pages/live-screen/" class="btn btn-sm btn-outline-primary mt-3">View Device</a>
            </div>
          </div>
        `).join('');
      }).catch(() => {});
}

function loadPageData() {
    const path = window.location.pathname;
    if (path === '/' || path === '/dashboard/') {
        renderDashboardFromApi();
    } else if (path === '/pages/whatsapp/') {
        renderWhatsAppPage();
    } else if (path === '/pages/sms/') {
        renderSmsPage();
    } else if (path === '/pages/calls/') {
        renderCallsPage();
    } else if (path === '/pages/recordings/') {
        renderRecordingsPage();
    } else if (path === '/pages/notifications/') {
        renderNotificationsPage();
    } else if (path === '/pages/devices/') {
        renderDevicesPage();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    injectShell();
    bindDeviceModal();
    wireInstallButton();
    loadPageData();
    startAdminRealtimeRefresh();
});
