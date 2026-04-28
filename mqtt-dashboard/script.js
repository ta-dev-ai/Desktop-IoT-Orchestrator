/*
  Mini dashboard en JavaScript vanilla.
  Objectif :
  - rester facile à lire pour un débutant
  - éviter les erreurs si on modifie le HTML plus tard
  - rester simple à convertir en React ensuite
*/

const API_BASE = "http://127.0.0.1:8000/api/commands";
const SYSTEM_STATUS_URL = "http://127.0.0.1:8000/api/system/status";
const terminalLog = document.getElementById("terminal-log");
const brokerStatus = document.getElementById("broker-status");
const logoutBtn = document.getElementById("logout-btn");
const themeToggleBtn = document.getElementById("theme-toggle");
const pageTitle = document.getElementById("page-title");
const pageSubtitle = document.getElementById("page-subtitle");
const dependencyReport = document.getElementById("dependency-report");
const systemStatusPill = document.getElementById("system-status-pill");
const refreshSystemBtn = document.getElementById("refresh-system-btn");

// Correspondance claire entre le bouton cliqué et la route FastAPI.
const commandLabels = {
  "start-broker": "Démarrer Broker",
  "stop-broker": "Arrêter Broker",
  "start-subscriber": "Démarrer Subscriber",
  "publish-temperature": "Envoyer Message",
  "restart-broker": "Redémarrer Broker",
  "open-terminal": "Ouvrir Terminal",
};

const viewMeta = {
  dashboard: {
    title: "Dashboard",
    subtitle: "Contrôlez votre serveur MQTT facilement",
    target: null,
  },
  commandes: {
    title: "Commandes",
    subtitle: "Lancez les actions rapides et consultez les commandes MQTT.",
    target: "commandes",
  },
  logs: {
    title: "Logs",
    subtitle: "Suivez les actions locales et les réponses FastAPI.",
    target: "logs",
  },
  settings: {
    title: "Settings",
    subtitle: "Vérifiez les dépendances et l'état système du projet.",
    target: null,
  },
};

function getTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function addLogLine(message, type = "INFO") {
  if (!terminalLog) return;

  const line = `[${getTimestamp()}] [${type}] ${message}`;
  terminalLog.textContent += `\n${line}`;
  terminalLog.scrollTop = terminalLog.scrollHeight;
}

function setBrokerStatus(status) {
  if (!brokerStatus) return;

  brokerStatus.textContent = status;
}

function setActiveMenu(viewName) {
  document.querySelectorAll("[data-view]").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === viewName);
  });
}

function setHeader(viewName) {
  const meta = viewMeta[viewName] || viewMeta.dashboard;

  if (pageTitle) pageTitle.textContent = meta.title;
  if (pageSubtitle) pageSubtitle.textContent = meta.subtitle;
}

function showDashboardSection(targetId) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    const isDashboard = panel.dataset.viewPanel === "dashboard";
    panel.hidden = !isDashboard;
    panel.classList.toggle("is-active", isDashboard);
  });

  if (!targetId) return;

  const target = document.getElementById(targetId);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function showSettingsView() {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    const isSettings = panel.dataset.viewPanel === "settings";
    panel.hidden = !isSettings;
    panel.classList.toggle("is-active", isSettings);
  });

  loadSystemStatus();
}

function showView(viewName) {
  const normalizedView = viewMeta[viewName] ? viewName : "dashboard";
  const meta = viewMeta[normalizedView];

  setActiveMenu(normalizedView);
  setHeader(normalizedView);

  if (normalizedView === "settings") {
    showSettingsView();
    return;
  }

  showDashboardSection(meta.target);
}

function renderSystemStatus(payload) {
  if (!dependencyReport || !systemStatusPill) return;

  const summary = Array.isArray(payload.summary) ? payload.summary.join("\n") : "Rapport indisponible.";
  dependencyReport.textContent = summary;

  systemStatusPill.textContent = payload.ok
    ? "Ready"
    : `Attention (${payload.missing_count || 0} manquant)`;
  systemStatusPill.classList.toggle("ok", Boolean(payload.ok));
  systemStatusPill.classList.toggle("warning", !payload.ok);
}

