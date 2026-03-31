// GSAP Animation Controller
document.addEventListener("DOMContentLoaded", () => {
  // Ensure GSAP is available
  if (typeof gsap === 'undefined') return;

  // 1. Initial Page Load Reveal
  initPageReveals();

  // 2. Setup Hover Interactions
  initHoverInteractions();
});

function initPageReveals() {
  const tl = gsap.timeline();

  // Reveal elements marked with .reveal-up
  const revealUps = document.querySelectorAll('.reveal-up');
  if (revealUps.length > 0) {
    tl.fromTo(revealUps, {
      y: 30, opacity: 0
    }, {
      y: 0,
      opacity: 1,
      duration: 0.8,
      stagger: 0.1,
      ease: "power3.out",
      clearProps: "all"
    }, 0.1);
  }

  // Reveal elements marked with .reveal-scale
  const revealScales = document.querySelectorAll('.reveal-scale');
  if (revealScales.length > 0) {
    tl.fromTo(revealScales, {
      scale: 0.9, opacity: 0
    }, {
      scale: 1,
      opacity: 1,
      duration: 0.8,
      stagger: 0.1,
      ease: "back.out(1.2)",
      clearProps: "all"
    }, 0.2);
  }

  // Reveal elements marked with .reveal-fade
  const revealFades = document.querySelectorAll('.reveal-fade');
  if (revealFades.length > 0) {
    tl.fromTo(revealFades, {
      opacity: 0
    }, {
      opacity: 1,
      duration: 1.2,
      stagger: 0.15,
      ease: "power2.out",
      clearProps: "all"
    }, 0);
  }
}

function initHoverInteractions() {
  // Magnetic Buttons (Subtle pull on hover)
  const magneticBtns = document.querySelectorAll('.magnetic-btn');
  
  magneticBtns.forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      
      gsap.to(btn, {
        x: x * 0.2,
        y: y * 0.2,
        duration: 0.4,
        ease: "power2.out"
      });
    });
    
    btn.addEventListener('mouseleave', () => {
      gsap.to(btn, {
        x: 0,
        y: 0,
        duration: 0.6,
        ease: "elastic.out(1, 0.3)"
      });
    });
  });
}

// Helper to animate cards sequentially on dynamic inject
window.animateFeedCards = function(selector = '.feed-card', container = document) {
  if (typeof gsap === 'undefined') return;
  const cards = container.querySelectorAll(selector);
  gsap.fromTo(cards, 
    { y: 40, opacity: 0 },
    { y: 0, opacity: 1, duration: 0.6, stagger: 0.08, ease: "power3.out" }
  );
};
