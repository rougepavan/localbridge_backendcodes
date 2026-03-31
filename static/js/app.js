// Global App Logic, API calls, and Utilities

const API_BASE = ''; // Same origin

/**
 * Strict email validation matching backend rules.
 */
function validateEmailString(email) {
    if (!email) return { isValid: false, message: "Email is required" };
    email = email.trim().toLowerCase();
    
    if (email.includes(' ')) return { isValid: false, message: "Email cannot contain spaces" };
    const parts = email.split('@');
    if (parts.length !== 2) return { isValid: false, message: "Email must contain exactly one '@'" };
    
    const [local, domain] = parts;
    if (local.length < 3) return { isValid: false, message: "Local part must be at least 3 characters" };
    if (local.includes('..')) return { isValid: false, message: "Local part cannot contain consecutive dots" };
    if (/^\d+$/.test(local)) return { isValid: false, message: "Local part cannot be only numbers" };
    if (!/^[a-z0-9._%+-]+$/.test(local)) return { isValid: false, message: "Invalid characters in local part" };
    
    const allowedDomains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'protonmail.com'];
    if (!allowedDomains.includes(domain)) {
        return { isValid: false, message: "Only public providers (Gmail, Yahoo, Hotmail, etc.) are allowed" };
    }
    
    return { isValid: true };
}

// Basic Toast Notification System
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? 
    `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>` : 
    `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;

  toast.innerHTML = `
    ${icon}
    <div style="font-weight: 500; font-size: 0.875rem;">${message}</div>
  `;

  container.appendChild(toast);
  
  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('show');
    toast.style.transform = 'translateX(0)';
  });

  setTimeout(() => {
    toast.style.transform = 'translateX(120%)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function togglePasswordVisibility(btn, inputId) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-indigo-600">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
                <line x1="1" y1="1" x2="23" y2="23"></line>
            </svg>
        `;
    } else {
        input.type = 'password';
        btn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
            </svg>
        `;
    }
}

/**
 * Premium Error Modal with Retry/Cancel buttons.
 */
function showErrorModal(message, retryCallback) {
  // Remove existing modal if any
  const existing = document.getElementById('error-modal-container');
  if (existing) existing.remove();

  const modalHtml = `
    <div id="error-modal-container" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[200] flex items-center justify-center p-4">
        <div id="error-modal" class="bg-white rounded-3xl w-full max-w-sm overflow-hidden shadow-2xl p-8 text-center transform scale-90 opacity-0">
            <div class="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg class="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
            </div>
            <h3 class="text-xl font-bold text-slate-800 mb-2">Connection Error</h3>
            <p class="text-slate-500 mb-8 leading-relaxed">${message}</p>
            
            <div class="flex flex-col gap-3">
                <button id="error-retry-btn" class="w-full btn-premium btn-premium-indigo py-3.5 rounded-xl text-white font-bold text-sm transform transition-transform active:scale-95">
                    Retry Connection
                </button>
                <button id="error-cancel-btn" class="w-full py-3.5 text-sm font-semibold text-slate-500 hover:bg-slate-50 rounded-xl transition-colors">
                    Cancel
                </button>
            </div>
        </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);

  const container = document.getElementById('error-modal-container');
  const modal = document.getElementById('error-modal');

  // GSAP Animation
  if (window.gsap) {
    gsap.to(modal, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(1.7)" });
  } else {
    modal.style.transform = 'scale(1)';
    modal.style.opacity = '1';
    modal.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
  }

  const closeModal = () => {
    if (window.gsap) {
        gsap.to(modal, { scale: 0.9, opacity: 0, duration: 0.3, onComplete: () => container.remove() });
    } else {
        container.remove();
    }
  };

  document.getElementById('error-retry-btn').onclick = () => {
    closeModal();
    if (retryCallback) retryCallback();
  };

  document.getElementById('error-cancel-btn').onclick = closeModal;
}

const AppState = {
  getUser: () => {
    try {
      return JSON.parse(localStorage.getItem('currentUser'));
    } catch {
      return null;
    }
  },
  setUser: (user) => {
    localStorage.setItem('currentUser', JSON.stringify(user));
  },
  logout: async () => {
    const user = AppState.getUser();
    if (user && user.email) {
      try {
        await fetch('/logout', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ email: user.email })
        });
      } catch (e) { console.error('Logout error', e); }
    }
    localStorage.removeItem('currentUser');
    window.location.href = '/login';
  },
  requireAuth: () => {
    // Disabled for debugging
  },
  getLocation: () => {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve(null),
        { timeout: 5000 }
      );
    });
  }
};

