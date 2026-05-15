/**
 * scanner.js — Scan code-barres BSG
 * Utilise QuaggaJS (bibliothèque légère, pas de dépendance native)
 * Intégration dans la vente directe et l'inventaire stock
 *
 * Usage dans un template :
 *   <div id="bsg-scanner-container"></div>
 *   <script src="{% static 'web/js/scanner.js' %}"></script>
 *   <script>BSGScanner.init({ onScan: code => console.log(code) })</script>
 */

const BSGScanner = (function () {
  'use strict';

  let quaggaLoaded = false;
  let scannerActive = false;
  let modal = null;

  // ── Charger QuaggaJS dynamiquement ───────────────────────────────────────
  function loadQuagga() {
    return new Promise((resolve, reject) => {
      if (quaggaLoaded) { resolve(); return; }
      const script    = document.createElement('script');
      script.src      = 'https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js';
      script.onload   = () => { quaggaLoaded = true; resolve(); };
      script.onerror  = () => reject(new Error('QuaggaJS non chargé'));
      document.head.appendChild(script);
    });
  }

  // ── Créer la modale scanner ───────────────────────────────────────────────
  function createModal() {
    const div = document.createElement('div');
    div.id    = 'bsg-scanner-modal';
    div.style.cssText = `
      position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:10000;
      display:flex;flex-direction:column;align-items:center;justify-content:center;
    `;
    div.innerHTML = `
      <div style="color:#fff;font-size:16px;font-weight:700;margin-bottom:16px">
        <i class="bi bi-upc-scan me-2"></i>Scanner un code-barres
      </div>
      <div id="bsg-viewport" style="position:relative;width:min(90vw,360px);height:240px;
                                     border-radius:14px;overflow:hidden;background:#000">
        <video id="bsg-video" style="width:100%;height:100%;object-fit:cover"></video>
        <!-- Viseur -->
        <div style="position:absolute;inset:30px;border:2px solid #e8593c;border-radius:8px;
                    box-shadow:0 0 0 9999px rgba(0,0,0,.4)"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                    color:#e8593c;font-size:11px;font-weight:600;text-align:center;
                    background:rgba(0,0,0,.5);padding:4px 10px;border-radius:6px">
          Centrez le code-barres
        </div>
      </div>
      <div id="bsg-scan-result" style="margin-top:16px;color:#fff;font-size:13px;min-height:24px;
                                        text-align:center"></div>
      <div style="display:flex;gap:10px;margin-top:16px">
        <button id="bsg-scan-manual" onclick="BSGScanner.showManual()"
                style="background:rgba(255,255,255,.15);color:#fff;border:none;
                       padding:10px 20px;border-radius:10px;cursor:pointer;font-size:13px">
          <i class="bi bi-keyboard me-1"></i>Saisie manuelle
        </button>
        <button onclick="BSGScanner.stop()"
                style="background:#e8593c;color:#fff;border:none;
                       padding:10px 20px;border-radius:10px;cursor:pointer;font-size:13px">
          <i class="bi bi-x-circle me-1"></i>Fermer
        </button>
      </div>
      <!-- Saisie manuelle (cachée par défaut) -->
      <div id="bsg-manual-input" style="display:none;margin-top:12px">
        <div style="display:flex;gap:8px">
          <input id="bsg-code-input" type="text" placeholder="Code ou référence produit"
                 style="border-radius:8px;border:none;padding:10px 14px;font-size:14px;width:220px"
                 onkeydown="if(event.key==='Enter')BSGScanner.submitManual()">
          <button onclick="BSGScanner.submitManual()"
                  style="background:#1e8449;color:#fff;border:none;padding:10px 16px;
                         border-radius:8px;cursor:pointer;font-weight:700">OK</button>
        </div>
      </div>
    `;
    document.body.appendChild(div);
    return div;
  }

  // ── API publique ──────────────────────────────────────────────────────────
  let _onScan = null;

  return {

    init: function (options = {}) {
      _onScan = options.onScan || (code => console.log('[BSG Scanner] Code :', code));
    },

    open: async function () {
      if (scannerActive) return;

      try {
        await loadQuagga();
      } catch (e) {
        alert('Impossible de charger le scanner. Vérifiez votre connexion.');
        return;
      }

      modal = createModal();
      scannerActive = true;

      // Petit délai pour que le DOM soit prêt
      setTimeout(() => {
        Quagga.init({
          inputStream: {
            name:        'Live',
            type:        'LiveStream',
            target:      document.getElementById('bsg-viewport'),
            constraints: { facingMode: 'environment', width: 640, height: 480 },
          },
          decoder: {
            readers: ['code_128_reader', 'ean_reader', 'ean_8_reader', 'code_39_reader', 'qr_reader'],
          },
          locate: true,
        }, err => {
          if (err) {
            document.getElementById('bsg-scan-result').textContent =
              'Caméra inaccessible — utilisez la saisie manuelle';
            document.getElementById('bsg-manual-input').style.display = 'block';
            return;
          }
          Quagga.start();
        });

        let lastCode = '';
        let lastTime = 0;

        Quagga.onDetected(result => {
          const code = result.codeResult.code;
          const now  = Date.now();

          // Anti-doublon : ignorer si même code dans les 2 dernières secondes
          if (code === lastCode && now - lastTime < 2000) return;
          lastCode = code;
          lastTime = now;

          document.getElementById('bsg-scan-result').innerHTML =
            `<span style="color:#1e8449;font-weight:700">✓ ${code}</span>`;

          // Vibration courte sur mobile
          if ('vibrate' in navigator) navigator.vibrate(200);

          // Callback + fermeture automatique après 500ms
          setTimeout(() => {
            this.stop();
            if (_onScan) _onScan(code);
          }, 500);
        });
      }, 200);
    },

    stop: function () {
      if (!scannerActive) return;
      try { Quagga.stop(); } catch (e) {}
      if (modal) { modal.remove(); modal = null; }
      scannerActive = false;
    },

    showManual: function () {
      document.getElementById('bsg-manual-input').style.display = 'block';
      document.getElementById('bsg-code-input').focus();
    },

    submitManual: function () {
      const code = document.getElementById('bsg-code-input').value.trim();
      if (!code) return;
      this.stop();
      if (_onScan) _onScan(code);
    },

  };

})();
