/// <reference lib="webworker" />
declare let self: ServiceWorkerGlobalScope

import { precacheAndRoute } from 'workbox-precaching'

// Precache assets built by Vite
precacheAndRoute(self.__WB_MANIFEST || [])

self.addEventListener('push', (event) => {
    let data: any = {}
    try {
        data = event.data?.json() ?? {}
    } catch (err) {
        console.error('Failed to parse push data', err)
    }

    const title = data.title || 'Snipsel Notification'
    const options = {
        body: data.body || '',
        icon: '/pwa-192x192.png',
        badge: '/pwa-192x192.png',
        data: data.url,
    }

    event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
    event.notification.close()
    if (event.notification.data) {
        event.waitUntil(self.clients.openWindow(event.notification.data))
    }
})
