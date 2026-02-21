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
  <h2 class="text-2xl font-semibold">Todos</h2>

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
