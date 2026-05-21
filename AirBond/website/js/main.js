/* bondarenkoventel — main.js */

/* ── Burger / side nav ── */
const burger     = document.getElementById('burger');
const sideNav    = document.getElementById('sideNav');
const navOverlay = document.getElementById('navOverlay');

function toggleNav(open) {
  burger.classList.toggle('open', open);
  sideNav.classList.toggle('open', open);
  navOverlay.classList.toggle('open', open);
  document.body.style.overflow = open ? 'hidden' : '';
}

burger.addEventListener('click', () => toggleNav(!sideNav.classList.contains('open')));
navOverlay.addEventListener('click', () => toggleNav(false));
sideNav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => toggleNav(false)));

/* ── Intersection Observer: fade-in ── */
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      /* animate progress bars when threat section is visible */
      e.target.querySelectorAll('.progress-bar__fill').forEach(bar => {
        bar.style.width = bar.dataset.width + '%';
      });
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll('.fade-in').forEach(el => io.observe(el));

/* also watch particle cards independently */
document.querySelectorAll('.particle-card').forEach(card => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.querySelectorAll('.progress-bar__fill').forEach(bar => {
          bar.style.width = bar.dataset.width + '%';
        });
        observer.disconnect();
      }
    });
  }, { threshold: 0.4 });
  observer.observe(card);
});

/* ── Virtual Home zone switcher ── */
const vhBtns = document.querySelectorAll('.vh-btn');
const popup  = document.getElementById('vhPopup');
const popupTitle = document.getElementById('vhPopupTitle');
const popupText  = document.getElementById('vhPopupText');

const zones = {
  bedroom: {
    title: '🛏 Бризер / Приточный клапан — Спальня',
    text:  'Фильтрует пыльцу и выхлопные газы. Работает тише шёпота, улучшая качество сна на 50%. Рекуперация тепла до 92% — никакого холодного сквозняка.',
    arrows: ['arrowBedroom'],
  },
  kitchen: {
    title: '🍳 Умная вытяжка — Кухня / Ванная',
    text:  'Удаляет запахи и избыточную влажность, предотвращая появление плесени и снижая риск развития астмы у детей. Автоматически усиливается при готовке.',
    arrows: ['arrowKitchen'],
  },
  mount: {
    title: '🔧 Скрытый монтаж — 1 день без грязи',
    text:  'Компактные устройства устанавливаются прямо в стену. Алмазное бурение Ø160 мм сохраняет высоту потолков и не портит готовый ремонт.',
    arrows: ['arrowMount'],
  },
};

function activateZone(zone) {
  /* hide all arrows */
  document.querySelectorAll('.air-arrow').forEach(a => a.classList.remove('visible'));

  const data = zones[zone];
  data.arrows.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('visible');
  });

  popupTitle.textContent = data.title;
  popupText.textContent  = data.text;
  popup.classList.add('show');
}

vhBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    vhBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activateZone(btn.dataset.zone);
  });
});

/* activate bedroom by default after short delay */
setTimeout(() => activateZone('bedroom'), 600);

/* ── FAQ accordion ── */
document.querySelectorAll('.faq-item__q').forEach(q => {
  q.addEventListener('click', () => {
    const item = q.closest('.faq-item');
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
    if (!isOpen) item.classList.add('open');
  });
});

/* ── Smooth scroll for all anchor links ── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

/* ── Header shadow on scroll ── */
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
  header.style.boxShadow = window.scrollY > 10
    ? '0 4px 24px rgba(0,0,0,.35)'
    : '0 2px 16px rgba(0,0,0,.25)';
});
