<script lang="ts">
  import { api, type TagCount } from '../lib/api';
  import { currentView, isLoading, searchError, searchQuery, searchResults } from '../lib/stores';

  type Mode = 'tags' | 'mentions';

  let mode = $state<Mode>('tags');
  let items = $state<TagCount[]>([]);
  let loadingList = $state(false);

  async function loadList() {
    loadingList = true;
    try {
      if (mode === 'tags') {
        const res = await api.tags.list();
        items = res.tags;
      } else {
        const res = await api.mentions.list();
        items = res.mentions;
      }
    } finally {
      loadingList = false;
    }
  }

  async function selectToken(name: string) {
    searchQuery.set('');
    searchError.set(null);
    searchResults.set(null);
    currentView.set({ type: 'search' });
    isLoading.set(true);
    try {
      const res = await api.search(mode === 'tags' ? { tag: name } : { mention: name });
      searchResults.set(res);
    } catch {
      searchResults.set(null);
      searchError.set('Search failed');
    } finally {
      isLoading.set(false);
    }
  }

  $effect(() => {
    loadList();
  });
</script>

<div class="space-y-4">
  <h2 class="text-2xl font-semibold">Tags / Mentions</h2>

  <div class="flex rounded-lg border bg-white p-1" role="tablist">
    <button
      type="button"
      role="tab"
      aria-selected={mode === 'tags'}
      class="flex-1 rounded-md px-4 py-3 text-base font-medium transition-colors {mode === 'tags'
        ? 'bg-slate-100 text-slate-900'
        : 'text-slate-600 hover:text-slate-900'}"
      onclick={() => {
        mode = 'tags';
        loadList();
      }}
    >
      <span class="flex items-center justify-center gap-2">
        <span aria-hidden="true">#</span>
        <span>Tags</span>
      </span>
    </button>
    <button
      type="button"
      role="tab"
      aria-selected={mode === 'mentions'}
      class="flex-1 rounded-md px-4 py-3 text-base font-medium transition-colors {mode === 'mentions'
        ? 'bg-slate-100 text-slate-900'
        : 'text-slate-600 hover:text-slate-900'}"
      onclick={() => {
        mode = 'mentions';
        loadList();
      }}
    >
      <span class="flex items-center justify-center gap-2">
        <span aria-hidden="true">@</span>
        <span>Mentions</span>
      </span>
    </button>
  </div>

  {#if loadingList}
    <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
  {:else if items.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">No {mode} yet</div>
  {:else}
    <div class="space-y-2">
      {#each items as it (it.name)}
        <button
          type="button"
          class="w-full rounded-lg border bg-white px-4 py-4 text-left transition-colors hover:bg-slate-50 active:bg-slate-100"
          onclick={() => selectToken(it.name)}
        >
          <div class="flex items-center justify-between gap-3">
            <span class="text-lg font-medium text-slate-900">
              <span class="text-slate-400" aria-hidden="true">{mode === 'tags' ? '#' : '@'}</span>{it.name}
            </span>
            <span class="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600">{it.count}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>
