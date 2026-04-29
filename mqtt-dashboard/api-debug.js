let API_ORIGIN = 'http://127.0.0.1:8000';

const tests = [
  { label: 'Identity', method: 'GET', path: '/api/debug/backend' },
  { label: 'Health', method: 'GET', path: '/health' },
  { label: 'Self-test', method: 'GET', path: '/api/debug/self-test' },
  { label: 'System status', method: 'GET', path: '/api/system/status' },
  { label: 'Runtime status', method: 'GET', path: '/api/system/runtime-status' },
  { label: 'Devices list', method: 'GET', path: '/api/devices' },
  { label: 'Port MQTT', method: 'POST', path: '/api/commands/verify-mqtt-port' },
  { label: 'Open terminal', method: 'POST', path: '/api/commands/open-terminal' },
  {
    label: 'Legacy publish',
    method: 'POST',
    path: '/publish',
    body: { topic: 'temperature', message: '25°C' },
  },
  {
    label: 'Publish message',
    method: 'POST',
    path: '/api/commands/publish-message',
    body: { topic: 'temperature', message: '25°C' },
  },
];

function createRouteRow(test) {
  const row = document.createElement('div');
  row.className = 'route';
  row.innerHTML = `
    <div><strong>${test.label}</strong><br><code>${test.method}</code></div>
    <div>
      <code>${test.path}</code>
      <pre data-output>En attente...</pre>
    </div>
    <div><button data-run>Tester</button></div>
  `;

  row.querySelector('[data-run]').addEventListener('click', () => runTest(test, row));
  return row;
}

async function runTest(test, row) {
  const output = row.querySelector('[data-output]');
  output.textContent = 'Test en cours...';
  output.className = '';

  try {
    const options = {
      method: test.method,
      mode: 'cors',
    };
    if (test.body) {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(test.body);
    }

    const url = API_ORIGIN + test.path;
    const response = await fetch(url, options);
    const text = await response.text();
    let body = text;

    try {
      body = JSON.stringify(JSON.parse(text), null, 2);
    } catch (error) {
      body = text;
    }

    output.className = response.ok ? 'ok' : 'fail';
    output.textContent = `URL: ${url}\nHTTP ${response.status} ${response.statusText}\n${body}`;
  } catch (error) {
    output.className = 'fail';
    output.textContent = `FAILED\nURL: ${API_ORIGIN + test.path}\nError: ${error.message}`;
  }
}

async function checkBackendIdentity() {
  const badge = document.getElementById('backend-id');
  const card = document.getElementById('identity-check');
  badge.textContent = 'Vérification...';
  card.className = 'identity-card';

  try {
    const response = await fetch(API_ORIGIN + '/api/debug/backend', { mode: 'cors' });
    const data = await response.json();

    if (data.backend === 'mqtt-control-api') {
      badge.textContent = `OK - ${data.version}`;
      card.classList.add('found');
    } else {
      badge.textContent = 'INCONNU (identifiant manquant)';
      card.classList.add('wrong');
    }
  } catch (error) {
    badge.textContent = 'INDISPONIBLE (erreur connexion)';
    card.classList.add('wrong');
  }
}

function init() {
  const originInput = document.getElementById('origin-input');
  const updateBtn = document.getElementById('update-origin');
  const container = document.getElementById('routes');

  API_ORIGIN = originInput.value.trim();

  // Re-build tests list
  container.innerHTML = '';
  tests.forEach((test) => container.appendChild(createRouteRow(test)));

  updateBtn.addEventListener('click', () => {
    API_ORIGIN = originInput.value.trim();
    checkBackendIdentity();
    // Re-run the tests if needed? No, let user do it.
    addLogLine(`Backend URL mise à jour : ${API_ORIGIN}`);
  });

  document.getElementById('run-all').addEventListener('click', async () => {
    const rows = [...document.querySelectorAll('.route')];
    for (let index = 0; index < tests.length; index += 1) {
      await runTest(tests[index], rows[index]);
    }
  });

  checkBackendIdentity();
}

function addLogLine(msg) {
  console.log(`[Diagnostic] ${msg}`);
}

window.addEventListener('DOMContentLoaded', init);
