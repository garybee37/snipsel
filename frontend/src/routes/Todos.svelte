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

<div class="space-y-3">
  <h2 class="text-lg font-semibold">Todos</h2>

  {#if items.length === 0}
    <div class="text-sm text-slate-500">No tasks found</div>
  {:else}
    <div class="space-y-2">
      {#each items as t}
        <div class="flex items-center gap-3 rounded-lg border bg-white px-3 py-2">
          <input type="checkbox" checked={t.task_done} on:change={() => toggleDone(t.id, t.task_done)} />
          <div class="flex-1">
            <div class="text-sm {t.task_done ? 'line-through text-slate-400' : ''}">
              {t.content_markdown ?? ''}
            </div>
            {#if t.done_at}
              <div class="text-xs text-slate-500">Done {new Date(t.done_at).toLocaleString()}</div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
