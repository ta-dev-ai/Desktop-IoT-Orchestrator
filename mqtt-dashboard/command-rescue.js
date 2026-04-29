// MVP rescue layer.
// The older dashboard script can keep a stale "backend unavailable" state.
// This layer handles real clicks directly against FastAPI and updates the UI.

(function () {
  const API_ROOT = "http://127.0.0.1:8000";
  const COMMANDS_URL = API_ROOT + "/api/commands";

  const labels = {
    "start-broker": "Démarrer Broker",
    "stop-broker": "Arrêter Broker",
    "start-subscriber": "Démarrer Subscriber",
    "publish-temperature": "Publier température 25°C",
    "publish-message": "Envoyer Message",
    "restart-broker": "Redémarrer Broker",
    "open-terminal": "Ouvrir Terminal",
    "verify-mqtt-port": "Vérifier le port 1883",
  };

  function nowTime() {
    return new Date().toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  function nowDateTime() {
    return new Date().toLocaleString("fr-FR");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function addLog(level, message) {
    const terminal =
      document.getElementById("live-logs") ||
      document.querySelector(".terminal") ||
      document.querySelector(".logs-terminal") ||
      document.querySelector("pre");

    if (!terminal) {
      return;
    }

    const line = document.createElement("div");
    line.textContent = `[${nowTime()}] [${level}] ${message}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }

  function closePublishModal() {
    const modal = document.getElementById("publish-modal");
    if (modal) {
      modal.hidden = true;
    }
  }

  function addMessage(topic, message, status) {
    const list = document.getElementById("message-list");
    if (!list) {
      return;
    }

    const item = document.createElement("div");
    item.className = "message-item";
    item.innerHTML = `
      <div class="message-main">
        <span class="message-bullet ${status === "Envoyé" ? "sent" : "received"}"></span>
        <strong>${escapeHtml(message)}</strong>
      </div>
      <div class="message-meta">
        <span>${escapeHtml(topic)}</span>
        <span> - ${escapeHtml(status)}</span>
        <span> - ${nowDateTime()}</span>
      </div>
    `;
    list.prepend(item);
  }

  async function postCommand(command, payload) {
    const url = `${COMMANDS_URL}/${command}`;
    const options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    };

    if (payload) {
      options.body = JSON.stringify(payload);
    }

    addLog("INFO", `${labels[command] || command}: demande envoyée...`);
    const response = await fetch(url, options);
    const text = await response.text();
    let data;

    try {
      data = JSON.parse(text);
    } catch (error) {
      data = { raw: text };
    }

    if (!response.ok || data.ok === false) {
      const reason = data.detail || data.message || data.raw || `HTTP ${response.status}`;
      throw new Error(reason);
    }

    addLog("OK", `${labels[command] || command}: ${data.message || "succès"}`);
    return data;
  }

  async function handleCommandButton(button) {
    const command = button.dataset.command;
    if (!command) {
      return;
    }

    button.disabled = true;
    button.classList.add("is-loading");

    try {
      await postCommand(command);
    } catch (error) {
      addLog("ERROR", `${labels[command] || command}: ${error.message}`);
    } finally {
      button.disabled = false;
      button.classList.remove("is-loading", "is-disabled");
    }
  }

  async function handlePublish(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    const topicInput = document.getElementById("publish-topic");
    const messageInput = document.getElementById("publish-message");
    const button = document.getElementById("submit-publish-message");
    const topic = (topicInput?.value || "temperature").trim();
    const message = (messageInput?.value || "").trim();

    if (!message) {
      addLog("ERROR", "Message vide: rien à envoyer.");
      return;
    }

    if (button) {
      button.disabled = true;
      button.classList.add("is-loading");
    }

    try {
      await postCommand("publish-message", { topic, message });
      addMessage(topic, message, "Envoyé");
      closePublishModal();
      if (messageInput) {
        messageInput.value = "";
      }
    } catch (error) {
      addLog("ERROR", `Envoyer Message: ${error.message}`);
    } finally {
      if (button) {
        button.disabled = false;
        button.classList.remove("is-loading", "is-disabled");
      }
    }
  }

  function wireRescueHandlers() {
    document.querySelectorAll("button[data-command]").forEach((button) => {
      if (button.dataset.rescueWired === "1") {
        return;
      }

      button.dataset.rescueWired = "1";
      button.addEventListener(
        "click",
        function (event) {
          event.preventDefault();
          event.stopPropagation();
          event.stopImmediatePropagation();
          handleCommandButton(button);
        },
        true
      );
    });

    const submitButton = document.getElementById("submit-publish-message");
    if (submitButton && submitButton.dataset.rescueWired !== "1") {
      submitButton.dataset.rescueWired = "1";
      submitButton.addEventListener("click", handlePublish, true);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireRescueHandlers);
  } else {
    wireRescueHandlers();
  }

  window.setInterval(wireRescueHandlers, 1000);
})();
