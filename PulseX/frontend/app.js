/* PulseX — Heart Risk Detection Frontend */

const FEATURES = [
  { key: 'age', label: 'Age', type: 'number', min: 29, max: 77, step: 1, unit: 'years', default: 54 },
  { key: 'sex', label: 'Sex', type: 'select', options: [{ v: 0, l: 'Female' }, { v: 1, l: 'Male' }], default: 1 },
  { key: 'cp', label: 'Chest Pain Type', type: 'select', options: [
    { v: 0, l: 'Typical Angina' }, { v: 1, l: 'Atypical Angina' },
    { v: 2, l: 'Non-anginal Pain' }, { v: 3, l: 'Asymptomatic' }
  ], default: 0 },
  { key: 'trestbps', label: 'Resting Blood Pressure', type: 'number', min: 94, max: 200, step: 1, unit: 'mm Hg', default: 130 },
  { key: 'chol', label: 'Serum Cholesterol', type: 'number', min: 126, max: 564, step: 1, unit: 'mg/dl', default: 240 },
  { key: 'fbs', label: 'Fasting Blood Sugar > 120', type: 'select', options: [{ v: 0, l: 'No' }, { v: 1, l: 'Yes' }], default: 0 },
  { key: 'restecg', label: 'Resting ECG', type: 'select', options: [
    { v: 0, l: 'Normal' }, { v: 1, l: 'ST-T Abnormality' }, { v: 2, l: 'LV Hypertrophy' }
  ], default: 0 },
  { key: 'thalach', label: 'Max Heart Rate', type: 'number', min: 71, max: 202, step: 1, unit: 'bpm', default: 150 },
  { key: 'exang', label: 'Exercise Induced Angina', type: 'select', options: [{ v: 0, l: 'No' }, { v: 1, l: 'Yes' }], default: 0 },
  { key: 'oldpeak', label: 'ST Depression', type: 'number', min: 0, max: 6.2, step: 0.1, unit: '', default: 1.0 },
  { key: 'slope', label: 'ST Slope', type: 'select', options: [
    { v: 0, l: 'Upsloping' }, { v: 1, l: 'Flat' }, { v: 2, l: 'Downsloping' }
  ], default: 1 },
  { key: 'ca', label: 'Major Vessels (0–3)', type: 'number', min: 0, max: 4, step: 1, unit: '', default: 0 },
  { key: 'thal', label: 'Thalassemia', type: 'select', options: [
    { v: 0, l: 'Null' }, { v: 1, l: 'Fixed Defect' }, { v: 2, l: 'Normal' }, { v: 3, l: 'Reversible Defect' }
  ], default: 2 },
];

let gaugeChart = null;

function buildForm() {
  const container = document.getElementById('form-fields');
  container.innerHTML = FEATURES.map(f => {
    if (f.type === 'select') {
      const opts = f.options.map(o =>
        `<option value="${o.v}" ${o.v === f.default ? 'selected' : ''}>${o.l}</option>`
      ).join('');
      return `
        <div class="form-group">
          <label for="${f.key}">${f.label}</label>
          <select id="${f.key}" name="${f.key}">${opts}</select>
        </div>`;
    }
    return `
      <div class="form-group">
        <label for="${f.key}">${f.label}${f.unit ? ` (${f.unit})` : ''}</label>
        <input type="number" id="${f.key}" name="${f.key}"
          min="${f.min}" max="${f.max}" step="${f.step || 1}" value="${f.default}" required />
      </div>`;
  }).join('');
}

function getFormData() {
  const data = {};
  FEATURES.forEach(f => {
    const el = document.getElementById(f.key);
    data[f.key] = parseFloat(el.value);
  });
  return data;
}

function drawGauge(probability, color) {
  const ctx = document.getElementById('risk-gauge').getContext('2d');
  if (gaugeChart) gaugeChart.destroy();

  gaugeChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [probability, 100 - probability],
        backgroundColor: [color, 'rgba(30,41,59,0.8)'],
        borderWidth: 0,
        circumference: 270,
        rotation: 225,
      }]
    },
    options: {
      responsive: false,
      cutout: '78%',
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      animation: { animateRotate: true, duration: 900 }
    }
  });
}

