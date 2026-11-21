/**
 * JalRakshak NCR — Core Frontend Integration & PWA Engine (Phase 7)
 * Engineered by Team NeerNetra (SustainX 2026)
 * Lead Backend & Systems Engineer: Kamal Shukla
 * 
 * Features:
 * 1. PWA Service Worker Registration & Offline Caching
 * 2. Network Online/Offline Status Indicator
 * 3. High-Contrast Accessibility Mode for Heavy Rain & Nighttime Glare
 * 4. Bilingual Localization (Hindi / English) Dictionary & One-Click Toggle
 * 5. Native Phone Dialer Execution (tel: protocols)
 * 6. Live Weather & Hotspots Backend Sync Engine
 * 7. Official Flood Insurance Certificate PDF Download Modal
 * 8. Real-time WebSocket Gateway Client
 */

// =========================================================================
// 1. BILINGUAL LOCALIZATION DICTIONARY (ENGLISH / HINDI)
// =========================================================================
const JALRAKSHAK_I18N = {
  en: {
    app_title: "NEERNETRA",
    app_subtitle: "SMART WATER COMMAND",
    role_civilian: "LOCAL CIVILIAN",
    role_official: "MCG OFFICIAL",
    btn_enter_workspace: "ENTER WORKSPACE",
    nav_overview: "COMMAND & WEATHER",
    nav_map: "MAP & ROUTES",
    nav_offline_sos: "OFFLINE SOS & SMS",
    nav_fleet: "EMERGENCY FLEET",
    nav_drains: "DRAIN CLEANERS",
    nav_settings: "SETTINGS",
    btn_submit_sos: "SUBMIT SOS",
    main_heading: "GURUGRAM FLOOD & RESCUE COMMAND",
    hdr_live_weather: "LIVE WEATHER STATION",
    kpi_road_safety: "ROAD SAFETY %",
    kpi_drain_status: "DRAIN CLEANERS",
    kpi_pending_sos: "PENDING SOS",
    kpi_fleet: "EMERGENCY FLEET",
    hdr_road_alerts: "PUBLIC ROAD ALERTS",
    hdr_speed_dial: "EMERGENCY SPEED DIAL",
    hdr_offline_sos: "OFFLINE SOS & ZERO-SIGNAL SMS COMMAND",
    hdr_theme_select: "APPLICATION THEME",
    hdr_lang_select: "ALL INDIAN LANGUAGES",
    badge_mesh_ready: "SMS & MESH READY",
    btn_switch_role: "SWITCH ROLE",
    lbl_weather_mode: "LIVE WEATHER",
    lbl_flood_passability: "FLOOD PASSABILITY",
    lbl_safe_route: "CALCULATE SAFE ROUTE",
    lbl_insurance_btn: "INSURANCE CERTIFICATE (PDF)"
  },
  hi: {
    app_title: "नीरनेत्र",
    app_subtitle: "स्मार्ट जल नियंत्रण कमान",
    role_civilian: "स्थानीय नागरिक",
    role_official: "एमसीजी अधिकारी",
    btn_enter_workspace: "कमान केंद्र में प्रवेश करें",
    nav_overview: "मौसम और नियंत्रण",
    nav_map: "मानचित्र और सुरक्षित मार्ग",
    nav_offline_sos: "ऑफ़लाइन एसओएस (SMS)",
    nav_fleet: "आपातकालीन वाहन बेड़ा",
    nav_drains: "जल निकासी नाले (36 Master)",
    nav_settings: "सेटिंग्स और भाषा",
    btn_submit_sos: "आपातकालीन SOS भेजें",
    main_heading: "गुरुग्राम बाढ़ नियंत्रण एवं बचाव कमान",
    hdr_live_weather: "लाइव मौसम स्टेशन",
    kpi_road_safety: "सड़क सुरक्षा दर",
    kpi_drain_status: "सफाई प्रगति",
    kpi_pending_sos: "सक्रिय संकट कॉल",
    kpi_fleet: "बचाव वाहन",
    hdr_road_alerts: "सड़क सुरक्षा अलर्ट",
    hdr_speed_dial: "आपातकालीन स्पीड डायल",
    hdr_offline_sos: "बिना इंटरनेट आपातकालीन SMS",
    hdr_theme_select: "एप्लिकेशन थीम",
    hdr_lang_select: "भारतीय भाषाएं",
    badge_mesh_ready: "एसएमएस एवं मेश सक्रिय",
    btn_switch_role: "भूमिका बदलें",
    lbl_weather_mode: "लाइव मौसम",
    lbl_flood_passability: "बाढ़ पारगम्यता",
    lbl_safe_route: "सुरक्षित मार्ग खोजें",
    lbl_insurance_btn: "बीमा प्रमाण पत्र (PDF)"
  }
};

