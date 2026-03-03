<script lang="ts">
  interface Props {
    title: string;
    message: string;
    confirmLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
  }

  let { title, message, confirmLabel = 'Löschen', onConfirm, onCancel }: Props = $props();

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      onConfirm();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-all"
  role="dialog"
  aria-modal="true"
  aria-labelledby="delete-modal-title"
  tabindex="-1"
  onclick={(e) => e.target === e.currentTarget && onCancel()}
>
  <div class="w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/10 p-6">
    <div class="flex flex-col items-center text-center">
      <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </div>
      
      <h2 id="delete-modal-title" class="text-xl font-bold text-slate-900 dark:text-slate-100">
        {title}
      </h2>
      
      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
        {message}
      </p>

      <div class="mt-8 flex w-full flex-col gap-3 sm:flex-row-reverse">
        <button
          type="button"
          class="flex h-11 flex-1 items-center justify-center rounded-xl bg-red-600 px-4 font-semibold text-white transition-all hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:bg-red-700 dark:hover:bg-red-600 sm:flex-initial sm:min-w-[100px]"
          onclick={onConfirm}
        >
          {confirmLabel}
        </button>
        <button
          type="button"
          class="flex h-11 flex-1 items-center justify-center rounded-xl bg-slate-100 px-4 font-medium text-slate-600 transition-colors hover:bg-slate-200 focus:outline-none dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 sm:flex-initial sm:min-w-[100px]"
          onclick={onCancel}
        >
          Abbrechen
        </button>
      </div>
    </div>
  </div>
</div>
