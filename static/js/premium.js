(function () {
  'use strict';

  // ── Announcement bar ──────────────────────────────────────
  var bar = document.getElementById('announcement-bar');
  if (bar) {
    if (sessionStorage.getItem('announcementDismissed')) {
      bar.style.display = 'none';
    } else {
      document.body.classList.add('has-announcement');
    }
  }

  window.dismissAnnouncement = function () {
    var b = document.getElementById('announcement-bar');
    if (!b) return;
    b.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
    b.style.transform = 'translateY(-100%)';
    b.style.opacity = '0';
    setTimeout(function () { b.style.display = 'none'; }, 320);
    sessionStorage.setItem('announcementDismissed', '1');
    document.body.classList.remove('has-announcement');
  };

  // ── Scroll animations ─────────────────────────────────────
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
      }
    });
  }, { threshold: 0.10, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.animate-on-scroll').forEach(function (el) {
    observer.observe(el);
  });

  // ── Mobile nav toggle ─────────────────────────────────────
  var toggle = document.querySelector('.nav-mobile-toggle');
  var drawer = document.querySelector('.nav-mobile-drawer');
  if (toggle && drawer) {
    toggle.addEventListener('click', function () {
      var isOpen = toggle.classList.contains('open');
      toggle.classList.toggle('open');
      if (isOpen) {
        drawer.classList.remove('open');
        setTimeout(function () { drawer.style.display = 'none'; }, 350);
      } else {
        drawer.style.display = 'flex';
        setTimeout(function () { drawer.classList.add('open'); }, 10);
      }
    });
  }

  // ── Nav: glass on scroll (landing page) ───────────────────
  var header = document.querySelector('.landing-header');
  if (header) {
    var onScroll = function () {
      if (window.scrollY > 20) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

})();
