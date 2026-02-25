<script lang="ts">
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults, searchType } from '../lib/stores';
  import { getCurrentUrl } from '../lib/router';
  import { currentUser } from '../lib/session';

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

  function openSnipsel(id: string) {
    collectionAnchor.set(null);
    currentView.set({ type: 'snipsel', id, returnTo: getCurrentUrl() });
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  const filters = [
    { label: 'All', value: undefined },
    { label: 'Notes', value: 'text' },
    { label: 'Images', value: 'image' },
    { label: 'Files', value: 'attachment' },
    { label: 'Tasks', value: 'task' },
  ];
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold">
    <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
    <span>Search</span>
  </h2>

  <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5">
    <div class="grid grid-cols-5">
      {#each filters as f}
        <button
          class="px-2 py-3 text-xs font-medium transition-colors border-l first:border-l-0 border-black/5 {$searchType === f.value ? 'text-slate-900' : 'text-slate-600 hover:text-slate-900'}"
          type="button"
          onclick={() => searchType.set(f.value)}
          style={$searchType === f.value ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
        >
          {f.label}
        </button>
      {/each}
    </div>
  </div>

  {#if $searchError}
    <div class="rounded-xl border border-red-200 bg-red-50/50 p-4 text-base text-red-700 backdrop-blur-md">
      {$searchError}
    </div>
  {/if}

  {#if $isLoading && !$searchResults}
    <div class="py-12 text-center text-slate-500">Searching...</div>
  {:else if $searchResults}
    <div class="space-y-3">
      <div class="flex items-center justify-between px-1">
        <div class="text-xs font-medium uppercase tracking-wider text-slate-500">
          Results for "{$searchQuery.trim() || '—'}"
        </div>
        <div class="text-xs text-slate-400">
          {$searchResults.snipsels.length} found
        </div>
      </div>

      {#if $searchResults.snipsels.length === 0}
        <div class="rounded-xl border border-slate-200 bg-white/80 p-8 text-center text-slate-500 backdrop-blur-md">
          No matches found
        </div>
      {:else}
        <div class="space-y-2">
          {#each $searchResults.snipsels as s (s.id)}
            <div class="flex w-full items-center gap-3 px-1 py-2">
              <button class="min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openSnipsel(s.id)}>
                <div class="min-w-0 flex-1">
                  <div class="line-clamp-2 text-lg font-medium text-slate-900">{s.content_markdown || '(No content)'}</div>
                  <div class="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                    <span class="font-semibold uppercase tracking-tight" style={`color: ${getAccent()}`}>{s.type}</span>
                    <span class="opacity-30">|</span>
                    <span>{formatDate(s.modified_at)}</span>
                  </div>
                </div>
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="py-12 text-center text-slate-500">
      Type a query in the header and press Enter to start searching.
    </div>
  {/if}
</div>
