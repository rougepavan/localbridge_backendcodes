/**
 * sidebar.js  —  Shared sidebar icons & active state for all dashboard pages.
 * Inject the sidebar logo and nav icons, then mark the current page as active.
 */

// ── Marketplace-themed SVG icons ──────────────────────────────────────────────
const NAV_ICONS = {
  discover: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
  </svg>`,
  post: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
    <circle cx="12" cy="13" r="3"/>
  </svg>`,
  matches: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
  </svg>`,
  history: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/>
    <polyline points="12 7 12 12 15 15"/>
  </svg>`,
  profile: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
    <path d="M8 21h8"/><path d="M12 17v4"/>
    <path d="M7 9.5C7 8.1 9.2 7 12 7s5 1.1 5 2.5-2.2 2.5-5 2.5S7 10.9 7 9.5z"/>
  </svg>`,
  logout: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>`,
  // Loop / exchange logo icon
  logo: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>
    <path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>
  </svg>`
};

const NAV_LINKS = [
  { href: '/dashboard', icon: 'discover', label: 'Discover' },
  { href: '/post',      icon: 'post',     label: 'Post Item' },
  { href: '/matches',   icon: 'matches',  label: 'Exchanges' },
  { href: '/history',   icon: 'history',  label: 'History' },
  { href: '/profile',   icon: 'profile',  label: 'My Profile' },
];

function buildSidebar() {
  // ── Logo ──────────────────────────────────────────────────────────────
  document.querySelectorAll('.sidebar-logo').forEach(el => {
    el.innerHTML = NAV_ICONS.logo + '<span>LocalBridge</span>';
  });

  // ── Nav Items ──────────────────────────────────────────────────────────
  document.querySelectorAll('.sidebar-nav').forEach(nav => {
    const cur = window.location.pathname;
    nav.innerHTML = NAV_LINKS.map(link => {
      const isActive = (link.href === '/dashboard')
        ? (cur === '/dashboard' || cur === '/')
        : cur.startsWith(link.href);
      return `<a href="${link.href}" class="nav-item${isActive ? ' active' : ''}">
        ${NAV_ICONS[link.icon]}<span>${link.label}</span>
      </a>`;
    }).join('');
  });

  // ── Logout Buttons ─────────────────────────────────────────────────────
  document.querySelectorAll('.sidebar-logout').forEach(btn => {
    btn.innerHTML = NAV_ICONS.logout + '<span>Log out</span>';
    btn.onclick = () => AppState.logout();
  });

  // ── Desktop Sidebar Toggle ───────────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');
  
  if (sidebar && toggleBtn) {
    // Restore state from localStorage
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
      sidebar.classList.add('collapsed');
    }
    
    // Remove existing listeners to avoid duplicates if buildSidebar is called multiple times
    const newToggleBtn = toggleBtn.cloneNode(true);
    toggleBtn.parentNode.replaceChild(newToggleBtn, toggleBtn);
    
    newToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
  }
}

// Run after DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', buildSidebar);
} else {
  buildSidebar();
}
