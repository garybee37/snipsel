export async function subscribeToPushNotifications() {
    console.log('[Push] Starting subscription flow...');
    if (!('serviceWorker' in navigator)) {
        throw new Error('Service workers are not supported.')
    }
    if (!('PushManager' in window)) {
        throw new Error('Push notifications are not supported.')
    }

    console.log('[Push] Requesting permission...');
    const permission = await Notification.requestPermission()
    console.log('[Push] Permission result:', permission);
    if (permission !== 'granted') {
        throw new Error('Notification permission denied.')
    }

    console.log('[Push] Waiting for service worker ready...');
    const registration = await navigator.serviceWorker.ready
    console.log('[Push] Service worker ready:', registration);

    console.log('[Push] Fetching VAPID public key...');
    // Fetch VAPID public key
    const response = await fetch('/api/notifications/vapid-public-key')
    if (!response.ok) {
        throw new Error('Failed to fetch VAPID public key. Status: ' + response.status)
    }
    const { vapidPublicKey } = await response.json()
    console.log('[Push] Got VAPID public key:', vapidPublicKey);

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

    console.log('[Push] Subscribing via PushManager...');
    const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedVapidKey,
    })
    console.log('[Push] Created push subscription:', subscription);

    console.log('[Push] Sending subscription to backend...');
    const subResponse = await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ subscription }),
    })
    console.log('[Push] Backend subscribe response status:', subResponse.status);

    if (!subResponse.ok) {
        throw new Error('Failed to save subscription on server.')
    }

    return subscription
}

export async function unsubscribeFromPushNotifications() {
    console.log('[Push] Starting unsubscribe flow...');
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        return
    }

    console.log('[Push] Waiting for service worker ready...');
    const registration = await navigator.serviceWorker.ready
    console.log('[Push] Service worker ready, getting subscription...');
    const subscription = await registration.pushManager.getSubscription()
    console.log('[Push] Current subscription:', subscription);

    if (subscription) {
        console.log('[Push] Unsubscribing locally...');
        await subscription.unsubscribe()

        console.log('[Push] Unsubscribing from backend...');
        const res = await fetch('/api/notifications/unsubscribe', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ endpoint: subscription.endpoint }),
        })
        console.log('[Push] Backend unsubscribe status:', res.status);
    }
}

export async function checkPushSubscription() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        return false
    }

    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    console.log('[Push] checkPushSubscription result: ', !!subscription);
    return !!subscription
}
