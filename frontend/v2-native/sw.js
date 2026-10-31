// ORYN Studio V2 migration: retire the old cached UI service worker.
// ORYN itself remains locally hosted on the Raspberry Pi without Internet.
self.addEventListener('install', e => { self.skipWaiting(); });
self.addEventListener('activate', e => {
  e.waitUntil(Promise.all([
    self.registration.unregister(),
    caches.keys().then(keys => Promise.all(keys.filter(k => k.toLowerCase().includes('oryn') || k.toLowerCase().includes('workbox')).map(k => caches.delete(k))))
  ]));
});
