// Bridge for desktop launcher contexts where the embedded page may not have
// a normal http/file origin. We force API calls toward the local FastAPI
// backend and enhance visible message timestamps.

(function () {
  const API_ORIGIN = "http://127.0.0.1:8000";
  const originalFetch = window.fetch.bind(window);

  function rewriteUrl(url) {
    if (typeof url !== "string") {
      return url;
    }

    if (url.startsWith(API_ORIGIN)) {
      return url;
    }

    if (
      url === "/health" ||
      url === "/logs" ||
      url.startsWith("/api/") ||
      url.startsWith("/health?") ||
      url.startsWith("/logs?")
    ) {
      return API_ORIGIN + url;
    }

    if (
      url === "health" ||
      url === "logs" ||
      url.startsWith("api/") ||
      url.startsWith("health?") ||
      url.startsWith("logs?")
    ) {
      return API_ORIGIN + "/" + url;
    }

    if (url.startsWith("null/")) {
      return API_ORIGIN + "/" + url.slice(5);
    }

    if (/^(file|qrc|about|app):/i.test(url)) {
      const match = url.match(/(\/api\/.*|\/health.*|\/logs.*)$/i);
      if (match) {
        return API_ORIGIN + match[1];
      }
    }

    return url;
  }

  window.fetch = function patchedFetch(input, init) {
    if (typeof input === "string") {
      return originalFetch(rewriteUrl(input), init);
    }

    if (input instanceof Request) {
      const rewritten = rewriteUrl(input.url);
      if (rewritten !== input.url) {
        return originalFetch(new Request(rewritten, input), init);
      }
    }

    return originalFetch(input, init);
  };

  function ensureVisibleTimestamp(item) {
    if (!(item instanceof HTMLElement) || item.dataset.timestampEnhanced === "1") {
      return;
    }

    const meta = item.querySelector(".message-meta");
    if (!meta) {
      return;
    }

    const stamp = document.createElement("span");
    stamp.className = "message-timestamp";
    stamp.textContent = " - " + new Date().toLocaleString("fr-FR");
    stamp.style.color = "#64748b";
    stamp.style.fontSize = "0.85rem";
    meta.appendChild(stamp);
    item.dataset.timestampEnhanced = "1";
  }

  function watchMessageList() {
    const list = document.getElementById("message-list");
    if (!list) {
      window.setTimeout(watchMessageList, 500);
      return;
    }

    list.querySelectorAll(".message-item").forEach(ensureVisibleTimestamp);

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof HTMLElement) {
            if (node.matches(".message-item")) {
              ensureVisibleTimestamp(node);
            }
            node.querySelectorAll?.(".message-item").forEach(ensureVisibleTimestamp);
          }
        });
      });
    });

    observer.observe(list, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", watchMessageList);
  } else {
    watchMessageList();
  }
})();
