import { writable, derived } from 'svelte/store';

/**
 * The expiry time of the global grace period.
 */
export const passcodeUnlockedUntil = writable<Date | null>(null);

/**
 * The sticky-unlocked collection ID.
 */
export const passcodeActiveCollectionId = writable<string | null>(null);

/**
 * Derived store that checks if a specific collection is unlocked.
 * A collection is unlocked if:
 * 1. It is the active sticky-unlocked collection.
 * 2. The global grace period has not expired.
 */
export const isPasscodeUnlocked = (collectionId: string) => derived(
    [passcodeUnlockedUntil, passcodeActiveCollectionId],
    ([$unlockedUntil, $activeCollectionId]) => {
        if ($activeCollectionId === collectionId) return true;
        if ($unlockedUntil !== null && new Date() < $unlockedUntil) return true;
        return false;
    }
);

/**
 * Updates the passcode unlock state.
 * @param collectionId The ID of the collection that was unlocked (sticky).
 * @param unlockedUntil ISO timestamp of when the grace period expires.
 */
export function setPasscodeUnlocked(collectionId: string, unlockedUntil: string) {
    passcodeActiveCollectionId.set(collectionId);
    passcodeUnlockedUntil.set(new Date(unlockedUntil));
}

/**
 * Resets the passcode unlock state.
 */
export function clearPasscodeState() {
    passcodeActiveCollectionId.set(null);
    passcodeUnlockedUntil.set(null);
}
