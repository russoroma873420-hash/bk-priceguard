/* bondarenkoventel v2 — main.js */

/* ── Hide float-btns on any touch device (JS fallback for CSS media query failures) ── */
if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
  const fb = document.querySelector('.float-btns');
  if (fb) fb.remove();
}

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
    const bars = e.target.querySelectorAll('.progress-bar__fill, .noise-bar__fill');
    if (bars.length) requestAnimationFrame(() => {
      bars.forEach(bar => { bar.style.width = (bar.dataset.width || '0') + '%'; });
    });
  });
}, { threshold: 0.15 });

document.querySelectorAll('.fade-in').forEach(el => io.observe(el));

/* ── CO2 Monitor Toggle ── */
let co2Interval = null;
let co2Value = 1200;
let ventOn = false;
let co2InView = false;
let _co2State = null;

/* Pause DOM updates when CO2 section is off-screen */
const _co2Section = document.getElementById('co2Monitor');
if (_co2Section) {
  new IntersectionObserver(entries => { co2InView = entries[0].isIntersecting; }, { threshold: 0 })
    .observe(_co2Section);
}

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
      if (co2InView) updateCo2Display(co2Value, valEl, heroVal, statusEl, monitor);
      if (co2Value <= 380) clearInterval(co2Interval);
    }, 300);
  } else {
    co2Interval = setInterval(() => {
      co2Value = Math.min(1400, co2Value + Math.floor(Math.random() * 20 + 8));
      if (co2InView) updateCo2Display(co2Value, valEl, heroVal, statusEl, monitor);
      if (co2Value >= 1400) clearInterval(co2Interval);
    }, 400);
  }
}

function updateCo2Display(val, valEl, heroVal, statusEl, monitor) {
  /* Always update number */
  valEl.textContent = val;
  if (heroVal) heroVal.textContent = val;

  /* Only update classes/text when state actually changes */
  const state = val < 700 ? 'good' : val < 1000 ? 'warn' : 'danger';
  if (state === _co2State) return;
  _co2State = state;

  if (state === 'good') {
    valEl.className    = 'co2-value good';
    statusEl.className = 'co2-status good';
    statusEl.textContent = '✓ Отлично';
    monitor.classList.remove('warn');
    monitor.classList.add('good');
  } else if (state === 'warn') {
    valEl.className    = 'co2-value';
    statusEl.className = 'co2-status';
    statusEl.textContent = '~ Допустимо';
    monitor.classList.remove('good');
    monitor.classList.add('warn');
  } else {
    valEl.className    = 'co2-value danger';
    statusEl.className = 'co2-status danger';
    statusEl.textContent = '⚠ Опасно';
    monitor.classList.remove('good', 'warn');
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
        if (co2InView) updateCo2Display(pulse, valEl, heroVal, statusEl, monitor);
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
const aiBubble   = document.getElementById('aiChatBubble');
const aiFloatBtn = document.getElementById('aiFloatBtn');
if (aiFloatBtn) aiFloatBtn.addEventListener('click', () => aiBubble.classList.toggle('open'));


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

/* ── Header shadow (class toggle only — no boxShadow mutation on scroll) ── */
const header = document.querySelector('.header');
let scrollRaf = false;
window.addEventListener('scroll', () => {
  if (scrollRaf) return;
  scrollRaf = true;
  requestAnimationFrame(() => {
    header.classList.toggle('scrolled', window.scrollY > 10);
    scrollRaf = false;
  });
}, { passive: true });

/* ── Shake keyframes ── */
const style = document.createElement('style');
style.textContent = `@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-8px)}75%{transform:translateX(8px)}}`;
document.head.appendChild(style);

/* ── Stats countUp animation ── */
const countUpObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    countUpObserver.unobserve(e.target);
    const el = e.target;
    const raw = el.textContent.replace(/\D/g, '');
    const target = parseInt(raw, 10);
    const suffix = el.textContent.replace(/[\d]/g, '');
    if (!target) return;
    let cur = 0;
    const step = Math.ceil(target / 60);
    const timer = setInterval(() => {
      cur = Math.min(cur + step, target);
      el.textContent = cur + suffix;
      if (cur >= target) clearInterval(timer);
    }, 25);
  });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-block__num').forEach(el => countUpObserver.observe(el));

