/*
  Mini dashboard en JavaScript vanilla.
  Objectif :
  - rester facile à lire pour un débutant
  - éviter les erreurs si on modifie le HTML plus tard
  - rester simple à convertir en React ensuite
*/

const API_ORIGIN =
  window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : window.location.origin;
const API_BASE = `${API_ORIGIN}/api/commands`;
const SYSTEM_STATUS_URL = `${API_ORIGIN}/api/system/status`;
const HEALTH_URL = `${API_ORIGIN}/health`;
const EVENTS_URL = `${API_ORIGIN}/api/debug/events`;
const MESSAGE_HISTORY_KEY = 'mqtt-dashboard-message-history';
let lastEventIndex = 0;
const terminalLog = document.getElementById('terminal-log');
const brokerStatus = document.getElementById('broker-status');
const logoutBtn = document.getElementById('logout-btn');
const themeToggleBtn = document.getElementById('theme-toggle');
const pageTitle = document.getElementById('page-title');
const pageSubtitle = document.getElementById('page-subtitle');
const dependencyReport = document.getElementById('dependency-report');
const systemStatusPill = document.getElementById('system-status-pill');
const refreshSystemBtn = document.getElementById('refresh-system-btn');
const messageList = document.getElementById('message-list');
const publishModal = document.getElementById('publish-modal');
const publishForm = document.getElementById('publish-form');
const publishTopicInput = document.getElementById('publish-topic');
const publishMessageInput = document.getElementById('publish-message');
const openPublishModalBtn = document.getElementById('open-publish-modal-btn');
const closePublishModalBtn = document.getElementById('close-publish-modal');
const cancelPublishModalBtn = document.getElementById('cancel-publish-modal');
const submitPublishMessageBtn = document.getElementById('submit-publish-message');
let backendAvailable = false;
let systemStatusCache = null;

// Correspondance claire entre le bouton cliqué et la route FastAPI.
const commandLabels = {
  'start-broker': 'Démarrer Broker',
  'stop-broker': 'Arrêter Broker',
  'start-subscriber': 'Démarrer Subscriber',
  'publish-temperature': 'Envoyer Message',
  'publish-message': 'Envoyer Message',
  'restart-broker': 'Redémarrer Broker',
  'open-terminal': 'Ouvrir Terminal',
  'verify-mqtt-port': 'Vérifier le port 1883',
};

const commandRequirements = {
  'start-broker': ['Mosquitto broker'],
  'stop-broker': [],
  'start-subscriber': ['Mosquitto subscriber'],
  'publish-temperature': ['Mosquitto publisher'],
  'publish-message': ['Mosquitto publisher'],
  'restart-broker': ['Mosquitto broker'],
  'open-terminal': [],
  'verify-mqtt-port': [],
};

const viewMeta = {
  dashboard: {
    title: 'Dashboard',
    subtitle: 'Contrôlez votre serveur MQTT facilement',
    target: null,
  },
  commandes: {
    title: 'Commandes',
    subtitle: 'Lancez les actions rapides et consultez les commandes MQTT.',
    target: 'commandes',
  },
  logs: {
    title: 'Logs',
    subtitle: 'Suivez les actions locales et les réponses FastAPI.',
    target: 'logs',
  },
  settings: {
    title: 'Settings',
    subtitle: "Vérifiez les dépendances et l'état système du projet.",
    target: null,
  },
  appareils: {
    title: 'Appareils',
    subtitle: 'Gérez vos capteurs et actionneurs MQTT.',
    target: null,
  },
};

function getTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function addLogLine(message, type = 'INFO') {
  if (!terminalLog) return;

  const line = `[${getTimestamp()}] [${type}] ${message}`;
  terminalLog.textContent += `\n${line}`;
  terminalLog.scrollTop = terminalLog.scrollHeight;
}

function getMissingDependencyNames() {
  if (!systemStatusCache || !Array.isArray(systemStatusCache.items)) return [];
  return systemStatusCache.items.filter((item) => !item.ok).map((item) => item.name);
}

