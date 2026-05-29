/* AirBond — calculator.js */

const TG_BOT_TOKEN = '8931211239:AAHx779bSDIBcde6Dlzn1lBcVvn-wKGJ7GQ';
const TG_CHAT_ID   = '652328822';

/* ── Quiz state ── */
const state = { type: null, area: 60, stage: null, region: null, source: null };

/* ── Step navigation ── */
function showStep(n) {
  document.querySelectorAll('.quiz__step').forEach(s => s.classList.remove('active'));
  const step = document.getElementById('step' + n);
  if (step) step.classList.add('active');
  for (let i = 1; i <= 4; i++) {
    document.getElementById('dot' + i).classList.toggle('done', i < n);
  }
}

function nextStep(current) {
  if (current === 1 && !state.type)  { shake(document.getElementById('step1')); return; }
  if (current === 3 && !state.stage) { shake(document.getElementById('step3')); return; }
  if (current === 2) state.area = parseInt(document.getElementById('areaSlider').value, 10);
  showStep(current + 1);
}

function prevStep(current) { showStep(current - 1); }

function shake(el) {
  el.style.animation = 'none';
  el.offsetHeight;
  el.style.animation = 'shake .3s ease';
  setTimeout(() => { el.style.animation = ''; }, 350);
}

/* ── Choice buttons ── */
document.querySelectorAll('.choice-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const step = btn.closest('.quiz__step');
    step.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    if (step.id === 'step1') state.type  = btn.dataset.val;
    if (step.id === 'step3') state.stage = btn.dataset.val;
  });
});

/* ── Result logic ── */
function showResult() {
  state.area   = parseInt(document.getElementById('areaSlider').value, 10);
  state.region = document.getElementById('regionSelect').value;

  let system;
  const cold = ['ural', 'sib', 'north'].includes(state.region);

  if (state.stage === 'finished') {
    system = `Децентрализованные рекуператоры с алмазным бурением (без вскрытия отделки). Монтаж 1 день — система готова сразу.`;
  } else if (state.stage === 'project' || state.stage === 'rough') {
    system = `Централизованная приточно-вытяжная установка с рекуперацией тепла и скрытыми воздуховодами в перекрытии.`;
  } else {
    system = `Комбинированная система: рекуператоры в жилых комнатах + вытяжные клапаны в санузлах.`;
  }
  if (cold) system += ' Усиленная морозостойкость до −45 °С для вашего региона.';

  const annualSaving = Math.round(state.area * 1200 * 0.92 / 1000) * 1000;
  const fmt = n => n.toLocaleString('ru-RU');
  const saving = `до ${fmt(annualSaving)} ₽ / сезон`;

  document.getElementById('resultSystemText').textContent = system;
  document.getElementById('resultSaving').textContent     = saving;

  document.querySelectorAll('.quiz__step').forEach(s => s.classList.remove('active'));
  document.getElementById('quizResult').classList.add('active');
  for (let i = 1; i <= 4; i++) document.getElementById('dot' + i).classList.add('done');

  const canvas = document.getElementById('roiChart');
  if (canvas && typeof Chart !== 'undefined') {
    if (canvas._chartInst) canvas._chartInst.destroy();
    const years   = [1, 2, 3, 4, 5, 6, 7];
    const savings = years.map(y => Math.round(annualSaving * y / 1000));
    const cost    = 85;
    canvas._chartInst = new Chart(canvas, {
      type: 'line',
      data: {
        labels: years.map(y => y + ' лет'),
        datasets: [{
          label: 'Накопленная экономия (тыс. ₽)',
          data: savings,
          borderColor: '#8BAF5A',
          backgroundColor: 'rgba(139,175,90,.15)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#8BAF5A',
        }, {
          label: 'Стоимость системы (тыс. ₽)',
          data: years.map(() => cost),
          borderColor: 'rgba(255,255,255,.3)',
          borderWidth: 1,
          borderDash: [6, 4],
          fill: false,
          pointRadius: 0,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: 'rgba(255,255,255,.7)', font: { size: 11 } } } },
        scales: {
          x: { ticks: { color: 'rgba(255,255,255,.6)', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.08)' } },
          y: { ticks: { color: 'rgba(255,255,255,.6)', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.08)' } }
        }
      }
    });
  }
}

/* ── UTM source detection ── */
function getUtmSource() {
  const p = new URLSearchParams(window.location.search);
  return p.get('utm_source') || p.get('utm_medium') || 'direct';
}

/* ── Telegram sender ── */
async function sendToTelegram(data) {
  if (!TG_BOT_TOKEN || TG_BOT_TOKEN === 'YOUR_BOT_TOKEN') return false;
  const regionMap = {
    msk:'Москва / МО', spb:'Санкт-Петербург', south:'Юг России',
    ural:'Урал', sib:'Сибирь', north:'Крайний Север', other:'Другой регион'
  };
  const typeMap  = { apartment:'Квартира', house:'Дом', commercial:'Коммерция' };
  const stageMap = { project:'Проект / нулевой цикл', rough:'Черновая отделка', finished:'Готовый ремонт' };

  const lines = [
    '🏠 Новая заявка AirBond',
    `👤 Имя: ${data.name || '—'}`,
    `📞 Телефон: ${data.phone || '—'}`,
  ];
  if (data.type)   lines.push(`🏠 Тип объекта: ${typeMap[data.type]   || data.type}`);
  if (data.area)   lines.push(`📐 Площадь: ${data.area} м²`);
  if (data.stage)  lines.push(`🔨 Стадия: ${stageMap[data.stage]  || data.stage}`);
  if (data.region) lines.push(`📍 Регион: ${regionMap[data.region] || data.region}`);
  if (data.saving) lines.push(`💰 Экономия: ${data.saving}`);
  lines.push(`📌 Источник: ${data.source || data.utm || 'direct'}`);
  lines.push(`🌐 Страница: ${window.location.href}`);
  lines.push(`🕐 Время: ${new Date().toLocaleString('ru-RU', { timeZone: 'Asia/Barnaul' })}`);

  try {
    const r = await fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: TG_CHAT_ID, text: lines.join('\n') }),
      keepalive: true,
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      console.error('Telegram API error:', r.status, err.description);
    }
    return r.ok;
  } catch (e) {
    console.error('Telegram fetch failed:', e);
    return false;
  }
}

