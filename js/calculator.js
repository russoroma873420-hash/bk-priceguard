/* bondarenkoventel — calculator.js */

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

/* Add shake keyframes */
const style = document.createElement('style');
style.textContent = `
  @keyframes shake {
    0%,100%{ transform: translateX(0); }
    25%    { transform: translateX(-8px); }
    75%    { transform: translateX(8px); }
  }
`;
document.head.appendChild(style);

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
}

/* ── Capture form ── */
function submitCapture() {
  const val = document.getElementById('capturePhone').value.trim();
  if (!val) {
    document.getElementById('capturePhone').style.borderColor = '#e05000';
    return;
  }
  /* In production: POST to backend / CRM */
  const btn = document.querySelector('.capture-form .btn');
  btn.textContent = '✓ Спасибо! Инженер свяжется с вами';
  btn.style.background = '#2e6e2a';
  btn.disabled = true;
  document.getElementById('capturePhone').disabled = true;
}
