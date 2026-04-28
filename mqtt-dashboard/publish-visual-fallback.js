// Filet de sécurité MVP:
// si la publication réussit mais que l'affichage de droite ne se met pas à jour,
// on ajoute nous-mêmes une ligne visible avec date et heure.

(function () {
  const originalFetch = window.fetch.bind(window);

  function findMessageList() {
    return document.getElementById("message-list");
  }

  function addSentMessage(topic, message) {
    const list = findMessageList();
    if (!list) {
      return;
    }

    const now = new Date();
    const item = document.createElement("div");
    item.className = "message-item";
    item.innerHTML = `
      <div class="message-main">
        <span class="message-bullet sent"></span>
        <strong>${escapeHtml(message)}</strong>
      </div>
      <div class="message-meta">
        <span>${escapeHtml(topic)}</span>
        <span> - Envoyé</span>
        <span> - ${now.toLocaleString("fr-FR")}</span>
      </div>
    `;

    list.prepend(item);
  }

  function closeModalIfOpen() {
    const modal = document.getElementById("publish-modal");
    if (modal) {
      modal.hidden = true;
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  window.fetch = async function patchedPublishFetch(input, init) {
    const response = await originalFetch(input, init);

    try {
      const url = typeof input === "string" ? input : input?.url || "";
      const isPublishCall =
        url.includes("/api/commands/publish-message") &&
        ((init && init.method === "POST") || !init?.method);

      if (!isPublishCall || !response.ok) {
        return response;
      }

      let topic = "temperature";
      let message = "";

      if (init && typeof init.body === "string") {
        try {
          const payload = JSON.parse(init.body);
          topic = payload.topic || topic;
          message = payload.message || message;
        } catch (error) {
          console.warn("Payload publish illisible", error);
        }
      }

      if (message) {
        addSentMessage(topic, message);
        closeModalIfOpen();
      }
    } catch (error) {
      console.warn("Fallback affichage publish échoué", error);
    }

    return response;
  };
})();
