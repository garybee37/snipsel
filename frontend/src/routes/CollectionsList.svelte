<script lang="ts">
  import { api, type Collection } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { collections, currentView, isLoading, pendingReference } from '../lib/stores';

  let showCreate = false;
  let newTitle = '';
  let newIcon = '🗒';
  let busy = false;

  type Filter = 'all' | 'favorites' | 'day' | 'mine' | 'shared' | 'templates';
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
      // modified
      const ta = Date.parse(a.modified_at);
      const tb = Date.parse(b.modified_at);
      if (ta === tb) return cmpString(a.title, b.title);
      return (ta - tb) * dir;
    });
    return copy;
  }

  function matchesFilter(c: Collection, f: Filter): boolean {
    if (f === 'favorites') return Boolean(c.is_favorite);
    if (f === 'day') return Boolean(c.list_for_day);
    if (f === 'mine') return c.access_level === 'owner';
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
      currentView.set({ type: 'collection', id: c.id });
      return;
    }
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

  $: if ($collections.length === 0) {
    loadCollections();
  }
</script>

<div class="space-y-2">
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h2 class="flex items-center gap-2 text-2xl font-semibold">
        <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M3 4h6a2 2 0 012 2v14H5a2 2 0 01-2-2V4z" />
          <path d="M13 6a2 2 0 012-2h6v14a2 2 0 01-2 2h-6V6z" />
        </svg>
        <span>Collections</span>
      </h2>
      <button
        class="rounded-md bg-slate-900 px-4 py-3 text-lg font-medium text-white"
        type="button"
        onclick={() => (showCreate = true)}
      >
        + New
      </button>
    </div>

    <div class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="overflow-hidden rounded-full border border-slate-200 bg-white">
        <div class="grid grid-cols-6">
          <button
            class="px-3 py-3 text-sm font-medium transition-colors {filter === 'all'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (filter = 'all')}
            style={filter === 'all' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            All
          </button>
          <button
            class="border-l border-black/5 px-3 py-3 text-sm font-medium transition-colors {filter === 'favorites'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (filter = 'favorites')}
            style={filter === 'favorites' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Favs
          </button>
          <button
            class="border-l border-black/5 px-3 py-3 text-sm font-medium transition-colors {filter === 'day'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (filter = 'day')}
            style={filter === 'day' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Days
          </button>
          <button
            class="border-l border-black/5 px-3 py-3 text-sm font-medium transition-colors {filter === 'mine'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (filter = 'mine')}
            style={filter === 'mine' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            My
          </button>
          <button
            class="border-l border-black/5 px-3 py-3 text-sm font-medium transition-colors {filter === 'shared'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (filter = 'shared')}
            style={filter === 'shared' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Shared
          </button>
          <button
            class="border-l border-black/5 px-3 py-3 text-sm font-medium transition-colors {filter === 'templates'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => (filter = 'templates')}
            style={filter === 'templates' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Templates
          </button>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <input
          class="min-w-0 flex-1 rounded-full border border-slate-200 bg-white/80 px-4 py-3 text-lg shadow-sm outline-none ring-1 ring-black/5"
          type="search"
          placeholder="Filter by title"
          bind:value={titleFilter}
        />

        <div class="ml-auto flex items-center gap-2">
          <div class="overflow-hidden rounded-full border border-slate-200 bg-white">
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
            class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 bg-white/80 text-lg text-slate-700 shadow-sm ring-1 ring-black/5 hover:bg-white"
            type="button"
            aria-label={sortDir === 'asc' ? 'Sort ascending' : 'Sort descending'}
            title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
            onclick={() => (sortDir = sortDir === 'asc' ? 'desc' : 'asc')}
          >
            {sortDir === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>
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
    <div class="space-y-2">
      {#each filtered as c}
        <div class="flex w-full items-center gap-3 px-1 py-2">
          <button class="flex flex-1 items-center gap-3 text-left" type="button" onclick={() => openCollection(c)}>
            <span class="text-3xl">{c.icon}</span>
            <div class="min-w-0 flex-1">
              <div class="truncate text-lg font-medium">{c.title}</div>
              <div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500">
                {#if c.access_level === 'read' || c.access_level === 'write'}
                  <span class="rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >shared</span
                  >
                {/if}
                {#if c.archived}
                  <span class="rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >archived</span
                  >
                {/if}
                {#if c.is_template}
                  <span class="rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
                    >template</span
                  >
                {/if}
              </div>
            </div>
          </button>

          <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5">
            <div class="flex">
              {#if filter === 'shared'}
                <div
                  class="grid h-11 w-12 place-items-center text-lg"
                  aria-label={c.access_level === 'owner' && c.shared_out ? 'Shared by you' : 'Shared with you'}
                  title={c.access_level === 'owner' && c.shared_out ? 'Shared by you' : 'Shared with you'}
                  style={
                    c.access_level === 'owner' && c.shared_out
                      ? `color: ${getAccent()}`
                      : undefined
                  }
                >
                  {#if c.access_level === 'owner' && c.shared_out}
                    ⇪
                  {:else}
                    ⇩
                  {/if}
                </div>
              {/if}
              <button
                class="grid h-11 w-12 place-items-center text-lg text-slate-700 hover:bg-black/5"
                type="button"
                aria-label={c.is_favorite ? 'Unfavorite' : 'Favorite'}
                title={c.is_favorite ? 'Unfavorite' : 'Favorite'}
                onclick={() => toggleFavorite(c)}
                style={c.is_favorite ? `color: ${getAccent()}` : undefined}
              >
                {c.is_favorite ? '♥' : '♡'}
              </button>
              <button
                class="grid h-11 w-12 place-items-center border-l border-black/5 text-lg text-slate-700 hover:bg-black/5"
                type="button"
                aria-label="Edit collection"
                title="Edit"
                onclick={() => editCollection(c)}
              >
                ⓘ
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
