<script lang="ts">
  import { api, type Collection, type Snipsel } from '../lib/api';
  import { currentView } from '../lib/stores';
  import { currentUser } from '../lib/session';

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = (hex || '').trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    return {
      r: parseInt(v.slice(0, 2), 16),
      g: parseInt(v.slice(2, 4), 16),
      b: parseInt(v.slice(4, 6), 16),
    };
  }

  function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
    const tt = Math.max(0, Math.min(1, t));
    return {
      r: clampByte(a.r + (b.r - a.r) * tt),
      g: clampByte(a.g + (b.g - a.g) * tt),
      b: clampByte(a.b + (b.b - a.b) * tt),
    };
  }

  function rgba(c: Rgb, alpha: number): string {
    const a = Math.max(0, Math.min(1, alpha));
    return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
  }

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  function getAccentTint(): string {
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : '#ffffff';
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

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

  <div class="flex items-center gap-2">
    <div class="flex flex-1 overflow-hidden rounded-full border border-slate-200 bg-white dark:border-white/10 dark:bg-slate-900" role="tablist">
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'collections'}
        class="flex-1 px-4 py-3 text-base font-medium transition-colors {activeTab === 'collections'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={activeTab === 'collections' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => activeTab = 'collections'}
      >
        Collections ({deletedCollections.length})
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'snipsels'}
        class="flex-1 border-l border-black/5 px-4 py-3 text-base font-medium transition-colors dark:border-white/5 {activeTab === 'snipsels'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        style={activeTab === 'snipsels' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        onclick={() => activeTab = 'snipsels'}
      >
        Snipsels ({deletedSnipsels.length})
      </button>
    </div>
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
