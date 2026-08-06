// MODO DESARROLLO: Caché desactivada para que los cambios se vean inmediatamente.

self.addEventListener('install', event => {
    self.skipWaiting(); // Forzar actualización inmediata
});

self.addEventListener('activate', event => {
    // Borrar absolutamente todas las cachés antiguas de Lovo
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    return caches.delete(cacheName);
                })
            );
        }).then(() => {
            return self.clients.claim(); // Tomar control inmediato
        })
    );
});

self.addEventListener('fetch', event => {
    const CACHE_NAME = 'inventario-lovo-v4';
    // Siempre ir a la red, nunca devolver de la caché (ideal para desarrollo)
    event.respondWith(
        fetch(event.request).catch(() => {
            // Si no hay internet, fallar limpiamente (en producción pondríamos offline support)
            return new Response("App en modo desarrollo: Requiere conexión.");
        })
    );
});
