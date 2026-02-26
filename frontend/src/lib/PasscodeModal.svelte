<script lang="ts">
  import { api, type ApiError } from './api';
  import { setPasscodeUnlocked } from './passcode';
  import { currentUser } from './session';
  import { currentView } from './stores';

  interface Props {
    collectionId: string;
    onSuccess: () => void;
    onCancel: () => void;
  }

  let { collectionId, onSuccess, onCancel }: Props = $props();

  let digits = $state(['', '', '', '']);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let attemptsRemaining = $state<number | null>(null);

  let inputRefs = $state<HTMLInputElement[]>([]);

  async function handleSubmit() {
    if (digits.some((d) => !d)) return;

    loading = true;
    error = null;
    try {
      const res = await api.passcode.verify({
        passcode: digits.join(''),
        collection_id: collectionId
      });

      setPasscodeUnlocked(collectionId, res.unlocked_until);
      onSuccess();
    } catch (e) {
      const apiError = e as ApiError;
      if (apiError.error?.code === 'force_logout') {
        await api.logout();
        currentUser.set(null);
        currentView.set({ type: 'loading' });
        return;
      }

      error = apiError.error?.message || 'Invalid passcode';
      attemptsRemaining = (apiError.error?.details?.attempts_remaining as number) ?? null;
      
      // Clear and refocus
      digits = ['', '', '', ''];
      inputRefs[0]?.focus();
    } finally {
      loading = false;
    }
  }

  function handleInput(index: number, e: Event) {
    const input = e.target as HTMLInputElement;
    const val = input.value.slice(-1);
    
    if (val && /^\d$/.test(val)) {
      digits[index] = val;
      if (index < 3) {
        inputRefs[index + 1]?.focus();
      } else {
        handleSubmit();
      }
    } else {
      digits[index] = '';
    }
  }

  function handleKeyDown(index: number, e: KeyboardEvent) {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs[index - 1]?.focus();
    }
  }

  function handlePaste(e: ClipboardEvent) {
    e.preventDefault();
    const pasteData = e.clipboardData?.getData('text') || '';
    const pasteDigits = pasteData.replace(/\D/g, '').split('').slice(0, 4);
    
    pasteDigits.forEach((digit, i) => {
      if (i < 4) digits[i] = digit;
    });

    if (pasteDigits.length > 0) {
      const nextIndex = Math.min(pasteDigits.length, 3);
      inputRefs[nextIndex]?.focus();
      if (pasteDigits.length >= 4) {
        handleSubmit();
      }
    }
  }
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
  role="dialog"
  aria-modal="true"
>
  <div class="mx-4 w-full max-w-sm rounded-2xl border border-slate-200 bg-white/95 p-8 shadow-2xl ring-1 ring-black/5 backdrop-blur-md">
    <div class="mb-6 flex flex-col items-center">
      <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-slate-900">Protected Collection</h2>
      <p class="mt-1 text-center text-sm text-slate-500">Enter your 4-digit passcode to unlock this collection.</p>
    </div>

    <div class="flex justify-center gap-3" onpaste={handlePaste}>
      {#each digits as digit, i}
        <input
          bind:this={inputRefs[i]}
          type="password"
          inputmode="numeric"
          maxlength="1"
          value={digit}
          class="h-16 w-14 rounded-xl border-2 border-slate-200 bg-white text-center text-2xl font-bold focus:border-indigo-500 focus:outline-none disabled:opacity-50"
          disabled={loading}
          oninput={(e) => handleInput(i, e)}
          onkeydown={(e) => handleKeyDown(i, e)}
        />
      {/each}
    </div>

    {#if error}
      <div class="mt-4 text-center">
        <p class="text-sm font-medium text-red-600">{error}</p>
        {#if attemptsRemaining !== null}
          <p class="mt-1 text-xs text-red-500">{attemptsRemaining} attempts remaining</p>
        {/if}
      </div>
    {/if}

    <div class="mt-8 flex flex-col gap-3">
      <button
        type="button"
        class="flex h-12 items-center justify-center rounded-xl bg-indigo-600 font-semibold text-white transition-all hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
        onclick={handleSubmit}
        disabled={loading || digits.some(d => !d)}
      >
        {#if loading}
          <svg class="h-5 w-5 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        {:else}
          Unlock Collection
        {/if}
      </button>
      
      <button
        type="button"
        class="h-12 rounded-xl font-medium text-slate-600 transition-colors hover:bg-slate-100 focus:outline-none disabled:opacity-50"
        onclick={onCancel}
        disabled={loading}
      >
        Cancel
      </button>
    </div>
  </div>
</div>