// --- Notifications System ---
function setupNotifications() {
  const user = AppState.getUser();
  if(!user) return;
  
  // Inject notification dropdown into DOM if missing
  let navActions = document.querySelector('.nav-actions');
  if(navActions && !document.getElementById('notifMenuBtn')) {
    // Look for the existing bell icon, or add one if it doesn't exist
    // Check if we already have a notification button to avoid duplication or removing wrong buttons
    if (document.getElementById('notifMenuBtn')) return;
    
    const notifMarkup = `
      <div class="relative cursor-pointer mr-4" id="notifMenuBtn">
          <button class="icon-btn" onclick="toggleNotifDropdown()">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
              <span id="notifBadge" class="hidden absolute top-0 right-0 w-2.5 h-2.5 bg-pink-500 border-2 border-white rounded-full"></span>
          </button>
          
          <div id="notifDropdown" class="hidden absolute right-0 mt-3 w-80 bg-white rounded-2xl shadow-xl border border-slate-100 z-50 overflow-hidden">
              <div class="px-4 py-3 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                  <h3 class="font-bold text-slate-800 text-sm">Notifications</h3>
                  <button onclick="markAllRead()" class="text-xs text-indigo-600 hover:text-indigo-800 font-semibold">Mark all read</button>
              </div>
              <div id="notifList" class="max-h-80 overflow-y-auto">
                  <div class="p-4 text-center text-sm text-slate-500">No new notifications.</div>
              </div>
          </div>
      </div>
    `;
    navActions.insertAdjacentHTML('afterbegin', notifMarkup);
  }

  fetchNotifications();
  setInterval(fetchNotifications, 10000); // Poll every 10s
}

window.toggleNotifDropdown = function() {
  const drop = document.getElementById('notifDropdown');
  if(drop) drop.classList.toggle('hidden');
}

window.markAllRead = async function() {
  const user = AppState.getUser();
  if(!user) return;
  try {
      await fetch('/notifications/read', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ email: user.email })
      });
      fetchNotifications();
  } catch(e) {}
}

async function fetchNotifications() {
  const user = AppState.getUser();
  if(!user || !user.email) return;
  try {
      const res = await fetch(`/notifications?email=${user.email}`);
      const data = await res.json();
      
      const badge = document.getElementById('notifBadge');
      const list = document.getElementById('notifList');
      
      if(!badge || !list) return;

      if(data.length > 0) {
          if (typeof window.lastNotifCount !== 'undefined' && data.length > window.lastNotifCount) {
              showToast('New notification: ' + data[0].message, 'info');
          }
          window.lastNotifCount = data.length;

          badge.classList.remove('hidden');
          
          const matchesNav = document.querySelector('a[href="/matches"]');
          if (matchesNav && !document.getElementById('matchesNavDot')) {
              matchesNav.insertAdjacentHTML('beforeend', '<span id="matchesNavDot" class="w-2.5 h-2.5 bg-pink-500 rounded-full ml-auto shadow-sm"></span>');
          }

          list.innerHTML = data.map(n => {
              let icon = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" class="text-indigo-500"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
              if(n.type === 'accepted') icon = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" class="text-green-500"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
              
              let dest = n.related_id ? `/product/0?match_id=${n.related_id}` : '#';
              
              return `
              <a href="${dest}" class="flex items-start gap-3 p-4 hover:bg-slate-50 border-b border-slate-50 transition-colors">
                  <div class="mt-0.5">${icon}</div>
                  <div class="flex-grow">
                      <p class="text-sm text-slate-800 leading-tight">${n.message}</p>
                      <p class="text-xs text-slate-400 mt-1">${new Date(n.created_at).toLocaleDateString()}</p>
                  </div>
              </a>
          `}).join('');
      } else {
          window.lastNotifCount = 0;
          badge.classList.add('hidden');
          const checkDot = document.getElementById('matchesNavDot');
          if(checkDot) checkDot.remove();
          list.innerHTML = '<div class="p-4 text-center text-sm text-slate-500">No new notifications.</div>';
      }
  } catch(e) {}
}

document.addEventListener("DOMContentLoaded", () => {
    setupNotifications();
});

// Helper for generic API forms
async function submitApiForm(formElement, url, method = 'POST') {
  const btn = formElement.querySelector('button[type="submit"]');
  const originalText = btn.innerHTML;
  btn.innerHTML = `<span class="animate-pulse">Loading...</span>`;
  btn.disabled = true;

  try {
    const isMultipart = formElement.enctype === 'multipart/form-data';
    const fetchOptions = {
      method: method
    };

    if (isMultipart) {
      fetchOptions.body = new FormData(formElement);
    } else {
      const data = Object.fromEntries(new FormData(formElement).entries());
      fetchOptions.headers = { 'Content-Type': 'application/json' };
      fetchOptions.body = JSON.stringify(data);
    }

    const response = await fetch(url, fetchOptions);
    const result = await response.json();
    return result;
  } catch (err) {
    console.error(err);
    throw new Error('Network error occurred.');
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}
