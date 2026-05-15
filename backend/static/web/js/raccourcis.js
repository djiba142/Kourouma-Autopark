/**
 * raccourcis.js — Raccourcis clavier globaux BSG
 *
 * Touche   Action
 * ─────────────────────────────────────────
 * N        Nouvelle vente directe
 * S        Recherche stock
 * F        Journal financier
 * C        Liste clients
 * A        Liste commandes
 * D        Dashboard
 * ?        Afficher/masquer cet aide
 * Echap    Fermer overlay
 *
 * Désactivé si focus sur <input>, <textarea>, <select>
 */

(function () {
  'use strict';

  const ROUTES = {
    'n': '/vente-directe/',
    's': '/stock/',
    'f': '/finances/rapport/',
    'c': '/clients/',
    'a': '/commandes/',
    'd': '/dashboard/',
  };

  const LABELS = {
    'N': ['Nouvelle Vente', 'bi-cart-plus'],
    'S': ['Inventaire Stock', 'bi-boxes'],
    'F': ['Finances', 'bi-graph-up-arrow'],
    'C': ['Clients', 'bi-people'],
    'A': ['Commandes', 'bi-receipt'],
    'D': ['Dashboard', 'bi-grid-1x2'],
    '?': ['Aide raccourcis', 'bi-keyboard'],
  };

  // ── Overlay aide ──────────────────────────────────────────────────────────
  function createOverlay() {
    const div = document.createElement('div');
    div.id    = 'bsg-shortcuts-overlay';
    div.style.cssText = `
      position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9999;
      display:flex;align-items:center;justify-content:center;
      opacity:0;transition:opacity .15s;pointer-events:none;
    `;
    div.innerHTML = `
      <div style="background:#fff;border-radius:20px;padding:2rem;width:420px;max-width:90vw;
                  box-shadow:0 20px 60px rgba(0,0,0,.3)">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem">
          <h5 style="margin:0;font-weight:700;color:#1a3a5c">
            <i class="bi bi-keyboard me-2"></i>Raccourcis clavier
          </h5>
          <button onclick="closeBsgOverlay()" style="background:none;border:none;font-size:18px;cursor:pointer;color:#6c757d">×</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          ${Object.entries(LABELS).map(([key, [label, icon]]) => `
            <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;
                        background:#f8f9fa;border-radius:10px">
              <kbd style="background:#1a3a5c;color:#fff;border-radius:6px;
                          padding:3px 8px;font-size:12px;font-weight:700;
                          min-width:26px;text-align:center">${key}</kbd>
              <span style="font-size:13px;color:#444">
                <i class="bi ${icon} me-1 text-muted"></i>${label}
              </span>
            </div>
          `).join('')}
        </div>
        <div style="margin-top:1rem;font-size:11px;color:#6c757d;text-align:center">
          Désactivé si vous tapez dans un champ de saisie
        </div>
      </div>`;
    document.body.appendChild(div);
    return div;
  }

  let overlay = null;

  function showOverlay() {
    if (!overlay) overlay = createOverlay();
    overlay.style.pointerEvents = 'auto';
    overlay.style.opacity       = '1';
  }

  window.closeBsgOverlay = function () {
    if (overlay) {
      overlay.style.opacity       = '0';
      overlay.style.pointerEvents = 'none';
    }
  };

  // Fermer en cliquant dehors
  document.addEventListener('click', e => {
    if (overlay && e.target === overlay) closeBsgOverlay();
  });

  // ── Gestionnaire de touches ───────────────────────────────────────────────
  document.addEventListener('keydown', e => {
    // Ignorer si focus sur un champ
    const tag = document.activeElement.tagName;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    const key = e.key.toLowerCase();

    if (e.key === '?') {
      e.preventDefault();
      showOverlay();
      return;
    }

    if (e.key === 'Escape') {
      closeBsgOverlay();
      return;
    }

    if (ROUTES[key]) {
      e.preventDefault();
      window.location.href = ROUTES[key];
    }
  });

  // ── Bouton aide flottant (bas droit) ─────────────────────────────────────
  const fab = document.createElement('button');
  fab.innerHTML = '<i class="bi bi-keyboard"></i>';
  fab.title     = 'Raccourcis clavier (?)';
  fab.style.cssText = `
    position:fixed;bottom:20px;right:20px;z-index:999;
    width:42px;height:42px;border-radius:50%;border:none;
    background:#1a3a5c;color:#fff;font-size:16px;
    box-shadow:0 4px 12px rgba(0,0,0,.2);cursor:pointer;
    display:flex;align-items:center;justify-content:center;
    opacity:.7;transition:opacity .15s;
  `;
  fab.addEventListener('mouseenter', () => fab.style.opacity = '1');
  fab.addEventListener('mouseleave', () => fab.style.opacity = '.7');
  fab.addEventListener('click', showOverlay);
  document.body.appendChild(fab);

})();