/* ═══════════════════════════════════════════
   LEAD MODAL
   ═══════════════════════════════════════════ */
function openLeadModal(source) {
  state.source = source || 'general';

  const modal   = document.getElementById('leadModal');
  const ctx     = document.getElementById('leadContext');
  const success = document.getElementById('leadSuccess');
  const btn     = document.getElementById('leadSubmitBtn');
  const nameEl  = document.getElementById('leadName');
  const phoneEl = document.getElementById('leadPhone');
  const consent = document.getElementById('leadConsent');

  success.style.display = 'none';
  btn.style.display     = '';
  btn.disabled          = false;
  btn.textContent       = 'Отправить заявку';
  nameEl.value  = '';
  phoneEl.value = '';
  consent.checked = false;
  nameEl.classList.remove('error');
  phoneEl.classList.remove('error');
  consent.closest('.lead-modal__consent').style.outline = '';

  if (source === 'calc' && state.type && state.area) {
    const sys = document.getElementById('resultSystemText')?.textContent || '';
    const sav = document.getElementById('resultSaving')?.textContent     || '';
    if (sys || sav) {
      ctx.style.display = 'block';
      ctx.innerHTML = (sys ? `<b>Система:</b> ${sys.slice(0,90)}…<br>` : '') +
                      (sav ? `<b>Экономия:</b> ${sav}` : '');
    } else {
      ctx.style.display = 'none';
    }
  } else {
    const labels = {
      'portfolio':   '🏠 Хочу такой же объект',
      'howwework':   '🔧 Запрос из «Как мы работаем»',
      'installment': '💳 Рассрочка',
      'final-cta':   '🎯 Финальная форма',
    };
    if (source && labels[source]) {
      ctx.textContent   = labels[source];
      ctx.style.display = 'block';
    } else {
      ctx.style.display = 'none';
    }
  }

  modal.dataset.source = state.source;
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  setTimeout(() => nameEl.focus(), 100);
}

function closeLeadModal() {
  const modal = document.getElementById('leadModal');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

async function submitLead() {
  const nameEl  = document.getElementById('leadName');
  const phoneEl = document.getElementById('leadPhone');
  const consent = document.getElementById('leadConsent');
  const btn     = document.getElementById('leadSubmitBtn');
  const success = document.getElementById('leadSuccess');

  const name  = nameEl.value.trim();
  const phone = phoneEl.value.trim();

  nameEl.classList.remove('error');
  phoneEl.classList.remove('error');
  consent.closest('.lead-modal__consent').style.outline = '';

  let valid = true;
  if (name.length < 2)  { nameEl.classList.add('error');  if (valid) nameEl.focus();  valid = false; }
  if (phone.replace(/\D/g, '').length < 11) {
    phoneEl.classList.add('error');
    if (valid) phoneEl.focus();
    valid = false;
  }
  if (!consent.checked) {
    consent.closest('.lead-modal__consent').style.outline = '2px solid #c0392b';
    valid = false;
  }
  if (!valid) return;

  btn.disabled    = true;
  btn.textContent = 'Отправляем…';

  const ok = await sendToTelegram({
    name, phone,
    type:   state.type,
    area:   state.area,
    stage:  state.stage,
    region: state.region,
    saving: document.getElementById('resultSaving')?.textContent || '',
    source: state.source,
    utm:    getUtmSource(),
  });

  if (typeof ym !== 'undefined') ym(window.YM_ID, 'reachGoal', 'lead_submit');

  if (ok) {
    btn.style.display     = 'none';
    success.style.display = 'block';
    setTimeout(closeLeadModal, 3500);
  } else {
    btn.disabled    = false;
    btn.textContent = 'Отправить заявку';
    const waText = encodeURIComponent(`Здравствуйте! Меня зовут ${name}, телефон ${phone}. Хочу узнать про вентиляцию.`);
    if (confirm('Ошибка отправки. Открыть WhatsApp для связи?')) {
      window.open(`https://wa.me/79029987030?text=${waText}`, '_blank');
      closeLeadModal();
    }
  }
}

/* ── Phone mask ── */
document.addEventListener('DOMContentLoaded', () => {
  const phoneEl = document.getElementById('leadPhone');
  if (!phoneEl) return;
  phoneEl.addEventListener('input', () => {
    let v = phoneEl.value.replace(/\D/g, '');
    if (v.startsWith('8')) v = '7' + v.slice(1);
    if (v.length > 11) v = v.slice(0, 11);
    let out = '';
    if (v.length > 0)  out = '+7';
    if (v.length > 1)  out += ' (' + v.slice(1, 4);
    if (v.length >= 4) out += ') ' + v.slice(4, 7);
    if (v.length >= 7) out += '-' + v.slice(7, 9);
    if (v.length >= 9) out += '-' + v.slice(9, 11);
    phoneEl.value = out;
  });
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeLeadModal();
});

document.addEventListener('click', e => {
  if (e.target.matches('.lead-modal__backdrop')) closeLeadModal();
});
