/* bondarenkoventel v2 — main.js */

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

/* ── Intersection Observer: fade-in + progress bars + noise bars ── */
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add('visible');
    e.target.querySelectorAll('.progress-bar__fill, .noise-bar__fill').forEach(bar => {
      bar.style.width = (bar.dataset.width || '0') + '%';
    });
  });
}, { threshold: 0.15 });

document.querySelectorAll('.fade-in').forEach(el => io.observe(el));

/* ── CO2 Monitor Toggle ── */
let co2Interval = null;
let co2Value = 1200;
let ventOn = false;

function toggleCo2() {
  const btn     = document.getElementById('co2Toggle');
  const valEl   = document.getElementById('co2Val');
  const heroVal = document.getElementById('co2HeroVal');
  const statusEl= document.getElementById('co2Status');
  const monitor = document.getElementById('co2Monitor');

  ventOn = !ventOn;
  btn.classList.toggle('on', ventOn);

  clearInterval(co2Interval);

  if (ventOn) {
    co2Interval = setInterval(() => {
      co2Value = Math.max(380, co2Value - Math.floor(Math.random() * 30 + 15));
      updateCo2Display(co2Value, valEl, heroVal, statusEl, monitor);
      if (co2Value <= 380) clearInterval(co2Interval);
    }, 300);
  } else {
    co2Interval = setInterval(() => {
      co2Value = Math.min(1400, co2Value + Math.floor(Math.random() * 20 + 8));
      updateCo2Display(co2Value, valEl, heroVal, statusEl, monitor);
      if (co2Value >= 1400) clearInterval(co2Interval);
    }, 400);
  }
}

function updateCo2Display(val, valEl, heroVal, statusEl, monitor) {
  valEl.textContent  = val;
  if (heroVal) heroVal.textContent = val;

  if (val < 700) {
    valEl.className   = 'co2-value good';
    statusEl.className= 'co2-status good';
    statusEl.textContent = '✓ Отлично';
    monitor.classList.add('good');
    monitor.style.boxShadow = '0 0 40px rgba(61,139,55,.4)';
  } else if (val < 1000) {
    valEl.className   = 'co2-value';
    statusEl.className= 'co2-status';
    statusEl.textContent = '~ Допустимо';
    monitor.classList.remove('good');
    monitor.style.boxShadow = '0 0 40px rgba(240,165,0,.35)';
  } else {
    valEl.className   = 'co2-value danger';
    statusEl.className= 'co2-status danger';
    statusEl.textContent = '⚠ Опасно';
    monitor.classList.remove('good');
    monitor.style.boxShadow = '0 0 40px rgba(192,57,43,.4)';
  }
}

/* Animate CO2 pulsing on load */
setTimeout(() => {
  const valEl    = document.getElementById('co2Val');
  const heroVal  = document.getElementById('co2HeroVal');
  const statusEl = document.getElementById('co2Status');
  const monitor  = document.getElementById('co2Monitor');
  if (valEl) {
    let pulse = 1200;
    let dir   = 1;
    setInterval(() => {
      if (!ventOn) {
        pulse += dir * 5;
        if (pulse >= 1260 || pulse <= 1150) dir *= -1;
        co2Value = pulse;
        updateCo2Display(pulse, valEl, heroVal, statusEl, monitor);
      }
    }, 200);
  }
}, 1000);

/* ── Virtual Home zone switcher ── */
const vhBtns = document.querySelectorAll('.vh-btn');
const popup  = document.getElementById('vhPopup');
const popupTitle = document.getElementById('vhPopupTitle');
const popupText  = document.getElementById('vhPopupText');

const zones = {
  bedroom: { title: '🛏 Бризер / Приточный клапан — Спальня', text: 'Фильтрует пыльцу и выхлопные газы. Тише шёпота. Рекуперация тепла до 92% — никакого холодного сквозняка.', arrows: ['arrowBedroom'] },
  kitchen:  { title: '🍳 Умная вытяжка — Кухня / Ванная', text: 'Удаляет запахи и избыточную влажность. Предотвращает плесень. Автоматически усиливается при готовке.', arrows: ['arrowKitchen'] },
  mount:    { title: '🔧 Скрытый монтаж — 1 день без грязи', text: 'Алмазное бурение Ø160 мм. Устройства в стене, высота потолков сохранена. Готовый ремонт не пострадает.', arrows: ['arrowMount'] },
};

function activateZone(zone) {
  document.querySelectorAll('.air-arrow').forEach(a => a.classList.remove('visible'));
  const data = zones[zone];
  data.arrows.forEach(id => { const el = document.getElementById(id); if (el) el.classList.add('visible'); });
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

setTimeout(() => activateZone('bedroom'), 600);

/* ── FAQ accordion ── */
document.querySelectorAll('.faq-item__q').forEach(q => {
  q.addEventListener('click', () => {
    const item   = q.closest('.faq-item');
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
    if (!isOpen) item.classList.add('open');
  });
});

/* ── AI Chat ── */
const aiBtn    = document.getElementById('aiChatBtn');
const aiBubble = document.getElementById('aiChatBubble');

aiBtn.addEventListener('click', () => {
  aiBubble.classList.toggle('open');
});

function scrollToSection(id) {
  aiBubble.classList.remove('open');
  const el = document.querySelector(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── Smooth scroll ── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  });
});

/* ── Header shadow ── */
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
  header.style.boxShadow = window.scrollY > 10 ? '0 4px 24px rgba(0,0,0,.35)' : '0 2px 16px rgba(0,0,0,.25)';
});

/* ── Shake keyframes ── */
const style = document.createElement('style');
style.textContent = `@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-8px)}75%{transform:translateX(8px)}}`;
document.head.appendChild(style);