function getCommandBlockReason(commandName) {
  if (!backendAvailable) {
    return "Le backend FastAPI n'est pas joignable.";
  }

  const missingNames = getMissingDependencyNames();
  const requiredNames = commandRequirements[commandName] || [];
  const blockedBy = requiredNames.find((name) => missingNames.includes(name));
  if (blockedBy) {
    return `${blockedBy} est manquant. Ouvrez Settings pour le détail.`;
  }

  return '';
}

function refreshCommandAvailability() {
  document.querySelectorAll('[data-command]').forEach((button) => {
    const commandName = button.dataset.command;
    const reason = getCommandBlockReason(commandName);
    button.disabled = Boolean(reason);
    button.title = reason;
    button.classList.toggle('is-disabled', Boolean(reason));
  });

  if (openPublishModalBtn) {
    const reason = getCommandBlockReason('publish-message');
    openPublishModalBtn.disabled = Boolean(reason);
    openPublishModalBtn.title = reason;
    openPublishModalBtn.classList.toggle('is-disabled', Boolean(reason));
  }
}

async function pingBackend() {
  try {
    const response = await fetch(HEALTH_URL);
    backendAvailable = response.ok;
  } catch {
    backendAvailable = false;
  }
  return backendAvailable;
}

function updateButtonFeedback(button, state, label) {
  if (!button) return;

  if (!button.dataset.defaultLabel) {
    button.dataset.defaultLabel = button.textContent.trim();
  }

  button.classList.remove('is-loading', 'is-success', 'is-error');

  if (state === 'loading') {
    button.classList.add('is-loading');
    button.disabled = true;
    button.textContent = label || 'En cours...';
    return;
  }

  if (state === 'success') {
    button.classList.add('is-success');
    button.disabled = false;
    button.textContent = label || 'Succès';
    window.setTimeout(() => updateButtonFeedback(button, 'idle'), 1300);
    return;
  }

  if (state === 'error') {
    button.classList.add('is-error');
    button.disabled = false;
    button.textContent = label || 'Erreur';
    window.setTimeout(() => updateButtonFeedback(button, 'idle'), 1500);
    return;
  }

  button.disabled = false;
  button.textContent = button.dataset.defaultLabel;
}