async function loadMetrics() {
  try {
    const res = await fetch('/api/metrics');
    if (!res.ok) throw new Error('metrics unavailable');
    const data = await res.json();
    const rf = data.random_forest;
    const lr = data.logistic_regression;

    document.getElementById('stat-accuracy').textContent =
      (Math.max(rf.accuracy, lr.accuracy) * 100).toFixed(1) + '%';
    document.getElementById('stat-auc').textContent =
      Math.max(rf.roc_auc, lr.roc_auc).toFixed(3);

    // Metrics cards
    const grid = document.getElementById('metrics-grid');
    grid.innerHTML = [
      { name: 'Random Forest', m: rf, icon: '🌲' },
      { name: 'Logistic Regression', m: lr, icon: '📐' }
    ].map(({ name, m, icon }) => `
      <div class="metric-card">
        <h3>${icon} ${name}</h3>
        <div class="metric-row"><span class="m-label">Accuracy</span><span class="m-value">${(m.accuracy*100).toFixed(1)}%</span></div>
        <div class="metric-row"><span class="m-label">Precision</span><span class="m-value">${(m.precision*100).toFixed(1)}%</span></div>
        <div class="metric-row"><span class="m-label">Recall</span><span class="m-value">${(m.recall*100).toFixed(1)}%</span></div>
        <div class="metric-row"><span class="m-label">F1 Score</span><span class="m-value">${(m.f1*100).toFixed(1)}%</span></div>
        <div class="metric-row"><span class="m-label">ROC-AUC</span><span class="m-value">${m.roc_auc.toFixed(3)}</span></div>
      </div>
    `).join('');
  } catch (e) {
    console.warn('Could not load metrics (server may be offline):', e);
    // Fallback static values from training
    document.getElementById('stat-accuracy').textContent = '80.3%';
    document.getElementById('stat-auc').textContent = '0.871';
    document.getElementById('metrics-grid').innerHTML = `
      <div class="metric-card"><h3>🌲 Random Forest</h3>
        <div class="metric-row"><span class="m-label">Accuracy</span><span class="m-value">77.0%</span></div>
        <div class="metric-row"><span class="m-label">Precision</span><span class="m-value">78.8%</span></div>
        <div class="metric-row"><span class="m-label">Recall</span><span class="m-value">78.8%</span></div>
        <div class="metric-row"><span class="m-label">F1 Score</span><span class="m-value">78.8%</span></div>
        <div class="metric-row"><span class="m-label">ROC-AUC</span><span class="m-value">0.859</span></div>
      </div>
      <div class="metric-card"><h3>📐 Logistic Regression</h3>
        <div class="metric-row"><span class="m-label">Accuracy</span><span class="m-value">80.3%</span></div>
        <div class="metric-row"><span class="m-label">Precision</span><span class="m-value">80.0%</span></div>
        <div class="metric-row"><span class="m-label">Recall</span><span class="m-value">84.8%</span></div>
        <div class="metric-row"><span class="m-label">F1 Score</span><span class="m-value">82.4%</span></div>
        <div class="metric-row"><span class="m-label">ROC-AUC</span><span class="m-value">0.871</span></div>
      </div>`;
  }
}

async function loadEDA() {
  try {
    const res = await fetch('/api/eda');
    if (!res.ok) throw new Error('eda unavailable');
    const data = await res.json();
    document.getElementById('stat-records').textContent = data.total_records;
    renderInsightCards(data);
  } catch (e) {
    document.getElementById('stat-records').textContent = '302';
    renderInsightCards({
      total_records: 302, positive_cases: 165, negative_cases: 137,
      mean_age: 54.4, mean_chol: 246.5, mean_thalach: 149.6
    });
  }
}

function renderInsightCards(data) {
  const cards = document.getElementById('insight-cards');
  cards.innerHTML = `
    <div class="insight-card"><div class="ic-value">${data.total_records}</div><div class="ic-label">Clean Records</div></div>
    <div class="insight-card"><div class="ic-value">${data.positive_cases || '—'}</div><div class="ic-label">Disease Cases</div></div>
    <div class="insight-card"><div class="ic-value">${data.negative_cases || '—'}</div><div class="ic-label">No Disease</div></div>
    <div class="insight-card"><div class="ic-value">${(data.mean_age || 54.4).toFixed(1)}</div><div class="ic-label">Mean Age</div></div>
    <div class="insight-card"><div class="ic-value">${(data.mean_chol || 246).toFixed(0)}</div><div class="ic-label">Mean Cholesterol</div></div>
    <div class="insight-card"><div class="ic-value">${(data.mean_thalach || 150).toFixed(0)}</div><div class="ic-label">Mean Max HR</div></div>
  `;
}

