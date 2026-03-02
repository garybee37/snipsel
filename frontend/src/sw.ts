/// <reference lib="webworker" />
declare let self: ServiceWorkerGlobalScope

import { precacheAndRoute } from 'workbox-precaching'

// Precache assets built by Vite
precacheAndRoute(self.__WB_MANIFEST || [])

self.addEventListener('push', (event) => {
    console.log('[ServiceWorker] Push event received!', event);
    let data: any = {}
    try {
        data = event.data?.json() ?? {}
        console.log('[ServiceWorker] Push data:', data);
    } catch (err) {
        console.error('[ServiceWorker] Failed to parse push data', err)
    }

    const title = data.title || 'Snipsel Notification'
    const options = {
        body: data.body || '',
        icon: '/pwa-192x192.png',
        badge: '/pwa-192x192.png',
        data: data.url,
    }

    console.log('[ServiceWorker] Showing notification:', title, options);
    event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
    console.log('[ServiceWorker] Notification click received!', event);
    event.notification.close()
    if (event.notification.data) {
        console.log('[ServiceWorker] Opening URL:', event.notification.data);
        event.waitUntil(self.clients.openWindow(event.notification.data))
    }
})