/* ── Appointment timer ── */
(function() {
  const el = document.getElementById('nextVisitDate');
  if (!el) return;
  const now = new Date();
  const days = ['вс','пн','вт','ср','чт','пт','сб'];
  const months = ['янв','фев','мар','апр','мая','июн','июл','авг','сен','окт','ноя','дек'];
  let d = new Date(now);
  d.setDate(d.getDate() + 2);
  while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() + 1);
  el.textContent = days[d.getDay()] + ', ' + d.getDate() + ' ' + months[d.getMonth()];
})();

/* ════ LEAD MODAL ════ */
const TG_BOT_TOKEN = '8931211239:AAHx779bSDIBcde6Dlzn1lBcVvn-wKGJ7GQ';
const TG_CHAT_ID   = '652328822';

function openLeadModal(source) {
  const modal   = document.getElementById('leadModal');
  const ctx     = document.getElementById('leadContext');
  const success = document.getElementById('leadSuccess');
  const btn     = document.getElementById('leadSubmitBtn');

  /* Сбрасываем предыдущее состояние */
  success.style.display = 'none';
  btn.style.display     = 'block';
  btn.disabled          = false;
  btn.textContent       = 'Отправить заявку';
  document.getElementById('leadName').value  = '';
  document.getElementById('leadPhone').value = '';
  document.getElementById('leadConsent').checked = false;
  document.getElementById('leadName').classList.remove('error');
  document.getElementById('leadPhone').classList.remove('error');

  /* Контекст — откуда открыли */
  const labels = {
    'calc':        '📊 Запрос после калькулятора',
    'portfolio':   '🏠 Хочу такой же объект',
    'howwework':   '🔧 Запрос из раздела «Как мы работаем»',
    'installment': '💳 Рассрочка',
    'final-cta':   '🎯 Финальная форма',
  };
  if (source && labels[source]) {
    ctx.textContent    = labels[source];
    ctx.style.display  = 'block';
  } else {
    ctx.style.display  = 'none';
  }
  modal.dataset.source = source || 'general';
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  setTimeout(() => document.getElementById('leadName').focus(), 100);
}

function closeLeadModal() {
  const modal = document.getElementById('leadModal');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
}

/* Закрытие по Escape */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeLeadModal();
});

async function submitLead() {
  const nameEl    = document.getElementById('leadName');
  const phoneEl   = document.getElementById('leadPhone');
  const consent   = document.getElementById('leadConsent');
  const btn       = document.getElementById('leadSubmitBtn');
  const success   = document.getElementById('leadSuccess');

  const name  = nameEl.value.trim();
  const phone = phoneEl.value.trim();

  /* Валидация */
  let valid = true;
  nameEl.classList.remove('error');
  phoneEl.classList.remove('error');

  if (name.length < 2) { nameEl.classList.add('error'); valid = false; }
  if (phone.length < 7) { phoneEl.classList.add('error'); valid = false; }
  if (!consent.checked) {
    consent.closest('label').style.color = 'var(--red)';
    valid = false;
    setTimeout(() => consent.closest('label').style.color = '', 2000);
  }
  if (!valid) return;

  btn.disabled    = true;
  btn.textContent = 'Отправляем…';

  const source = document.getElementById('leadModal').dataset.source || 'general';
  const page   = window.location.href;
  const text =
    `🏠 *Новая заявка AirBond*\n` +
    `👤 Имя: ${name}\n` +
    `📞 Телефон: ${phone}\n` +
    `📌 Источник: ${source}\n` +
    `🌐 Страница: ${page}\n` +
    `🕐 Время: ${new Date().toLocaleString('ru-RU', {timeZone:'Asia/Barnaul'})}`;

  try {
    const res = await fetch(
      `https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id:    TG_CHAT_ID,
          text:       text,
          parse_mode: 'Markdown'
        })
      }
    );
    const data = await res.json();

    if (data.ok) {
      /* Успех — Метрика */
      if (window.ym) ym(109337901, 'reachGoal', 'lead_submit');
      btn.style.display     = 'none';
      success.style.display = 'block';
      setTimeout(() => closeLeadModal(), 3500);
    } else {
      throw new Error(data.description || 'Telegram error');
    }
  } catch (err) {
    btn.disabled    = false;
    btn.textContent = 'Отправить заявку';
    /* Fallback — открываем WhatsApp с данными */
    const waText = encodeURIComponent(`Здравствуйте! Меня зовут ${name}, телефон ${phone}. Хочу узнать про вентиляцию.`);
    if (confirm('Ошибка отправки. Открыть WhatsApp для связи?')) {
      window.open(`https://wa.me/79029987030?text=${waText}`, '_blank');
      closeLeadModal();
    }
  }
}
