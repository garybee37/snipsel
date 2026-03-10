<script lang="ts">
  import { api, type Collection, type Snipsel } from '../lib/api';
  import { currentView } from '../lib/stores';

  let deletedCollections = $state<Collection[]>([]);
  let deletedSnipsels = $state<Snipsel[]>([]);
  let isBusy = $state(false);
  let errorMsg = $state('');
  
  let activeTab: 'collections' | 'snipsels' = $state('collections');

  async function loadTrash() {
    isBusy = true;
    errorMsg = '';
    try {
      const [colRes, snipRes] = await Promise.all([
        api.collections.trash(),
        api.snipsels.trash()
      ]);
      deletedCollections = colRes.collections;
      deletedSnipsels = snipRes.snipsels;
    } catch (err: any) {
      errorMsg = err.error?.message || 'Failed to load deleted items';
    } finally {
      isBusy = false;
    }
  }

  async function restoreCollection(id: string) {
    isBusy = true;
    errorMsg = '';
    try {
      await api.collections.restore(id);
      deletedCollections = deletedCollections.filter(c => c.id !== id);
    } catch (err: any) {
      errorMsg = err.error?.message || 'Failed to restore collection';
    } finally {
      isBusy = false;
    }
  }

  async function restoreSnipsel(id: string) {
    isBusy = true;
    errorMsg = '';
    try {
      // Find today's collection ID to restore snipsel into
      const res = await api.collections.today();
      await api.snipsels.restore(id, res.collection.id);
      deletedSnipsels = deletedSnipsels.filter(s => s.id !== id);
    } catch (err: any) {
      errorMsg = err.error?.message || 'Failed to restore snipsel';
    } finally {
      isBusy = false;
    }
  }

  function formatDate(dateString: string | null | undefined) {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    });
  }

  $effect(() => {
    loadTrash();
  });
</script>

<div class="space-y-4">
  <div class="flex items-center gap-2">
    <button
      class="rounded-full p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
      onclick={() => currentView.set({ type: 'settings' })}
      title="Back to Settings"
      aria-label="Back to Settings"
    >
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
    </button>
    <h2 class="flex items-center gap-2 text-2xl font-semibold">
      <svg class="h-6 w-6 text-slate-700 dark:text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="3 6 5 6 21 6" />
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      </svg>
      <span>Recycle Bin</span>
    </h2>
  </div>

  {#if errorMsg}
    <div class="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
      {errorMsg}
    </div>
  {/if}

  <div class="flex gap-4 border-b border-slate-200 dark:border-slate-800">
    <button
      class="px-4 py-2 text-sm font-medium border-b-2 {activeTab === 'collections' ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}"
      onclick={() => activeTab = 'collections'}
    >
      Collections ({deletedCollections.length})
    </button>
    <button
      class="px-4 py-2 text-sm font-medium border-b-2 {activeTab === 'snipsels' ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}"
      onclick={() => activeTab = 'snipsels'}
    >
      Snipsels ({deletedSnipsels.length})
    </button>
  </div>

  <div class="mt-4">
    {#if activeTab === 'collections'}
      {#if deletedCollections.length === 0}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">No deleted collections found.</div>
      {:else}
        <div class="grid gap-3 sm:grid-cols-2">
          {#each deletedCollections as col (col.id)}
            <div class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div class="min-w-0 flex-1 pl-2">
                <div class="flex items-center gap-2">
                  <span class="text-xl">{col.icon}</span>
                  <span class="truncate font-medium text-slate-900 dark:text-slate-100">{col.title}</span>
                </div>
                <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Deleted: {formatDate((col as any).deleted_at)}
                </div>
              </div>
              <button
                class="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                onclick={() => restoreCollection(col.id)}
                disabled={isBusy}
              >
                Restore
              </button>
            </div>
          {/each}
        </div>
      {/if}
    {:else}
      {#if deletedSnipsels.length === 0}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">No deleted snipsels found.</div>
      {:else}
        <div class="grid gap-3 sm:grid-cols-2">
          {#each deletedSnipsels as snip (snip.id)}
            <div class="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div class="min-w-0 flex-1 pl-2">
                <div class="line-clamp-2 text-sm text-slate-900 dark:text-slate-100">
                  {snip.content_markdown || '(Empty)'}
                </div>
                <div class="mt-1 flex gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span class="uppercase tracking-wide">[{snip.type}]</span>
                  <span>Deleted: {formatDate((snip as any).deleted_at)}</span>
                </div>
              </div>
              <button
                class="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                onclick={() => restoreSnipsel(snip.id)}
                disabled={isBusy}
                title="Restores to Today's collection"
              >
                Restore
              </button>
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</div>
