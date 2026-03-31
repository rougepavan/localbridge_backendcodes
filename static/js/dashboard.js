/**
 * dashboard.js  —  Shared logic for all dashboard pages:
 * • Loads and displays the logged-in user's name + avatar in the top navbar
 * • Sets up notification badge polling
 * • Populates user stats wherever .stat-count elements exist
 */

document.addEventListener('DOMContentLoaded', async () => {

  // 1. Require authentication on every dashboard page
  // AppState.requireAuth();

  const user = AppState.getUser();
  if (!user || !user.email) return;

  // 2. Fetch full user profile from backend
  try {
    const res  = await fetch(`/user-details?email=${encodeURIComponent(user.email)}`);
    const data = await res.json();

    if (!data.error) {
      // Merge into state so subsequent pages also have fresh data
      const updated = { ...user, ...data };
      AppState.setUser(updated);

      // ── Navbar name
      const navName = document.getElementById('navName');
      if (navName) navName.textContent = data.name || user.email;

      // ── Navbar avatar
      const navAvatar = document.getElementById('navAvatar');
      if (navAvatar) {
        navAvatar.src = data.profile_image
          ? `/static/uploads/${data.profile_image}`
          : `https://ui-avatars.com/api/?name=${encodeURIComponent(data.name || 'U')}&background=4f46e5&color=fff&bold=true`;
        navAvatar.alt = data.name || 'User';
      }

      // ── Sidebar user card (if page has one)
      document.querySelectorAll('.sidebar-user-name').forEach(el => el.textContent = data.name || 'User');
      document.querySelectorAll('.sidebar-user-email').forEach(el => el.textContent = data.email || '');
      document.querySelectorAll('.sidebar-user-avatar').forEach(el => {
        el.src = data.profile_image
          ? `/static/uploads/${data.profile_image}`
          : `https://ui-avatars.com/api/?name=${encodeURIComponent(data.name || 'U')}&background=4f46e5&color=fff&bold=true`;
      });

      // ── Stat counters (profile page, etc.)
      const traded = document.getElementById('stat-trades');
      const posted = document.getElementById('stat-posted');
      const rating = document.getElementById('stat-rating');
      const trust  = document.getElementById('stat-trust');
      if (traded) traded.textContent = data.trades ?? 0;
      if (posted) posted.textContent = data.posted ?? 0;
      if (rating) rating.textContent = data.rating ? parseFloat(data.rating).toFixed(1) : '0.0';
      if (trust)  trust.textContent  = (data.trust ?? 50) + '%';
    }
  } catch (e) {
    console.warn('Failed to load user details:', e);
  }

  // 3. Mobile sidebar toggle
  const menuBtn = document.getElementById('sidebarMenuBtn');
  const sidebar  = document.getElementById('sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => sidebar.classList.toggle('mobile-open'));
  }

  // 4. Profile menu button → navigate to /profile
  const profileBtn = document.getElementById('profileMenuBtn');
  if (profileBtn) {
    profileBtn.style.cursor = 'pointer';
    profileBtn.addEventListener('click', () => window.location.href = '/profile');
  }

  // 5. Notification polling (every 30 s)
  if (typeof setupNotifications === 'function') setupNotifications();
});
