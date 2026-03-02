export async function subscribeToPushNotifications() {
    if (!('serviceWorker' in navigator)) {
        throw new Error('Service workers are not supported.')
    }
    if (!('PushManager' in window)) {
        throw new Error('Push notifications are not supported.')
    }

    const permission = await Notification.requestPermission()
    if (permission !== 'granted') {
        throw new Error('Notification permission denied.')
    }

    const registration = await navigator.serviceWorker.ready

    // Fetch VAPID public key
    const response = await fetch('/api/notifications/vapid-public-key')
    if (!response.ok) {
        throw new Error('Failed to fetch VAPID public key.')
    }
    const { vapidPublicKey } = await response.json()

    function urlBase64ToUint8Array(base64String: string) {
        const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')

        const rawData = window.atob(base64)
        const outputArray = new Uint8Array(rawData.length)

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i)
        }
        return outputArray
    }

    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey)

    const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedVapidKey,
    })

    const subResponse = await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ subscription }),
    })

    if (!subResponse.ok) {
        throw new Error('Failed to save subscription on server.')
    }

    return subscription
}

export async function unsubscribeFromPushNotifications() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        return
    }

    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()

    if (subscription) {
        await subscription.unsubscribe()

        await fetch('/api/notifications/unsubscribe', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ endpoint: subscription.endpoint }),
        })
    }
}

export async function checkPushSubscription() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        return false
    }

    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    return !!subscription
}
