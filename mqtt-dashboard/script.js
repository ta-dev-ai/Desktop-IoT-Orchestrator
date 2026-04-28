/*
  Mini dashboard en JavaScript vanilla.
  Objectif :
  - rester facile à lire pour un débutant
  - éviter les erreurs si on modifie le HTML plus tard
  - rester simple à convertir en React ensuite
*/

const API_BASE = "http://127.0.0.1:8000/api/commands";
const terminalLog = document.getElementById("terminal-log");
const brokerStatus = document.getElementById("broker-status");
const logoutBtn = document.getElementById("logout-btn");
const themeToggleBtn = document.getElementById("theme-toggle");

// Correspondance claire entre le bouton cliqué et la route FastAPI.
const commandLabels = {
  "start-broker": "Démarrer Broker",
  "stop-broker": "Arrêter Broker",
  "start-subscriber": "Démarrer Subscriber",
  "publish-temperature": "Envoyer Message",
  "restart-broker": "Redémarrer Broker",
  "open-terminal": "Ouvrir Terminal",
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

function seedInitialLog() {
  addLogLine("Dashboard chargé");
  addLogLine("Prêt à exécuter les commandes MQTT");
}

// Initialisation de l'interface.
wireButtons();
wireLogout();
wireThemeToggle();
initTheme();
seedInitialLog();
