/**
 * pwa.js — Enregistrement PWA BSG
 * À inclure dans base.html avant </body>
 */
(function () {
  'use strict';

  // ── Enregistrement Service Worker ─────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/web/js/sw.js', { scope: '/' })
        .then(reg => {
          console.log('[BSG PWA] Service Worker actif :', reg.scope);

          // Vérifier les mises à jour toutes les 60 secondes
          setInterval(() => reg.update(), 60000);
        })
        .catch(err => console.warn('[BSG PWA] Enregistrement échoué :', err));
    });
  }

  // ── Détection hors ligne ──────────────────────────────────────────────────
  function updateOnlineStatus() {
    const banner = document.getElementById('bsg-offline-banner');
    if (!banner) return;
    if (navigator.onLine) {
      banner.style.display = 'none';
    } else {
      banner.style.display = 'flex';
    }
  }

  window.addEventListener('online',  updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);

  // Créer le bandeau hors ligne
  window.addEventListener('DOMContentLoaded', () => {
    const banner = document.createElement('div');
    banner.id    = 'bsg-offline-banner';
    banner.style.cssText = `
      display:none;position:fixed;bottom:0;left:0;right:0;z-index:9998;
      background:#c0392b;color:#fff;padding:10px 20px;
      align-items:center;justify-content:center;gap:10px;
      font-size:13px;font-weight:600;
    `;
    banner.innerHTML = `
      <i class="bi bi-wifi-off"></i>
      Vous êtes hors ligne — Les données affichées peuvent être en cache.
      <button onclick="window.location.reload()"
              style="background:rgba(255,255,255,.2);border:none;color:#fff;
                     padding:4px 12px;border-radius:6px;cursor:pointer;font-size:12px">
        Réessayer
      </button>`;
    document.body.appendChild(banner);
    updateOnlineStatus();
  });

  // ── Prompt installation ───────────────────────────────────────────────────
  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();
    deferredPrompt = e;

    // Afficher le bouton d'installation si disponible
    const btn = document.getElementById('bsg-install-btn');
    if (btn) btn.style.display = 'flex';
  });

  window.bsgInstallPWA = function () {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(result => {
      if (result.outcome === 'accepted') {
        console.log('[BSG PWA] Installée sur le device');
      }
      deferredPrompt = null;
      const btn = document.getElementById('bsg-install-btn');
      if (btn) btn.style.display = 'none';
    });
  };

})();
