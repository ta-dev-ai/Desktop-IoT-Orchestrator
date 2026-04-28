// MVP fallback:
// If the dashboard preflight logic becomes too strict and keeps buttons disabled
// even when the backend is ready, we restore clickability here.
// The backend remains the source of truth and will return a real error if needed.

(function () {
  const SELECTORS = [
    'button[data-command]',
    '#open-publish-modal-btn',
    '.command-action button',
  ];

  function unlockButtons() {
    document.querySelectorAll(SELECTORS.join(',')).forEach((button) => {
      if (!(button instanceof HTMLButtonElement)) {
        return;
      }

      button.disabled = false;
      button.removeAttribute('disabled');
      button.classList.remove('is-disabled');
      button.removeAttribute('title');
      button.style.pointerEvents = 'auto';
      button.style.opacity = '';
      button.style.cursor = '';
    });
  }

  function startFallbackUnlock() {
    unlockButtons();
    window.setInterval(unlockButtons, 800);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startFallbackUnlock);
  } else {
    startFallbackUnlock();
  }
})();
