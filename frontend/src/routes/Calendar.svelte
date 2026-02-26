<script lang="ts">
  import { api } from '../lib/api';
  import { collectionAnchor, currentCollection, currentView, isLoading, toLocalIsoDay } from '../lib/stores';
  import { currentUser } from '../lib/session';

  let cursor = $state(new Date());
  let dayCollections = $state<Map<string, { icon: string | null }>>(new Map());

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

  function startOfMonth(d: Date) {
    return new Date(d.getFullYear(), d.getMonth(), 1);
  }

  function addMonths(d: Date, delta: number) {
    return new Date(d.getFullYear(), d.getMonth() + delta, 1);
  }

  function monthLabel(d: Date) {
    return d.toLocaleString(undefined, { month: 'long', year: 'numeric' });
  }

  function getGridDays(d: Date): Array<{ day: Date; inMonth: boolean }> {
    const first = startOfMonth(d);
    const start = new Date(first);
    const weekday = (start.getDay() + 6) % 7;
    start.setDate(start.getDate() - weekday);

    const out: Array<{ day: Date; inMonth: boolean }> = [];
    for (let i = 0; i < 42; i += 1) {
      const day = new Date(start);
      day.setDate(start.getDate() + i);
      out.push({ day, inMonth: day.getMonth() === d.getMonth() });
    }
    return out;
  }

  async function loadHighlights() {
    isLoading.set(true);
    try {
      const res = await api.collections.list(true);
      const map = new Map<string, { icon: string | null }>();
      for (const c of res.collections) {
        if (c.list_for_day) map.set(c.list_for_day, { icon: c.icon });
      }
      dayCollections = map;
    } finally {
      isLoading.set(false);
    }
  }

  $effect(() => {
    void cursor;
    loadHighlights();
  });

  async function openDay(day: Date) {
    const iso = toLocalIsoDay(day);
    isLoading.set(true);
    try {
      const res = await api.collections.today(iso);
      currentCollection.set(res.collection);
      collectionAnchor.set(null);
      currentView.set({ type: 'collection', id: res.collection.id });
    } finally {
      isLoading.set(false);
    }
  }

  function isSameLocalDay(a: Date, b: Date) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }

  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  function handleMonthChange(e: Event) {
    const val = (e.currentTarget as HTMLInputElement).value; // YYYY-MM
    if (!val) return;
    const [y, m] = val.split('-').map(Number);
    cursor = new Date(y, m - 1, 1);
  }

  function toMonthValue(d: Date) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    return `${y}-${m}`;
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between gap-3">
    <h2 class="flex items-center gap-2 text-2xl font-semibold">
      <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <path d="M16 2v4" />
        <path d="M8 2v4" />
        <path d="M3 10h18" />
      </svg>
      <span>{monthLabel(cursor)}</span>
    </h2>

    <div class="relative overflow-hidden rounded-full border border-slate-200 bg-white px-3 py-1.5 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 transition-colors">
      <input 
        type="month" 
        class="absolute inset-0 cursor-pointer opacity-0" 
        value={toMonthValue(cursor)} 
        onchange={handleMonthChange}
      />
      <div class="flex items-center gap-2 text-sm font-medium text-slate-600 pointer-events-none">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>Jump to...</span>
      </div>
    </div>
  </div>

  <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5">
    <div class="grid grid-cols-3">
      <button
        class="px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
        type="button"
        onclick={() => (cursor = addMonths(cursor, -1))}
      >
        Prev
      </button>
      <button
        class="border-l border-black/5 px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
        type="button"
        onclick={() => (cursor = new Date())}
      >
        Today
      </button>
      <button
        class="border-l border-black/5 px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
        type="button"
        onclick={() => (cursor = addMonths(cursor, 1))}
      >
        Next
      </button>
    </div>
  </div>

  <div class="grid grid-cols-7 gap-1 text-center text-sm font-medium text-slate-500">
    {#each weekdays as w}
      <div class="py-1">{w}</div>
    {/each}
  </div>

  <div class="grid grid-cols-7 gap-1">
    {#each getGridDays(cursor) as cell}
      {@const iso = toLocalIsoDay(cell.day)}
      {@const collectionData = dayCollections.get(iso)}
      {@const hasCollection = !!collectionData}
      {@const isToday = isSameLocalDay(cell.day, new Date())}
      {@const showIcon = collectionData?.icon && collectionData.icon !== '📅'}
      <button
        class="relative aspect-square rounded-lg text-lg transition-colors {cell.inMonth
          ? 'bg-white hover:bg-slate-50'
          : 'bg-slate-50 text-slate-400 hover:bg-slate-100'}"
        type="button"
        onclick={() => openDay(cell.day)}
        style={isToday ? `box-shadow: inset 0 0 0 2px ${getAccent()}` : undefined}
      >
        {#if showIcon}
          <span class="absolute -right-1 -top-1 flex h-[22px] w-[22px] items-center justify-center rounded-full bg-white text-[12px] shadow-sm ring-1 ring-black/5">
            {collectionData.icon}
          </span>
        {/if}
        <span
          class="mx-auto grid h-10 w-10 place-items-center rounded-full text-base {hasCollection
            ? 'font-semibold'
            : isToday
              ? 'bg-slate-100 font-semibold text-slate-900'
              : cell.inMonth
                ? 'text-slate-800'
                : 'text-slate-400'}"
          style={hasCollection ? `background-color: ${getAccent()}; color: white` : undefined}
        >
          {cell.day.getDate()}
        </span>
      </button>
    {/each}
  </div>
</div>
