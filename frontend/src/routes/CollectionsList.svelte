<script lang="ts">
  import { api, type Collection } from '../lib/api';
  import { collections, currentView, isLoading, pendingReference } from '../lib/stores';

  let showCreate = false;
  let newTitle = '';
  let newIcon = '🗒';
  let busy = false;

  type Filter = 'all' | 'favorites' | 'day' | 'normal';
  let filter: Filter = 'all';
  let titleFilter = '';

  function matchesFilter(c: Collection, f: Filter): boolean {
    if (f === 'favorites') return Boolean(c.is_favorite);
    if (f === 'day') return Boolean(c.list_for_day);
    if (f === 'normal') return !c.list_for_day;
    return true;
  }

  function matchesTitle(c: Collection, qRaw: string): boolean {
    const q = qRaw.trim().toLowerCase();
    if (!q) return true;
    return c.title.toLowerCase().includes(q);
  }

  $: filtered = $collections.filter((c) => matchesFilter(c, filter) && matchesTitle(c, titleFilter));

  async function loadCollections() {
    isLoading.set(true);
    try {
      const res = await api.collections.list();
      collections.set(res.collections);
    } finally {
      isLoading.set(false);
    }
  }

  async function openCollection(c: Collection) {
    const pending = $pendingReference;
    if (pending) {
      for (const id of pending.snipselIds) {
        await api.snipsels.reference(c.id, id);
        if (pending.mode === 'move' && pending.fromCollectionId) {
          await api.snipsels.delete(pending.fromCollectionId, id);
        }
      }
      pendingReference.set(null);
      currentView.set({ type: 'collection', id: c.id });
      return;
    }
    currentView.set({ type: 'collection', id: c.id });
  }

  function editCollection(c: Collection) {
    currentView.set({ type: 'collection_settings', id: c.id });
  }

  async function createCollection() {
    if (!newTitle.trim()) return;
    busy = true;
    try {
      const res = await api.collections.create({ title: newTitle.trim(), icon: newIcon || '🗒' });
      collections.update((list) => [res.collection, ...list]);
      showCreate = false;
      newTitle = '';
      newIcon = '🗒';
    } finally {
      busy = false;
    }
  }

  $: if ($collections.length === 0) {
    loadCollections();
  }
</script>

<div class="space-y-2">
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-semibold">Collections</h2>
      <button
        class="rounded-md bg-slate-900 px-4 py-3 text-lg font-medium text-white"
        type="button"
        onclick={() => (showCreate = true)}
      >
        + New
      </button>
    </div>

    <div class="flex flex-col gap-3 rounded-lg border bg-white p-3">
      <div class="flex flex-wrap gap-2">
        <button
          class="rounded-md border px-4 py-2 text-base {filter === 'all' ? 'bg-slate-100 font-medium' : 'bg-white'}"
          type="button"
          onclick={() => (filter = 'all')}
        >
          All
        </button>
        <button
          class="rounded-md border px-4 py-2 text-base {filter === 'favorites' ? 'bg-slate-100 font-medium' : 'bg-white'}"
          type="button"
          onclick={() => (filter = 'favorites')}
        >
          Favorites
        </button>
        <button
          class="rounded-md border px-4 py-2 text-base {filter === 'day' ? 'bg-slate-100 font-medium' : 'bg-white'}"
          type="button"
          onclick={() => (filter = 'day')}
        >
          Days
        </button>
        <button
          class="rounded-md border px-4 py-2 text-base {filter === 'normal' ? 'bg-slate-100 font-medium' : 'bg-white'}"
          type="button"
          onclick={() => (filter = 'normal')}
        >
          Lists
        </button>
      </div>

      <input
        class="w-full rounded-md border px-4 py-3 text-lg"
        type="search"
        placeholder="Filter by title"
        bind:value={titleFilter}
      />
    </div>
  </div>

  {#if showCreate}
    <form
      class="rounded-lg border bg-slate-50 p-3"
      onsubmit={(e) => {
        e.preventDefault();
        createCollection();
      }}
    >
      <div class="mb-2 flex gap-2">
        <input
          class="w-16 rounded-md border px-2 py-1.5 text-center text-lg"
          bind:value={newIcon}
          maxlength={2}
          placeholder="📋"
        />
        <input
          class="flex-1 rounded-md border px-4 py-3 text-lg"
          bind:value={newTitle}
          placeholder="Collection title"
        />
      </div>
      <div class="flex gap-2">
        <button
          class="rounded-md bg-slate-900 px-4 py-3 text-lg font-medium text-white"
          type="submit"
          disabled={busy || !newTitle.trim()}
        >
          Create
        </button>
        <button
          class="rounded-md border px-4 py-3 text-lg"
          type="button"
          onclick={() => (showCreate = false)}
        >
          Cancel
        </button>
      </div>
    </form>
  {/if}

  {#if $isLoading}
    <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
  {:else if filtered.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">No collections yet</div>
  {:else}
    <div class="space-y-3">
      {#each filtered as c}
        <div class="flex w-full items-center gap-4 rounded-lg border bg-white px-4 py-4">
          <button class="flex flex-1 items-center gap-3 text-left" type="button" onclick={() => openCollection(c)}>
            <span class="text-3xl">{c.icon}</span>
            <span class="flex-1 text-lg font-medium">{c.title}</span>
            {#if c.is_favorite}
              <span class="text-xl" aria-hidden="true">♥</span>
            {/if}
            {#if c.archived}
              <span class="rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-600">archived</span>
            {/if}
          </button>
          <button
            class="grid h-12 w-12 place-items-center rounded-md border text-xl text-slate-700 hover:bg-slate-50"
            type="button"
            aria-label="Edit collection"
            title="Edit"
            onclick={() => editCollection(c)}
          >
            ⓘ
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>