// =========================================================================
// 2. THEME & HIGH-CONTRAST ACCESSIBILITY MODE
// =========================================================================
function setAppTheme(theme) {
  document.body.setAttribute('data-theme', theme);
  try {
    localStorage.setItem('jalrakshak_theme', theme);
  } catch (e) {}

  // Update theme buttons in settings
  ['light', 'dark', 'contrast'].forEach(t => {
    const btn = document.getElementById('themeBtn_' + t);
    if (btn) {
      if (t === theme) {
        btn.classList.add('border-brand-600', 'is-selected');
        btn.classList.remove('border-slate-200');
      } else {
        btn.classList.remove('border-brand-600', 'is-selected');
        btn.classList.add('border-slate-200');
      }
    }
  });

  // Update contrast button label if present
  const contrastBtn = document.getElementById('topBarContrastBtn');
  if (contrastBtn) {
    if (theme === 'contrast') {
      contrastBtn.classList.add('bg-amber-400', 'text-black', 'border-amber-500');
      contrastBtn.classList.remove('bg-[#F8FAFD]', 'text-slate-700');
    } else {
      contrastBtn.classList.remove('bg-amber-400', 'text-black', 'border-amber-500');
      contrastBtn.classList.add('bg-[#F8FAFD]', 'text-slate-700');
    }
  }

  if (typeof showToast === 'function') {
    showToast(`THEME: ${theme.toUpperCase()}`);
  }
}

function toggleQuickContrast() {
  const current = document.body.getAttribute('data-theme') || 'light';
  const target = current === 'contrast' ? 'light' : 'contrast';
  setAppTheme(target);
}

// =========================================================================
// 3. BILINGUAL LANGUAGE LOCALIZATION (ENGLISH / HINDI)
// =========================================================================
function setAppLanguage(code) {
  const langKey = (code === 'hi') ? 'hi' : 'en';
  try {
    localStorage.setItem('jalrakshak_lang', langKey);
  } catch (e) {}

  const dict = JALRAKSHAK_I18N[langKey];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  const activeBadge = document.getElementById('activeLangBadge');
  if (activeBadge) activeBadge.textContent = langKey.toUpperCase();

  const toggleText = document.getElementById('topBarLangText');
  if (toggleText) toggleText.textContent = langKey === 'en' ? 'हिन्दी' : 'English';

  if (typeof showToast === 'function') {
    showToast(`LANGUAGE: ${langKey === 'hi' ? 'हिन्दी (HINDI)' : 'ENGLISH'}`);
  }
}

function toggleBilingualLanguage() {
  let currentLang = 'en';
  try {
    currentLang = localStorage.getItem('jalrakshak_lang') || 'en';
  } catch (e) {}
  const targetLang = currentLang === 'en' ? 'hi' : 'en';
  setAppLanguage(targetLang);
}

// =========================================================================
// 4. NATIVE PHONE DIALER EXECUTION (tel: protocols)
// =========================================================================
function triggerSpeedDialCall(title, number) {
  if (typeof showToast === 'function') {
    showToast(`DIALLING ${title.toUpperCase()} (${number})...`);
  }
  const cleanNumber = number.replace(/[^0-9+]/g, '');
  window.location.href = `tel:${cleanNumber}`;
}

// =========================================================================
// 5. PWA SERVICE WORKER & ONLINE/OFFLINE NETWORK LISTENER
// =========================================================================
function initPWAAndNetwork() {
  // Register ServiceWorker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
      .then(reg => console.log('[PWA] ServiceWorker registered with scope:', reg.scope))
      .catch(err => console.warn('[PWA] ServiceWorker registration failed:', err));
  }

  function updateStatus() {
    const isOnline = navigator.onLine;
    const badge = document.getElementById('networkStatusBadge');
    if (badge) {
      if (isOnline) {
        badge.className = 'hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-extrabold shadow-2xs';
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> ONLINE (LIVE SYNC)';
      } else {
        badge.className = 'hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-300 text-[10px] font-extrabold shadow-2xs';
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping"></span> OFFLINE (CACHED)';
        if (typeof showToast === 'function') {
          showToast('NETWORK OFFLINE: USING CACHED HYDROLOGICAL DATA');
        }
      }
    }
  }

  window.addEventListener('online', updateStatus);
  window.addEventListener('offline', updateStatus);
  updateStatus();
}