function loadMessageHistory() {
  try {
    return JSON.parse(localStorage.getItem(MESSAGE_HISTORY_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveMessageHistory(items) {
  localStorage.setItem(MESSAGE_HISTORY_KEY, JSON.stringify(items.slice(-20)));
}

function renderMessageHistory() {
  if (!messageList) return;

  const items = loadMessageHistory();
  if (!items.length) return;

  messageList.innerHTML = '';
  items.forEach((item) => appendMessageItem(item, false));
}

function appendMessageItem(item, persist = true) {
  if (!messageList) return;

  const li = document.createElement('li');
  li.className = 'message-item';
  li.dataset.messageType = item.type;
  li.innerHTML = `
    <span class="message-dot ${item.type === 'incoming' ? 'incoming' : 'outgoing'}"></span>
    <span class="message-main">${item.message}</span>
    <span class="message-meta">${item.topic} · ${item.type === 'incoming' ? 'Reçu' : 'Envoyé'} · ${item.time}</span>
  `;
  messageList.prepend(li);

  if (!persist) return;

  const history = loadMessageHistory();
  history.push(item);
  saveMessageHistory(history);
}

function setBrokerStatus(status) {
  if (!brokerStatus) return;
  brokerStatus.textContent = status;
  brokerStatus.classList.remove('ok', 'warning', 'offline');

  if (status === 'Connecté') {
    brokerStatus.classList.add('ok');
  } else if (status === 'Déconnecté') {
    brokerStatus.classList.add('offline');
  } else {
    brokerStatus.classList.add('warning');
  }
}

function setActiveMenu(viewName) {
  document.querySelectorAll('[data-view]').forEach((item) => {
    item.classList.toggle('active', item.dataset.view === viewName);
  });
}

function setHeader(viewName) {
  const meta = viewMeta[viewName] || viewMeta.dashboard;

  if (pageTitle) pageTitle.textContent = meta.title;
  if (pageSubtitle) pageSubtitle.textContent = meta.subtitle;
}

function showDashboardSection(targetId) {
  document.querySelectorAll('[data-view-panel]').forEach((panel) => {
    const isDashboard = panel.dataset.viewPanel === 'dashboard';
    panel.hidden = !isDashboard;
    panel.classList.toggle('is-active', isDashboard);
  });

  if (!targetId) return;

  const target = document.getElementById(targetId);
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function showSettingsView() {
  document.querySelectorAll('[data-view-panel]').forEach((panel) => {
    const isSettings = panel.dataset.viewPanel === 'settings';
    panel.hidden = !isSettings;
    panel.classList.toggle('is-active', isSettings);
  });

  loadSystemStatus();
}

function showView(viewName) {
  const normalizedView = viewMeta[viewName] ? viewName : 'dashboard';
  const meta = viewMeta[normalizedView];

  setActiveMenu(normalizedView);
  setHeader(normalizedView);

  if (normalizedView === 'settings') {
    showSettingsView();
    return;
  }

  if (normalizedView === 'appareils') {
    showAppareilsView();
    return;
  }

  showDashboardSection(meta.target);
}

function showAppareilsView() {
  document.querySelectorAll('[data-view-panel]').forEach((panel) => {
    const isAppareils = panel.dataset.viewPanel === 'appareils';
    panel.hidden = !isAppareils;
    panel.classList.toggle('is-active', isAppareils);
  });
}

function renderSystemStatus(payload) {
  if (!dependencyReport || !systemStatusPill) return;

  systemStatusCache = payload;

  const summary = Array.isArray(payload.summary)
    ? payload.summary.join('\n')
    : 'Rapport indisponible.';
  dependencyReport.textContent = summary;

  systemStatusPill.textContent = payload.ok
    ? 'Ready'
    : `Attention (${payload.missing_count || 0} manquant)`;
  systemStatusPill.classList.toggle('ok', Boolean(payload.ok));
  systemStatusPill.classList.toggle('warning', !payload.ok);
  refreshCommandAvailability();
}

async function loadProjectStats() {
  const brokerText = document.getElementById('stat-broker-text');
  const receivedText = document.getElementById('stat-received-count');
  const sentText = document.getElementById('stat-sent-count');
  const clientsText = document.getElementById('stat-clients-count');

  if (!brokerText || !receivedText) return;

  try {
    const response = await fetch(`${API_ORIGIN}/api/system/stats`);
    const data = await response.json();
    if (data.ok) {
      brokerText.textContent = data.broker_running ? 'Actif' : 'Arrêté';
      receivedText.textContent = data.counts.responses || 0;
      sentText.textContent = data.counts.commands || 0;
      clientsText.textContent = data.clients || 0;

      // Mise à jour du badge global de statut
      setBrokerStatus(data.broker_running ? 'Connecté' : 'Déconnecté');

      // Update sidebar as well
      const sidebarBrokerStatus = document.getElementById('broker-status');
      if (sidebarBrokerStatus) {
        sidebarBrokerStatus.textContent = data.broker_running ? 'Connecté' : 'Déconnecté';
        const dot = sidebarBrokerStatus.previousElementSibling;
        if (dot && dot.classList.contains('status-dot')) {
          dot.className = `status-dot ${data.broker_running ? 'online' : 'offline'}`;
        }
      }
    }
  } catch (error) {
    console.error('Impossible de charger les stats', error);
  }
}

async function loadSystemStatus() {
  if (!dependencyReport || !systemStatusPill) return;

  dependencyReport.textContent = 'Chargement du rapport système...';
  systemStatusPill.textContent = 'Chargement';
  systemStatusPill.classList.remove('ok', 'warning');

  try {
    const response = await fetch(SYSTEM_STATUS_URL);
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.detail || `Erreur HTTP ${response.status}`);
    }

    renderSystemStatus(payload);
    addLogLine('Rapport système chargé', 'SYSTEM');
  } catch (error) {
    systemStatusCache = null;
    dependencyReport.textContent = `Impossible de charger le statut système.\n${error.message}`;
    systemStatusPill.textContent = 'Erreur';
    systemStatusPill.classList.add('warning');
    addLogLine(`Statut système indisponible: ${error.message}`, 'ERROR');
    refreshCommandAvailability();
  }
}

function applyTheme(theme) {
  // Le thème est stocké sur <body> pour que CSS puisse changer les variables.
  if (!document.body || !themeToggleBtn) return;

  document.body.dataset.theme = theme === 'night' ? 'night' : 'light';
  themeToggleBtn.textContent = theme === 'night' ? 'Mode clair' : 'Mode nuit';
  themeToggleBtn.setAttribute(
    'aria-label',
    theme === 'night' ? 'Activer le mode clair' : 'Activer le mode nuit bleu',
  );
  localStorage.setItem('mqtt-dashboard-theme', theme);
}

function initTheme() {
  if (!window.matchMedia || !themeToggleBtn) return;

  const savedTheme = localStorage.getItem('mqtt-dashboard-theme');
  const preferredTheme =
    savedTheme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'night' : 'light');
  applyTheme(preferredTheme);
}

/*
  Fonction principale du dashboard.
  Elle suit exactement le flux demandé :
  1. écrire un log local immédiatement
  2. appeler FastAPI
  3. afficher la réponse JSON
  4. gérer les erreurs réseau / backend
*/
async function runCommand(commandName, options = {}) {
  const label = commandLabels[commandName] || commandName;
  const triggerButton = options.triggerButton;
  const payloadBody = options.payloadBody;
  const reason = getCommandBlockReason(commandName);

  if (reason) {
    addLogLine(`${label} bloqué: ${reason}`, 'ERROR');
    updateButtonFeedback(triggerButton, 'error', 'Indispo');
    throw new Error(reason);
  }

  // 1) Feedback immédiat dans le terminal.
  addLogLine(`Commande lancée : ${label}`, 'INFO');
  updateButtonFeedback(triggerButton, 'loading', 'En cours...');

  try {
    // 2) Appel POST vers le backend FastAPI.
    const response = await fetch(`${API_BASE}/${commandName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: payloadBody ? JSON.stringify(payloadBody) : undefined,
    });

    // On lit quand même la réponse pour pouvoir afficher l'erreur du backend.
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.detail || `Erreur HTTP ${response.status}`);
    }

    // 3) Réponse réussie: on l'ajoute dans le terminal.
    addLogLine(JSON.stringify(payload), 'API');
    updateButtonFeedback(triggerButton, 'success', 'OK');

    // Petite logique visuelle pour refléter l'état du broker.
    if (commandName === 'start-broker' || commandName === 'restart-broker') {
      setBrokerStatus('Connecté');
    }

    if (commandName === 'stop-broker') {
      setBrokerStatus('Déconnecté');
    }

    if (commandName === 'publish-message' && payload.topic && payload.payload) {
      appendMessageItem({
        type: 'outgoing',
        topic: payload.topic,
        message: payload.payload,
        time: getTimestamp(),
      });
    }

    return payload;
  } catch (error) {
    // 4) Si FastAPI n'est pas lancé ou ne répond pas, on reste lisible.
    addLogLine(`Impossible de contacter FastAPI: ${error.message}`, 'ERROR');
    updateButtonFeedback(triggerButton, 'error', 'Erreur');
    throw error;
  }
}

function wireButtons() {
  if (typeof document.querySelectorAll !== 'function') return;

  document.querySelectorAll('[data-command]').forEach((button) => {
    button.addEventListener('click', () => {
      runCommand(button.dataset.command, { triggerButton: button }).catch(() => {
        // The log panel already explains the error to the user.
      });
    });
  });
}

function openPublishModal() {
  if (!publishModal) return;
  publishModal.hidden = false;
  if (publishTopicInput) publishTopicInput.focus();
}

function closePublishModal() {
  if (!publishModal) return;
  publishModal.hidden = true;
}

function wirePublishModal() {
  if (openPublishModalBtn) {
    openPublishModalBtn.addEventListener('click', openPublishModal);
  }

  if (closePublishModalBtn) {
    closePublishModalBtn.addEventListener('click', closePublishModal);
  }

  if (cancelPublishModalBtn) {
    cancelPublishModalBtn.addEventListener('click', closePublishModal);
  }

  if (publishModal) {
    publishModal.addEventListener('click', (event) => {
      if (event.target === publishModal) {
        closePublishModal();
      }
    });
  }

  if (!publishForm) return;

  publishForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const reason = getCommandBlockReason('publish-message');
    if (reason) {
      addLogLine(`Envoi bloqué: ${reason}`, 'ERROR');
      return;
    }

    const topic = publishTopicInput ? publishTopicInput.value.trim() : '';
    const message = publishMessageInput ? publishMessageInput.value.trim() : '';

    if (!topic || !message) {
      addLogLine('Le topic et le message sont obligatoires.', 'ERROR');
      return;
    }

    try {
      await runCommand('publish-message', {
        triggerButton: submitPublishMessageBtn,
        payloadBody: { topic, message },
      });
      closePublishModal();
    } catch {
      // The error is already visible in the logs.
    }
  });
}

function wireNavigation() {
  document.querySelectorAll('[data-view]').forEach((item) => {
    item.addEventListener('click', (event) => {
      event.preventDefault();
      showView(item.dataset.view);
    });
  });
}

function wireLogout() {
  if (!logoutBtn) return;

  logoutBtn.addEventListener('click', () => {
    addLogLine('Déconnexion fictive demandée', 'INFO');
  });
}

function wireThemeToggle() {
  if (!themeToggleBtn) return;

  themeToggleBtn.addEventListener('click', () => {
    const nextTheme = document.body.dataset.theme === 'night' ? 'light' : 'night';
    applyTheme(nextTheme);
    addLogLine(`Thème ${nextTheme === 'night' ? 'dark blue night' : 'clair'} activé`, 'INFO');
  });
}

function wireSettingsActions() {
  if (!refreshSystemBtn) return;

  refreshSystemBtn.addEventListener('click', () => {
    loadSystemStatus();
  });
}

function seedInitialLog() {
  addLogLine('Dashboard chargé');
  addLogLine('Vérification du backend et des dépendances...');
}

async function syncBackgroundEvents() {
  if (!backendAvailable) return;

  try {
    const response = await fetch(EVENTS_URL);
    const payload = await response.json().catch(() => ({}));

    if (response.ok && Array.isArray(payload.items)) {
      const newItems = payload.items.slice(lastEventIndex);
      newItems.forEach((item) => {
        // On affiche le log dans le terminal
        addLogLine(item.message, item.type.toUpperCase());

        // Si le message provient du Subscriber, on l'ajoute à la liste des messages reçus
        if (item.type === 'response' && item.message.includes('[Sub]')) {
          const content = item.message.replace('[Sub]', '').trim();
          appendMessageItem({
            type: 'incoming',
            topic: 'MQTT (Sub)',
            message: content,
            time: getTimestamp(),
          });
        }
      });
      lastEventIndex = payload.items.length;
    }
  } catch (error) {
    console.error('Erreur de synchronisation des logs:', error);
  }
}

async function bootstrapDashboard() {
  await pingBackend();
  if (!backendAvailable) {
    addLogLine('Backend FastAPI indisponible. Vérifiez le launcher.', 'ERROR');
    refreshCommandAvailability();
    return;
  }

  addLogLine('Backend FastAPI joignable.', 'SYSTEM');
  await loadSystemStatus();
  await loadProjectStats();

  // Initial sync to grab current logs
  await syncBackgroundEvents();

  // Refresh stats and background logs periodically
  window.setInterval(loadProjectStats, 5000);
  window.setInterval(syncBackgroundEvents, 3000);
}

// Initialisation de l'interface.
wireButtons();
wireNavigation();
wireLogout();
wireThemeToggle();
wireSettingsActions();
wirePublishModal();
initTheme();
renderMessageHistory();
seedInitialLog();
bootstrapDashboard();
