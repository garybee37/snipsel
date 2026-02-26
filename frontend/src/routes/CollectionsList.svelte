<script lang="ts">
  import { api, type Collection } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { collections, collectionAnchor, currentView, isLoading, pendingReference } from '../lib/stores';

  let showCreate = false;
  let newTitle = '';
  let newIcon = '🗒';
  let busy = false;

  type Filter = 'all' | 'favorites' | 'day' | 'mine' | 'shared' | 'templates' | 'archive';
  let filter: Filter = 'favorites';
  let titleFilter = '';

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = hex.trim();
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
    const base = { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  type SortKey = 'modified' | 'name';
  type SortDir = 'desc' | 'asc';
  let sortKey: SortKey = 'modified';
  let sortDir: SortDir = 'desc';

  let didInitialLoad = false;

  function cmpString(a: string, b: string): number {
    return a.localeCompare(b, undefined, { sensitivity: 'base' });
  }

  function sortCollections(list: Collection[], key: SortKey, dirRaw: SortDir): Collection[] {
    const dir = dirRaw === 'asc' ? 1 : -1;
    const copy = [...list];
    copy.sort((a, b) => {
      if (key === 'name') {
        return cmpString(a.title, b.title) * dir;
      }
      const ta = Date.parse(a.modified_at);
      const tb = Date.parse(b.modified_at);
      if (ta === tb) return cmpString(a.title, b.title);
      return (ta - tb) * dir;
    });
    return copy;
  }

  function matchesFilter(c: Collection, f: Filter): boolean {
    if (f === 'archive') return Boolean(c.archived);
    if (c.archived && f !== 'all') return false;
    if (f === 'favorites') return Boolean(c.is_favorite);
    if (f === 'day') return Boolean(c.list_for_day);
    if (f === 'mine') return c.access_level === 'owner' && !c.list_for_day && !c.is_template;
    if (f === 'shared') {
      return (
        c.access_level === 'read' ||
        c.access_level === 'write' ||
        (c.access_level === 'owner' && Boolean(c.shared_out))
      );
    }
    if (f === 'templates') return Boolean(c.is_template);
    return true;
  }

  function matchesTitle(c: Collection, qRaw: string): boolean {
    const q = qRaw.trim().toLowerCase();
    if (!q) return true;
    return c.title.toLowerCase().includes(q);
  }

  $: filtered = sortCollections(
    $collections.filter((c) => matchesFilter(c, filter) && matchesTitle(c, titleFilter)),
    sortKey,
    sortDir
  );

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
      collectionAnchor.set(null);
      currentView.set({ type: 'collection', id: c.id });
      return;
    }
    collectionAnchor.set(null);
    currentView.set({ type: 'collection', id: c.id });
  }

  async function toggleFavorite(c: Collection) {
    const next = !Boolean(c.is_favorite);
    collections.update((list) => list.map((x) => (x.id === c.id ? { ...x, is_favorite: next } : x)));
    try {
      if (next) {
        await api.collections.favorite(c.id);
      } else {
        await api.collections.unfavorite(c.id);
      }
    } catch {
      collections.update((list) => list.map((x) => (x.id === c.id ? { ...x, is_favorite: !next } : x)));
    }
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

  $: if (!didInitialLoad) {
    didInitialLoad = true;
    loadCollections();
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h2 class="flex items-center gap-2 text-2xl font-semibold text-slate-800">
      <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M3 4h6a2 2 0 012 2v14H5a2 2 0 01-2-2V4z" />
        <path d="M13 6a2 2 0 012-2h6v14a2 2 0 01-2 2h-6V6z" />
      </svg>
      <span>Collections</span>
    </h2>
    <button
      class="grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all"
      type="button"
      onclick={() => (showCreate = true)}
      aria-label="New collection"
      title="New collection"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style={`color: ${getAccent()}`}>
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
      </svg>
    </button>
  </div>

  <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5">
    <div class="grid grid-cols-7">
      <button
        class="grid place-items-center py-3 text-sm transition-colors {filter === 'all'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900'}"
        type="button"
        onclick={() => (filter = 'all')}
        style={filter === 'all' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="All"
      >
        <span class="text-xl font-bold leading-none mt-1">*</span>
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'favorites'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900'}"
        type="button"
        onclick={() => (filter = 'favorites')}
        style={filter === 'favorites' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Favs"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'day'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900'}"
        type="button"
        onclick={() => (filter = 'day')}
        style={filter === 'day' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Days"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'mine'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900'}"
        type="button"
        onclick={() => (filter = 'mine')}
        style={filter === 'mine' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="My"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'shared'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900'}"
        type="button"
        onclick={() => (filter = 'shared')}
        style={filter === 'shared' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Shared"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'templates'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900'}"
        type="button"
        onclick={() => (filter = 'templates')}
        style={filter === 'templates' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Templates"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <line x1="3" y1="9" x2="21" y2="9"/>
          <line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
      </button>
      <button
        class="grid place-items-center border-l border-black/5 py-3 text-sm transition-colors {filter === 'archive'
          ? 'text-slate-900'
          : 'text-slate-600 hover:text-slate-900'}"
        type="button"
        onclick={() => (filter = 'archive')}
        style={filter === 'archive' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        title="Archive"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
      </button>
    </div>
  </div>

  <div class="flex items-center gap-3">
    <input
      class="min-w-0 flex-1 rounded-full border border-slate-200 bg-white px-4 py-2 text-base shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20"
      type="search"
      placeholder="Filter by title"
      bind:value={titleFilter}
    />

    <div class="ml-auto flex items-center gap-2">
      <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5">
        <div class="flex">
          <button
            class="px-4 py-2 text-sm font-medium {sortKey === 'modified'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (sortKey = 'modified')}
            style={sortKey === 'modified' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Modified
          </button>
          <button
            class="border-l border-black/5 px-4 py-2 text-sm font-medium {sortKey === 'name'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (sortKey = 'name')}
            style={sortKey === 'name' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Name
          </button>
        </div>
      </div>

      <button
        class="grid h-10 w-10 place-items-center rounded-full border border-slate-200 bg-white text-lg text-slate-700 shadow-sm ring-1 ring-black/5 hover:bg-white transition-all"
        type="button"
        aria-label={sortDir === 'asc' ? 'Sort ascending' : 'Sort descending'}
        title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
        onclick={() => (sortDir = sortDir === 'asc' ? 'desc' : 'asc')}
      >
        {sortDir === 'asc' ? '↑' : '↓'}
      </button>
    </div>
  </div>

  {#if showCreate}
    <form
      class="space-y-4 rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-xl ring-1 ring-black/5 backdrop-blur-md"
      onsubmit={(e) => {
        e.preventDefault();
        createCollection();
      }}
    >
      <div class="flex gap-3">
        <input
          class="w-20 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-center text-2xl shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
          bind:value={newIcon}
          maxlength={2}
          placeholder="📋"
        />
        <input
          class="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-lg shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
          bind:value={newTitle}
          placeholder="Collection title"
        />
      </div>
      <div class="flex gap-2">
        <button
          class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-3 text-base font-bold shadow-sm ring-1 ring-black/5 transition-all hover:bg-slate-50 disabled:opacity-50"
          style={`color: ${getAccent()}`}
          type="submit"
          disabled={busy || !newTitle.trim()}
        >
          {busy ? 'Creating...' : 'Create Collection'}
        </button>
        <button
          class="rounded-full border border-slate-200 bg-white px-6 py-3 text-base font-medium text-slate-600 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-all"
          type="button"
          onclick={() => (showCreate = false)}
        >
          Cancel
        </button>
      </div>
    </form>
  {/if}

  {#if $isLoading}
    <div class="py-8 text-center text-sm text-slate-500 font-medium">Loading collections...</div>
  {:else if filtered.length === 0}
    <div class="py-8 text-center text-sm text-slate-500 font-medium">No collections found</div>
  {:else}
    <div class="space-y-2">
      {#each filtered as c}
        <div class="flex w-full items-center gap-3 px-1 py-2 group">
          <button class="flex flex-1 items-center gap-3 text-left" type="button" onclick={() => openCollection(c)}>
            <span class="text-3xl transition-transform group-hover:scale-110">{c.icon}</span>
            <div class="min-w-0 flex-1">
              <div class="truncate text-lg font-medium text-slate-800">{c.title}</div>
              <div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500">
                {#if c.access_level === 'read' || c.access_level === 'write'}
                  <span class="rounded-full px-2 py-0.5 font-medium" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >shared</span
                  >
                {/if}
                {#if c.archived}
                  <span class="rounded-full px-2 py-0.5 font-medium" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >archived</span
                  >
                {/if}
                {#if c.is_template}
                  <span class="rounded-full px-2 py-0.5 font-medium" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >template</span
                  >
                {/if}
              </div>
            </div>
          </button>

          <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 flex h-11 items-center px-1">
            {#if filter === 'shared'}
              <div
                class="grid h-10 w-10 place-items-center text-lg"
                aria-label={c.access_level === 'owner' && c.shared_out ? 'Shared by you' : 'Shared with you'}
                title={c.access_level === 'owner' && c.shared_out ? 'Shared by you' : 'Shared with you'}
                style={
                  c.access_level === 'owner' && c.shared_out
                    ? `color: ${getAccent()}`
                    : undefined
                }
              >
                {#if c.access_level === 'owner' && c.shared_out}
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M7 11l5-5m0 0l5 5m-5-5v12" />
                  </svg>
                {:else}
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 13l-5 5m0 0l-5-5m5 5V6" />
                  </svg>
                {/if}
              </div>
              <div class="h-6 w-px bg-slate-100 mx-0.5"></div>
            {/if}
            <button
              class="grid h-9 w-9 place-items-center rounded-full text-slate-400 hover:bg-slate-50 transition-colors"
              type="button"
              aria-label={c.is_favorite ? 'Unfavorite' : 'Favorite'}
              title={c.is_favorite ? 'Unfavorite' : 'Favorite'}
              onclick={() => toggleFavorite(c)}
              style={c.is_favorite ? `color: ${getAccent()}` : undefined}
            >
              {#if c.is_favorite}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 fill-current" viewBox="0 0 24 24">
                  <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              {:else}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              {/if}
            </button>
            <div class="h-6 w-px bg-slate-100 mx-0.5"></div>
            <button
              class="grid h-9 w-9 place-items-center rounded-full text-slate-400 hover:bg-slate-50 transition-colors"
              type="button"
              aria-label="Edit collection"
              title="Edit"
              onclick={() => editCollection(c)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