async function loadSystemStatus() {
  if (!dependencyReport || !systemStatusPill) return;

  dependencyReport.textContent = "Chargement du rapport système...";
  systemStatusPill.textContent = "Chargement";
  systemStatusPill.classList.remove("ok", "warning");

  try {
    const response = await fetch(SYSTEM_STATUS_URL);
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.detail || `Erreur HTTP ${response.status}`);
    }

    renderSystemStatus(payload);
    addLogLine("Rapport système chargé", "SYSTEM");
  } catch (error) {
    dependencyReport.textContent = `Impossible de charger le statut système.\n${error.message}`;
    systemStatusPill.textContent = "Erreur";
    systemStatusPill.classList.add("warning");
    addLogLine(`Statut système indisponible: ${error.message}`, "ERROR");
  }
}

function applyTheme(theme) {
  // Le thème est stocké sur <body> pour que CSS puisse changer les variables.
  if (!document.body || !themeToggleBtn) return;

  document.body.dataset.theme = theme === "night" ? "night" : "light";
  themeToggleBtn.textContent = theme === "night" ? "Mode clair" : "Mode nuit";
  themeToggleBtn.setAttribute(
    "aria-label",
    theme === "night" ? "Activer le mode clair" : "Activer le mode nuit bleu"
  );
  localStorage.setItem("mqtt-dashboard-theme", theme);
}

function initTheme() {
  if (!window.matchMedia || !themeToggleBtn) return;

  const savedTheme = localStorage.getItem("mqtt-dashboard-theme");
  const preferredTheme =
    savedTheme || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "night" : "light");
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
async function runCommand(commandName) {
  const label = commandLabels[commandName] || commandName;

  // 1) Feedback immédiat dans le terminal.
  addLogLine(`Commande lancée : ${label}`, "INFO");

  try {
    // 2) Appel POST vers le backend FastAPI.
    const response = await fetch(`${API_BASE}/${commandName}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    // On lit quand même la réponse pour pouvoir afficher l'erreur du backend.
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.detail || `Erreur HTTP ${response.status}`);
    }

    // 3) Réponse réussie: on l'ajoute dans le terminal.
    addLogLine(JSON.stringify(payload), "API");

    // Petite logique visuelle pour refléter l'état du broker.
    if (commandName === "start-broker" || commandName === "restart-broker") {
      setBrokerStatus("Connecté");
    }

    if (commandName === "stop-broker") {
      setBrokerStatus("Déconnecté");
    }
  } catch (error) {
    // 4) Si FastAPI n'est pas lancé ou ne répond pas, on reste lisible.
    addLogLine(`Impossible de contacter FastAPI: ${error.message}`, "ERROR");
  }
}

function wireButtons() {
  if (typeof document.querySelectorAll !== "function") return;

  document.querySelectorAll("[data-command]").forEach((button) => {
    button.addEventListener("click", () => {
      runCommand(button.dataset.command);
    });
  });
}

function wireNavigation() {
  document.querySelectorAll("[data-view]").forEach((item) => {
    item.addEventListener("click", (event) => {
      event.preventDefault();
      showView(item.dataset.view);
    });
  });
}

function wireLogout() {
  if (!logoutBtn) return;

  logoutBtn.addEventListener("click", () => {
    addLogLine("Déconnexion fictive demandée", "INFO");
  });
}

function wireThemeToggle() {
  if (!themeToggleBtn) return;

  themeToggleBtn.addEventListener("click", () => {
    const nextTheme = document.body.dataset.theme === "night" ? "light" : "night";
    applyTheme(nextTheme);
    addLogLine(`Thème ${nextTheme === "night" ? "dark blue night" : "clair"} activé`, "INFO");
  });
}

function wireSettingsActions() {
  if (!refreshSystemBtn) return;

  refreshSystemBtn.addEventListener("click", () => {
    loadSystemStatus();
  });
}

function seedInitialLog() {
  addLogLine("Dashboard chargé");
  addLogLine("Prêt à exécuter les commandes MQTT");
}

// Initialisation de l'interface.
wireButtons();
wireNavigation();
wireLogout();
wireThemeToggle();
wireSettingsActions();
initTheme();
seedInitialLog();
