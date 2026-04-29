// Module MVP pour gérer des appareils MQTT externes.
// Cette couche reste simple: registre local via FastAPI, fiche de connexion,
// statut configuré et suppression. Le but est de rendre le prototype complet
// sans casser le dashboard existant.

(function () {
  const API_ROOT =
    window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : window.location.origin;
  const DEVICE_LIST_URL = API_ROOT + '/api/devices';

  function createStyles() {
    if (document.getElementById('devices-module-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'devices-module-styles';
    style.textContent = `
      .devices-section {
        margin-top: 24px;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        background: #ffffff;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
        padding: 24px;
      }
      .devices-section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 18px;
      }
      .devices-section-title h3 {
        margin: 0;
        font-size: 1.5rem;
        color: #0f172a;
      }
      .devices-section-title p {
        margin: 6px 0 0;
        color: #64748b;
      }
      .devices-grid {
        display: flex;
        gap: 20px;
        align-items: flex-start;
        flex-wrap: wrap;
      }
      .devices-card {
        flex: 1 1 320px;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        background: #f8fafc;
        padding: 18px;
      }
      .devices-card h4 {
        margin: 0 0 14px;
        font-size: 1.05rem;
        color: #0f172a;
      }
      .devices-form {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .devices-form-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }
      .devices-form label {
        display: flex;
        flex-direction: column;
        gap: 6px;
        color: #334155;
        font-size: 0.95rem;
        flex: 1 1 180px;
      }
      .devices-form input,
      .devices-form select,
      .devices-form textarea {
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 12px 14px;
        background: #ffffff;
        color: #0f172a;
        font: inherit;
      }
      .devices-form textarea {
        min-height: 88px;
        resize: vertical;
      }
      .devices-form button,
      .device-item-actions button {
        border: none;
        border-radius: 12px;
        padding: 12px 16px;
        background: linear-gradient(135deg, #6366f1, #7c3aed);
        color: #ffffff;
        font-weight: 700;
        cursor: pointer;
      }
      .device-secondary-button {
        background: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
      }
      .devices-feedback {
        min-height: 22px;
        color: #475569;
        font-size: 0.95rem;
      }
      .device-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .device-item {
        border: 1px solid #dbeafe;
        border-radius: 16px;
        background: #ffffff;
        padding: 16px;
      }
      .device-item-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        flex-wrap: wrap;
      }
      .device-item-title {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .device-item-title strong {
        color: #0f172a;
        font-size: 1rem;
      }
      .device-meta,
      .device-config pre {
        color: #475569;
        font-size: 0.92rem;
      }
      .device-badges {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
      }
      .device-badge {
        border-radius: 999px;
        padding: 6px 10px;
        background: #e0e7ff;
        color: #4338ca;
        font-size: 0.85rem;
        font-weight: 600;
      }
      .device-item-actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 14px;
      }
      .device-config {
        margin-top: 14px;
        border-top: 1px solid #e2e8f0;
        padding-top: 14px;
      }
      .device-config pre {
        margin: 8px 0 0;
        background: #0f172a;
        color: #e2e8f0;
        padding: 14px;
        border-radius: 12px;
        overflow: auto;
      }
      .device-empty {
        color: #64748b;
        padding: 18px 0;
      }
      .sidebar-device-link {
        cursor: pointer;
      }
    `;
    document.head.appendChild(style);
  }

  function getDashboardAnchor() {
    return (
      document.querySelector('.messages-section') ||
      document.querySelector('.dashboard-main') ||
      document.querySelector('main') ||
      document.body
    );
  }

  function buildSection() {
    const container = document.getElementById('devices-container');
    if (!container) return;

    container.innerHTML = `
      <div class="devices-section-header">
        <div class="devices-section-title">
          <h3>Appareils MQTT</h3>
          <p>Ajoute un appareil, prépare sa connexion au broker et vérifie sa configuration.</p>
        </div>
      </div>
      <div class="devices-grid">
        <div class="devices-card">
          <h4>Ajouter un appareil</h4>
          <form id="device-form" class="devices-form">
            <div class="devices-form-row">
              <label>
                Nom
                <input id="device-name" name="name" placeholder="ESP32 Salon" required />
              </label>
              <label>
                Type
                <input id="device-type" name="device_type" placeholder="sensor" />
              </label>
            </div>
            <div class="devices-form-row">
              <label>
                Adresse IP / Host
                <input id="device-host" name="host" placeholder="192.168.1.25" />
              </label>
              <label>
                Rôle
                <select id="device-role" name="role">
                  <option value="subscriber">subscriber</option>
                  <option value="publisher">publisher</option>
                  <option value="both">both</option>
                </select>
              </label>
            </div>
            <div class="devices-form-row">
              <label>
                Topics écoute
                <input id="device-topics-sub" name="topics_sub" placeholder="temperature, humidity" />
              </label>
              <label>
                Topics publication
                <input id="device-topics-pub" name="topics_pub" placeholder="temperature/ack" />
              </label>
            </div>
            <label>
              Notes
              <textarea id="device-notes" name="notes" placeholder="Capteur température salon"></textarea>
            </label>
            <button type="submit">Ajouter appareil</button>
            <div id="devices-feedback" class="devices-feedback"></div>
          </form>
        </div>
        <div class="devices-card">
          <h4>Liste des appareils</h4>
          <div id="device-list" class="device-list">
            <div class="device-empty">Chargement des appareils...</div>
          </div>
        </div>
      </div>
    `;
    return container;
  }

  function formatConfigBlock(config) {
    return [
      `Broker : ${config.broker_host}`,
      `Port : ${config.broker_port}`,
      `Topic principal : ${config.primary_topic}`,
      '',
      'Exemple subscribe :',
      config.subscribe_example,
      '',
      'Exemple publish :',
      config.publish_example,
    ].join('\n');
  }

  async function loadDeviceConfig(deviceId) {
    const response = await fetch(
      API_ROOT + '/api/devices/' + encodeURIComponent(deviceId) + '/mqtt-config',
    );
    return response.json();
  }

  async function loadDeviceStatus(deviceId) {
    const response = await fetch(
      API_ROOT + '/api/devices/' + encodeURIComponent(deviceId) + '/status',
    );
    return response.json();
  }

  async function deleteDevice(deviceId) {
    await fetch(API_ROOT + '/api/devices/' + encodeURIComponent(deviceId), {
      method: 'DELETE',
    });
  }

  function renderDevice(device, listElement) {
    const item = document.createElement('article');
    item.className = 'device-item';
    item.innerHTML = `
      <div class="device-item-header">
        <div class="device-item-title">
          <strong>${escapeHtml(device.name || 'Appareil MQTT')}</strong>
          <span class="device-meta">${escapeHtml(device.type || 'generic')} • ${escapeHtml(device.host || 'host non renseigné')}</span>
        </div>
        <span class="device-badge">${escapeHtml(device.role || 'subscriber')}</span>
      </div>
      <div class="device-badges">
        ${(device.topics_sub || []).map((topic) => `<span class="device-badge">écoute: ${escapeHtml(topic)}</span>`).join('')}
        ${(device.topics_pub || []).map((topic) => `<span class="device-badge">publie: ${escapeHtml(topic)}</span>`).join('')}
      </div>
      <div class="device-item-actions">
        <button type="button" data-action="config">Voir configuration</button>
        <button type="button" data-action="status" class="device-secondary-button">Voir statut</button>
        <button type="button" data-action="delete" class="device-secondary-button">Supprimer</button>
      </div>
      <div class="device-config" hidden></div>
    `;

    const configPanel = item.querySelector('.device-config');

    item.querySelector('[data-action="config"]').addEventListener('click', async function () {
      configPanel.hidden = false;
      configPanel.innerHTML = '<strong>Chargement de la configuration MQTT...</strong>';
      const result = await loadDeviceConfig(device.id);
      if (!result.ok) {
        configPanel.innerHTML = '<strong>Configuration introuvable.</strong>';
        return;
      }
      configPanel.innerHTML = `
        <strong>Configuration MQTT</strong>
        <pre>${escapeHtml(formatConfigBlock(result.mqtt_config))}</pre>
      `;
    });

    item.querySelector('[data-action="status"]').addEventListener('click', async function () {
      configPanel.hidden = false;
      configPanel.innerHTML = '<strong>Vérification du statut...</strong>';
      const result = await loadDeviceStatus(device.id);
      if (!result.ok) {
        configPanel.innerHTML = '<strong>Statut introuvable.</strong>';
        return;
      }
      configPanel.innerHTML = `
        <strong>État appareil</strong>
        <pre>${escapeHtml(
          [
            `State : ${result.status.state}`,
            `Broker : ${result.status.mqtt_host}`,
            `Port : ${result.status.mqtt_port}`,
            `Broker ready : ${result.status.broker_ready ? 'oui' : 'non'}`,
            `Dernière trace : ${result.status.last_seen || 'n/a'}`,
          ].join('\n'),
        )}</pre>
      `;
    });

    item.querySelector('[data-action="delete"]').addEventListener('click', async function () {
      if (!window.confirm(`Supprimer l'appareil "${device.name}" ?`)) {
        return;
      }
      await deleteDevice(device.id);
      await refreshDevices();
    });

    listElement.appendChild(item);
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function refreshDevices() {
    const listElement = document.getElementById('device-list');
    if (!listElement) {
      return;
    }

    listElement.innerHTML = '<div class="device-empty">Chargement des appareils...</div>';

    try {
      const response = await fetch(DEVICE_LIST_URL);
      const result = await response.json();
      listElement.innerHTML = '';

      if (!result.ok || !Array.isArray(result.items) || result.items.length === 0) {
        listElement.innerHTML =
          '<div class="device-empty">Aucun appareil enregistré pour le moment.</div>';
        return;
      }

      result.items.forEach((device) => renderDevice(device, listElement));
    } catch (error) {
      listElement.innerHTML =
        '<div class="device-empty">Impossible de charger les appareils.</div>';
    }
  }

  function serializeFormToPayload(form) {
    const payload = {};
    new FormData(form).forEach((value, key) => {
      payload[key] = String(value);
    });
    return payload;
  }

  function wireForm() {
    const form = document.getElementById('device-form');
    const feedback = document.getElementById('devices-feedback');
    if (!form || !feedback) {
      return;
    }

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      feedback.textContent = "Ajout de l'appareil en cours...";

      try {
        const payload = serializeFormToPayload(form);
        const response = await fetch(DEVICE_LIST_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const result = await response.json();

        if (!result.ok) {
          feedback.textContent = "Impossible d'ajouter l'appareil.";
          return;
        }

        feedback.textContent = 'Appareil ajouté avec succès.';
        form.reset();
        await refreshDevices();
      } catch (error) {
        feedback.textContent = "Erreur réseau pendant l'ajout de l'appareil.";
      }
    });
  }

  function initDevicesModule() {
    createStyles();
    buildSection();
    wireForm();
    refreshDevices();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDevicesModule);
  } else {
    initDevicesModule();
  }
})();
