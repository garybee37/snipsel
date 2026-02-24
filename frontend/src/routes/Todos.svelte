<script lang="ts">
  import { api, type SearchSnipselHit } from '../lib/api';
  import { collectionAnchor, currentView, isLoading } from '../lib/stores';
  import { currentUser } from '../lib/session';

  let items: SearchSnipselHit[] = [];

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

  async function load() {
    isLoading.set(true);
    try {
      const res = await api.search({ type: 'task' });
      items = res.snipsels;
    } finally {
      isLoading.set(false);
    }
  }

  async function toggleDone(id: string, current: boolean) {
    collectionAnchor.set(null);
    await api.snipsels.update(id, { task_done: !current });
    await load();
  }

  function openInfo(id: string) {
    collectionAnchor.set(null);
    currentView.set({ type: 'snipsel', id });
  }

  function openInCollection(t: SearchSnipselHit) {
    const collectionId = (t.collection_id ?? '').trim();
    if (!collectionId) {
      openInfo(t.id);
      return;
    }
    currentView.set({ type: 'collection', id: collectionId });
    const pos = typeof t.position === 'number' ? t.position : undefined;
    if (pos) {
      collectionAnchor.set({ collectionId, pos });
    } else {
      collectionAnchor.set({ collectionId, snipselId: t.id });
    }
  }

  load();
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold">
    <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
    </svg>
    <span>Todos</span>
  </h2>

  {#if items.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">No open tasks</div>
  {:else}
    <div class="space-y-2">
      {#each items as t}
        <div class="flex w-full items-center gap-3 px-1 py-2">
          <button
            class="grid h-8 w-8 place-items-center rounded-full border border-slate-300 bg-white"
            type="button"
            aria-label="Mark done"
            title="Done"
            style={`border-color: ${getAccent()}`}
            onclick={() => toggleDone(t.id, false)}
          ></button>

          <button class="min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openInCollection(t)}>
            <div class="min-w-0 flex-1">
              <div class="truncate text-lg font-medium text-slate-900">{t.content_markdown ?? ''}</div>
              <div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500">
                <span class="rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}>
                  {t.collection_icon ? `${t.collection_icon} ` : ''}{t.collection_title ?? 'Collection'}
                </span>
              </div>
            </div>
          </button>

          <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5">
            <div class="flex">
              <button
                class="grid h-11 w-12 place-items-center text-lg text-slate-700 hover:bg-black/5"
                type="button"
                aria-label="Info"
                title="Info"
                onclick={() => openInfo(t.id)}
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
