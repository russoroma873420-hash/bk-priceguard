/* AirBond — calculator.js */

const state = { type: null, area: 60, stage: null, region: null };

/* ── Step navigation ── */
function showStep(n) {
  document.querySelectorAll('.quiz__step').forEach(s => s.classList.remove('active'));
  const step = document.getElementById('step' + n);
  if (step) step.classList.add('active');

  /* update progress dots */
  for (let i = 1; i <= 4; i++) {
    document.getElementById('dot' + i).classList.toggle('done', i < n);
  }
}

function nextStep(current) {
  /* validate current step */
  if (current === 1 && !state.type) {
    shake(document.getElementById('step1'));
    return;
  }
  if (current === 3 && !state.stage) {
    shake(document.getElementById('step3'));
    return;
  }
  if (current === 2) {
    state.area = parseInt(document.getElementById('areaSlider').value, 10);
  }
  showStep(current + 1);
}

function prevStep(current) {
  showStep(current - 1);
}

function shake(el) {
  el.style.animation = 'none';
  el.offsetHeight; /* reflow */
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

  /* Derive recommendation */
  let system, saving;
  const cold = ['ural', 'sib'].includes(state.region);

  if (state.stage === 'finished') {
    system = `Децентрализованные рекуператоры с алмазным бурением (без вскрытия отделки). ` +
             `Монтаж 1 день — система готова к использованию сразу.`;
  } else if (state.stage === 'project' || state.stage === 'rough') {
    system = `Централизованная приточно-вытяжная установка с рекуперацией тепла и ` +
             `скрытыми воздуховодами в перекрытии. Оптимальное решение для комплексного климата.`;
  } else {
    system = `Комбинированная система: рекуператоры в жилых комнатах + вытяжные клапаны в санузлах.`;
  }

  if (cold) system += ' Усиленная морозостойкость до −45 °С для вашего региона.';

  /* Saving calculation: base 1200 rub/m2/year, 92% recovery => 0.92*1200*area / 12 per month */
  const annualSaving = Math.round(state.area * 1200 * 0.92 / 1000) * 1000;
  const fmt = (n) => n.toLocaleString('ru-RU');
  saving = `до ${fmt(annualSaving)} ₽ / сезон`;

  document.getElementById('resultSystemText').textContent = system;
  document.getElementById('resultSaving').textContent     = saving;

  /* Switch view */
  document.querySelectorAll('.quiz__step').forEach(s => s.classList.remove('active'));
  document.getElementById('quizResult').classList.add('active');

  /* Update dots — all done */
  for (let i = 1; i <= 4; i++) document.getElementById('dot' + i).classList.add('done');

  /* ROI Chart */
  const canvas = document.getElementById('roiChart');
  if (canvas && typeof Chart !== 'undefined') {
    if (canvas._chartInst) canvas._chartInst.destroy();
    const years = [1, 2, 3, 4, 5, 6, 7];
    const savings = years.map(y => Math.round(annualSaving * y / 1000));
    const cost = 85; // baseline 85k
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

const TG_BOT_TOKEN = '8931211239:AAHx779bSDIBcde6Dlzn1lBcVvn-wKGJ7GQ';
const TG_CHAT_ID   = '652328822';

async function sendToTelegram(data) {
  if (!TG_BOT_TOKEN || TG_BOT_TOKEN === 'YOUR_BOT_TOKEN') return false;
  const regionMap = {
    moscow:'Москва / МО', spb:'Санкт-Петербург', center:'Центральная Россия',
    south:'Юг России', volga:'Поволжье', ural:'Урал', sib:'Сибирь / Дальний Восток', other:'Другой регион'
  };
  const typeMap = { flat:'Квартира', house:'Дом', office:'Офис / коммерция' };
  const stageMap = { project:'Проект / черновая', rough:'Черновая отделка', finished:'Чистовая / жилая' };

  const lines = [
    '🏠 <b>Новая заявка — AirBond</b>',
    '',
    `👤 Имя: ${data.name || '—'}`,
    `📱 Телефон: ${data.phone || '—'}`,
  ];
  if (data.type)   lines.push(`🏠 Тип объекта: ${typeMap[data.type] || data.type}`);
  if (data.area)   lines.push(`📐 Площадь: ${data.area} м²`);
  if (data.stage)  lines.push(`🔨 Стадия: ${stageMap[data.stage] || data.stage}`);
  if (data.region) lines.push(`📍 Регион: ${regionMap[data.region] || data.region}`);
  if (data.system) lines.push(`\n⚙️ Рекомендация: ${data.system.slice(0, 120)}...`);
  if (data.saving) lines.push(`💰 Расчётная экономия: ${data.saving}`);
  lines.push(`\n⏰ ${new Date().toLocaleString('ru-RU')}`);

  try {
    const r = await fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: TG_CHAT_ID, text: lines.join('\n'), parse_mode: 'HTML' })
    });
    return r.ok;
  } catch { return false; }
}

/* ── Lead modal ── */
function openLeadModal(source) {
  const modal = document.getElementById('leadModal');
  const ctx   = document.getElementById('leadContext');

  if (source === 'calc' && state.type && state.area) {
    const sys  = document.getElementById('resultSystemText')?.textContent || '';
    const sav  = document.getElementById('resultSaving')?.textContent || '';
    if (sys || sav) {
      ctx.style.display = 'block';
      ctx.innerHTML = (sys ? `<b>Система:</b> ${sys.slice(0,90)}…<br>` : '') +
                      (sav ? `<b>Экономия:</b> ${sav}` : '');
    }
  } else {
    ctx.style.display = 'none';
  }

  document.getElementById('leadSuccess').style.display = 'none';
  document.getElementById('leadSubmitBtn').style.display = '';
  document.getElementById('leadName').value  = '';
  document.getElementById('leadPhone').value = '';
  document.getElementById('leadConsent').checked = false;
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}

function closeLeadModal() {
  const modal = document.getElementById('leadModal');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

async function submitLead() {
  const name    = document.getElementById('leadName').value.trim();
  const phone   = document.getElementById('leadPhone').value.trim();
  const consent = document.getElementById('leadConsent').checked;
  const nameEl  = document.getElementById('leadName');
  const phoneEl = document.getElementById('leadPhone');

  nameEl.classList.remove('error');
  phoneEl.classList.remove('error');

  let valid = true;
  if (!name)    { nameEl.classList.add('error');  nameEl.focus(); valid = false; }
  if (!phone || phone.replace(/\D/g,'').length < 11) {
    phoneEl.classList.add('error');
    if (valid) phoneEl.focus();
    valid = false;
  }
  if (!consent) {
    document.getElementById('leadConsent').closest('.lead-modal__consent').style.outline = '2px solid #c0392b';
    valid = false;
  }
  if (!valid) return;

  const btn = document.getElementById('leadSubmitBtn');
  btn.disabled = true;
  btn.textContent = 'Отправляем…';

  await sendToTelegram({
    name, phone,
    type:   state.type,
    area:   state.area,
    stage:  state.stage,
    region: state.region,
    system: document.getElementById('resultSystemText')?.textContent || '',
    saving: document.getElementById('resultSaving')?.textContent || '',
  });

  /* Yandex.Metrika goal */
  if (typeof ym !== 'undefined') ym(window.YM_ID, 'reachGoal', 'lead_submit');

  btn.style.display = 'none';
  document.getElementById('leadSuccess').style.display = 'block';

  setTimeout(closeLeadModal, 3500);
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

  /* Close modal on Escape */
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeLeadModal();
  });
});
