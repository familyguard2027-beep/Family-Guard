
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
  <div class="top-actions">
    <div class="bell"><i class="bi bi-bell"></i><span class="bell-dot"></span></div>
    <div class="user-avatar">👩🏻</div>
    <div class="lang">EN <i class="bi bi-caret-down-fill"></i></div>
    <a class="logout-btn" href="/logout/" title="Logout admin">
      <i class="bi bi-box-arrow-right"></i><span>Logout</span>
    </a>
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
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.onclick = () => {
            document.querySelector('.app-shell').classList.toggle('sidebar-collapsed');
        };
    }
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
        document.body.insertAdjacentHTML("beforeend", `<div class="modal fade" id="bindModal" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content"><div class="modal-header"><h5 class="modal-title">Bind Authorized Device</h5><button class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><p class="text-muted small">Enter the pairing details for a device whose owner has authorized monitoring.</p><label class="form-label">Device name</label><input id="deviceName" class="form-control mb-3" placeholder="e.g. John's Galaxy S23"><label class="form-label">Device ID</label><input id="deviceId" class="form-control mb-3" placeholder="device-01"><label class="form-label">OS</label><input id="deviceOs" class="form-control mb-3" placeholder="Android 14"><label class="form-label">Battery</label><input id="deviceBattery" class="form-control mb-3" placeholder="78"><label class="form-label">Risk level</label><input id="deviceRisk" class="form-control mb-3" placeholder="Low"><label class="form-label">Pairing code</label><input id="pairingCode" class="form-control" placeholder="Enter pairing code"></div><div class="modal-footer"><button class="btn btn-light" data-bs-dismiss="modal">Cancel</button><button class="try-btn" data-bs-dismiss="modal" id="submitBinding">Create Pairing</button></div></div></div></div>`);
    }
    document.querySelectorAll("[data-action='bind']").forEach(b => b.onclick = () => new bootstrap.Modal(document.getElementById("bindModal")).show());
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
            const pairingCode = document.getElementById('pairingCode').value || '';
            formData.append('name', name);
            formData.append('device_id', deviceId);
            formData.append('os', os);
            formData.append('battery', battery);
            formData.append('risk_level', risk);
            formData.append('connection_status', 'Online');
            if (pairingCode) formData.append('pairing_code', pairingCode);
            safeJsonFetch('/api/bind-device/', {
                method: 'POST',
                body: formData,
            }).then(r => {
                if (!r.ok) return r.json().then(payload => Promise.reject(payload));
                return r.json();
            }).then(payload => {
                const msg = payload.detail || 'Device paired successfully.';
                if (payload.device && payload.device.pairing_token) {
                   const childUrl = `${location.origin}/child/consent/${payload.device.pairing_token}/`;
                   const devicePage = '/pages/devices/';
                   alert(`${msg}. Child consent URL: ${childUrl}`);
                   window.location.href = devicePage;
                } else {
                   alert(msg);
                   window.location.href = '/pages/devices/';
                }
              }).catch(err => {
                console.error(err);
                alert('Pairing failed.');
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
document.addEventListener("DOMContentLoaded", () => {
    injectShell();
    bindDeviceModal();
    wireInstallButton();
});