// =========================================================================
// 6. LIVE BACKEND SYNCHRONIZATION (WEATHER & HOTSPOTS)
// =========================================================================
async function syncRealOpenMeteoWeather(showFeedback) {
  try {
    const res = await fetch('/api/v1/weather/current');
    if (res.ok) {
      const w = await res.json();
      const topBar = document.getElementById('topBarWeatherQuick');
      if (topBar) {
        topBar.textContent = `${w.temperature_c}°C • ${w.precipitation_mm_hr} mm/hr`;
      }
      if (typeof updateWeatherTileAnimations === 'function') {
        updateWeatherTileAnimations(w.temperature_c, 0, w.precipitation_mm_hr, w.humidity_percent);
      }
      if (showFeedback && typeof showToast === 'function') {
        showToast(`LIVE WEATHER SYNCED: ${w.precipitation_mm_hr} mm/hr (${w.alert_level})`);
      }
    }
  } catch (e) {
    console.warn('[Sync] Weather sync fallback:', e);
  }
}

async function syncBackendHotspotsML() {
  try {
    const res = await fetch('/api/v1/hotspots');
    if (res.ok) {
      const data = await res.json();
      if (data && data.hotspots && typeof floodSpots !== 'undefined') {
        // Update local floodSpots array with persistent backend depth
        data.hotspots.forEach(backendSpot => {
          const local = floodSpots.find(s => s.id === backendSpot.id);
          if (local) {
            local.stormDepth = backendSpot.current_depth_cm;
            local.currentDepth = backendSpot.current_depth_cm;
            local.drainCleaned = Boolean(backendSpot.drain_cleaned);
            local.pumpAssigned = Boolean(backendSpot.pump_assigned);
          }
        });
        if (typeof renderOverviewScreen === 'function') {
          renderOverviewScreen();
        }
        if (typeof updateMapMarkers === 'function') {
          updateMapMarkers();
        }
      }
    }
  } catch (e) {
    console.warn('[Sync] Hotspots sync fallback:', e);
  }
}