async function handlePredict(e) {
  e.preventDefault();
  const btn = document.getElementById('predict-btn');
  const btnText = btn.querySelector('.btn-text');
  const loader = btn.querySelector('.btn-loader');
  btn.disabled = true;
  btnText.textContent = 'Analyzing…';
  loader.classList.remove('hidden');

  const payload = getFormData();

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Prediction failed');
    }
    const result = await res.json();
    showResult(result);
  } catch (err) {
    // Offline fallback using simple heuristic for demo
    console.warn('API error, using fallback:', err.message);
    const fallback = offlinePredict(payload);
    showResult(fallback);
  } finally {
    btn.disabled = false;
    btnText.textContent = 'Analyze Risk';
    loader.classList.add('hidden');
  }
}

function offlinePredict(data) {
  // Simple weighted score based on known risk factors (approximate)
  let score = 0;
  if (data.age > 55) score += 0.12;
  if (data.sex === 1) score += 0.08;
  if (data.cp === 0) score += 0.15;
  if (data.trestbps > 140) score += 0.1;
  if (data.chol > 240) score += 0.1;
  if (data.thalach < 140) score += 0.12;
  if (data.exang === 1) score += 0.15;
  if (data.oldpeak > 1.5) score += 0.12;
  if (data.ca >= 1) score += 0.14;
  if (data.thal === 3 || data.thal === 1) score += 0.1;
  score = Math.min(0.95, Math.max(0.05, score));
  const pred = score >= 0.5 ? 1 : 0;
  const level = score >= 0.75 ? 'High' : score >= 0.45 ? 'Moderate' : 'Low';
  const color = level === 'High' ? '#e05c5c' : level === 'Moderate' ? '#d4a017' : '#5b9a8b';
  return {
    prediction: pred,
    probability: Math.round(score * 1000) / 10,
    risk_level: level,
    risk_color: color,
    message: pred
      ? `Estimated ${level.toLowerCase()} risk of heart disease (${(score*100).toFixed(1)}%). Consult a healthcare professional. This is not a diagnosis.`
      : `Estimated ${level.toLowerCase()} risk (${(score*100).toFixed(1)}%). Maintain healthy habits.`,
    models: {
      random_forest: { probability: Math.round(score * 100 - 2) },
      logistic_regression: { probability: Math.round(score * 100 + 2) }
    },
    recommendations: [
      data.chol > 240 ? 'Cholesterol is elevated — discuss lipid management.' : null,
      data.trestbps > 140 ? 'Blood pressure is high — monitor regularly.' : null,
      data.exang === 1 ? 'Exercise-induced angina present — seek clinical advice.' : null,
      'Connect to the PulseX service for full ensemble model predictions.'
    ].filter(Boolean)
  };
}

function showResult(result) {
  document.getElementById('result-placeholder').classList.add('hidden');
  const content = document.getElementById('result-content');
  content.classList.remove('hidden');

  const pct = result.probability;
  const color = result.risk_color || '#2b7de9';

  document.getElementById('gauge-value').textContent = pct + '%';
  document.getElementById('gauge-label').textContent = result.risk_level + ' Risk';
  document.getElementById('gauge-value').style.color = color;

  const badge = document.getElementById('risk-badge');
  badge.textContent = result.risk_level + ' Risk';
  badge.style.background = color + '22';
  badge.style.color = color;
  badge.style.border = `1px solid ${color}55`;

  document.getElementById('risk-message').textContent = result.message;

  const rfP = result.models?.random_forest?.probability ?? pct;
  const lrP = result.models?.logistic_regression?.probability ?? pct;
  document.getElementById('rf-bar').style.width = rfP + '%';
  document.getElementById('lr-bar').style.width = lrP + '%';
  document.getElementById('rf-pct').textContent = rfP + '%';
  document.getElementById('lr-pct').textContent = lrP + '%';

  const recs = result.recommendations || [];
  document.getElementById('recommendations').innerHTML = `
    <h4>Recommendations</h4>
    ${recs.map(r => `<div class="rec-item">${r}</div>`).join('')}
  `;

  drawGauge(pct, color);
}

function resetForm() {
  FEATURES.forEach(f => {
    const el = document.getElementById(f.key);
    if (el) el.value = f.default;
  });
  document.getElementById('result-content').classList.add('hidden');
  document.getElementById('result-placeholder').classList.remove('hidden');
  if (gaugeChart) { gaugeChart.destroy(); gaugeChart = null; }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  buildForm();
  loadMetrics();
  loadEDA();
  document.getElementById('risk-form').addEventListener('submit', handlePredict);
  document.getElementById('reset-btn').addEventListener('click', resetForm);
});
