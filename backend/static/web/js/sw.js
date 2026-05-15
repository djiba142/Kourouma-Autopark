/**
 * sw.js — Service Worker BSG Dashboard
 * Mode hors ligne : cache les pages principales
 * Sync automatique au retour de connexion
 */

const CACHE_NAME    = 'bsg-cache-v1';
const OFFLINE_URL   = '/offline/';

// Pages à mettre en cache immédiatement
const PRECACHE = [
  '/',
  '/dashboard/',
  '/commandes/',
  '/stock/',
  '/clients/',
  '/offline/',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
];

// ── Installation ──────────────────────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE.map(url => new Request(url, { cache: 'reload' })))
        .catch(err => console.warn('[SW] Précache partiel :', err));
    })
  );
  self.skipWaiting();
});

// ── Activation — supprime les anciens caches ──────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Interception des requêtes ─────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const req = event.request;

  // Ne pas intercepter les requêtes POST (formulaires, API)
  if (req.method !== 'GET') return;

  // Ne pas intercepter les requêtes vers d'autres domaines que CDN autorisés
  const url = new URL(req.url);
  const allowedHosts = ['cdn.jsdelivr.net', 'unpkg.com'];
  if (url.origin !== self.location.origin && !allowedHosts.includes(url.hostname)) return;

  event.respondWith(
    fetch(req)
      .then(response => {
        // Mettre en cache la réponse fraîche
        if (response && response.status === 200 && response.type === 'basic') {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, responseClone));
        }
        return response;
      })
      .catch(() => {
        // Hors ligne : essayer le cache
        return caches.match(req).then(cached => {
          if (cached) return cached;
          // Page HTML non cachée → page offline
          if (req.headers.get('accept')?.includes('text/html')) {
            return caches.match(OFFLINE_URL);
          }
        });
      })
  );
});

// ── Background Sync — envoi des formulaires en attente ───────────────────────
self.addEventListener('sync', event => {
  if (event.tag === 'sync-ventes') {
    event.waitUntil(syncVentesEnAttente());
  }
});

async function syncVentesEnAttente() {
  // Les ventes créées hors ligne sont stockées dans IndexedDB
  // et envoyées ici au retour de connexion
  try {
    const db = await openDB();
    const tx = db.transaction('pending_ventes', 'readwrite');
    const store = tx.objectStore('pending_ventes');
    const ventes = await store.getAll();

    for (const vente of ventes) {
      try {
        await fetch('/vente-directe/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(vente),
        });
        await store.delete(vente.id);
      } catch (e) {
        console.warn('[SW] Sync vente échouée, réessai plus tard');
      }
    }
  } catch (e) {
    console.warn('[SW] Background sync :', e);
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('bsg-offline', 1);
    req.onupgradeneeded = e => {
      e.target.result.createObjectStore('pending_ventes', { keyPath: 'id', autoIncrement: true });
    };
    req.onsuccess = e => resolve(e.target.result);
    req.onerror   = e => reject(e.target.error);
  });
}
