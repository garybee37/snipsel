import { idbGetSyncQueue, idbRemoveSync } from './db';
import { requestJson } from './api';

let syncInProgress = false;

export async function processSyncQueue() {
    if (syncInProgress) return;
    if (!navigator.onLine) return; // Only process if online

    syncInProgress = true;
    try {
        const queue = await idbGetSyncQueue();
        const idMap: Record<string, string> = {}; // Maps temp IDs to real server IDs

        for (const op of queue) {
            if (!navigator.onLine) break; // Network went down during sync

            try {
                // Apply ID translations to endpoint and body
                let endpoint = op.endpoint;
                let bodyStr = op.body ? JSON.stringify(op.body) : undefined;

                for (const [tempId, realId] of Object.entries(idMap)) {
                    endpoint = endpoint.replace(tempId, realId);
                    if (bodyStr) {
                        bodyStr = bodyStr.replace(new RegExp(tempId, 'g'), realId);
                    }
                }

                const res = await requestJson<any>(endpoint, {
                    method: op.method,
                    body: bodyStr,
                });

                // If this was a collection creation endpoint, map its ID
                if (op.method === 'POST' && res?.collection?.id && op.endpoint === '/api/collections') {
                    if (op.body && (op.body as any)._tempId) {
                        idMap[(op.body as any)._tempId] = res.collection.id;
                    }
                }

                // If this was a snipsel creation endpoint, map its ID
                if (op.method === 'POST' && res?.item?.snipsel_id && op.endpoint.endsWith('/snipsels')) {
                    // We need to extract the temp ID that was originally generated.
                    // Unfortunately op doesn't store the tempId directly. 
                    // However, we modified api.ts so we can append the tempId to the queue op.
                    if (op.body && (op.body as any)._tempId) {
                        idMap[(op.body as any)._tempId] = res.item.snipsel_id;
                    }
                }

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
