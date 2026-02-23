<script lang="ts">
  import { api, type SearchSnipselHit } from '../lib/api';
  import { isLoading } from '../lib/stores';

  let items: SearchSnipselHit[] = [];

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
    await api.snipsels.update(id, { task_done: !current });
    await load();
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
    <div class="text-base text-slate-500">No tasks found</div>
  {:else}
    <div class="space-y-3">
      {#each items as t}
        <div class="flex items-center gap-4 rounded-lg border bg-white px-4 py-4">
          <input class="h-6 w-6" type="checkbox" checked={t.task_done} on:change={() => toggleDone(t.id, t.task_done)} />
          <div class="flex-1">
            <div class="text-lg {t.task_done ? 'line-through text-slate-400' : ''}">
              {t.content_markdown ?? ''}
            </div>
            {#if t.done_at}
              <div class="mt-1 text-base text-slate-500">Done {new Date(t.done_at).toLocaleString()}</div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
