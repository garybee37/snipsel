import { idbGetSyncQueue, idbRemoveSync } from './db';
import { requestJson } from './api';

let syncInProgress = false;

export async function processSyncQueue() {
    if (syncInProgress) return;
    if (!navigator.onLine) return; // Only process if online

    syncInProgress = true;
    try {
        const queue = await idbGetSyncQueue();
        for (const op of queue) {
            if (!navigator.onLine) break; // Network went down during sync

            try {
                await requestJson(op.endpoint, {
                    method: op.method,
                    body: op.body ? JSON.stringify(op.body) : undefined,
                });

                // Success -> remove from queue
                await idbRemoveSync(op.id);
            } catch (err: any) {
                // If the error is a controlled ApiError (400, 403, 404), drop it to unblock queue.
                if (err?.error?.code && err.error.code !== 'network_error' && err.error.code !== 'unknown_error') {
                    console.warn('[Sync Queue] Dropping failed operation (client error)', op, err);
                    await idbRemoveSync(op.id);
                } else {
                    // Network error or 500, we keep it to retry later
                    console.error('[Sync Queue] Transient error, stopping queue processing', op, err);
                    break;
                }
            }
        }
    } finally {
        syncInProgress = false;
    }
}

export function initSyncManager() {
    if (typeof window !== 'undefined') {
        window.addEventListener('online', () => {
            processSyncQueue();
        });
        window.addEventListener('snipsel-sync-queued', () => {
            processSyncQueue();
        });

        // Initial run
        setTimeout(processSyncQueue, 1000);
    }
}
