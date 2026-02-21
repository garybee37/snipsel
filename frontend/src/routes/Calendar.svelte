<script lang="ts">
  import { api } from '../lib/api';
  import { currentCollection, currentView, isLoading, toLocalIsoDay } from '../lib/stores';

  let cursor = $state(new Date());

  let dayCollections = $state<Set<string>>(new Set());

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
      const set = new Set<string>();
      for (const c of res.collections) {
        if (c.list_for_day) set.add(c.list_for_day);
      }
      dayCollections = set;
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
      currentView.set({ type: 'collection', id: res.collection.id });
    } finally {
      isLoading.set(false);
    }
  }

  function isSameLocalDay(a: Date, b: Date) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }

  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
</script>

<div class="space-y-3">
  <div class="flex items-center justify-between">
    <h2 class="text-xl font-semibold">{monthLabel(cursor)}</h2>
    <div class="flex gap-2">
      <button class="rounded-md border px-3 py-2 text-base" type="button" onclick={() => (cursor = addMonths(cursor, -1))}>
        Prev
      </button>
      <button class="rounded-md border px-3 py-2 text-base" type="button" onclick={() => (cursor = new Date())}>
        Today
      </button>
      <button class="rounded-md border px-3 py-2 text-base" type="button" onclick={() => (cursor = addMonths(cursor, 1))}>
        Next
      </button>
    </div>
  </div>

  <div class="grid grid-cols-7 gap-1 text-center text-sm text-slate-500">
    {#each weekdays as w}
      <div class="py-1">{w}</div>
    {/each}
  </div>

  <div class="grid grid-cols-7 gap-1">
    {#each getGridDays(cursor) as cell}
      {@const iso = toLocalIsoDay(cell.day)}
      {@const hasCollection = dayCollections.has(iso)}
      {@const isToday = isSameLocalDay(cell.day, new Date())}
      <button
        class="relative aspect-square rounded-lg text-base transition-colors {cell.inMonth
          ? 'bg-white hover:bg-slate-50'
          : 'bg-slate-50 text-slate-400 hover:bg-slate-100'} {isToday ? 'ring-2 ring-indigo-400' : ''}"
        type="button"
        onclick={() => openDay(cell.day)}
      >
        <span
          class="mx-auto grid h-12 w-12 place-items-center rounded-full text-base {hasCollection
            ? 'bg-indigo-600 text-white font-semibold'
            : isToday
              ? 'bg-indigo-50 text-indigo-700 font-semibold'
              : cell.inMonth
                ? 'text-slate-800'
                : 'text-slate-400'}"
        >
          {cell.day.getDate()}
        </span>
      </button>
    {/each}
  </div>
</div>