// =========================================================================
// 7. OFFICIAL FLOOD INSURANCE CERTIFICATE PDF MODAL & DOWNLOAD
// =========================================================================
function openInsuranceModal() {
  let modal = document.getElementById('insuranceClaimModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'insuranceClaimModal';
    modal.className = 'fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4';
    modal.innerHTML = `
      <div class="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg">
              <i class="fa-solid fa-file-shield"></i>
            </div>
            <div>
              <h3 class="text-sm font-extrabold text-slate-900 headline-caps">FLOOD INSURANCE CERTIFICATE</h3>
              <p class="text-[11px] text-slate-500 font-medium">Official MCG & DDMA Act-of-God Verification PDF</p>
            </div>
          </div>
          <button onclick="closeInsuranceModal()" class="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <form id="insuranceClaimForm" onsubmit="handleInsuranceSubmit(event)" class="space-y-3">
          <div>
            <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Vehicle Owner / Claimant Name *</label>
            <input type="text" id="claimantName" required placeholder="e.g. Kamal Shukla" class="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:border-[#0284c7] focus:outline-none" />
          </div>

          <div class="grid grid-cols-2 gap-2.5">
            <div>
              <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Contact Phone *</label>
              <input type="tel" id="claimantPhone" required placeholder="+91-9811223344" class="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:border-[#0284c7] focus:outline-none" />
            </div>
            <div>
              <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Aadhaar (Last 4 Digits)</label>
              <input type="text" id="claimantAadhaar" maxlength="4" placeholder="4590" class="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:border-[#0284c7] focus:outline-none" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2.5">
            <div>
              <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Vehicle Reg Number *</label>
              <input type="text" id="claimantReg" required placeholder="HR-26-DK-9012" class="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:border-[#0284c7] focus:outline-none uppercase font-mono font-bold" />
            </div>
            <div>
              <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Make & Model *</label>
              <input type="text" id="claimantModel" required placeholder="Honda City / Hyundai Creta" class="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:border-[#0284c7] focus:outline-none" />
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Inundation Incident Location *</label>
            <input type="text" id="claimantLocation" required placeholder="Rajiv Chowk Underpass South Exit (NH-48)" class="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:border-[#0284c7] focus:outline-none" />
          </div>

          <div class="grid grid-cols-2 gap-2.5">
            <div>
              <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Flood Water Depth (cm)</label>
              <input type="number" id="claimantDepth" value="115" min="10" max="250" class="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:border-[#0284c7] focus:outline-none font-bold text-rose-600" />
            </div>
            <div>
              <label class="block text-[11px] font-bold text-slate-700 headline-caps mb-1">Statutory Authority</label>
              <div class="text-xs p-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-600 font-bold">Sec 34 DM Act, 2005</div>
            </div>
          </div>

          <div class="pt-2">
            <button type="submit" id="generateCertBtn" class="w-full py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-extrabold text-xs shadow-md transition flex items-center justify-center gap-2">
              <i class="fa-solid fa-file-arrow-down"></i>
              <span>GENERATE OFFICIAL MCG CERTIFICATE (PDF)</span>
            </button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);
  }
  modal.classList.remove('hidden');
}

function closeInsuranceModal() {
  const modal = document.getElementById('insuranceClaimModal');
  if (modal) modal.classList.add('hidden');
}

async function handleInsuranceSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById('generateCertBtn');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>COMPILING CRYPTOGRAPHIC PDF...</span>';

  const payload = {
    citizen_name: document.getElementById('claimantName').value,
    citizen_phone: document.getElementById('claimantPhone').value,
    citizen_aadhaar_last4: document.getElementById('claimantAadhaar').value || '4590',
    vehicle_registration: document.getElementById('claimantReg').value,
    vehicle_make_model: document.getElementById('claimantModel').value,
    incident_location: document.getElementById('claimantLocation').value,
    flood_water_depth_cm: parseInt(document.getElementById('claimantDepth').value, 10) || 115
  };

  try {
    const res = await fetch('/api/v1/agency/insurance-certificate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MCG_Flood_Certificate_${payload.vehicle_registration.replace(/[^A-Za-z0-9]/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      closeInsuranceModal();
      if (typeof showToast === 'function') {
        showToast('OFFICIAL FLOOD CERTIFICATE PDF GENERATED & DOWNLOADED');
      }
    } else {
      const err = await res.json();
      alert('Certificate generation failed: ' + (err.detail || 'Unknown error'));
    }
  } catch (err) {
    alert('Network error while generating certificate: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// =========================================================================
// 8. REAL-TIME WEBSOCKET GATEWAY CLIENT
// =========================================================================
let liveSocket = null;
function initLiveWebSocket() {
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || '127.0.0.1:8000';
    const wsUrl = `${protocol}//${host}/ws/live?room=officials`;

    liveSocket = new WebSocket(wsUrl);

    liveSocket.onopen = () => {
      console.log('[WebSocket] Real-time disaster gateway connected.');
    };

    liveSocket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('[WebSocket Alert Received]:', msg);
        if (msg.event === 'sos:new_alert') {
          if (typeof showToast === 'function') {
            showToast(`EMERGENCY SOS: ${msg.data.caller_name} at ${msg.data.location_name} (${msg.data.water_level_gauge})`);
          }
          if (typeof playAlertTone === 'function') {
            playAlertTone();
          }
        }
      } catch (e) {}
    };

    liveSocket.onclose = () => {
      console.warn('[WebSocket] Connection closed. Retrying in 5s...');
      setTimeout(initLiveWebSocket, 5000);
    };

    liveSocket.onerror = (err) => {
      console.warn('[WebSocket] Connection error:', err);
    };
  } catch (e) {
    console.warn('[WebSocket] Failed to initialize live socket:', e);
  }
}

// =========================================================================
// 9. AUTOMATIC BOOTSTRAP ON LOAD
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
  // Restore theme
  try {
    const savedTheme = localStorage.getItem('jalrakshak_theme') || 'light';
    setAppTheme(savedTheme);
  } catch (e) {}

  // Restore language
  try {
    const savedLang = localStorage.getItem('jalrakshak_lang') || 'en';
    setAppLanguage(savedLang);
  } catch (e) {}

  // Initialize PWA and network listener
  initPWAAndNetwork();

  // Initialize Live WebSocket
  initLiveWebSocket();
});
